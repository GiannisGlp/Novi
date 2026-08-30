"""Interaction outcome recording (plan 22, Phase 18, Tasks 18.1–18.2).

Every meaningful interaction records: input, perception context, retrieved
memories, cognitive decision, chosen dialogue act, generated response, user
reaction, correction and outcome. Explicit user corrections become
high-confidence learning evidence (Task 18.2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

MAX_OUTCOME_HISTORY = 64


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class InteractionOutcome:
    interaction_id: str
    input_text: str
    person: str
    dialogue_act: str = ""
    response_text: str = ""
    reply_source: str = ""
    retrieved_memory_ids: list[str] = field(default_factory=list)
    perception_context: list[str] = field(default_factory=list)
    decision_reason: str = ""
    user_reaction: str = ""  # "" | correction | thanks | follow_up | none
    correction: str = ""
    outcome: str = ""  # "" | acknowledged | corrected | ignored
    confidence: float = 0.0
    at: str = field(default_factory=utc_now_iso)

    def snapshot(self) -> dict[str, Any]:
        return {
            "interaction_id": self.interaction_id,
            "input_text": self.input_text,
            "person": self.person,
            "dialogue_act": self.dialogue_act,
            "response_text": self.response_text,
            "reply_source": self.reply_source,
            "retrieved_memory_ids": list(self.retrieved_memory_ids),
            "perception_context": list(self.perception_context),
            "decision_reason": self.decision_reason,
            "user_reaction": self.user_reaction,
            "correction": self.correction,
            "outcome": self.outcome,
            "confidence": round(self.confidence, 3),
            "at": self.at,
        }


class OutcomeRecorder:
    """Bounded recorder; persists important outcomes through a callback."""

    def __init__(self) -> None:
        self._outcomes: list[InteractionOutcome] = []

    def record(self, outcome: InteractionOutcome) -> None:
        self._outcomes.append(outcome)
        self._outcomes = self._outcomes[-MAX_OUTCOME_HISTORY:]

    def recent(self, limit: int = 8) -> list[InteractionOutcome]:
        return list(self._outcomes[-limit:])

    def latest(self) -> InteractionOutcome | None:
        return self._outcomes[-1] if self._outcomes else None

    def corrections(self) -> list[InteractionOutcome]:
        """Task 18.2: explicit corrections are learning evidence."""
        return [o for o in self._outcomes if o.user_reaction == "correction"]

    def snapshot(self) -> dict[str, Any]:
        return {"count": len(self._outcomes), "recent": [o.snapshot() for o in self.recent(8)]}
