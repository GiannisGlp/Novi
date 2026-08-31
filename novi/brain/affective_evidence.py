"""Canonical affective evidence record (plan 24, Phase 1).

Every affective interpretation must be grounded in an *observable* evidence
record. Novi may reason about speech patterns, volume, tempo, pauses, words,
facial expression, gaze, gesture, interaction behavior, conversation history
and explicit statements — never about a private mental state directly.

``AffectiveEvidence`` preserves the source of each signal so downstream
fusion (Phase 3) can weight by source reliability and retain provenance.

Example (plan §5):

    {
      "signal_type": "speech_volume",
      "value": "high",
      "confidence": 0.91,
      "source": "microphone",
      "timestamp": "..."
    }

Deterministic and hardware-free: this module only defines the record and
constructs instances; providers are injected by callers.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class AffectiveEvidence:
    """One observable affective signal, with its source preserved.

    Fields (plan §5):
      evidence_id  — unique id for this record
      timestamp    — when the signal was captured (ISO-8601 UTC)
      source       — the sensor/provider that produced it (e.g. "microphone")
      modality     — voice | language | vision | body | context | ...
      signal_type  — speech_rate | speech_volume | pause_frequency |
                     lexical_marker | facial_signal | orientation | ...
      value        — the observed value (e.g. "high", "correction", "uncertain")
      confidence   — how confident the provider is in this observation [0,1]
      reliability  — how reliable this source is for this signal [0,1]
      provenance   — the exact estimator/algorithm that produced the value
      subject      — who the signal is about (abstract person id)
    """

    signal_type: str
    value: str
    confidence: float
    source: str
    modality: str
    subject: str = ""
    reliability: float = 0.5
    provenance: str = ""
    timestamp: str = field(default_factory=utc_now_iso)
    evidence_id: str = field(default_factory=lambda: f"ev-{uuid.uuid4().hex[:8]}")

    def __post_init__(self) -> None:
        # frozen dataclass: clamp via object.__setattr__
        object.__setattr__(self, "confidence", _clamp01(self.confidence))
        object.__setattr__(self, "reliability", _clamp01(self.reliability))

    def snapshot(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "timestamp": self.timestamp,
            "source": self.source,
            "modality": self.modality,
            "signal_type": self.signal_type,
            "value": self.value,
            "confidence": round(self.confidence, 3),
            "reliability": round(self.reliability, 3),
            "provenance": self.provenance,
            "subject": self.subject,
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "AffectiveEvidence":
        return cls(
            evidence_id=str(data.get("evidence_id", "") or f"ev-{uuid.uuid4().hex[:8]}"),
            timestamp=str(data.get("timestamp", "") or utc_now_iso()),
            source=str(data.get("source", "")),
            modality=str(data.get("modality", "")),
            signal_type=str(data.get("signal_type", "")),
            value=str(data.get("value", "")),
            confidence=float(data.get("confidence", 0.0)),
            reliability=float(data.get("reliability", 0.5)),
            provenance=str(data.get("provenance", "")),
            subject=str(data.get("subject", "")),
        )


def make_evidence(
    *,
    source: str,
    modality: str,
    signal_type: str,
    value: str,
    confidence: float,
    subject: str = "",
    reliability: float | None = None,
    provenance: str = "",
    timestamp: str = "",
) -> AffectiveEvidence:
    """Convenience constructor with auto id/timestamp and default reliability.

    ``reliability`` defaults to the confidence when not supplied, so a caller
    that only knows how sure it is still produces a usable record.
    """
    return AffectiveEvidence(
        signal_type=signal_type,
        value=value,
        confidence=confidence,
        source=source,
        modality=modality,
        subject=subject,
        reliability=reliability if reliability is not None else confidence,
        provenance=provenance,
        timestamp=timestamp or utc_now_iso(),
    )
