"""Learned importance scoring for memories (gap-audit plan Phase C4).

Importance = f(curiosity trait, evidence confidence, attention score):
a deterministic, explainable scorer stamped into memory provenance at admit
time and consumed by retrieval ranking and consolidation priority.

Design boundaries:
  - Deterministic and bounded (0..1); no learned parameters yet — the curiosity
    trait comes from the Soul and modulates how much novelty is valued.
  - Importance is metadata, never a privacy class or an authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PROTECTED_IMPORTANCE = 0.8  # consolidation exempts records at/above this

_TRUST_BY_VERIFICATION = {"verified": 1.0, "consolidated": 0.8, "unverified": 0.4}


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


@dataclass(frozen=True)
class ImportanceWeights:
    confidence: float = 0.40
    attention: float = 0.25
    novelty: float = 0.35


class ImportanceModel:
    """Scores how much a memory is worth keeping, in [0, 1]."""

    def __init__(
        self,
        *,
        weights: ImportanceWeights | None = None,
        curiosity_trait: float = 0.85,
        novelty_floor: float = 0.2,
        novelty_decay: float = 0.1,
    ) -> None:
        self.weights = weights or ImportanceWeights()
        self.curiosity_trait = _clamp01(curiosity_trait)
        self.novelty_floor = _clamp01(novelty_floor)
        self.novelty_decay = max(0.0, min(1.0, novelty_decay))

    def novelty_for(self, seen_count: int) -> float:
        """First sight of something is maximally novel; repeats decay to a floor."""
        if seen_count <= 0:
            return 1.0
        return max(self.novelty_floor, 1.0 - self.novelty_decay * seen_count)

    def score(self, *, confidence: float = 0.5, attention: float = 0.0, novelty: float = 0.5) -> float:
        """Weighted fusion; the curiosity trait scales the novelty term."""
        w = self.weights
        total = w.confidence + w.attention + w.novelty
        if total <= 0:
            return 0.0
        # A curious mind discounts familiarity more: the novelty term is
        # scaled by (0.6 + 0.4 * trait), so trait=1 keeps full novelty weight
        # and trait=0 keeps only 60% of it.
        novelty_term = _clamp01(novelty) * (0.6 + 0.4 * self.curiosity_trait)
        raw = (
            _clamp01(confidence) * w.confidence
            + _clamp01(attention) * w.attention
            + novelty_term * w.novelty
        )
        return _clamp01(raw / total)


def provenance_trust(record: Any) -> float:
    """How trustworthy a record's origin is, in [0, 1] (retrieval weighting).

    Combines verification status with the source recorded at admission;
    unknown fields degrade gracefully toward the middle of the scale.
    """
    verification = str(getattr(record, "verification_status", "") or "").lower()
    provenance = getattr(record, "provenance", None)
    source_class = ""
    if isinstance(provenance, dict):
        source_class = str(provenance.get("source_class") or provenance.get("source") or "").lower()

    base = _TRUST_BY_VERIFICATION.get(verification, 0.6)
    sensor_bonus = 0.0
    if any(k in source_class for k in ("sensor", "camera", "vision")):
        sensor_bonus = 0.1
    penalty = 0.0 if verification == "verified" else 0.05
    return _clamp01(base + sensor_bonus - penalty)


def record_importance(record: Any) -> float:
    """Stamped importance of a record; falls back to its confidence."""
    provenance = getattr(record, "provenance", None)
    if isinstance(provenance, dict):
        raw = provenance.get("importance")
        if raw is not None:
            return _clamp01(raw)
    return _clamp01(getattr(record, "confidence", 0.0))
