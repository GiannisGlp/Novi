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
class Goal:
    goal_id: str
    kind: str
    target: tuple[float, float] | str
    priority: float
    max_steps: int
    created_cycle: int

    @classmethod
    def reach(cls, x: float, y: float, *, priority: float = 1.0, max_steps: int = 100, created_cycle: int = 0, goal_id: str = "") -> "Goal":
        return cls(goal_id or f"goal-{uuid4().hex[:12]}", "reach", (float(x), float(y)), priority, max_steps, created_cycle)

    @classmethod
    def investigate(cls, entity: str, *, priority: float = 1.0, max_steps: int = 5, created_cycle: int = 0, goal_id: str = "") -> "Goal":
        """A bounded curiosity goal: observe a target for up to ``max_steps`` cycles."""
        return cls(goal_id or f"goal-{uuid4().hex[:12]}", "investigate", entity, priority, max_steps, created_cycle)


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
    ) -> None:
        self.move_distance = move_distance
        self.turn_degrees = turn_degrees
        self.reach_threshold = reach_threshold
        self.heading_tolerance = heading_tolerance
        self.active: GoalState | None = None
        self.history: list[GoalState] = []
        self._pending: list[GoalState] = []
        self.conflict_resolutions: list[ConflictResolution] = []
        self._resolution_seq = 0
        self._resolved_pairs: set[tuple[str, str]] = set()

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
        state.status = GoalStatus.PENDING
        if state not in self._pending:
            self._pending.append(state)
            self._pending.sort(key=lambda s: s.goal.priority, reverse=True)
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
            return "rejected_challenger"

        self._record_conflict(
            active_goal_id=active.goal.goal_id, challenger_goal_id=challenger.goal.goal_id,
            basis="utility", outcome="rejected_challenger", reason="unresolved_conflict_keeps_active",
            cycle=cycle,
        )
        return "rejected_challenger"

    def _supersede_active_for(self, challenger: GoalState, *, cycle: int) -> str:
        active = self.active
        if active is not None:
            active.status = GoalStatus.SUPERSEDED
        self._pending.remove(challenger) if challenger in self._pending else None
        challenger.status = GoalStatus.ACTIVE
        self.active = challenger
        self.history.append(challenger)
        self._record_conflict(
            active_goal_id=active.goal.goal_id if active else "(none)",
            challenger_goal_id=challenger.goal.goal_id,
            basis="user_priority" if challenger.goal.priority > 2.0 else "utility",
            outcome="superseded_active", cycle=cycle,
        )
        return "superseded_active"

    def _pause_active_for(self, challenger: GoalState, *, cycle: int) -> str:
        active = self.active
        if active is not None:
            active.status = GoalStatus.PAUSED
            active.block_reason = "paused_for_higher_priority"
            self._pending.append(active)
            self._pending.sort(key=lambda s: s.goal.priority, reverse=True)
        self._pending.remove(challenger) if challenger in self._pending else None
        challenger.status = GoalStatus.ACTIVE
        self.active = challenger
        self.history.append(challenger)
        self._record_conflict(
            active_goal_id=active.goal.goal_id if active else "(none)",
            challenger_goal_id=challenger.goal.goal_id,
            basis="utility", outcome="paused_active", reason="resource_constrained", cycle=cycle,
        )
        return "paused_active"

    def adopt(self, goal: Goal, *, cycle: int = 0, resource_constrained: bool = False) -> GoalState:
        """Adopt ``goal`` as the immediate active goal.

        Explicit/governed goals (e.g. user commands) take the active slot
        immediately. If a goal is already active, the adoption goes through
        conflict resolution (doc 04 §Goal Conflicts): the challenger either
        supersedes the active goal, pauses it (resource-constrained), or is
        rejected and queued.
        """
        challenger = GoalState(goal, GoalStatus.PENDING, 0)
        if self.active is not None and self.active.status is GoalStatus.ACTIVE:
            outcome = self.resolve_conflict(challenger, cycle=cycle, resource_constrained=resource_constrained)
            if outcome == "rejected_challenger":
                self._pending.append(challenger)
                self._pending.sort(key=lambda s: s.goal.priority, reverse=True)
                return challenger
            return challenger if self.active is challenger else challenger
        challenger.status = GoalStatus.ACTIVE
        self.active = challenger
        self.history.append(challenger)
        return challenger

    def enqueue(self, goal: Goal) -> GoalState:
        """Queue a goal for later pursuit, selected by priority (higher wins)."""
        state = GoalState(goal, GoalStatus.PENDING, 0)
        self._pending.append(state)
        self._pending.sort(key=lambda s: s.goal.priority, reverse=True)
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
        """Promote pending goals via conflict resolution.

        Conflict resolution decides outcome (doc 04 §Goal Conflicts): higher
        priority wins within a kind; explicit reach goals beat curiosity;
        when resources are constrained, a lower-priority active goal is paused
        (not discarded) for a higher-priority challenger. Each active/challenger
        pair is resolved at most once so rejected challengers are not
        re-recorded every cycle as they wait in the queue.
        """
        if not self._pending:
            return
        top = self._pending[0]
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

    @property
    def conflict_resolution_count(self) -> int:
        return len(self.conflict_resolutions)

    def resolutions(self, *, goal_id: str | None = None) -> tuple[ConflictResolution, ...]:
        if goal_id is None:
            return tuple(self.conflict_resolutions)
        return tuple(r for r in self.conflict_resolutions
                     if r.active_goal_id == goal_id or r.challenger_goal_id == goal_id)
