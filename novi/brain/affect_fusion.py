"""Multimodal affect fusion (plan 24, Phase 3).

Combines ``AffectiveEvidence`` records from voice, language, face/expression,
body orientation, gaze, gesture, conversation context and interaction history
into per-dimension likelihoods, weighted by source reliability.

Rules (plan §7):
  - weighted evidence based on source reliability;
  - if modalities conflict (strong, disagreeing contributions), retain
    uncertainty — confidence is capped, both sides are preserved;
  - a neutral face never means "emotion = false" — a neutral/uncertain signal
    contributes a moderate likelihood, it does not cancel other modalities.

Deterministic and hardware-free: providers are injected; this module only
combines evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .affective_evidence import AffectiveEvidence

CONFLICT_THRESHOLD = 0.6
CONFLICT_SPREAD = 0.4  # two strong contributions this far apart → conflict
CONFLICT_CONFIDENCE_CAP = 0.5


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


# signal_type → affective dimension (plan §7 example mapping)
_SIGNAL_DIMENSION: dict[str, str] = {
    "speech_volume": "frustration_likelihood",
    "speech_rate": "frustration_likelihood",
    "lexical_marker": "frustration_likelihood",
    "conversation_context": "frustration_likelihood",
    "interaction_history": "frustration_likelihood",
    "facial_signal": "frustration_likelihood",
    "pause_frequency": "fatigue_likelihood",
    "speech_energy": "stress_likelihood",
    "orientation": "engagement",
    "gaze": "engagement",
    "gesture": "arousal_estimate",
}

# categorical value → likelihood for the mapped dimension. "neutral" and
# "uncertain" are moderate (0.5), never 0 — a neutral face is not evidence of
# "no emotion" (plan §7).
_CATEGORICAL_LIKELIHOOD: dict[str, float] = {
    "high": 0.8,
    "medium": 0.5,
    "low": 0.2,
    "uncertain": 0.5,
    "neutral": 0.5,
    "calm": 0.2,
    "correction": 0.88,
    "positive": 0.8,
    "negative": 0.2,
    "toward_novi": 0.7,
    "away_from_novi": 0.3,
    "present": 0.7,
    "absent": 0.3,
}


def _value_likelihood(value: str) -> float | None:
    """Interpret an evidence value as a likelihood [0,1] or None if unknown."""
    try:
        return _clamp01(float(value))
    except (TypeError, ValueError):
        return _CATEGORICAL_LIKELIHOOD.get(str(value).strip().lower())


@dataclass
class FusedAffect:
    """One fused affective dimension (plan §7)."""

    dimension: str
    value: float
    confidence: float
    contributions: list[AffectiveEvidence] = field(default_factory=list)
    conflict: bool = False

    def snapshot(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "value": round(self.value, 3),
            "confidence": round(self.confidence, 3),
            "conflict": self.conflict,
            "contributions": [c.snapshot() for c in self.contributions],
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "FusedAffect":
        return cls(
            dimension=str(data.get("dimension", "")),
            value=float(data.get("value", 0.0)),
            confidence=float(data.get("confidence", 0.0)),
            conflict=bool(data.get("conflict", False)),
            contributions=[
                AffectiveEvidence.from_snapshot(c) for c in data.get("contributions", [])
            ],
        )


class AffectFusion:
    """Reliability-weighted multimodal affect fusion with conflict retention."""

    def __init__(
        self,
        *,
        conflict_threshold: float = CONFLICT_THRESHOLD,
        conflict_spread: float = CONFLICT_SPREAD,
    ) -> None:
        self.conflict_threshold = conflict_threshold
        self.conflict_spread = conflict_spread

    def fuse(self, evidence: list[AffectiveEvidence]) -> dict[str, FusedAffect]:
        """Combine evidence into per-dimension fused likelihoods."""
        by_dimension: dict[str, list[AffectiveEvidence]] = {}
        for ev in evidence:
            dimension = _SIGNAL_DIMENSION.get(ev.signal_type)
            if dimension is None:
                continue  # unknown signal type — ignore, never guess
            by_dimension.setdefault(dimension, []).append(ev)

        result: dict[str, FusedAffect] = {}
        for dimension, group in by_dimension.items():
            weighted_sum = 0.0
            weight_sum = 0.0
            likelihoods: list[float] = []
            for ev in group:
                likelihood = _value_likelihood(ev.value)
                if likelihood is None:
                    continue
                w = _clamp01(ev.reliability)
                weighted_sum += likelihood * w
                weight_sum += w
                likelihoods.append(likelihood)
            if weight_sum <= 0.0:
                continue
            value = _clamp01(weighted_sum / weight_sum)

            # confidence: reliability-weighted average of the contributors'
            # confidences, capped on conflict.
            confidence = sum(_clamp01(ev.confidence) * _clamp01(ev.reliability) for ev in group) / weight_sum
            conflict = self._is_conflict(likelihoods)
            if conflict:
                confidence = min(confidence, CONFLICT_CONFIDENCE_CAP)

            result[dimension] = FusedAffect(
                dimension=dimension,
                value=value,
                confidence=_clamp01(confidence),
                contributions=list(group),
                conflict=conflict,
            )
        return result

    @staticmethod
    def _is_conflict(likelihoods: list[float]) -> bool:
        """Two strong, disagreeing contributions → conflict (plan §7)."""
        strong = [l for l in likelihoods if l >= CONFLICT_THRESHOLD or l <= 1.0 - CONFLICT_THRESHOLD]
        if len(strong) < 2:
            return False
        return max(strong) - min(strong) >= CONFLICT_SPREAD
