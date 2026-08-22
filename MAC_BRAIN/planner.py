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
    params: dict[str, Any] = field(default_factory=dict)  # validated action arguments

    def snapshot(self) -> dict[str, Any]:
        return {"description": self.description, "kind": self.kind, "action": self.action, "expected_outcome": self.expected_outcome, "status": self.status, "params": dict(self.params)}


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
            PlanStep(description=s["description"], kind=s["kind"], action=s.get("action", "wait"), expected_outcome=s.get("expected_outcome", ""), status=s["status"], params=dict(s.get("params") or {}))
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


@dataclass(frozen=True)
class PlanCheck:
    """One named validation check with a pass/fail verdict and detail."""
    name: str
    passed: bool
    detail: str = ""


@dataclass
class PlanValidation:
    """Structured plan-validation result (docs/02-autonomy/05 §Plan Validation)."""
    plan_id: str
    valid: bool
    checks: list[PlanCheck] = field(default_factory=list)

    @property
    def issues(self) -> tuple[str, ...]:
        return tuple(c.detail for c in self.checks if not c.passed)

    def snapshot(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "valid": self.valid,
            "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail} for c in self.checks],
        }


# Valid plan-step statuses and the maximum plan length (bounded plans).
_PLAN_STEP_STATUSES = frozenset({"pending", "active", "completed", "failed", "cancelled"})
_PLAN_STATUSES = frozenset({"running", "completed", "failed", "cancelled"})
MAX_PLAN_STEPS = 16
MIN_PLAN_STEPS = 1


