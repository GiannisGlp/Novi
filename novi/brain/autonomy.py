"""Bounded autonomy goal layer for the Mac Brain.

Implements a deliberately small, bounded goal model: a goal has a target and a
hard step budget (``max_steps``), and the controller turns that into multi-cycle
virtual-body movement (turn + move-forward). A goal can never move forever:
it either reaches its target within the budget (COMPLETED) or is forced to
FAILED once the budget is exhausted.

This is the autonomy-facing "choose and pursue" layer. It only proposes bounded
actions; Policy/Safety still gates every resulting action via the runtime.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import uuid4


class GoalStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    BLOCKED = "blocked"
    SUPERSEDED = "superseded"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    COMPLETED = "completed"
    FAILED = "failed"


# States from which a goal can be resumed (non-terminal, resumable).
_RESUMABLE_STATES = frozenset({
    GoalStatus.PENDING, GoalStatus.ACTIVE, GoalStatus.PAUSED, GoalStatus.BLOCKED,
})

# Terminal states: a goal in one of these is no longer pursuable.
_TERMINAL_STATES = frozenset({
    GoalStatus.COMPLETED, GoalStatus.FAILED, GoalStatus.SUPERSEDED,
    GoalStatus.CANCELLED, GoalStatus.EXPIRED,
})


@dataclass(frozen=True)
class ConflictResolution:
    """A recorded goal-conflict resolution (canonical authority: doc 04 §Goal Conflicts)."""
    resolution_id: str
    active_goal_id: str
    challenger_goal_id: str
    basis: str  # safety | user_priority | critical_operation | dependency | utility
    outcome: str  # superseded_active | paused_active | rejected_challenger
    reason: str = ""
    cycle: int = 0


@dataclass(frozen=True)
class GoalArbitration:
    """An auditable arbitration record: why one goal won (doc 02 Steps 3-4)."""
    arbitration_id: str
    winner_goal_id: str
    loser_goal_id: str
    basis: str                    # safety | user_priority | urgency | utility | resource
    score_winner: dict[str, Any]
    score_loser: dict[str, Any]
    cycle: int = 0


@dataclass(frozen=True)
class Goal:
    goal_id: str
    kind: str
    target: tuple[float, float] | str
    priority: float
    max_steps: int
    created_cycle: int
    # Doc 02 Step 1 schema extensions (all defaulted: backward compatible).
    source: str = "human"            # human | routine | safety | prediction | exploration | system
    urgency: float = 0.0             # 0..1; deadline pressure
    deadline_cycle: int = 0          # 0 = no deadline
    authority_requirement: str = "ASSISTED"
    resource_budget: float = 1.0     # relative cost budget (higher = more expensive)
    safety_relevant: bool = False    # safety goals dominate arbitration (A-GOAL-01)

    @classmethod
    def reach(cls, x: float, y: float, *, priority: float = 1.0, max_steps: int = 100, created_cycle: int = 0, goal_id: str = "", **kwargs: Any) -> "Goal":
        return cls(goal_id or f"goal-{uuid4().hex[:12]}", "reach", (float(x), float(y)), priority, max_steps, created_cycle, **kwargs)

    @classmethod
    def investigate(cls, entity: str, *, priority: float = 1.0, max_steps: int = 5, created_cycle: int = 0, goal_id: str = "", **kwargs: Any) -> "Goal":
        """A bounded curiosity goal: observe a target for up to ``max_steps`` cycles."""
        return cls(goal_id or f"goal-{uuid4().hex[:12]}", "investigate", entity, priority, max_steps, created_cycle, **kwargs)


@dataclass
class GoalState:
    goal: Goal
    status: GoalStatus = GoalStatus.ACTIVE
    steps_taken: int = 0
    paused_cycles: int = 0  # cycles spent paused (for resumability tracking)
    block_reason: str = ""  # why the goal is blocked (if blocked)
    validity_expires_cycle: int = 0  # 0 = no validity bound; else expiry cycle


@dataclass(frozen=True)
class StepCommand:
    action: str
    parameters: dict[str, Any]


class BoundedGoalController:
    """Converts a bounded reach goal into turn/move-forward commands.

    The robot pose is read from the body each cycle, so the controller only ever
    proposes the *next* step; the runtime executes it through the governed action
    path. Steps are counted on every cycle while a goal is active, guaranteeing
    the goal is bounded regardless of whether it makes progress.
    """

    def __init__(
        self,
        *,
        move_distance: float = 0.5,
        turn_degrees: float = 10.0,
        reach_threshold: float = 0.5,
        heading_tolerance: float = 5.0,
        resource_priority_floor: float = 0.0,
        max_background_goals: int = 3,
    ) -> None:
        self.move_distance = move_distance
        self.turn_degrees = turn_degrees
        self.reach_threshold = reach_threshold
        self.heading_tolerance = heading_tolerance
        # Doc 02 Step 7: while resources are constrained, pending goals below
        # this priority floor are postponed rather than promoted.
        self.resource_priority_floor = resource_priority_floor
        # Doc 02 Step 8: cap on self-generated background goals.
        self.max_background_goals = max_background_goals
        self.active: GoalState | None = None
        self.history: list[GoalState] = []
        self._pending: list[GoalState] = []
        self.conflict_resolutions: list[ConflictResolution] = []
        self.arbitrations: list[GoalArbitration] = []
        self._resolution_seq = 0
        self._resolved_pairs: set[tuple[str, str]] = set()
        self._revalidation_required: set[str] = set()

    # ---- lifecycle API (canonical authority: docs/02-autonomy/04 §Goal Lifecycle) ----

    def pause(self, goal_id: str, *, reason: str = "") -> bool:
        """Pause a non-terminal goal; it keeps its step budget and can be resumed."""
        state = self._find(goal_id)
        if state is None or state.status not in _RESUMABLE_STATES or state.status is GoalStatus.PAUSED:
            return False
        state.status = GoalStatus.PAUSED
        state.block_reason = reason or "paused"
        return True

    def resume(self, goal_id: str) -> bool:
        """Resume a paused/blocked goal; promoted to ACTIVE when the slot is free."""
        state = self._find(goal_id)
        if state is None or state.status not in (GoalStatus.PAUSED, GoalStatus.BLOCKED):
            return False
        if goal_id in self._revalidation_required:
            return False  # must be reaccepted explicitly after restart (doc 02 Step 5)
        state.status = GoalStatus.PENDING
        if state not in self._pending:
            self._pending.append(state)
            self._pending.sort(key=lambda s: self.arbitration_key(s.goal), reverse=True)
        state.block_reason = ""
        # When the active slot is free, promote immediately (resume is explicit).
        if self.active is None or self.active.status is not GoalStatus.ACTIVE:
            self._pending.remove(state)
            state.status = GoalStatus.ACTIVE
            self.active = state
            self.history.append(state)
        return True

    def block(self, goal_id: str, *, reason: str = "dependency_unmet") -> bool:
        """Block a goal (e.g. dependency/precondition unmet) without discarding it."""
        state = self._find(goal_id)
        if state is None or state.status in _TERMINAL_STATES:
            return False
        if state.status is GoalStatus.ACTIVE and self.active is state:
            self.active = None
        state.status = GoalStatus.BLOCKED
        state.block_reason = reason
        return True

    def cancel(self, goal_id: str, *, reason: str = "cancelled") -> bool:
        """Cancel a goal: terminal, not resumable."""
        state = self._find(goal_id)
        if state is None or state.status in _TERMINAL_STATES:
            return False
        if state.status is GoalStatus.ACTIVE and self.active is state:
            self.active = None
        if state in self._pending:
            self._pending.remove(state)
        state.status = GoalStatus.CANCELLED
        return True

    def expire(self, goal_id: str) -> bool:
        """Expire a goal whose validity window has passed: terminal, not resumable."""
        state = self._find(goal_id)
        if state is None or state.status in _TERMINAL_STATES:
            return False
        if state.status is GoalStatus.ACTIVE and self.active is state:
            self.active = None
        if state in self._pending:
            self._pending.remove(state)
        state.status = GoalStatus.EXPIRED
        return True

    def _find(self, goal_id: str) -> GoalState | None:
        candidates: list[GoalState | None] = [self.active]
        candidates.extend(self._pending)
        candidates.extend(self.history)
        for s in candidates:
            if s is not None and s.goal.goal_id == goal_id:
                return s
        return None

    # ---- deterministic arbitration (doc 02 Step 3, gate A-GOAL-01) ----

    @staticmethod
    def arbitration_key(goal: Goal) -> tuple[Any, ...]:
        """Deterministic, auditable ranking key.

        Order: safety relevance > priority > urgency > deadline pressure >
        freshness (later-created wins ties). A pure function of the goal and
        the world/policy state: the same state always picks the same winner.
        The score is a decision aid, never permission to bypass safety.
        """
        deadline_pressure = 0.0 if goal.deadline_cycle == 0 else 1.0 / max(1, goal.deadline_cycle)
        return (
            int(goal.safety_relevant),
            goal.priority,
            goal.urgency,
            deadline_pressure,
            goal.created_cycle,
        )

    def score_of(self, goal: Goal) -> dict[str, Any]:
        """Breakdown of the arbitration score for a goal (auditable explanation)."""
        key = self.arbitration_key(goal)
        return {
            "safety_relevant": bool(key[0]),
            "priority": key[1],
            "urgency": key[2],
            "deadline_pressure": key[3],
            "created_cycle": key[4],
        }

    def _record_arbitration(
        self, *, winner: Goal, loser: Goal, basis: str, cycle: int = 0,
    ) -> None:
        self.arbitrations.append(GoalArbitration(
            arbitration_id=f"arb-{len(self.arbitrations) + 1}",
            winner_goal_id=winner.goal_id, loser_goal_id=loser.goal_id,
            basis=basis, score_winner=self.score_of(winner), score_loser=self.score_of(loser),
            cycle=cycle,
        ))

    def _is_background(self, goal: Goal) -> bool:
        """Self-generated goals (doc 02 Step 8) are capped."""
        return goal.source in ("exploration", "prediction", "routine", "system")

    @property
    def background_count(self) -> int:
        """Number of non-terminal background goals currently held."""
        count = 0
        if self.active is not None and self._is_background(self.active.goal) \
                and self.active.status not in _TERMINAL_STATES:
            count += 1
        for state in self._pending:
            if self._is_background(state.goal) and state.status not in _TERMINAL_STATES:
                count += 1
        return count

    def _record_conflict(
        self,
        *,
        active_goal_id: str,
        challenger_goal_id: str,
        basis: str,
        outcome: str,
        reason: str = "",
        cycle: int = 0,
    ) -> None:
        self._resolution_seq += 1
        self.conflict_resolutions.append(ConflictResolution(
            resolution_id=f"conflict-{self._resolution_seq}",
            active_goal_id=active_goal_id,
            challenger_goal_id=challenger_goal_id,
            basis=basis,
            outcome=outcome,
            reason=reason,
            cycle=cycle,
        ))

    # ---- conflict resolution (canon authority: doc 04 §Goal Conflicts) ----

    def resolve_conflict(
        self,
        challenger: GoalState,
        *,
        cycle: int = 0,
        resource_constrained: bool = False,
    ) -> str:
        """Resolve a conflict between the active goal and a challenger.

        Canonical order (doc 04 §Goal Conflicts):
          1. hard safety constraints;
          2. explicit user priority;
          3. critical system operation;
          4. task dependencies;
          5. utility/cost;
          6. pause or abandon lower-priority goals;
          7. record the conflict and resolution.

        Returns the outcome: superseded_active | paused_active | rejected_challenger.
        """
        active = self.active
        if active is None or active.status is not GoalStatus.ACTIVE:
            self._record_conflict(
                active_goal_id="(none)", challenger_goal_id=challenger.goal.goal_id,
                basis="availability", outcome="rejected_challenger", reason="no_active_goal",
                cycle=cycle,
            )
            return "rejected_challenger"

        # Safety dominance (doc 02 Step 4 / A-GOAL-01): a safety goal beats any
        # lower-authority goal regardless of kind; the reverse is rejected.
        if challenger.goal.safety_relevant and not active.goal.safety_relevant:
            return self._supersede_active_for(challenger, cycle=cycle, basis="safety")
        if active.goal.safety_relevant and not challenger.goal.safety_relevant:
            self._record_conflict(
                active_goal_id=active.goal.goal_id, challenger_goal_id=challenger.goal.goal_id,
                basis="safety", outcome="rejected_challenger",
                reason="active_safety_goal_dominates", cycle=cycle,
            )
            self._record_arbitration(winner=active.goal, loser=challenger.goal, basis="safety", cycle=cycle)
            return "rejected_challenger"

        # Same kind: higher priority wins; ties keep the active goal
        # (utility/cost comparison per doc 04 §Goal Conflicts).
        if active.goal.kind == challenger.goal.kind:
            if challenger.goal.priority > active.goal.priority:
                if resource_constrained:
                    return self._pause_active_for(challenger, cycle=cycle)
                return self._supersede_active_for(challenger, cycle=cycle)
            self._record_conflict(
                active_goal_id=active.goal.goal_id, challenger_goal_id=challenger.goal.goal_id,
                basis="utility", outcome="rejected_challenger",
                reason="active_goal_higher_or_equal_priority", cycle=cycle,
            )
            self._record_arbitration(winner=active.goal, loser=challenger.goal, basis="utility", cycle=cycle)
            return "rejected_challenger"

        # Different kinds: investigate (curiosity) yields to reach (explicit goal).
        if active.goal.kind == "investigate" and challenger.goal.kind == "reach":
            return self._supersede_active_for(challenger, cycle=cycle)
        if active.goal.kind == "reach" and challenger.goal.kind == "investigate":
            self._record_conflict(
                active_goal_id=active.goal.goal_id, challenger_goal_id=challenger.goal.goal_id,
                basis="utility", outcome="rejected_challenger",
                reason="explicit_goal_beats_curiosity", cycle=cycle,
            )
            self._record_arbitration(winner=active.goal, loser=challenger.goal, basis="utility", cycle=cycle)
            return "rejected_challenger"

        self._record_conflict(
            active_goal_id=active.goal.goal_id, challenger_goal_id=challenger.goal.goal_id,
            basis="utility", outcome="rejected_challenger", reason="unresolved_conflict_keeps_active",
            cycle=cycle,
        )
        self._record_arbitration(winner=active.goal, loser=challenger.goal, basis="utility", cycle=cycle)
        return "rejected_challenger"

    def _supersede_active_for(self, challenger: GoalState, *, cycle: int, basis: str | None = None) -> str:
        active = self.active
        if active is not None:
            active.status = GoalStatus.SUPERSEDED
        self._pending.remove(challenger) if challenger in self._pending else None
        challenger.status = GoalStatus.ACTIVE
        self.active = challenger
        self.history.append(challenger)
        reason_basis = basis or ("user_priority" if challenger.goal.priority > 2.0 else "utility")
        self._record_conflict(
            active_goal_id=active.goal.goal_id if active else "(none)",
            challenger_goal_id=challenger.goal.goal_id,
            basis=reason_basis,
            outcome="superseded_active", cycle=cycle,
        )
        if active is not None:
            self._record_arbitration(
                winner=challenger.goal, loser=active.goal,
                basis=reason_basis, cycle=cycle,
            )
        return "superseded_active"

    def _pause_active_for(self, challenger: GoalState, *, cycle: int) -> str:
        active = self.active
        if active is not None:
            active.status = GoalStatus.PAUSED
            active.block_reason = "paused_for_higher_priority"
            self._pending.append(active)
            self._pending.sort(key=lambda s: self.arbitration_key(s.goal), reverse=True)
        self._pending.remove(challenger) if challenger in self._pending else None
        challenger.status = GoalStatus.ACTIVE
        self.active = challenger
        self.history.append(challenger)
        self._record_conflict(
            active_goal_id=active.goal.goal_id if active else "(none)",
            challenger_goal_id=challenger.goal.goal_id,
            basis="utility", outcome="paused_active", reason="resource_constrained", cycle=cycle,
        )
        if active is not None:
            self._record_arbitration(winner=challenger.goal, loser=active.goal, basis="utility", cycle=cycle)
        return "paused_active"

    def adopt(self, goal: Goal, *, cycle: int = 0, resource_constrained: bool = False) -> GoalState:
        """Adopt ``goal`` as the immediate active goal.

        Explicit/governed goals (e.g. user commands) take the active slot
        immediately. If a goal is already active, the adoption goes through
        conflict resolution (doc 04 §Goal Conflicts): the challenger either
        supersedes the active goal, pauses it (resource-constrained), or is
        rejected and queued.
        """
        if self._is_background(goal) and self.background_count >= self.max_background_goals:
            state = GoalState(goal, GoalStatus.BLOCKED, 0)
            state.block_reason = "background_goal_limit"
            self.history.append(state)
            return state
        challenger = GoalState(goal, GoalStatus.PENDING, 0)
        if self.active is not None and self.active.status is GoalStatus.ACTIVE:
            outcome = self.resolve_conflict(challenger, cycle=cycle, resource_constrained=resource_constrained)
            if outcome == "rejected_challenger":
                self._pending.append(challenger)
                self._pending.sort(key=lambda s: self.arbitration_key(s.goal), reverse=True)
                return challenger
            return challenger if self.active is challenger else challenger
        challenger.status = GoalStatus.ACTIVE
        self.active = challenger
        self.history.append(challenger)
        return challenger

    def enqueue(self, goal: Goal) -> GoalState:
        """Queue a goal for later pursuit, selected by the arbitration key."""
        if self._is_background(goal) and self.background_count >= self.max_background_goals:
            # Doc 02 Step 8: cap self-generated goals; record the rejection.
            state = GoalState(goal, GoalStatus.BLOCKED, 0)
            state.block_reason = "background_goal_limit"
            self.history.append(state)
            return state
        state = GoalState(goal, GoalStatus.PENDING, 0)
        self._pending.append(state)
        self._pending.sort(key=lambda s: self.arbitration_key(s.goal), reverse=True)
        return state

    @property
    def has_active(self) -> bool:
        return self.active is not None and self.active.status is GoalStatus.ACTIVE

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    @property
    def pending_goals(self) -> tuple[GoalState, ...]:
        return tuple(self._pending)

    def _reconcile(self, *, cycle: int = 0, resource_constrained: bool = False) -> None:
        """Promote pending goals via deterministic arbitration.

        The arbitration key (doc 02 Step 3) decides the winner: safety goals
        dominate, then priority, urgency, deadline pressure, freshness. When
        resources are constrained, goals below the priority floor are
        postponed rather than promoted (doc 02 Step 7). Each active/challenger
        pair is resolved at most once so rejected challengers are not
        re-recorded every cycle as they wait in the queue.
        """
        if not self._pending:
            return
        self._pending.sort(key=lambda s: self.arbitration_key(s.goal), reverse=True)
        top = self._pending[0]
        if resource_constrained and top.goal.priority < self.resource_priority_floor:
            return  # postpone low-value goals until resources recover
        if self.active is None or self.active.status is not GoalStatus.ACTIVE:
            self._pending.pop(0)
            top.status = GoalStatus.ACTIVE
            self.active = top
            self.history.append(top)
            return
        pair = (self.active.goal.goal_id, top.goal.goal_id)
        if pair in self._resolved_pairs:
            return
        self.resolve_conflict(top, cycle=cycle, resource_constrained=resource_constrained)
        self._resolved_pairs.add(pair)

    def step(self, body: Any, *, cycle: int = 0, resource_constrained: bool = False) -> StepCommand:
        self._reconcile(cycle=cycle, resource_constrained=resource_constrained)
        state = self.active
        if state is None or state.status is not GoalStatus.ACTIVE:
            return StepCommand("wait", {})

        # Validity expiry: a goal with a validity bound that has passed is
        # expired (terminal) rather than pursued (doc 04 §Goal Lifecycle:
        # goals must not survive beyond their validity period).
        if state.validity_expires_cycle and cycle > state.validity_expires_cycle:
            state.status = GoalStatus.EXPIRED
            self.active = None
            return StepCommand("stop", {})

        # Every cycle counts toward the budget, so the goal is always bounded.
        state.steps_taken += 1

        if state.goal.kind == "investigate":
            # Bounded observation: observe once per cycle for max_steps cycles,
            # then complete on the cycle after the budget is spent.
            if state.steps_taken > state.goal.max_steps:
                state.status = GoalStatus.COMPLETED
                self.active = None
                return StepCommand("stop", {})
            return StepCommand("observe", {})

        if state.steps_taken > state.goal.max_steps:
            state.status = GoalStatus.FAILED
            self.active = None
            return StepCommand("stop", {})

        target = state.goal.target
        if not isinstance(target, tuple) or len(target) != 2:
            state.status = GoalStatus.FAILED
            self.active = None
            return StepCommand("wait", {})

        tx, ty = target
        x, y, heading = body.x_m, body.y_m, body.heading_deg
        distance = math.hypot(tx - x, ty - y)
        if distance <= self.reach_threshold:
            state.status = GoalStatus.COMPLETED
            self.active = None
            return StepCommand("stop", {})

        desired = math.degrees(math.atan2(ty - y, tx - x))
        diff = (desired - heading + 180.0) % 360.0 - 180.0
        if abs(diff) > self.heading_tolerance:
            if diff > 0:
                return StepCommand("turn_left", {"degrees": self.turn_degrees})
            return StepCommand("turn_right", {"degrees": self.turn_degrees})
        return StepCommand("move_forward", {"distance_m": self.move_distance})

    # ---- observation / query API ----

    def status_of(self, goal_id: str) -> GoalStatus | None:
        state = self._find(goal_id)
        return state.status if state is not None else None

    def set_validity(self, goal_id: str, expires_cycle: int) -> bool:
        """Give a goal a validity bound: past this cycle it expires (doc 04)."""
        state = self._find(goal_id)
        if state is None:
            return False
        state.validity_expires_cycle = max(0, int(expires_cycle))
        return True

    # ---- restart revalidation (doc 02 Step 5) ----

    def mark_requires_revalidation(self, goal_id: str) -> bool:
        """Block a goal until its physical preconditions are revalidated.

        A goal restored after restart must not resume physical action merely
        because it was active before shutdown. Until ``reaccept`` is called,
        the goal stays BLOCKED and cannot be resumed.
        """
        state = self._find(goal_id)
        if state is None or state.status in _TERMINAL_STATES:
            return False
        self._revalidation_required.add(goal_id)
        if state.status is GoalStatus.ACTIVE and self.active is state:
            self.active = None
        if state in self._pending:
            self._pending.remove(state)
        state.status = GoalStatus.BLOCKED
        state.block_reason = "revalidation_required"
        return True

    def reaccept(self, goal_id: str) -> bool:
        """Explicit revalidation: the goal re-enters the arbitration queue."""
        state = self._find(goal_id)
        if state is None or goal_id not in self._revalidation_required:
            return False
        self._revalidation_required.discard(goal_id)
        state.block_reason = ""
        state.status = GoalStatus.PENDING
        if state not in self._pending:
            self._pending.append(state)
            self._pending.sort(key=lambda s: self.arbitration_key(s.goal), reverse=True)
        return True

    @property
    def conflict_resolution_count(self) -> int:
        return len(self.conflict_resolutions)

    def resolutions(self, *, goal_id: str | None = None) -> tuple[ConflictResolution, ...]:
        if goal_id is None:
            return tuple(self.conflict_resolutions)
        return tuple(r for r in self.conflict_resolutions
                     if r.active_goal_id == goal_id or r.challenger_goal_id == goal_id)
