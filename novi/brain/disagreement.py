"""Disagreement maturity (plan 24, Phase 13).

Novi disagrees without "You're wrong." The phrasing scales with evidence
strength and uncertainty (plan §17):

  - strong evidence: "I don't think that's correct based on what I can see."
  - uncertain:      "I might be missing something, but..."
  - mild:           "I think that's slightly different from what the data shows."

Evidence is always provided rather than escalating.

Deterministic and hardware-free.
"""

from __future__ import annotations

from typing import Any

STRONG_EVIDENCE = 0.7
HIGH_UNCERTAINTY = 0.5


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


class DisagreementBuilder:
    """Renders a mature disagreement scaled to evidence and uncertainty."""

    def build(
        self,
        *,
        claim: str,
        evidence_strength: float,
        uncertainty: float,
        evidence: str,
    ) -> str:
        strength = _clamp01(evidence_strength)
        uncertainty = _clamp01(uncertainty)

        if strength >= STRONG_EVIDENCE and uncertainty < HIGH_UNCERTAINTY:
            opener = "I don't think that's correct based on what I can see"
        elif uncertainty >= HIGH_UNCERTAINTY:
            opener = "I might be missing something, but I think that's not quite right"
        else:
            opener = "I think that's slightly different from what the data shows"

        return f"{opener}. {evidence}."
