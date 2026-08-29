"""Curiosity and exploration for the Mac Brain (06_AUTONOMY doc 06).

Curiosity is an *information-seeking policy*, not a desire to stay busy:

  Unknown / uncertainty → potential information gain → expected usefulness
  → risk + cost → exploration goal → safe observation → knowledge update

Components:

- ``NoveltyDetector`` — novelty sources (doc 06 Step 1): unseen object,
  unexplored region, unexpected event, prediction error, contradictory
  observations, newly available sensor, changed environment. Every candidate
  carries an *information hypothesis*: what uncertainty will the action reduce?
- ``CuriosityScorer`` — ``expected_uncertainty_reduction × future_usefulness
  - cost - risk`` (doc 06 Step 3). Novelty alone is never a reason to explore.
- ``ExplorationBudget`` — bounds every episode: duration, distance, energy,
  perception calls, retries, forbidden regions, immediate stop conditions
  (doc 06 Step 4).
- ``ExplorationPlanner`` — incremental, safe-first order: existing sensors →
  viewpoint → nearby area → move only if necessary; stops when the expected
  information gain drops below threshold (doc 06 Step 5).
- ``CuriosityGoalGenerator`` — produces bounded exploration goals (source
  "exploration") only when there is spare autonomy budget; capped like other
  background goals (doc 06 Step 2 + doc 02 Step 8).
- ``ExplorationPreferenceLearner`` — records which explorations actually
  improved future task performance and weights usefulness accordingly
  (doc 06 Step 7) — never optimizing for novelty alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class NoveltyCandidate:
    candidate_id: str
    target: str
    novelty_type: str       # unseen_object | unexplored_region | unexpected_event |
                            # prediction_error | contradiction | new_sensor | changed_environment
    information_hypothesis: str
    uncertainty: float = 1.0        # how much uncertainty this could reduce

    def snapshot(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id, "target": self.target,
            "novelty_type": self.novelty_type,
            "information_hypothesis": self.information_hypothesis,
            "uncertainty": round(self.uncertainty, 4),
        }


class NoveltyDetector:
    """Detects novelty sources and forms candidates with hypotheses (doc 06 Step 1)."""

    def candidates(
        self,
        *,
        unseen_objects: tuple[str, ...] = (),
        unexplored_regions: tuple[str, ...] = (),
        unexpected_events: tuple[str, ...] = (),
        prediction_errors: tuple[str, ...] = (),
        contradictions: tuple[str, ...] = (),
        new_sensors: tuple[str, ...] = (),
        changed_environment: tuple[str, ...] = (),
    ) -> tuple[NoveltyCandidate, ...]:
        candidates: list[NoveltyCandidate] = []
        for target in unseen_objects:
            candidates.append(self._make(target, "unseen_object",
                                         f"identify unseen object {target}", 0.8))
        for target in unexplored_regions:
            candidates.append(self._make(target, "unexplored_region",
                                         f"map region {target}", 0.7))
        for target in unexpected_events:
            candidates.append(self._make(target, "unexpected_event",
                                         f"explain unexpected event {target}", 0.9))
        for target in prediction_errors:
            candidates.append(self._make(target, "prediction_error",
                                         f"resolve prediction error at {target}", 0.85))
        for target in contradictions:
            candidates.append(self._make(target, "contradiction",
                                         f"resolve contradictory observations of {target}", 0.75))
        for target in new_sensors:
            candidates.append(self._make(target, "new_sensor",
                                         f"characterize new sensor {target}", 0.6))
        for target in changed_environment:
            candidates.append(self._make(target, "changed_environment",
                                         f"assess change at {target}", 0.7))
        return tuple(candidates)

    @staticmethod
    def _make(target: str, novelty_type: str, hypothesis: str, uncertainty: float) -> NoveltyCandidate:
        return NoveltyCandidate(
            candidate_id=f"nov-{uuid4().hex[:10]}", target=target,
            novelty_type=novelty_type, information_hypothesis=hypothesis,
            uncertainty=uncertainty,
        )


class CuriosityScorer:
    """``expected_uncertainty_reduction × future_usefulness - cost - risk``
    (doc 06 Step 3). Never explore merely because something is novel."""

    def score(
        self,
        *,
        uncertainty_reduction: float,
        future_usefulness: float,
        cost: float,
        risk: float,
    ) -> float:
        return uncertainty_reduction * future_usefulness - cost - risk


@dataclass(frozen=True)
class ExplorationBudget:
    max_duration_cycles: int = 20
    max_distance_m: float = 10.0
    max_energy: float = 1.0
    max_perception_calls: int = 5
    max_retries: int = 2
    forbidden_regions: tuple[tuple[float, float, float, float], ...] = ()
    stop_gain_threshold: float = 0.05      # below this, exploration stops

    def exhausted(self, *, cycles: int, distance_m: float, energy: float,
                  perception_calls: int, retries: int) -> bool:
        return (
            cycles >= self.max_duration_cycles
            or distance_m >= self.max_distance_m
            or energy >= self.max_energy
            or perception_calls >= self.max_perception_calls
            or retries >= self.max_retries
        )

    def region_forbidden(self, x: float, y: float) -> bool:
        return any(
            rx1 <= x <= rx2 and ry1 <= y <= ry2
            for rx1, ry1, rx2, ry2 in self.forbidden_regions
        )


@dataclass
class ExplorationStep:
    """One safe observation step (doc 06 Step 5: existing sensors first)."""
    action: str                      # observe | rotate_camera | inspect_nearby | move
    target: str
    gain: float

    def snapshot(self) -> dict[str, Any]:
        return {"action": self.action, "target": self.target, "gain": round(self.gain, 4)}


class ExplorationPlanner:
    """Incremental, safe-first exploration; stops when gain drops below threshold."""

    def __init__(self, budget: ExplorationBudget | None = None,
                 scorer: CuriosityScorer | None = None) -> None:
        self.budget = budget or ExplorationBudget()
        self.scorer = scorer or CuriosityScorer()
        self._camera_rotations = 0

    def plan(self, candidate: NoveltyCandidate, *, future_usefulness: float = 0.5) -> list[ExplorationStep]:
        """Build the exploration step ladder for a candidate, bounded by gain."""
        steps: list[ExplorationStep] = []
        # 1. Existing sensors first (cheap, safe).
        steps.append(ExplorationStep("observe", candidate.target, self._gain(candidate, 0.5, future_usefulness)))
        # 2. Rotate camera if safe (bounded rotations).
        if self._camera_rotations < 2:
            steps.append(ExplorationStep("rotate_camera", candidate.target, self._gain(candidate, 0.35, future_usefulness)))
        # 3. Inspect nearby area.
        steps.append(ExplorationStep("inspect_nearby", candidate.target, self._gain(candidate, 0.2, future_usefulness)))
        # 4. Move only if necessary.
        steps.append(ExplorationStep("move", candidate.target, self._gain(candidate, 0.1, future_usefulness)))
        # Drop steps whose gain is below the stop threshold.
        return [step for step in steps if step.gain >= self.budget.stop_gain_threshold]

    def _gain(self, candidate: NoveltyCandidate, usefulness_factor: float, future_usefulness: float) -> float:
        return self.scorer.score(
            uncertainty_reduction=candidate.uncertainty * usefulness_factor,
            future_usefulness=future_usefulness,
            cost=0.1 * (usefulness_factor + 0.5),
            risk=0.05 if usefulness_factor > 0.1 else 0.0,
        )


@dataclass(frozen=True)
class ExplorationGoal:
    """A bounded exploration goal (doc 06 Step 4-5)."""
    goal_id: str
    target: str
    max_steps: int
    budget: ExplorationBudget

    def snapshot(self) -> dict[str, Any]:
        return {"goal_id": self.goal_id, "target": self.target,
                "max_steps": self.max_steps,
                "budget": {k: v for k, v in self.budget.__dict__.items() if not isinstance(v, tuple)}}


class CuriosityGoalGenerator:
    """Generates bounded exploration goals only when there is spare budget
    (doc 06 Step 2); capped like other background goals (doc 02 Step 8)."""

    def __init__(self, *, max_background_goals: int = 3, max_steps_per_goal: int = 10) -> None:
        self.max_background_goals = max_background_goals
        self.max_steps_per_goal = max_steps_per_goal
        self._generated: list[ExplorationGoal] = []

    def generate(self, candidate: NoveltyCandidate, *, budget: ExplorationBudget | None = None,
                 spare_autonomy_budget: bool = True) -> ExplorationGoal | None:
        if not spare_autonomy_budget:
            return None
        if len(self._generated) >= self.max_background_goals:
            return None
        goal = ExplorationGoal(
            goal_id=f"explore-{uuid4().hex[:10]}", target=candidate.target,
            max_steps=self.max_steps_per_goal, budget=budget or ExplorationBudget(),
        )
        self._generated.append(goal)
        return goal

    def generated(self) -> tuple[ExplorationGoal, ...]:
        return tuple(self._generated)


@dataclass
class ExplorationOutcome:
    exploration_id: str
    target: str
    improved_future_task: bool       # did this exploration actually pay off?
    gain: float = 0.0

    def snapshot(self) -> dict[str, Any]:
        return {"exploration_id": self.exploration_id, "target": self.target,
                "improved_future_task": self.improved_future_task, "gain": round(self.gain, 4)}


class ExplorationPreferenceLearner:
    """Learns which explorations improved future task performance (doc 06 Step 7).

    Usefulness weights are updated from verified outcomes, so the policy drifts
    toward useful exploration — not novelty-seeking.
    """

    def __init__(self) -> None:
        self._outcomes: list[ExplorationOutcome] = []
        self._usefulness_by_type: dict[str, float] = {}

    def record(self, *, target: str, novelty_type: str, improved_future_task: bool, gain: float = 0.0) -> None:
        self._outcomes.append(ExplorationOutcome(
            exploration_id=f"exp-{uuid4().hex[:10]}", target=target,
            improved_future_task=improved_future_task, gain=gain,
        ))
        current = self._usefulness_by_type.get(novelty_type, 0.5)
        # Small learning step from verified outcomes only.
        updated = current + (0.1 if improved_future_task else -0.05)
        self._usefulness_by_type[novelty_type] = max(0.0, min(1.0, updated))

    def usefulness(self, novelty_type: str) -> float:
        return self._usefulness_by_type.get(novelty_type, 0.5)

    def outcomes(self) -> tuple[ExplorationOutcome, ...]:
        return tuple(self._outcomes)
