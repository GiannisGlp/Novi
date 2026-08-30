"""Evaluation metrics for social cognition (plan 22, Phase 24).

Do not evaluate "human-like" only by subjective impression. Track:
grounding accuracy, memory retrieval precision/recall, contradiction
handling, turn-taking success, repetition rate, unnecessary verbosity,
appropriate/unnecessary/missed/duplicate initiative, cooldown violations,
and unsupported claim rate (plan §28).

The target is not "talk more like a human" — it is behave appropriately
given the same evidence and context a situated partner would have.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricsReport:
    counters: dict[str, int] = field(default_factory=dict)
    rates: dict[str, float] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        return {
            "counters": dict(self.counters),
            "rates": {k: round(v, 4) for k, v in self.rates.items()},
        }


class SocialMetricsTracker:
    """Deterministic counters over interaction evidence (plan §28)."""

    def __init__(self) -> None:
        self._c: dict[str, int] = {}
        self._denominators: dict[str, int] = {}

    def _inc(self, key: str, n: int = 1) -> None:
        self._c[key] = self._c.get(key, 0) + n

    def _den(self, key: str, n: int = 1) -> None:
        self._denominators[key] = self._denominators.get(key, 0) + n

    # ---- grounding (plan §28 Grounding) ----
    def record_grounding(self, *, correct: bool) -> None:
        self._den("grounding_attempts")
        if correct:
            self._inc("grounding_hits")
        else:
            self._inc("grounding_misses")

    # ---- memory ----
    def record_retrieval(self, *, relevant: bool) -> None:
        self._den("retrievals")
        if relevant:
            self._inc("retrieval_relevant")

    def record_contradiction_handled(self) -> None:
        self._inc("contradictions_handled")

    # ---- conversation ----
    def record_repetition(self) -> None:
        self._inc("repetitions")
        self._den("utterances")

    def record_verbosity_violation(self) -> None:
        self._inc("verbosity_violations")

    def record_utterance(self) -> None:
        self._den("utterances")

    # ---- initiative (plan §28 Initiative) ----
    def record_initiative(self, *, appropriate: bool, duplicate: bool = False, missed: bool = False) -> None:
        self._den("initiative_opportunities")
        if duplicate:
            self._inc("duplicate_initiatives")
        elif missed:
            self._inc("missed_initiatives")
        elif appropriate:
            self._inc("appropriate_initiatives")
        else:
            self._inc("unnecessary_initiatives")

    def record_cooldown_violation(self) -> None:
        self._inc("cooldown_violations")

    # ---- safety (plan §28 Safety) ----
    def record_unsupported_claim(self) -> None:
        self._inc("unsupported_claims")
        self._den("claims")

    def record_claim(self) -> None:
        self._den("claims")

    def record_ambiguous_action_blocked(self) -> None:
        self._inc("ambiguous_actions_blocked")

    # ---- report ----
    def report(self) -> MetricsReport:
        def rate(key: str, den: str) -> float:
            d = self._denominators.get(den, 0)
            return self._c.get(key, 0) / d if d else 0.0

        return MetricsReport(
            counters=dict(self._c),
            rates={
                "grounding_accuracy": rate("grounding_hits", "grounding_attempts"),
                "retrieval_precision": rate("retrieval_relevant", "retrievals"),
                "repetition_rate": rate("repetitions", "utterances"),
                "appropriate_initiative_rate": rate("appropriate_initiatives", "initiative_opportunities"),
                "unnecessary_initiative_rate": rate("unnecessary_initiatives", "initiative_opportunities"),
                "missed_initiative_rate": rate("missed_initiatives", "initiative_opportunities"),
                "duplicate_initiative_rate": rate("duplicate_initiatives", "initiative_opportunities"),
                "unsupported_claim_rate": rate("unsupported_claims", "claims"),
                "cooldown_violations": float(self._c.get("cooldown_violations", 0)),
            },
        )
