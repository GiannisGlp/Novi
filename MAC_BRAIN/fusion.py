"""Multimodal fusion for the Mac Brain.

Implements docs/03-cognition/03 (multimodal cognition) and docs/02-novi-brain/16
(multimodal fusion) as a deterministic, model-independent layer:

  - normalizes observations from independent modalities into `ModalityObservation`;
  - **temporal alignment** via a bounded freshness window (stale evidence is rejected);
  - **entity association** groups observations by entity;
  - **evidence fusion** combines per-entity evidence with a noisy-OR confidence that
    rises with agreement across modalities and retains all per-modality provenance;
  - **conflict handling** — when the same entity has several strong, disagreeing
    values, both are preserved, confidence is reduced, and no false certainty is set;
  - **graceful degradation** — missing/failed modalities do not block the rest.

Boundaries honored (docs/03-cognition 03):
  - The fused result retains all contributing evidence (nothing is deleted).
  - Raw audio/video stay local; this layer only fuses derived observations.
  - Confidence reflects reliability and freshness; it never fabricates certainty.
  - Fusing is deterministic and replayable given the same input sequence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable

CONFLICT_THRESHOLD = 0.6


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


@dataclass(frozen=True)
class ModalityObservation:
    modality: str
    entity: str
    value: str
    confidence: float
    captured_at: str = ""
    received_at: str = ""
    source: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "modality": self.modality,
            "entity": self.entity,
            "value": self.value,
            "confidence": round(self.confidence, 3),
            "captured_at": self.captured_at,
            "received_at": self.received_at,
            "source": self.source,
        }


@dataclass
class FusedEvent:
    entity: str
    value: str
    confidence: float
    modalities: tuple[str, ...]
    contributions: tuple[ModalityObservation, ...]
    conflict: bool
    captured_at: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "entity": self.entity,
            "value": self.value,
            "confidence": round(self.confidence, 3),
            "modalities": list(self.modalities),
            "conflict": self.conflict,
            "captured_at": self.captured_at,
            "contributions": [c.snapshot() for c in self.contributions],
        }


def _noisy_or(confidences: Iterable[float]) -> float:
    product = 1.0
    for c in confidences:
        product *= 1.0 - _clamp01(c)
    return 1.0 - product


class MultimodalFusion:
    """Confidence-weighted multimodal event fusion with provenance retention."""

    def __init__(self, max_age: float = 5.0, conflict_threshold: float = CONFLICT_THRESHOLD) -> None:
        self.max_age = max_age  # temporal freshness window (arbitrary time units)
        self.conflict_threshold = conflict_threshold
        self._recent: list[FusedEvent] = []

    def ingest(self, observations: Iterable[ModalityObservation]) -> tuple[FusedEvent, ...]:
        """Fuse observations into events. Returns the fused events for this batch."""
        obs = list(observations)
        if not obs:
            return ()
        newest = max((o.received_at for o in obs), default="")
        # temporal alignment: reject stale observations older than max_age
        fresh = [o for o in obs if self._age(o.received_at, newest) <= self.max_age]
        by_entity: dict[str, list[ModalityObservation]] = {}
        for o in fresh:
            by_entity.setdefault(o.entity, []).append(o)

        events: list[FusedEvent] = []
        for entity, group in by_entity.items():
            by_value: dict[str, list[ModalityObservation]] = {}
            for o in group:
                by_value.setdefault(o.value, []).append(o)
            for value, vgroup in by_value.items():
                conf = _noisy_or(o.confidence for o in vgroup)
                mods = tuple(sorted({o.modality for o in vgroup}))
                latest = max((o.received_at for o in vgroup), default="")
                events.append(
                    FusedEvent(entity=entity, value=value, confidence=conf, modalities=mods, contributions=tuple(vgroup), conflict=False, captured_at=latest)
                )
            # conflict handling: several strong, disagreeing values for the same entity
            strong = [e for e in events if e.entity == entity and e.confidence >= self.conflict_threshold]
            if len(strong) > 1:
                for e in strong:
                    e.conflict = True
                    e.confidence = min(e.confidence, 0.5)
        events.sort(key=lambda e: (e.entity, e.value))
        self._recent.extend(events)
        self._recent = self._recent[-100:]
        return tuple(events)

    @staticmethod
    def _parse(ts: str) -> float | None:
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None

    def _age(self, a: str, b: str) -> float:
        pa, pb = self._parse(a), self._parse(b)
        if pa is None or pb is None:
            return 0.0  # cannot measure age; do not reject
        return max(0.0, pb - pa)

    def recent(self, limit: int = 20) -> list[FusedEvent]:
        return self._recent[-limit:]

    def snapshot(self) -> dict[str, Any]:
        return {"recent": [e.snapshot() for e in self._recent]}

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "MultimodalFusion":
        model = cls()
        for row in data.get("recent", []):
            model._recent.append(
                FusedEvent(
                    entity=row["entity"],
                    value=row["value"],
                    confidence=row["confidence"],
                    modalities=tuple(row["modalities"]),
                    contributions=tuple(
                        ModalityObservation(
                            modality=c["modality"], entity=c["entity"], value=c["value"], confidence=c["confidence"], captured_at=c.get("captured_at", ""), received_at=c.get("received_at", ""), source=c.get("source", "")
                        )
                        for c in row.get("contributions", [])
                    ),
                    conflict=row.get("conflict", False),
                    captured_at=row.get("captured_at", ""),
                )
            )
        return model
