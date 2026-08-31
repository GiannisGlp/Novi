"""Perspective-taking engine (plan 24, Phase 5).

Maintains multiple hypotheses about the user's affective/social state rather
than assuming a single interpretation, then selects behavior that is robust
across the likely interpretations (plan §9).

Example (plan §9): "Fine. Whatever." → H1 frustrated .55, H2 tired .20,
H3 disengaged .15, H4 casual .10. The robust action is the one with the most
probability mass — e.g. "reduce pressure, ask only if necessary" — because it
is safe under the most likely readings. This is more mature than claiming
certainty about a private mental state.

Deterministic and hardware-free: hypotheses are scored from supplied priors
and evidence; the engine never invents interpretations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .affective_evidence import utc_now_iso


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


@dataclass
class PerspectiveHypothesis:
    """One candidate interpretation of the user's state (plan §9)."""

    interpretation: str
    probability: float = 0.0
    supporting_evidence: list[str] = field(default_factory=list)
    contradictory_evidence: list[str] = field(default_factory=list)
    expected_observations: list[str] = field(default_factory=list)
    consequence: str = ""
    updated_at: str = field(default_factory=utc_now_iso)

    def snapshot(self) -> dict[str, Any]:
        return {
            "interpretation": self.interpretation,
            "probability": round(self.probability, 3),
            "supporting_evidence": list(self.supporting_evidence),
            "contradictory_evidence": list(self.contradictory_evidence),
            "expected_observations": list(self.expected_observations),
            "consequence": self.consequence,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "PerspectiveHypothesis":
        return cls(
            interpretation=str(data.get("interpretation", "")),
            probability=float(data.get("probability", 0.0)),
            supporting_evidence=list(data.get("supporting_evidence", [])),
            contradictory_evidence=list(data.get("contradictory_evidence", [])),
            expected_observations=list(data.get("expected_observations", [])),
            consequence=str(data.get("consequence", "")),
            updated_at=str(data.get("updated_at", "")),
        )


class PerspectiveEngine:
    """Scored hypotheses about the user's state + robust action selection."""

    def __init__(self) -> None:
        self._hypotheses: list[PerspectiveHypothesis] = []
        self._utterance: str = ""

    def hypothesize(
        self,
        utterance: str,
        *,
        interpretations: list[str],
        priors: list[float],
        supporting: list[list[str]] | None = None,
        contradictory: list[list[str]] | None = None,
        expected: list[list[str]] | None = None,
        consequences: list[str] | None = None,
    ) -> list[PerspectiveHypothesis]:
        """Create scored hypotheses from priors and evidence (plan §9)."""
        self._utterance = utterance
        self._hypotheses = []
        n = len(interpretations)
        if n == 0:
            return self._hypotheses
        priors = [priors[i] if i < len(priors) else 0.0 for i in range(n)]
        total = sum(priors) or 1.0
        for i, interpretation in enumerate(interpretations):
            self._hypotheses.append(
                PerspectiveHypothesis(
                    interpretation=interpretation,
                    probability=_clamp01(priors[i] / total),
                    supporting_evidence=list(supporting[i]) if supporting and i < len(supporting) else [],
                    contradictory_evidence=list(contradictory[i]) if contradictory and i < len(contradictory) else [],
                    expected_observations=list(expected[i]) if expected and i < len(expected) else [],
                    consequence=consequences[i] if consequences and i < len(consequences) else "",
                )
            )
        return self._hypotheses

    def update(self, interpretation: str, *, supports: bool, strength: float = 0.5) -> PerspectiveHypothesis | None:
        """Adjust one hypothesis's probability on new evidence, then renormalize."""
        hyp = self._find(interpretation)
        if hyp is None:
            return None
        factor = 1.0 + _clamp01(strength) if supports else 1.0 - _clamp01(strength)
        hyp.probability = _clamp01(hyp.probability * factor)
        self._renormalize()
        hyp.updated_at = utc_now_iso()
        return hyp

    def robust_action(self, default: str = "") -> str:
        """Select the consequence with the most probability mass (plan §9)."""
        if not self._hypotheses:
            return default
        mass: dict[str, float] = {}
        for hyp in self._hypotheses:
            key = hyp.consequence or default
            mass[key] = mass.get(key, 0.0) + hyp.probability
        if not mass:
            return default
        return max(mass, key=mass.get)

    def best(self) -> PerspectiveHypothesis | None:
        return max(self._hypotheses, key=lambda h: h.probability) if self._hypotheses else None

    def all(self) -> list[PerspectiveHypothesis]:
        return list(self._hypotheses)

    def utterance(self) -> str:
        return self._utterance

    def snapshot(self) -> dict[str, Any]:
        return {
            "utterance": self._utterance,
            "hypotheses": [h.snapshot() for h in self._hypotheses],
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "PerspectiveEngine":
        engine = cls()
        engine._utterance = str(data.get("utterance", ""))
        engine._hypotheses = [PerspectiveHypothesis.from_snapshot(h) for h in data.get("hypotheses", [])]
        return engine

    def _find(self, interpretation: str) -> PerspectiveHypothesis | None:
        for hyp in self._hypotheses:
            if hyp.interpretation == interpretation:
                return hyp
        return None

    def _renormalize(self) -> None:
        total = sum(h.probability for h in self._hypotheses) or 1.0
        for hyp in self._hypotheses:
            hyp.probability = _clamp01(hyp.probability / total)
