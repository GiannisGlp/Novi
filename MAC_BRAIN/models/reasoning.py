from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from .provider import MacModelProvider


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
    existing model runtime. Requires a ``MacModelProvider`` whose backend returns
    a JSON payload of the form ``{"action": "<name>", "parameters": {...}}``.

    The model must only ever be offered a *bounded* set of actions; the returned
    action is validated against the allowlist at decision time and Policy/Safety
    still gates execution.
    """

    def __init__(self, provider: MacModelProvider, *, allowed_actions: frozenset[str], default_action: str = "observe") -> None:
        self.provider = provider
        self.allowed_actions = allowed_actions
        self.default_action = default_action

    def decide(self, *, conclusion: str, confidence: float, situation: dict[str, Any], recall: Any = ()) -> ActionIntent:
        result = self.provider.invoke(
            {"conclusion": conclusion, "confidence": confidence, "situation": situation, "recall": list(recall)},
            invocation_id="reasoning-llm",
        )
        raw = result.output if result.status == "completed_on_time" else {}
        action = str(raw.get("action", self.default_action))
        parameters = dict(raw.get("parameters", {})) if isinstance(raw.get("parameters"), dict) else {}
        if action not in self.allowed_actions:
            action = self.default_action
            parameters = {}
        recalled = f" recalled={len(recall)}"
        return ActionIntent(action=action, parameters=parameters, rationale=f"llm:{conclusion}{recalled if recall else ''}")
