"""Deterministic autonomy supervisor for the Mac Brain (06_AUTONOMY doc 01).

Implements the canonical autonomy control loop from
``docs/plans/06_AUTONOMY/01_AUTONOMY_ARCHITECTURE.md``:

  ingest events → refresh world → expire stale → evaluate goal → check safety
  → information need → select/revise plan → policy approval → execute at most
  one bounded action → verify → update state/memory → schedule next tick.

Hard rules enforced here:

- **One tick executes at most one bounded action.** An unbounded sequence can
  never be emitted from a single tick.
- **Only ``AuthorizedAction`` reaches the executor.** Model/planner output
  produces ``ActionProposal``; only the policy layer (GovernanceGuard) can
  turn it into an ``AuthorizedAction`` (doc 01 Step 6).
- **Leases bound everything.** Every goal, plan and action carries creation,
  deadline, max duration, owner, authority level and retry budget; expired
  leases transition to recovery or safe stop (doc 01 Step 4).
- **Cancellation is idempotent** and propagates; a cancelled action can never
  resume (doc 01 Step 7).
- **Health degrades authority.** A degraded dependency reduces the autonomy
  authority level instead of silently continuing (doc 01 Step 8).
- **Every transition is an immutable event** with event type, goal/plan/skill/
  action refs, authority, reason, cycle and producer (doc 01 Step 5).

The supervisor is fully deterministic: it never spawns threads, never sleeps,
and reads time only from the injected ``SimClock`` (replayable in tests).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol
from uuid import uuid4

# ---------------------------------------------------------------------------
# Autonomy state (canonical: novi.contracts autonomy-state/1.0.0)
# ---------------------------------------------------------------------------


class AutonomyState(str, Enum):
    IDLE = "IDLE"
    OBSERVING = "OBSERVING"
    INTERPRETING = "INTERPRETING"
    GOAL_PENDING = "GOAL_PENDING"
    PLANNING = "PLANNING"
    AWAITING_AUTHORITY = "AWAITING_AUTHORITY"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    RECOVERING = "RECOVERING"
    PAUSED = "PAUSED"
    SAFE_STOP = "SAFE_STOP"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Canonical authority levels (doc 01 Step 2). Order matters: higher index =
# more authority.
AUTHORITY_LEVELS: tuple[str, ...] = (
    "PASSIVE", "ASSISTED", "BOUNDED_AUTONOMY", "SUPERVISED_AUTONOMY", "FULL_LOCAL_AUTONOMY",
)

# Legal state transitions (doc 01 Step 1: every transition has an event).
# Expressed as (source, destination) pairs; anything else is rejected.
_LEGAL_TRANSITIONS: frozenset[tuple[AutonomyState, AutonomyState]] = frozenset({
    (AutonomyState.IDLE, AutonomyState.OBSERVING),
    (AutonomyState.IDLE, AutonomyState.GOAL_PENDING),
    (AutonomyState.OBSERVING, AutonomyState.INTERPRETING),
    (AutonomyState.OBSERVING, AutonomyState.IDLE),
    (AutonomyState.INTERPRETING, AutonomyState.PLANNING),
    (AutonomyState.INTERPRETING, AutonomyState.IDLE),
    (AutonomyState.GOAL_PENDING, AutonomyState.PLANNING),
    (AutonomyState.GOAL_PENDING, AutonomyState.OBSERVING),
    (AutonomyState.GOAL_PENDING, AutonomyState.IDLE),
    (AutonomyState.PLANNING, AutonomyState.AWAITING_AUTHORITY),
    (AutonomyState.PLANNING, AutonomyState.EXECUTING),
    (AutonomyState.PLANNING, AutonomyState.RECOVERING),
    (AutonomyState.PLANNING, AutonomyState.IDLE),
    (AutonomyState.OBSERVING, AutonomyState.PLANNING),
    (AutonomyState.AWAITING_AUTHORITY, AutonomyState.EXECUTING),
    (AutonomyState.AWAITING_AUTHORITY, AutonomyState.PLANNING),
    (AutonomyState.AWAITING_AUTHORITY, AutonomyState.PAUSED),
    (AutonomyState.EXECUTING, AutonomyState.VERIFYING),
    (AutonomyState.EXECUTING, AutonomyState.RECOVERING),
    (AutonomyState.EXECUTING, AutonomyState.PAUSED),
    (AutonomyState.VERIFYING, AutonomyState.EXECUTING),   # next step
    (AutonomyState.VERIFYING, AutonomyState.PLANNING),    # replan
    (AutonomyState.VERIFYING, AutonomyState.AWAITING_AUTHORITY),  # next step needs approval
    (AutonomyState.VERIFYING, AutonomyState.COMPLETED),
    (AutonomyState.VERIFYING, AutonomyState.FAILED),
    (AutonomyState.VERIFYING, AutonomyState.RECOVERING),
    (AutonomyState.RECOVERING, AutonomyState.PLANNING),
    (AutonomyState.RECOVERING, AutonomyState.IDLE),
    (AutonomyState.RECOVERING, AutonomyState.GOAL_PENDING),
    (AutonomyState.RECOVERING, AutonomyState.SAFE_STOP),
    (AutonomyState.PAUSED, AutonomyState.IDLE),
    (AutonomyState.PAUSED, AutonomyState.RECOVERING),
    (AutonomyState.SAFE_STOP, AutonomyState.IDLE),        # explicit recovery conditions only
    (AutonomyState.COMPLETED, AutonomyState.IDLE),
    (AutonomyState.FAILED, AutonomyState.IDLE),
    (AutonomyState.FAILED, AutonomyState.RECOVERING),
})

# States that can be reached only with a valid, unexpired lease.
_ACTIVE_STATES = frozenset({AutonomyState.PLANNING, AutonomyState.EXECUTING, AutonomyState.VERIFYING})

# Recoverable states: an episode ending here can continue next tick.
_RECOVERABLE_STATES = frozenset({
    AutonomyState.IDLE, AutonomyState.OBSERVING, AutonomyState.INTERPRETING,
    AutonomyState.GOAL_PENDING, AutonomyState.PLANNING, AutonomyState.AWAITING_AUTHORITY,
    AutonomyState.EXECUTING, AutonomyState.VERIFYING, AutonomyState.RECOVERING,
    AutonomyState.PAUSED,
})

# Terminal states (an episode cannot continue from here without a reset).
_TERMINAL_STATES = frozenset({AutonomyState.SAFE_STOP, AutonomyState.COMPLETED, AutonomyState.FAILED})


# ---------------------------------------------------------------------------
# Simulated clock (replayable; doc 11 Phase 1 item 8)
# ---------------------------------------------------------------------------


class SimClock:
    """Deterministic cycle counter; the only time source the supervisor uses."""

    def __init__(self, *, start: int = 0) -> None:
        self._cycle = int(start)

    @property
    def cycle(self) -> int:
        return self._cycle

    def tick(self, n: int = 1) -> int:
        self._cycle += int(n)
        return self._cycle


# ---------------------------------------------------------------------------
# Records (shapes follow the frozen autonomy contracts)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Lease:
    """Bounds an active goal/plan/action (doc 01 Step 4)."""

    lease_id: str
    owner: str                    # goal_id / plan_id / action authorization_id
    authority_level: str
    created_cycle: int
    deadline_cycle: int           # hard deadline; 0 = none
    max_duration_cycles: int      # 0 = none
    retry_budget: int = 0

    def expired(self, cycle: int) -> bool:
        if self.deadline_cycle and cycle > self.deadline_cycle:
            return True
        return bool(self.max_duration_cycles and cycle - self.created_cycle > self.max_duration_cycles)


class CancellationToken:
    """Idempotent cancellation (doc 01 Step 7). Cancelled can never un-cancel."""

    def __init__(self) -> None:
        self._cancelled = False
        self.cancelled_at_cycle: int | None = None

    def cancel(self, cycle: int) -> None:
        if not self._cancelled:
            self._cancelled = True
            self.cancelled_at_cycle = cycle

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    def snapshot(self) -> dict[str, Any]:
        return {"cancelled": self._cancelled, "cancelled_at_cycle": self.cancelled_at_cycle}


@dataclass(frozen=True)
class AutonomyEvent:
    """Immutable event for every autonomy transition (doc 01 Step 5)."""

    event_id: str
    event_type: str
    cycle: int
    reason: str
    producer: str
    state: str = ""
    goal_id: str = ""
    plan_id: str = ""
    skill_id: str = ""
    action_ref: str = ""
    authority: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id, "event_type": self.event_type, "cycle": self.cycle,
            "reason": self.reason, "producer": self.producer, "state": self.state,
            "goal_id": self.goal_id, "plan_id": self.plan_id, "skill_id": self.skill_id,
            "action_ref": self.action_ref, "authority": self.authority,
        }


@dataclass(frozen=True)
class AuthorizedAction:
    """The only object the executor may consume (doc 01 Step 6)."""

    authorization_id: str
    action: str
    parameters: dict[str, Any]
    proposal_ref: str
    grant_ref: str
    authority_level: str
    issued_cycle: int
    expires_cycle: int
    idempotency_key: str

    def expired(self, cycle: int) -> bool:
        return cycle > self.expires_cycle


@dataclass(frozen=True)
class VerificationResult:
    verification_id: str
    target_ref: str
    method: str
    status: str                       # PASS | FAIL | INCONCLUSIVE | UNVERIFIABLE
    observed_evidence: dict[str, Any]
    error: str = ""

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


@dataclass(frozen=True)
class ActionResult:
    result_id: str
    action_ref: str
    outcome: str                      # SUCCESS | PARTIAL | FAILED | TIMEOUT | CANCELLED | UNVERIFIED
    cycle: int
    observed_effects: dict[str, Any] = field(default_factory=dict)
    verification: VerificationResult | None = None
    error: str = ""

    @property
    def succeeded(self) -> bool:
        return self.outcome == "SUCCESS"


@dataclass(frozen=True)
class AutonomyHealth:
    health_id: str
    cycle: int
    overall_status: str               # HEALTHY | DEGRADED | UNAVAILABLE
    components: dict[str, str] = field(default_factory=dict)  # name -> healthy|degraded|unavailable

    @property
    def degraded(self) -> bool:
        return self.overall_status != "HEALTHY"

    def snapshot(self) -> dict[str, Any]:
        return {
            "health_id": self.health_id, "cycle": self.cycle,
            "overall_status": self.overall_status,
            "components": dict(self.components),
        }


# ---------------------------------------------------------------------------
# Collaborator protocols (deterministic fakes in tests; real wiring later)
# ---------------------------------------------------------------------------


class Executor(Protocol):
    """Executes an authorized action against the world/body."""

    def execute(self, action: AuthorizedAction, *, cycle: int) -> ActionResult: ...


class Verifier(Protocol):
    """Verifies an executed action's effect against expected outcomes."""

    def verify(self, action: AuthorizedAction, result: ActionResult, *, cycle: int) -> VerificationResult: ...


