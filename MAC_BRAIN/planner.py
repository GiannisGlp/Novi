"""Multi-step planning for the Mac Brain.

Decomposes a goal into an ordered, **typed** step plan (determine → execute →
verify, with expected outcomes), tracks each step's status, and supports
replanning/cancellation when observations invalidate assumptions.

Boundaries honored (docs/02-autonomy/01):
  - Plans are context for the autonomy controller; the controller and
    Policy/Safety still gate every executed action.
  - A plan is revisable: replan/cancel are first-class operations.
  - Steps carry expected outcomes so progress is verifiable, not assumed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class PlanStep:
    description: str
    kind: str  # typed step
    action: str = "wait"
    expected_outcome: str = ""
    status: str = "pending"  # pending | active | completed | failed | cancelled

    def snapshot(self) -> dict[str, Any]:
        return {"description": self.description, "kind": self.kind, "action": self.action, "expected_outcome": self.expected_outcome, "status": self.status}


@dataclass
class Plan:
    plan_id: str
    goal_id: str
    goal_kind: str
    steps: list[PlanStep] = field(default_factory=list)
    status: str = "running"  # running | completed | failed | cancelled
    created_cycle: int = 0

    def current_step(self) -> PlanStep | None:
        for step in self.steps:
            if step.status in ("pending", "active"):
                return step
        return None

    @property
    def complete(self) -> bool:
        return self.status == "completed"

    def snapshot(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal_id": self.goal_id,
            "goal_kind": self.goal_kind,
            "status": self.status,
            "created_cycle": self.created_cycle,
            "current": self.current_step().description if self.current_step() else None,
            "steps": [s.snapshot() for s in self.steps],
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "Plan":
        steps = [
            PlanStep(description=s["description"], kind=s["kind"], action=s.get("action", "wait"), expected_outcome=s.get("expected_outcome", ""), status=s["status"])
            for s in data.get("steps", [])
        ]
        return cls(
            plan_id=data["plan_id"],
            goal_id=data["goal_id"],
            goal_kind=data["goal_kind"],
            steps=steps,
            status=data.get("status", "running"),
            created_cycle=data.get("created_cycle", 0),
        )


class Planner:
    """Builds and advances bounded multi-step plans from goals."""

    def plan(self, goal: Any, *, cycle: int = 0) -> Plan:
        if goal.kind == "reach":
            steps = [
                PlanStep("evaluate heading and distance to target", "evaluate", "observe", "know_target_heading"),
                PlanStep("navigate toward the target", "navigate", "move_forward", "approach_target"),
                PlanStep("verify arrival within threshold", "verify", "stop", "goal_reached"),
            ]
        elif goal.kind == "investigate":
            steps = [
                PlanStep("locate the target entity", "locate", "observe", "target_found"),
                PlanStep("observe the target", "track", "observe", "target_observed"),
                PlanStep("conclude and stop", "conclude", "stop", "observation_complete"),
            ]
        else:
            steps = [
                PlanStep("determine context", "determine", "observe", "context_clear"),
                PlanStep("execute the action", "execute", "observe", "action_done"),
                PlanStep("verify the outcome", "verify", "stop", "outcome_verified"),
            ]
        return Plan(plan_id=f"plan-{uuid4().hex[:12]}", goal_id=goal.goal_id, goal_kind=goal.kind, steps=steps, status="running", created_cycle=cycle)

    def start(self, plan: Plan) -> None:
        if plan.steps:
            plan.steps[0].status = "active"

    def advance(self, plan: Plan) -> PlanStep | None:
        """Mark the current step complete and activate the next. Returns the new active step."""
        for i, step in enumerate(plan.steps):
            if step.status == "active":
                step.status = "completed"
                if i + 1 < len(plan.steps):
                    plan.steps[i + 1].status = "active"
                    return plan.steps[i + 1]
                plan.status = "completed"
                return None
        return None

    def fail(self, plan: Plan, *, reason: str = "assumption_invalidated") -> None:
        current = plan.current_step()
        if current is not None:
            current.status = "failed"
        plan.status = "failed"

    def cancel(self, plan: Plan) -> None:
        for step in plan.steps:
            if step.status in ("pending", "active"):
                step.status = "cancelled"
        plan.status = "cancelled"

    def replan(self, goal: Any, *, cycle: int = 0) -> Plan:
        """Build a fresh plan (assumptions invalidated)."""
        return self.plan(goal, cycle=cycle)
