from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .provider import MacModelProvider
from .validation import StructuredOutputValidator, ValidationResult, action_output_spec


@dataclass(frozen=True)
class ActionIntent:
    """A bounded behavioral decision produced by a reasoning provider."""

    action: str
    parameters: dict[str, Any]
    rationale: str

    def as_proposal_fields(self) -> dict[str, Any]:
        return {"action": self.action, "parameters": self.parameters, "reason": self.rationale}


class ReasoningProvider(Protocol):
    """Capability boundary for the reasoning/behavioral layer.

    Maps a cognition conclusion into a concrete bounded action intent. This is
    the autonomy-facing decision: Cognition understands, this layer chooses what
    to pursue, and Policy/Safety still gates the resulting ActionProposal.

    ``recall`` is a sequence of serializable memory summaries retrieved before
    the decision (relevant past experience), used as additional context.
    """

    def decide(self, *, conclusion: str, confidence: float, situation: Any, recall: Any = ()) -> ActionIntent: ...


class DeterministicReasoningProvider:
    """Bounded symbolic reasoning: maps cognition conclusions to actions.

    Deterministic and CI-safe. This is the default reasoning layer and is kept
    deliberately simple; safety-critical reasoning must not be a black box.
    """

    ACTION_MAP = {
        "person_alice_is_relevant_to_current_situation": "observe",
        "environmental_change_is_relevant": "inspect",
        "human_speech_observed": "observe",
        "no_high_salience_change_detected": "wait",
        "causal_change_inferred": "inspect",
        "goal_relevant_change": "observe",
    }
    DEFAULT_ACTION = "observe"

    def decide(self, *, conclusion: str, confidence: float, situation: dict[str, Any], recall: Any = ()) -> ActionIntent:
        action = self.ACTION_MAP.get(conclusion, self.DEFAULT_ACTION)
        rationale = conclusion
        if recall:
            rationale = f"{conclusion} (recalled {len(recall)} relevant memories)"
        return ActionIntent(action=action, parameters={}, rationale=rationale)