class WorldState(Protocol):
    """Ground truth provider: observations, freshness, expiry."""

    def refresh(self, *, cycle: int) -> dict[str, Any]: ...
    def expire_stale(self, *, cycle: int) -> list[str]: ...
    def needs_information(self, goal: Any, *, cycle: int) -> bool: ...


class GoalSource(Protocol):
    """Provides the current goal and records its terminal status."""

    def active_goal(self, *, cycle: int) -> Any | None: ...
    def complete_goal(self, goal_id: str, status: str, *, cycle: int) -> None: ...


class PlannerLike(Protocol):
    """Builds/advances plans. (brain.Planner satisfies this shape.)"""

    def plan(self, goal: Any, *, cycle: int) -> Any: ...
    def start(self, plan: Any) -> None: ...
    def advance(self, plan: Any) -> Any | None: ...
    def fail(self, plan: Any, *, reason: str) -> None: ...
    def cancel(self, plan: Any) -> None: ...
    def replan(self, goal: Any, *, cycle: int) -> Any: ...


class Proposer(Protocol):
    """Turns the next plan step into an ActionProposal."""

    def propose(self, step: Any, *, goal_id: str, plan_id: str, cycle: int) -> Any: ...


# ---------------------------------------------------------------------------
# The supervisor
# ---------------------------------------------------------------------------


