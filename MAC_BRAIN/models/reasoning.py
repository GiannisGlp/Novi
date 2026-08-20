from __future__ import annotations

import json
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
    }
    DEFAULT_ACTION = "observe"

    def decide(self, *, conclusion: str, confidence: float, situation: dict[str, Any], recall: Any = ()) -> ActionIntent:
        action = self.ACTION_MAP.get(conclusion, self.DEFAULT_ACTION)
        rationale = conclusion
        if recall:
            rationale = f"{conclusion} (recalled {len(recall)} relevant memories)"
        return ActionIntent(action=action, parameters={}, rationale=rationale)


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