class DeliberativeReasoningProvider:
    """Situation-aware reasoning (Reasoning 2.0).

    Scores candidate actions from the full situation (conclusion, confidence,
    knowledge relations, goal context, recalled memories, and the latest
    reflection) instead of a single conclusion→action lookup. Deterministic and
    CI-safe; Policy/Safety still gates every action at execution time.
    """

    def __init__(self, *, default_action: str = "observe") -> None:
        self.default_action = default_action
        # Phase 3b: explicit alternative evaluation — success/cost/risk triples
        # with one fixed, auditable evaluator per provider.
        from .deliberation import AlternativeEvaluator
        self.evaluator = AlternativeEvaluator()
        self.last_option_scores: dict[str, Any] = {}
        self.last_action: str = self.default_action

    def decide(self, *, conclusion: str, confidence: float, situation: dict[str, Any], recall: Any = ()) -> ActionIntent:
        success = self._score(conclusion, confidence, situation, recall)
        option_scores = self._option_scores(success, confidence, situation)
        options = sorted(option_scores)
        any_signal = any(s.expected_success > 0.0 for s in option_scores.values())
        if any_signal:
            action, self.last_option_scores = self.evaluator.select(options, option_scores, fallback=self.default_action)
        else:
            # When no signal is present every score is 0.0; fall back to the
            # configured safe default instead of picking the first action.
            action = self.default_action
            self.last_option_scores = option_scores
        self.last_action = action
        best = self.last_option_scores.get(action)
        evidence = f" success={best.expected_success:.2f} cost={best.cost:.2f} risk={best.risk:.2f}" if best else ""
        recalled = f" recalled={len(recall)}" if recall else ""
        rationale = f"deliberative:{conclusion} best={action}{recalled}{evidence}"
        return ActionIntent(action=action, parameters={}, rationale=rationale)

    def _option_scores(self, success: dict[str, float], confidence: float, situation: dict[str, Any]) -> dict[str, Any]:
        """Phase 3b: turn evidence into explicit success/cost/risk triples.

        - expected_success: accumulated evidence, gated by cognitive
          confidence (an uncertain world caps every option);
        - cost: declared per-action budget; repeating a just-FAILED action
          costs more (self-correction), and looking around is cheap;
        - risk: base exposure per action class, scaled up by uncertainty.
        """
        from .deliberation import OptionScore
        situation = situation or {}
        base_cost = {"observe": 0.1, "wait": 0.05, "inspect": 0.15, "move_forward": 0.35, "turn_left": 0.25, "turn_right": 0.25}
        base_risk = {"observe": 0.05, "wait": 0.02, "inspect": 0.1, "move_forward": 0.3, "turn_left": 0.2, "turn_right": 0.2}
        reflection = situation.get("reflection")
        c = max(0.0, min(1.0, float(confidence)))
        scored: dict[str, Any] = {}
        for action, evidence in success.items():
            expected_success = max(0.0, min(1.0, evidence * (0.6 + 0.4 * c)))
            cost = base_cost.get(action, 0.2)
            risk = min(1.0, base_risk.get(action, 0.1) + (1.0 - c) * 0.2)
            if reflection and not reflection.get("effective", True) and str(reflection.get("action", "")) == action:
                # Phase 3b: repeating a just-failed action is expensive.
                cost = min(1.0, cost + 0.5)
                expected_success = max(0.0, expected_success - 0.2)
            scored[action] = OptionScore(action=action, expected_success=expected_success, cost=cost, risk=risk)
        return scored

    def _score(self, conclusion: str, confidence: float, situation: dict[str, Any], recall: Any) -> dict[str, float]:
        """Success-evidence accumulation over the full situation (unchanged
        signal semantics; explicit cost/risk tables live in _option_scores)."""
        situation = situation or {}
        scores: dict[str, float] = {a: 0.0 for a in ("inspect", "observe", "wait", "move_forward", "turn_left", "turn_right")}
        inferences = situation.get("inferences") or []
        relations = situation.get("relations") or []
        goal = situation.get("goal")
        reflection = situation.get("reflection")

        # Causal/environmental change -> investigate
        if conclusion == "causal_change_inferred" or inferences:
            scores["inspect"] += 1.0
        if conclusion == "environmental_change_is_relevant":
            scores["inspect"] += 0.8
        # Person / speech present -> attend
        if conclusion == "person_alice_is_relevant_to_current_situation":
            scores["observe"] += 0.9
        if conclusion == "human_speech_observed":
            scores["observe"] += 1.0
        # Goal context: near target -> observe (goal controller drives movement)
        if goal and goal.get("distance_to_goal") is not None:
            distance = float(goal["distance_to_goal"])
            if distance < 0.5:
                scores["observe"] += 0.7
            elif distance < 2.0:
                scores["move_forward"] += 0.6
        # Recalled memories relevant -> attend
        if recall:
            scores["observe"] += 0.3
        # No salience -> wait
        if conclusion == "no_high_salience_change_detected" and not relations and not goal:
            scores["wait"] += 1.0
        # Self-correction: if the last action was ineffective, avoid repeating it
        # and prefer to look around instead (Phase 3b: the avoid signal stays in
        # the evidence map; the explicit cost rise for the failed action lives
        # in _option_scores).
        if reflection and not reflection.get("effective", True):
            prev = str(reflection.get("action", ""))
            if prev in scores:
                scores[prev] -= 1.0
            scores["observe"] += 0.5
        return scores


class LLMReasoningProvider:
    """Real reasoning model behind ``MacModelProvider``.

    Delegates the conclusion→action decision to a local LLM reached through the
    existing model runtime. The model's JSON output is run through a
    structured-output validator against the allowed-action schema; a failing or
    out-of-allowlist result is rejected and replaced with the safe default action.

    The model must only ever be offered a *bounded* set of actions; Policy/Safety
    still gates every resulting action at execution time.
    """

    def __init__(self, provider: MacModelProvider, *, allowed_actions: frozenset[str], default_action: str = "observe") -> None:
        self.provider = provider
        self.allowed_actions = allowed_actions
        self.default_action = default_action
        self._validator = StructuredOutputValidator(action_output_spec(allowed_actions))
        self.last_validation: ValidationResult | None = None

    def decide(self, *, conclusion: str, confidence: float, situation: dict[str, Any], recall: Any = ()) -> ActionIntent:
        result = self.provider.invoke(
            {"conclusion": conclusion, "confidence": confidence, "situation": situation, "recall": list(recall)},
            invocation_id="reasoning-llm",
        )
        raw = result.output if result.status == "completed_on_time" else {}
        validation = self._validator.validate(raw)
        self.last_validation = validation
        if not validation.valid or not validation.value.get("action"):
            action = self.default_action
            parameters: dict[str, Any] = {}
        else:
            action = str(validation.value["action"])
            parameters = dict(validation.value.get("parameters", {}))
        recalled = f" recalled={len(recall)}"
        return ActionIntent(action=action, parameters=parameters, rationale=f"llm:{conclusion}{recalled if recall else ''}")
