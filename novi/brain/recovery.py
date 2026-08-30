"""Recovery and metacognition for the Mac Brain (06_AUTONOMY doc 07).

Makes Novi aware of the reliability of its own decisions and able to recover
from failures without turning every failure into uncontrolled learning:

- ``FailureClassifier`` — the doc 07 Step 4 failure taxonomy
  (perception / localization / world-model / planning / precondition /
  execution / verification / resource / safety / dependency /
  human-interruption).
- ``RecoveryPlanner`` — maps a failure to a bounded strategy and retry budget
  (retry / refresh_perception / replan / alternative_skill / ask_user /
  safe_stop). Repeating an action that physically failed without new
  information is forbidden (doc 07 Step 5).
- ``ConfidenceProfile`` — decomposed confidence (perception, world-state,
  identity, plan, action, verification); never one global number
  (doc 07 Step 1).
- ``CounterfactualRecorder`` — after a failure: what Novi believed, what it
  expected, what happened, why, what information would have prevented it, and
  whether the planner/perception policy should change (doc 07 Step 7).
- ``RegressionMemory`` — every promoted lesson creates a regression scenario
  (doc 07 Step 10), so Novi cannot relearn a failure in a future version.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class FailureClass(str, Enum):
    PERCEPTION = "perception"
    LOCALIZATION = "localization"
    WORLD_MODEL = "world-model"
    PLANNING = "planning"
    PRECONDITION = "precondition"
    EXECUTION = "execution"
    VERIFICATION = "verification"
    RESOURCE = "resource"
    SAFETY = "safety"
    DEPENDENCY = "dependency"
    HUMAN_INTERRUPTION = "human-interruption"


# Recovery strategies (doc 05 Step 7 / doc 07 Step 4).
RETRY = "retry"
REFRESH_PERCEPTION = "refresh_perception"
REPLAN = "replan"
ALTERNATIVE_SKILL = "alternative_skill"
ASK_USER = "ask_user"
SAFE_STOP = "safe_stop"

# Per-class retry budgets: retrying a physically-failed action without new
# information is forbidden, so physical classes get 0 retries (doc 07 Step 5).
_CLASS_BUDGET: dict[FailureClass, int] = {
    FailureClass.PERCEPTION: 2,
    FailureClass.LOCALIZATION: 1,
    FailureClass.WORLD_MODEL: 1,
    FailureClass.PLANNING: 2,
    FailureClass.PRECONDITION: 0,
    FailureClass.EXECUTION: 1,
    FailureClass.VERIFICATION: 1,
    FailureClass.RESOURCE: 0,
    FailureClass.SAFETY: 0,
    FailureClass.DEPENDENCY: 2,
    FailureClass.HUMAN_INTERRUPTION: 0,
}

_CLASS_STRATEGY: dict[FailureClass, str] = {
    FailureClass.PERCEPTION: REFRESH_PERCEPTION,
    FailureClass.LOCALIZATION: REFRESH_PERCEPTION,
    FailureClass.WORLD_MODEL: REFRESH_PERCEPTION,
    FailureClass.PLANNING: REPLAN,
    FailureClass.PRECONDITION: ALTERNATIVE_SKILL,
    FailureClass.EXECUTION: RETRY,
    FailureClass.VERIFICATION: REFRESH_PERCEPTION,
    FailureClass.RESOURCE: ASK_USER,
    FailureClass.SAFETY: SAFE_STOP,
    FailureClass.DEPENDENCY: RETRY,
    FailureClass.HUMAN_INTERRUPTION: SAFE_STOP,
}

_KEYWORDS: tuple[tuple[FailureClass, tuple[str, ...]], ...] = (
    (FailureClass.SAFETY, ("safety", "estop", "emergency", "forbidden", "invariant", "denied")),
    (FailureClass.HUMAN_INTERRUPTION, ("interrupt", "cancelled", "cancel", "operator")),
    (FailureClass.LOCALIZATION, ("localiz", "pose", "odometry", "slam")),
    (FailureClass.PERCEPTION, ("percept", "sensor", "camera", "detect", "frame", "stale")),
    (FailureClass.WORLD_MODEL, ("world", "belief", "contradict", "provenance", "entity")),
    (FailureClass.PLANNING, ("plan", "planner", "decompos", "step")),
    (FailureClass.PRECONDITION, ("precondition", "not_localized", "route_blocked", "missing")),
    (FailureClass.VERIFICATION, ("verif", "postcondition", "unverified", "tolerance")),
    (FailureClass.RESOURCE, ("resource", "budget", "battery", "energy", "thermal", "compute")),
    (FailureClass.DEPENDENCY, ("dependency", "unavailable", "timeout", "model_unavailable")),
    (FailureClass.EXECUTION, ("execut", "action", "motion", "actuator", "motor")),
)


class FailureClassifier:
    """Classifies a failure from its error text / outcome (doc 07 Step 4)."""

    def classify(self, *, reason: str = "", outcome: str = "") -> FailureClass:
        text = f"{reason} {outcome}".lower()
        for failure_class, keywords in _KEYWORDS:
            if any(keyword in text for keyword in keywords):
                return failure_class
        return FailureClass.EXECUTION


@dataclass(frozen=True)
class RecoveryPlan:
    recovery_id: str
    failure_class: FailureClass
    strategy: str
    retry_budget: int
    reason: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "recovery_id": self.recovery_id,
            "failure_class": self.failure_class.value,
            "strategy": self.strategy,
            "retry_budget": self.retry_budget,
            "reason": self.reason,
        }


class RecoveryPlanner:
    """Maps a classified failure to a bounded recovery plan (doc 07 Step 4-5)."""

    def __init__(self, classifier: FailureClassifier | None = None) -> None:
        self.classifier = classifier or FailureClassifier()
        self.plans: list[RecoveryPlan] = []

    def plan_for(self, *, reason: str = "", outcome: str = "", budget_override: int | None = None) -> RecoveryPlan:
        failure_class = self.classifier.classify(reason=reason, outcome=outcome)
        strategy = _CLASS_STRATEGY[failure_class]
        budget = _CLASS_BUDGET[failure_class] if budget_override is None else max(0, int(budget_override))
        plan = RecoveryPlan(
            recovery_id=f"rec-{uuid4().hex[:10]}",
            failure_class=failure_class, strategy=strategy, retry_budget=budget,
            reason=reason or outcome,
        )
        self.plans.append(plan)
        return plan

    def is_infinite(self, plan: RecoveryPlan) -> bool:
        """A plan that retries with no budget is an infinite loop — forbidden."""
        return plan.strategy == RETRY and plan.retry_budget <= 0


@dataclass
class ConfidenceProfile:
    """Decomposed confidence (doc 07 Step 1) — never a single global number."""
    perception: float = 0.0
    world_state: float = 0.0
    identity: float = 0.0
    plan: float = 0.0
    action: float = 0.0
    verification: float = 0.0

    def is_confident(self, minimums: dict[str, float]) -> tuple[bool, list[str]]:
        """All named components must meet their thresholds."""
        missing: list[str] = []
        for name, minimum in minimums.items():
            if getattr(self, name, 0.0) < minimum:
                missing.append(name)
        return (not missing, missing)

    def snapshot(self) -> dict[str, Any]:
        return {name: round(getattr(self, name), 4)
                for name in ("perception", "world_state", "identity", "plan", "action", "verification")}


@dataclass
class CounterfactualRecord:
    """What Novi believed vs. what happened (doc 07 Step 7)."""
    record_id: str
    failure_ref: str
    believed: dict[str, Any]
    expected: dict[str, Any]
    happened: dict[str, Any]
    discrepancy_reason: str
    information_that_would_prevent: str
    policy_should_change: bool
    cycle: int = 0

    def snapshot(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id, "failure_ref": self.failure_ref,
            "believed": dict(self.believed), "expected": dict(self.expected),
            "happened": dict(self.happened), "discrepancy_reason": self.discrepancy_reason,
            "information_that_would_prevent": self.information_that_would_prevent,
            "policy_should_change": self.policy_should_change, "cycle": self.cycle,
        }


class CounterfactualRecorder:
    def __init__(self) -> None:
        self._records: list[CounterfactualRecord] = []

    def record(self, *, failure_ref: str, believed: dict[str, Any], expected: dict[str, Any],
               happened: dict[str, Any], discrepancy_reason: str,
               information_that_would_prevent: str, policy_should_change: bool,
               cycle: int = 0) -> CounterfactualRecord:
        record = CounterfactualRecord(
            record_id=f"cf-{uuid4().hex[:10]}", failure_ref=failure_ref,
            believed=dict(believed), expected=dict(expected), happened=dict(happened),
            discrepancy_reason=discrepancy_reason,
            information_that_would_prevent=information_that_would_prevent,
            policy_should_change=policy_should_change, cycle=cycle,
        )
        self._records.append(record)
        return record

    def records(self) -> tuple[CounterfactualRecord, ...]:
        return tuple(self._records)

    def policy_change_candidates(self) -> tuple[CounterfactualRecord, ...]:
        return tuple(r for r in self._records if r.policy_should_change)


@dataclass
class Lesson:
    lesson_id: str
    title: str
    evidence_refs: tuple[str, ...] = ()
    verified: bool = False
    regression_scenarios: list[str] = field(default_factory=list)

    def snapshot(self) -> dict[str, Any]:
        return {"lesson_id": self.lesson_id, "title": self.title,
                "evidence_refs": list(self.evidence_refs), "verified": self.verified,
                "regression_scenarios": list(self.regression_scenarios)}


class RegressionMemory:
    """Promoted lessons create regression scenarios (doc 07 Step 10).

    Only verified lessons may be promoted; an unverified lesson is never
    treated as learned knowledge (A-META-01: zero unverified promotions).
    """

    def __init__(self) -> None:
        self._lessons: dict[str, Lesson] = {}
        self._promotion_attempts: list[dict[str, Any]] = []
        self._rollbacks: list[str] = []

    def propose(self, *, title: str, evidence_refs: tuple[str, ...] = ()) -> Lesson:
        lesson = Lesson(lesson_id=f"lesson-{uuid4().hex[:10]}", title=title,
                        evidence_refs=tuple(evidence_refs))
        self._lessons[lesson.lesson_id] = lesson
        return lesson

    def promote(self, lesson: Lesson, *, regression_scenario: str) -> bool:
        """Promote only if verified; attach a regression scenario."""
        self._promotion_attempts.append({"lesson_id": lesson.lesson_id, "verified": lesson.verified})
        if not lesson.verified:
            return False
        if regression_scenario not in lesson.regression_scenarios:
            lesson.regression_scenarios.append(regression_scenario)
        return True

    def scenarios_for(self, lesson_id: str) -> tuple[str, ...]:
        lesson = self._lessons.get(lesson_id)
        return tuple(lesson.regression_scenarios) if lesson else ()

    def rollback(self, lesson_id: str) -> bool:
        """Roll back a promoted lesson (doc 11 Phase 11 item 7).

        Triggered when the lesson's regression scenario fails: the lesson is
        un-promoted, its regression scenarios are cleared, and it can never be
        re-promoted without fresh verification.
        """
        lesson = self._lessons.get(lesson_id)
        if lesson is None or not lesson.verified:
            return False
        lesson.verified = False
        lesson.regression_scenarios.clear()
        self._rollbacks.append(lesson_id)
        return True

    def rollbacks(self) -> tuple[str, ...]:
        return tuple(self._rollbacks)

    def unverified_promotions(self) -> int:
        return sum(1 for a in self._promotion_attempts if not a["verified"])

    def lessons(self) -> tuple[Lesson, ...]:
        return tuple(self._lessons.values())

    def snapshot(self) -> dict[str, Any]:
        """Phase 4c: persist lessons/attempts/rollbacks (learning survives restart)."""
        return {
            "lessons": [lesson.snapshot() for lesson in self._lessons.values()],
            "promotion_attempts": list(self._promotion_attempts),
            "rollbacks": list(self._rollbacks),
        }

    def from_snapshot(self, data: dict[str, Any]) -> "RegressionMemory":
        for s in data.get("lessons", []):
            try:
                lesson = Lesson(
                    lesson_id=str(s.get("lesson_id", "")),
                    title=str(s.get("title", "")),
                    evidence_refs=tuple(str(e) for e in s.get("evidence_refs", [])),
                    verified=bool(s.get("verified", False)),
                    regression_scenarios=[str(r) for r in s.get("regression_scenarios", [])],
                )
            except (TypeError, ValueError):
                continue  # malformed lesson: skip, never crash the brain
            if lesson.lesson_id:
                self._lessons[lesson.lesson_id] = lesson
        self._promotion_attempts = [a for a in data.get("promotion_attempts", []) if isinstance(a, dict)]
        self._rollbacks = [str(r) for r in data.get("rollbacks", [])]
        return self
