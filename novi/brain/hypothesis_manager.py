"""Hypothesis manager — real alternatives for predictive cognition (plan 22,
Phase 9, Tasks 9.2–9.3).

When a prediction fails, the brain must not jump straight to speech. It
generates competing hypotheses, scores them on probability / expected
evidence / risk / cost / relevance, gathers evidence, and only then updates
its belief (and optionally spawns a goal).

Deterministic and hardware-free: scoring is rule-based and explainable.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


@dataclass
class Hypothesis:
    label: str
    probability: float = 0.5
    expected_evidence: list[str] = field(default_factory=list)
    risk: float = 0.0  # cost of acting on it if wrong
    cost: float = 0.0  # cost of investigating it
    relevance: float = 0.5  # relevance to the current goal/situation
    evidence_for: int = 0
    evidence_against: int = 0
    hypothesis_id: str = field(default_factory=lambda: f"hyp-{uuid.uuid4().hex[:8]}")

    @property
    def score(self) -> float:
        """Composite: probability × relevance, discounted by risk/cost."""
        base = _clamp01(self.probability * self.relevance)
        discounted = base - 0.15 * self.risk - 0.05 * self.cost
        return _clamp01(discounted)

    def snapshot(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "label": self.label,
            "probability": round(self.probability, 3),
            "expected_evidence": list(self.expected_evidence),
            "risk": round(self.risk, 3),
            "cost": round(self.cost, 3),
            "relevance": round(self.relevance, 3),
            "evidence_for": self.evidence_for,
            "evidence_against": self.evidence_against,
            "score": round(self.score, 3),
        }


class HypothesisManager:
    """Maintains competing explanations of one observation (Task 9.3)."""

    def __init__(self, *, max_alternatives: int = 4) -> None:
        self._hypotheses: list[Hypothesis] = []
        self.max_alternatives = max_alternatives
        self.observation: str = ""
        self._resolved: Hypothesis | None = None

    # ---- generation ----

    def generate(
        self,
        observation: str,
        alternatives: list[str],
        *,
        prior: list[float] | None = None,
        evidence: list[list[str]] | None = None,
        risks: list[float] | None = None,
        costs: list[float] | None = None,
        relevance: list[float] | None = None,
    ) -> list[Hypothesis]:
        """Create scored alternatives for an observed prediction failure.

        Example (plan §9): "Vano closes laptop and picks up keys" →
          A: Vano is leaving          B: Vano is taking a break
          C: Vano is changing location
        """
        self.observation = observation
        self._resolved = None
        self._hypotheses = []
        n = min(len(alternatives), self.max_alternatives)
        for i in range(n):
            self._hypotheses.append(
                Hypothesis(
                    label=alternatives[i],
                    probability=_clamp01(prior[i] if prior and i < len(prior) else 0.5),
                    expected_evidence=list(evidence[i]) if evidence and i < len(evidence) else [],
                    risk=_clamp01(risks[i]) if risks and i < len(risks) else 0.0,
                    cost=_clamp01(costs[i]) if costs and i < len(costs) else 0.0,
                    relevance=_clamp01(relevance[i]) if relevance and i < len(relevance) else 0.5,
                )
            )
        return list(self._hypotheses)

    # ---- evidence ----

    def update_belief(self, *, label: str, supports: bool, strength: float = 1.0) -> Hypothesis | None:
        """Apply one piece of evidence to a hypothesis (Task 9.2)."""
        hyp = self._by_label(label)
        if hyp is None:
            return None
        strength = _clamp01(strength)
        if supports:
            hyp.evidence_for += 1
            hyp.probability = _clamp01(hyp.probability + 0.15 * strength)
        else:
            hyp.evidence_against += 1
            hyp.probability = _clamp01(hyp.probability - 0.2 * strength)
        return hyp

    def resolve(self) -> Hypothesis | None:
        """Return the winner when it is clearly ahead; else None (ambiguity
        is preserved — belief revision never forces a choice)."""
        ranked = sorted(self._hypotheses, key=lambda h: h.score, reverse=True)
        if not ranked:
            return None
        best, second = ranked[0], (ranked[1] if len(ranked) > 1 else None)
        if second is None or best.score - second.score >= 0.2:
            self._resolved = best
            return best
        return None

    # ---- queries ----

    def _by_label(self, label: str) -> Hypothesis | None:
        for hyp in self._hypotheses:
            if hyp.label.lower() == str(label).lower():
                return hyp
        return None

    def all(self) -> list[Hypothesis]:
        return list(self._hypotheses)

    def best(self) -> Hypothesis | None:
        ranked = sorted(self._hypotheses, key=lambda h: h.score, reverse=True)
        return ranked[0] if ranked else None

    def snapshot(self) -> dict[str, Any]:
        return {
            "observation": self.observation,
            "alternatives": [h.snapshot() for h in self._hypotheses],
            "resolved": self._resolved.snapshot() if self._resolved else None,
        }
