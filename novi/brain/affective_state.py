"""Transient affective state (plan 24, Phase 2).

A short-lived, continuously-recomputed estimate of the user's affective
state, derived from observable evidence. Every dimension carries:

    value         — the estimate [0,1]
    confidence    — how confident Novi is in the estimate [0,1]
    source        — which modality/fusion produced it
    last_updated  — ISO-8601 UTC timestamp
    decay_seconds — how fast the dimension decays without reinforcement

These are *estimates from observable signals*, never clinical measurements or
definitive emotional diagnoses (plan §6). The state must be transient: it
decays toward baseline unless reinforced, so a single tense interaction does
not become the permanent emotional state of the conversation (plan §28).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# The canonical dimension set (plan §6). Each is a likelihood/estimate, not a
# diagnosis.
DIMENSIONS: tuple[str, ...] = (
    "valence_estimate",
    "arousal_estimate",
    "engagement",
    "frustration_likelihood",
    "fatigue_likelihood",
    "stress_likelihood",
    "enthusiasm_likelihood",
    "confusion_likelihood",
    "comfort_likelihood",
    "social_availability",
)

DEFAULT_DECAY_SECONDS = 90.0


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AffectiveDimension:
    """One dimension of the affective state (plan §6)."""

    value: float = 0.0
    confidence: float = 0.0
    source: str = ""
    last_updated: str = field(default_factory=utc_now_iso)
    decay_seconds: float = DEFAULT_DECAY_SECONDS

    def __post_init__(self) -> None:
        self.value = _clamp01(self.value)
        self.confidence = _clamp01(self.confidence)

    def snapshot(self) -> dict[str, Any]:
        return {
            "value": round(self.value, 3),
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "last_updated": self.last_updated,
            "decay_seconds": self.decay_seconds,
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "AffectiveDimension":
        return cls(
            value=float(data.get("value", 0.0)),
            confidence=float(data.get("confidence", 0.0)),
            source=str(data.get("source", "")),
            last_updated=str(data.get("last_updated", "") or utc_now_iso()),
            decay_seconds=float(data.get("decay_seconds", DEFAULT_DECAY_SECONDS)),
        )


class AffectiveState:
    """Transient, decaying affective state over the canonical dimensions."""

    DIMENSIONS: tuple[str, ...] = DIMENSIONS

    def __init__(self) -> None:
        self.dimensions: dict[str, AffectiveDimension] = {
            name: AffectiveDimension() for name in DIMENSIONS
        }

    def update(
        self,
        name: str,
        *,
        value: float,
        confidence: float,
        source: str,
        decay_seconds: float = DEFAULT_DECAY_SECONDS,
        now: str | None = None,
    ) -> bool:
        """Set/refresh one dimension. Unknown names are ignored (fail safe)."""
        if name not in self.dimensions:
            return False
        self.dimensions[name] = AffectiveDimension(
            value=_clamp01(value),
            confidence=_clamp01(confidence),
            source=source,
            last_updated=now or utc_now_iso(),
            decay_seconds=decay_seconds,
        )
        return True

    def decay(self, elapsed_seconds: float) -> None:
        """Exponential decay toward baseline (plan §28).

        state(t) = state(previous) × decay + new_evidence. Without new
        evidence each dimension falls toward 0 at its own rate.
        """
        for dim in self.dimensions.values():
            if dim.value <= 0.0:
                continue
            rate = 1.0 / max(dim.decay_seconds, 1.0)
            dim.value = _clamp01(dim.value * (1.0 - rate * elapsed_seconds))

    def get(self, name: str) -> AffectiveDimension | None:
        return self.dimensions.get(name)

    def peak(self) -> tuple[str, AffectiveDimension]:
        """The highest-confidence, highest-value dimension (for policy)."""
        best_name = DIMENSIONS[0]
        best = self.dimensions[best_name]
        for name, dim in self.dimensions.items():
            if dim.value * dim.confidence > best.value * best.confidence:
                best_name, best = name, dim
        return best_name, best

    def snapshot(self) -> dict[str, Any]:
        return {name: dim.snapshot() for name, dim in self.dimensions.items()}

    @classmethod
    def from_snapshot(cls, data: dict[str, Any] | None) -> "AffectiveState":
        state = cls()
        if not data:
            return state
        for name, raw in data.items():
            if name in state.dimensions:
                state.dimensions[name] = AffectiveDimension.from_snapshot(raw)
        return state
