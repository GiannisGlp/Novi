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
    COMPLETED = "completed"
    FAILED = "failed"
    SUPERSEDED = "superseded"


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

    def adopt(self, goal: Goal) -> GoalState:
        """Adopt ``goal`` as the immediate active goal.

        Explicit/governed goals (e.g. user commands) take the active slot
        immediately; any previously active goal is safely superseded.
        """
        if self.active is not None and self.active.status is GoalStatus.ACTIVE:
            self.active.status = GoalStatus.SUPERSEDED
        self.active = GoalState(goal, GoalStatus.ACTIVE, 0)
        self.history.append(self.active)
        return self.active

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

    def _reconcile(self) -> None:
        """Promote the highest-priority pending goal, safely superseding a
        lower-priority active goal. Higher ``priority`` wins."""
        if not self._pending:
            return
        top = self._pending[0]
        if self.active is None or self.active.status is not GoalStatus.ACTIVE:
            self._pending.pop(0)
            top.status = GoalStatus.ACTIVE
            self.active = top
            self.history.append(top)
        elif top.goal.priority > self.active.goal.priority:
            self.active.status = GoalStatus.SUPERSEDED
            self._pending.pop(0)
            top.status = GoalStatus.ACTIVE
            self.active = top
            self.history.append(top)

    def step(self, body: Any, *, cycle: int = 0) -> StepCommand:
        self._reconcile()
        state = self.active
        if state is None or state.status is not GoalStatus.ACTIVE:
            return StepCommand("wait", {})

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