class AutonomySupervisor:
    """Deterministic 12-step autonomy loop (doc 01 Step 3)."""

    def __init__(
        self,
        *,
        clock: SimClock | None = None,
        executor: Executor,
        verifier: Verifier,
        world: WorldState,
        goals: GoalSource,
        planner: PlannerLike,
        proposer: Proposer,
        guard: Any,                          # GovernanceGuard-compatible evaluate()/confirm()
        authority_level: str = "BOUNDED_AUTONOMY",
        max_action_retries: int = 2,
        action_timeout_cycles: int = 10,
        max_events: int = 2048,
        health_checker: Any | None = None,   # callable(cycle) -> AutonomyHealth; None = healthy
    ) -> None:
        self.clock = clock or SimClock()
        self.executor = executor
        self.verifier = verifier
        self.world = world
        self.goals = goals
        self.planner = planner
        self.proposer = proposer
        self.guard = guard
        self.max_action_retries = max_action_retries
        self.action_timeout_cycles = action_timeout_cycles
        self._health_checker = health_checker

        self.state = AutonomyState.IDLE
        self.authority = authority_level
        self._inbox: list[AutonomyEvent] = []
        # Bounded ledger: oldest spill first, spills counted (never silent).
        self._max_events = max(1, int(max_events))
        self._events: list[AutonomyEvent] = []
        self._dropped_events = 0
        self._goal: Any | None = None
        self._plan: Any | None = None
        self._plan_lease: Lease | None = None
        self._active_action: AuthorizedAction | None = None
        self._action_lease: Lease | None = None
        self._cancel: CancellationToken | None = None
        self._retries_left: int = 0
        self._planner_failures: int = 0
        self._health: AutonomyHealth | None = None
        self._pending_proposal: Any | None = None
        self._pending_grant: Any | None = None
        self._confirmed_grant: Any | None = None
        self._executed_count = 0
        self._unauthorized_attempts = 0
        self._tick_count = 0
        self._finished: bool = False

    # ---- event / audit API (doc 01 Step 5) ----

    def _emit(self, event_type: str, *, reason: str, producer: str, **refs: str) -> AutonomyEvent:
        event = AutonomyEvent(
            event_id=f"evt-{uuid4().hex[:12]}",
            event_type=event_type,
            cycle=self.clock.cycle,
            reason=reason,
            producer=producer,
            state=self.state.value,
            goal_id=refs.get("goal_id", ""),
            plan_id=refs.get("plan_id", ""),
            skill_id=refs.get("skill_id", ""),
            action_ref=refs.get("action_ref", ""),
            authority=refs.get("authority", self.authority),
        )
        self._events.append(event)
        overflow = len(self._events) - self._max_events
        if overflow > 0:
            del self._events[:overflow]
            self._dropped_events += overflow
        return event

    def post(self, event: AutonomyEvent) -> None:
        """Ingest an external event (step 1 of the tick)."""
        self._inbox.append(event)

    @property
    def events(self) -> tuple[AutonomyEvent, ...]:
        return tuple(self._events)

    @property
    def dropped_events(self) -> int:
        """Ledger spills so far (bounded-memory accounting, never silent)."""
        return self._dropped_events

    @property
    def executed_count(self) -> int:
        return self._executed_count

    @property
    def unauthorized_attempts(self) -> int:
        return self._unauthorized_attempts

    @property
    def tick_count(self) -> int:
        return self._tick_count

    @property
    def finished(self) -> bool:
        return self._finished

    @property
    def active_action(self) -> AuthorizedAction | None:
        return self._active_action

    def health(self) -> AutonomyHealth | None:
        return self._health

    # ---- state machine (doc 01 Step 1: legal transitions only) ----

    def _transition(self, destination: AutonomyState, *, reason: str, producer: str) -> bool:
        source = self.state
        if source is destination:
            return True
        if (source, destination) not in _LEGAL_TRANSITIONS:
            self._emit("TRANSITION_REJECTED", reason=reason, producer=producer)
            return False
        self.state = destination
        self._emit("STATE_CHANGED", reason=reason, producer=producer)
        return True

    # ---- cancellation (doc 01 Step 7) ----

    def cancel(self, *, reason: str = "operator_cancel") -> None:
        """Idempotent cancellation: propagates to the current action/plan/goal."""
        if self._cancel is not None and self._cancel.cancelled:
            return
        if self._cancel is None:
            self._cancel = CancellationToken()
        self._cancel.cancel(self.clock.cycle)
        self._emit("CANCELLED", reason=reason, producer="operator")
        # Propagate to planner-level state.
        if self._plan is not None:
            self.planner.cancel(self._plan)

    def _force_state(self, destination: AutonomyState, *, reason: str, producer: str) -> None:
        """Emergency transitions bypass the table (doc 08: e-stop may interrupt any state)."""
        self.state = destination
        self._emit("STATE_CHANGED", reason=reason, producer=producer)

    def _cancelled(self) -> bool:
        return self._cancel is not None and self._cancel.cancelled

    def emergency_stop(self, *, reason: str = "emergency_stop") -> None:
        """Enter SAFE_STOP from any state (doc 08 Step 6 semantics).

        Cancels the active goal and blocks the loop; only an explicit
        ``reset()`` (recovery conditions met) re-enters IDLE.
        """
        self.cancel(reason=reason)
        if self._goal is not None:
            self.goals.complete_goal(self._goal.goal_id, "cancelled", cycle=self.clock.cycle)
        self._force_state(AutonomyState.SAFE_STOP, reason=reason, producer="safety_monitor")
        self._emit("EMERGENCY_STOP", reason=reason, producer="safety_monitor")
        self._active_action = None
        self._action_lease = None

    def reset(self) -> None:
        """Explicit recovery conditions satisfied: back to IDLE (doc 08 Step 6)."""
        if self.state is not AutonomyState.SAFE_STOP and self.state is not AutonomyState.FAILED:
            return
        self.state = AutonomyState.IDLE
        self._cancel = None
        self._goal = None
        self._plan = None
        self._plan_lease = None
        self._active_action = None
        self._action_lease = None
        self._retries_left = 0
        self._finished = False
        self._emit("RESET", reason="recovery_conditions_met", producer="supervisor")

    # ---- health (doc 01 Step 8) ----

    def _check_health(self) -> AutonomyHealth:
        if self._health_checker is None:
            return AutonomyHealth(health_id=f"h-{self.clock.cycle}", cycle=self.clock.cycle,
                                  overall_status="HEALTHY", components={"safety_monitor": "healthy"})
        health = self._health_checker(self.clock.cycle)
        self._health = health
        # Degraded dependencies reduce authority (never silently continue).
        if health.overall_status == "UNAVAILABLE" and self.authority != "PASSIVE":
            self.authority = "PASSIVE"
            self._emit("AUTHORITY_REDUCED", reason="health_unavailable", producer="supervisor")
        elif health.overall_status == "DEGRADED" and self.authority == "SUPERVISED_AUTONOMY":
            self.authority = "BOUNDED_AUTONOMY"
            self._emit("AUTHORITY_REDUCED", reason="health_degraded", producer="supervisor")
        elif health.overall_status == "DEGRADED" and self.authority == "BOUNDED_AUTONOMY":
            self.authority = "ASSISTED"
            self._emit("AUTHORITY_REDUCED", reason="health_degraded", producer="supervisor")
        return health

    # ---- the 12-step tick (doc 01 Step 3) ----

    def tick(self, *, max_actions_per_tick: int = 1) -> dict[str, Any]:
        """Run exactly one autonomy cycle. Never more than one action executes."""
        self._tick_count += 1
        cycle = self.clock.cycle
        # SAFE_STOP blocks the autonomy loop until explicit recovery conditions
        # are met via reset() (doc 08 Step 6: never auto-resume).
        if self.state is AutonomyState.SAFE_STOP:
            return self.snapshot()

        # 1. ingest new events
        while self._inbox:
            event = self._inbox.pop(0)
            self._emit("EVENT_INGESTED", reason=event.event_type, producer="inbox",
                       goal_id=event.goal_id, action_ref=event.action_ref)

        # 2. refresh world state
        try:
            self.world.refresh(cycle=cycle)
        except Exception as exc:  # deterministic fault-injection surface
            self._transition(AutonomyState.RECOVERING, reason=f"world_refresh_failed: {exc}", producer="world")
            return self._end_tick(cycle)

        # 3. expire stale observations
        try:
            self.world.expire_stale(cycle=cycle)
        except Exception as exc:
            self._transition(AutonomyState.RECOVERING, reason=f"world_expiry_failed: {exc}", producer="world")
            return self._end_tick(cycle)

        # 8b. health before anything that moves (check safety conditions)
        health = self._check_health()
        if health.overall_status == "UNAVAILABLE":
            # Emergency bypass: any state -> SAFE_STOP (doc 08 Step 6).
            if self._goal is not None:
                self.goals.complete_goal(self._goal.goal_id, "cancelled", cycle=cycle)
            self._force_state(AutonomyState.SAFE_STOP, reason="health_unavailable", producer="supervisor")
            self._emit("EMERGENCY_STOP", reason="health_unavailable", producer="supervisor")
            self._finished = True
            return self._end_tick(cycle)

        # 4. evaluate active goal
        goal = self.goals.active_goal(cycle=cycle)
        if goal is None:
            if self.state not in (AutonomyState.IDLE, AutonomyState.OBSERVING, AutonomyState.PAUSED):
                self._transition(AutonomyState.IDLE, reason="no_active_goal", producer="goal_manager")
            self._goal = None
            self._plan = None
            return self._end_tick(cycle)

        # A completed/failed episode followed by a fresh goal is a new episode
        # (multi-goal streams; the supervisor is not permanently finished).
        if self._finished:
            self._finished = False
            self._emit("EPISODE_START", reason="new_goal", producer="goal_manager",
                       goal_id=goal.goal_id)

        if self._goal is None or self._goal.goal_id != goal.goal_id:
            self._goal = goal
            self._transition(AutonomyState.GOAL_PENDING, reason="goal_acquired", producer="goal_manager")
            self._plan = None
            self._plan_lease = None
            self._retries_left = self.max_action_retries
            self._planner_failures = 0

        if self._cancelled():
            self.goals.complete_goal(goal.goal_id, "cancelled", cycle=cycle)
            self._transition(AutonomyState.IDLE, reason="goal_cancelled", producer="supervisor")
            return self._end_tick(cycle)

        # 6. determine whether new information is required
        if self.world.needs_information(goal, cycle=cycle):
            self._transition(AutonomyState.OBSERVING, reason="information_need", producer="supervisor")
            self._emit("PERCEPTION_NEEDED", reason="information_need", producer="supervisor",
                       goal_id=goal.goal_id)
            return self._end_tick(cycle)

        # 7. select/revise plan
        if self._plan is None or self._plan_lease is None or self._plan_lease.expired(cycle):
            try:
                plan = self.planner.plan(goal, cycle=cycle)
            except Exception as exc:
                self._planner_failures += 1
                if self._planner_failures >= 3:
                    # Planner is persistently unavailable for this goal: fail the
                    # goal so the loop stays bounded (RECOVERING is not a loop).
                    self.goals.complete_goal(goal.goal_id, "failed", cycle=cycle)
                    self._transition(AutonomyState.RECOVERING, reason="planner_unavailable", producer="planner")
                else:
                    self._transition(AutonomyState.RECOVERING, reason=f"planner_failed: {exc}", producer="planner")
                return self._end_tick(cycle)
            self._planner_failures = 0
            self._plan = plan
            self.planner.start(plan)
            self._plan_lease = Lease(
                lease_id=f"lease-plan-{uuid4().hex[:8]}", owner=plan.plan_id,
                authority_level=self.authority, created_cycle=cycle,
                deadline_cycle=0, max_duration_cycles=64,
            )
            self._transition(AutonomyState.PLANNING, reason="plan_selected", producer="planner")
            self._emit("PLAN_SELECTED", reason="goal_requires_plan", producer="planner",
                       goal_id=goal.goal_id, plan_id=plan.plan_id)

        plan = self._plan
        assert plan is not None
        step = plan.current_step()
        if step is None:
            self.goals.complete_goal(goal.goal_id, "completed", cycle=cycle)
            self._transition(AutonomyState.COMPLETED, reason="plan_complete", producer="supervisor")
            self._finished = True
            return self._end_tick(cycle)

        # 8. request policy approval (proposal -> grant -> authorized action)
        if self._confirmed_grant is not None and self._pending_proposal is not None:
            # Operator-approved action from a previous AWAITING_AUTHORITY tick.
            proposal = self._pending_proposal
            grant = self._confirmed_grant
            self._pending_proposal = None
            self._confirmed_grant = None
        else:
            proposal = self.proposer.propose(step, goal_id=goal.goal_id, plan_id=plan.plan_id, cycle=cycle)
            grant = self.guard.evaluate(proposal)
        if not grant.is_allowed:
            if grant.decision == "REQUIRE_CONFIRMATION":
                self._pending_proposal = proposal
                self._pending_grant = grant
                self._transition(AutonomyState.AWAITING_AUTHORITY, reason="requires_confirmation", producer="governance")
                self._emit("AWAITING_APPROVAL", reason=grant.reason, producer="governance",
                           goal_id=goal.goal_id, plan_id=plan.plan_id, action_ref=proposal.proposal_id)
                return self._end_tick(cycle)
            self._unauthorized_attempts += 1
            self._emit("ACTION_DENIED", reason=grant.reason, producer="governance",
                       goal_id=goal.goal_id, action_ref=proposal.proposal_id)
            # A denied action is not executable; the plan cannot proceed — fail
            # the goal so the loop stays bounded (no infinite denial loop).
            self.planner.fail(self._plan, reason=grant.reason)
            self.goals.complete_goal(goal.goal_id, "failed", cycle=cycle)
            self._transition(AutonomyState.RECOVERING, reason=f"action_denied: {grant.reason}", producer="governance")
            return self._end_tick(cycle)

        # 9. execute at most one bounded action (lease-checked)
        authorized = AuthorizedAction(
            authorization_id=f"authz-{uuid4().hex[:12]}",
            action=proposal.action,
            parameters=dict(getattr(proposal, "parameters", {})),
            proposal_ref=proposal.proposal_id,
            grant_ref=grant.grant_id,
            authority_level=self.authority,
            issued_cycle=cycle,
            expires_cycle=cycle + self.action_timeout_cycles,
            idempotency_key=f"{proposal.proposal_id}:{cycle}",
        )
        self._active_action = authorized
        self._action_lease = Lease(
            lease_id=f"lease-act-{uuid4().hex[:8]}", owner=authorized.authorization_id,
            authority_level=self.authority, created_cycle=cycle,
            deadline_cycle=authorized.expires_cycle, max_duration_cycles=self.action_timeout_cycles,
        )
        if self._cancelled():
            self._active_action = None
            self._action_lease = None
            return self._end_tick(cycle)

        self._transition(AutonomyState.EXECUTING, reason="authorized_action", producer="supervisor")
        self._emit("ACTION_STARTED", reason=grant.reason, producer="executor",
                   goal_id=goal.goal_id, plan_id=plan.plan_id,
                   action_ref=authorized.authorization_id)

        try:
            result = self.executor.execute(authorized, cycle=cycle)
        except Exception as exc:
            result = ActionResult(
                result_id=f"res-{uuid4().hex[:12]}", action_ref=authorized.authorization_id,
                outcome="FAILED", cycle=cycle, error=f"executor_error: {exc}",
            )
        self._executed_count += 1

        # 10. verify it
        self._transition(AutonomyState.VERIFYING, reason="action_executed", producer="supervisor")
        verification = self.verifier.verify(authorized, result, cycle=cycle)
        result = ActionResult(
            result_id=result.result_id, action_ref=result.action_ref, outcome=result.outcome,
            cycle=result.cycle, observed_effects=result.observed_effects,
            verification=verification, error=result.error,
        )

        # 11. update state and memory
        self._active_action = None
        self._action_lease = None
        if result.succeeded and verification.passed:
            self._emit("ACTION_VERIFIED", reason=verification.method, producer="verifier",
                       goal_id=goal.goal_id, action_ref=authorized.authorization_id)
            self.planner.advance(self._plan)
            self._retries_left = self.max_action_retries
        elif result.outcome in ("TIMEOUT", "FAILED") and self._retries_left > 0:
            self._retries_left -= 1
            self._transition(AutonomyState.RECOVERING, reason="retry_within_budget", producer="supervisor")
            self._emit("ACTION_RETRY", reason=result.error or result.outcome, producer="supervisor",
                       goal_id=goal.goal_id, action_ref=authorized.authorization_id)
        else:
            # Retry budget exhausted, verification failed, or outcome unverifiable:
            # fail the plan and the goal so the loop stays bounded (doc 07 Step 5:
            # repeating a failed action without new information is forbidden).
            self.planner.fail(self._plan, reason=result.error or verification.error or "retry_budget_exhausted")
            self.goals.complete_goal(goal.goal_id, "failed", cycle=cycle)
            self._transition(AutonomyState.RECOVERING, reason="goal_failed", producer="supervisor")
            self._emit("ACTION_FAILED", reason=result.error or verification.error or "unverified",
                       producer="verifier", goal_id=goal.goal_id,
                       action_ref=authorized.authorization_id)

        # 12. schedule the next tick
        return self._end_tick(cycle)

    def _end_tick(self, cycle: int) -> dict[str, Any]:
        # The simulated clock advances every tick (not only action ticks), so
        # leases and timeouts expire on wall-tick time regardless of progress.
        self.clock.tick()
        return self.snapshot()

    def confirm_pending(self, *, cycle: int) -> bool:
        """Operator confirms an AWAITING_AUTHORITY action (doc 08 Step 7)."""
        if self.state is not AutonomyState.AWAITING_AUTHORITY:
            return False
        self._emit("APPROVED", reason="operator_confirmation", producer="operator")
        return True

    def approve(self) -> bool:
        """Resume from AWAITING_AUTHORITY; the confirmed grant is remembered.

        The approval is explicit, scoped to the pending proposal, and cannot be
        transferred to an unrelated action (doc 08 Step 7).
        """
        if self.state is not AutonomyState.AWAITING_AUTHORITY:
            return False
        if self._pending_grant is None:
            return False
        confirmed = self.guard.confirm(self._pending_grant.grant_id)
        if confirmed is None or not confirmed.is_allowed:
            return False
        self._confirmed_grant = confirmed
        self._pending_grant = None
        self._transition(AutonomyState.PLANNING, reason="approved_by_operator", producer="operator")
        return True

    # ---- observation ----

    def snapshot(self) -> dict[str, Any]:
        from .canonical_autonomy import project_supervisor_state
        return {
            "cycle": self.clock.cycle,
            "state": self.state.value,
            "canonical_state": project_supervisor_state(self.state),
            "authority": self.authority,
            "goal_id": self._goal.goal_id if self._goal is not None else None,
            "plan_id": self._plan.plan_id if self._plan is not None else None,
            "tick_count": self._tick_count,
            "executed_count": self._executed_count,
            "unauthorized_attempts": self._unauthorized_attempts,
            "finished": self._finished,
            "cancelled": self._cancelled(),
            "health": self._health.snapshot() if self._health is not None else None,
        }
