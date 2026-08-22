"""Voice and face recognition provider boundaries for the Mac Brain (rule 6).

Portable capability interfaces for recognising who is speaking (speaker/voice
ID) and who a detected face belongs to (face ID). They feed the existing
PersonIdentity layer as additional evidence streams (modality="voice" and
modality="face") so cross-modal identity can reach the verified tier
(docs/03-cognition/06 identity, docs/04-memory-and-knowledge/06 entity resolution).

Per the project model policy, a candidate becomes an official provider only
after on-device execution with representative inputs and evidence. These
deterministic stubs let the brain wiring be exercised and tested now; real
speaker/face embedding models are future deployment providers behind the same
Protocols. Recognition is evidence, never authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class SpeakerIdResult:
    name: str
    confidence: float


@dataclass(frozen=True)
class FaceIdResult:
    name: str
    confidence: float


class SpeakerIdProvider(Protocol):
    """Identify who is speaking from acoustic features (voice biometrics)."""

    def identify(self, *, audio_features: Mapping[str, Any]) -> SpeakerIdResult | None: ...


class FaceIdProvider(Protocol):
    """Identify who a detected face/track belongs to."""

    def identify(self, *, detection: Mapping[str, Any]) -> FaceIdResult | None: ...


class DeterministicSpeakerId:
    """Deterministic stub speaker-ID: maps a voiceprint key to a known name."""

    def __init__(self, mapping: Mapping[str, str] | None = None, *, confidence: float = 0.8) -> None:
        self.mapping = dict(mapping or {})
        self.confidence = confidence

    def identify(self, *, audio_features: Mapping[str, Any]) -> SpeakerIdResult | None:
        key = str(audio_features.get('voiceprint', '')).strip().lower() if audio_features else ''
        if not key:
            return None
        name = self.mapping.get(key)
        if not name:
            return None
        return SpeakerIdResult(name=name, confidence=self.confidence)


class DeterministicFaceId:
    """Deterministic stub face-ID: maps a detection label/track to a known name."""

    def __init__(self, mapping: Mapping[str, str] | None = None, *, confidence: float = 0.8) -> None:
        self.mapping = dict(mapping or {})
        self.confidence = confidence

    def identify(self, *, detection: Mapping[str, Any]) -> FaceIdResult | None:
        label = str(detection.get('label', '')).strip().lower() if detection else ''
        track = str(detection.get('track', '')).strip().lower() if detection else ''
        for key in (track, label):
            if key and key in self.mapping:
                return FaceIdResult(name=self.mapping[key], confidence=self.confidence)
        return None