class PlanValidator:
    """Validates a plan before execution (authority: docs/02-autonomy/05 §Plan Validation).

    Checks (in doc order):
      1. schema validation (well-formed plan/step fields);
      2. capability existence (step actions are known runtime actions);
      3. argument validation (numeric arguments are finite and in-range);
      4. resource availability (bounded step count / mandatory fields);
      5. spatial constraints (reach targets must be finite coordinates);
      6. safety policy (plan is safely terminable: last step is verify/stop
         or a stop action is reachable);
      7. temporal validity (non-negative creation cycle);
      8. status consistency (step statuses form a valid lifecycle prefix).
    """

    def __init__(self, *, available_actions: set[str] | None = None) -> None:
        self._actions = set(available_actions) if available_actions is not None else _KNOWN_ACTIONS

    def validate(self, plan: Plan) -> PlanValidation:
        checks: list[PlanCheck] = []
        checks.append(self._check_schema(plan))
        checks.append(self._check_capabilities(plan))
        checks.append(self._check_arguments(plan))
        checks.append(self._check_bound(plan))
        checks.append(self._check_spatial(plan))
        checks.append(self._check_terminability(plan))
        checks.append(self._check_temporal(plan))
        checks.append(self._check_statuses(plan))
        return PlanValidation(plan_id=plan.plan_id, valid=all(c.passed for c in checks), checks=checks)

    # ---- individual checks ----

    def _check_schema(self, plan: Plan) -> PlanCheck:
        if not plan.plan_id:
            return PlanCheck("schema", False, "plan_id missing")
        if not plan.goal_id:
            return PlanCheck("schema", False, "goal_id missing")
        if not plan.goal_kind:
            return PlanCheck("schema", False, "goal_kind missing")
        if not plan.steps:
            return PlanCheck("schema", False, "plan has no steps")
        for i, s in enumerate(plan.steps):
            if not s.description or not s.kind or not s.action:
                return PlanCheck("schema", False, f"step {i} has an empty required field")
        return PlanCheck("schema", True, f"{len(plan.steps)} well-formed steps")

    def _check_capabilities(self, plan: Plan) -> PlanCheck:
        unknown = [s.action for s in plan.steps if s.action not in self._actions]
        if unknown:
            return PlanCheck("capabilities", False, f"unknown actions: {sorted(set(unknown))}")
        return PlanCheck("capabilities", True, "all step actions are known capabilities")

    def _check_arguments(self, plan: Plan) -> PlanCheck:
        for i, s in enumerate(plan.steps):
            if s.action == "move_forward" and not s.expected_outcome:
                return PlanCheck("arguments", False, f"step {i} move_forward lacks expected_outcome")
        return PlanCheck("arguments", True, "step arguments acceptable")

    def _check_bound(self, plan: Plan) -> PlanCheck:
        if len(plan.steps) > MAX_PLAN_STEPS:
            return PlanCheck("bounded", False, f"{len(plan.steps)} steps exceeds max {MAX_PLAN_STEPS}")
        if len(plan.steps) < MIN_PLAN_STEPS:
            return PlanCheck("bounded", False, "plan must have at least one step")
        return PlanCheck("bounded", True, f"{len(plan.steps)} steps within [{MIN_PLAN_STEPS}, {MAX_PLAN_STEPS}]")

    def _check_spatial(self, plan: Plan) -> PlanCheck:
        for i, s in enumerate(plan.steps):
            v = s.params.get("distance_m")
            if v is not None and (not isinstance(v, (int, float)) or not _finite(v) or v <= 0 or v > 100.0):
                return PlanCheck("spatial", False, f"step {i} has invalid distance_m: {v!r}")
        return PlanCheck("spatial", True, "spatial arguments finite and in-range")

    def _check_terminability(self, plan: Plan) -> PlanCheck:
        # A plan must be safely terminable: the final step verifies/stops, or
        # any step can issue "stop" (a safe terminal action).
        last = plan.steps[-1]
        if last.action == "stop":
            return PlanCheck("safety", True, "final step is a safe stop")
        if last.kind in ("verify", "conclude", "determine"):
            return PlanCheck("safety", True, f"final step ({last.kind}) verifies before termination")
        if any(s.action == "stop" for s in plan.steps):
            return PlanCheck("safety", True, "a stop step is reachable in the plan")
        return PlanCheck("safety", False, "plan is not safely terminable (no stop reachable)")

    def _check_temporal(self, plan: Plan) -> PlanCheck:
        if plan.created_cycle < 0:
            return PlanCheck("temporal", False, f"created_cycle {plan.created_cycle} is negative")
        return PlanCheck("temporal", True, f"created at cycle {plan.created_cycle}")

    def _check_statuses(self, plan: Plan) -> PlanCheck:
        if plan.status not in _PLAN_STATUSES:
            return PlanCheck("statuses", False, f"invalid plan status {plan.status!r}")
        active_count = 0
        for i, s in enumerate(plan.steps):
            if s.status not in _PLAN_STEP_STATUSES:
                return PlanCheck("statuses", False, f"step {i} invalid status {s.status!r}")
            if s.status == "active":
                active_count += 1
        if active_count > 1:
            return PlanCheck("statuses", False, "more than one active step")
        # Prefix consistency: no completed/failed/cancelled step after an active/pending one.
        seen_nonterminal = False
        for i, s in enumerate(plan.steps):
            if s.status in ("active", "pending"):
                seen_nonterminal = True
            elif seen_nonterminal and s.status in ("completed", "failed", "cancelled"):
                return PlanCheck("statuses", False, f"terminal step {i} after non-terminal step")
        return PlanCheck("statuses", True, "step status lifecycle is consistent")


def _finite(v: object) -> bool:
    import math
    if isinstance(v, bool):
        return True
    try:
        return math.isfinite(float(v))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False


# Known runtime actions (aligns with MAC_BRAIN/io.py ALLOWED_ACTIONS).
_KNOWN_ACTIONS = frozenset({
    "inspect", "move_forward", "turn_left", "turn_right", "stop", "wait", "observe", "speak",
})


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

    def validate(self, plan: Plan, *, available_actions: set[str] | None = None) -> PlanValidation:
        """Validate a plan before execution (canonical authority: docs/02-autonomy/05 §Plan Validation)."""
        return PlanValidator(available_actions=available_actions).validate(plan)

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
