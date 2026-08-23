"""Non-speech audio / hearing for the Mac Brain.

Implements the offline-hearing subset of docs/02-novi-brain/13_AUDIO_AND_HEARING:
VAD-style speech/non-speech classification, **sound-event detection** over an
extensible taxonomy, acoustic anomaly/novelty representation, direction-of-arrival
(optional, uncertain), and audio-quality monitoring.

Determinism boundary (mirrors perception): a real sound-event-detection model /
front-end (future/Jetson) supplies an `AudioFrame` feature descriptor; the
deterministic `Hearing` driver turns that evidence into typed, confident,
provenance-carrying `AudioEvent`s and degrades gracefully when ASR is absent
(a failed model must never make Novi deaf).

- Speech is VAD evidence, never proof of address (13 §10).
- Unknown sounds produce an anomaly representation, never a forced class (13 §11).
- Direction is an uncertain measurement fused with vision, never asserted exact.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

# Extensible acoustic-event taxonomy (non-speech). Maps alias -> canonical class.
TAXONOMY = (
    "silence", "speech", "knock", "footstep", "door", "impact", "object_fall",
    "glass_break", "alarm", "appliance", "machinery", "vehicle", "animal",
    "clap", "cry", "laugh", "cough", "sneeze", "unknown",
)
_ALIAS = {
    "knock": "knock", "knocking": "knock", "rap": "knock",
    "footstep": "footstep", "steps": "footstep", "footsteps": "footstep",
    "door": "door", "door_slam": "door", "open_door": "door", "close_door": "door",
    "impact": "impact", "bang": "impact", "thud": "impact", "impact_sound": "impact",
    "object_fall": "object_fall", "drop": "object_fall", "falling": "object_fall",
    "glass_break": "glass_break", "glass_breaking": "glass_break", "break": "glass_break",
    "alarm": "alarm", "siren": "alarm", "beep": "alarm",
    "appliance": "appliance", "kitchen": "appliance", "fridge": "appliance",
    "machinery": "machinery", "machine": "machinery",
    "vehicle": "vehicle", "car": "vehicle", "traffic": "vehicle",
    "animal": "animal", "dog": "animal", "bark": "animal", "cat": "animal", "bird": "animal",
    "clap": "clap", "clapping": "clap",
    "cry": "cry", "crying": "cry", "weep": "cry",
    "laugh": "laugh", "laughter": "laugh",
    "cough": "cough", "coughing": "cough",
    "sneeze": "sneeze", "sneezing": "sneeze",
}
# Non-speech events that deserve attention even at modest intensity.
_ALERT_EVENTS = {"alarm", "impact", "glass_break", "object_fall", "cry", "animal", "door", "vehicle"}


@dataclass
class AudioFrame:
    """One frame of acoustic evidence from the capture/frontend pipeline."""
    rms: float = 0.0  # mean loudness 0..1
    peak: float = 0.0  # peak amplitude 0..1 (>=1.0 -> clipping)
    speech: bool = False  # VAD proxy: speech-like activity present
    event_hint: str | None = None  # optional class label from a real SED frontend / replay
    hint_confidence: float = 0.0
    direction_deg: float | None = None  # direction-of-arrival (uncertain)
    novelty: float = 0.0  # 0..1 novelty/anomaly score
    noise_level: float = 0.0
    channel_fault: bool = False
    captured_at: str = ""


@dataclass
class AudioEvent:
    event_type: str
    speech: bool
    confidence: float
    intensity: float
    direction_deg: float | None = None
    novelty: float = 0.0
    anomaly: bool = False
    source: str = "audio.sed"
    captured_at: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "speech": self.speech,
            "confidence": round(self.confidence, 3),
            "intensity": round(self.intensity, 3),
            "direction_deg": self.direction_deg,
            "novelty": round(self.novelty, 3),
            "anomaly": self.anomaly,
            "source": self.source,
            "captured_at": self.captured_at,
        }


@dataclass
class AudioQuality:
    clip: bool
    saturation: bool
    silence: bool
    excess_noise: bool
    channel_fault: bool

    def snapshot(self) -> dict[str, Any]:
        return {"clip": self.clip, "saturation": self.saturation, "silence": self.silence, "excess_noise": self.excess_noise, "channel_fault": self.channel_fault}


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


class Hearing:
    """Deterministic audio-event + quality analysis over an AudioFrame."""

    def __init__(self, *, silence_threshold: float = 0.05, anomaly_novelty: float = 0.7, impulse_threshold: float = 0.7) -> None:
        self.silence_threshold = silence_threshold
        self.anomaly_novelty = anomaly_novelty
        self.impulse_threshold = impulse_threshold

    # ---- event detection ----
    def detect(self, frame: AudioFrame) -> tuple[AudioEvent, ...]:
        rms = _clamp01(frame.rms)
        events: list[AudioEvent] = []
        if rms < self.silence_threshold and not frame.speech:
            events.append(self._ev("silence", False, frame, confidence=_clamp01(1.0 - rms / self.silence_threshold), intensity=rms))
            return tuple(events)
        if frame.speech:
            events.append(self._ev("speech", True, frame, confidence=_clamp01(rms + 0.2), intensity=rms))
            return tuple(events)
        # Non-speech: prefer a real frontend/replay hint; fall back to energy/novelty.
        if frame.event_hint:
            etype = _ALIAS.get(frame.event_hint.lower(), "unknown")
            confidence = frame.hint_confidence if frame.hint_confidence > 0 else _clamp01(rms)
            anomaly = etype == "unknown" or frame.novelty >= self.anomaly_novelty
        else:
            etype = "unknown" if frame.novelty >= self.anomaly_novelty else ("impact" if rms >= self.impulse_threshold else "environmental")
            confidence = _clamp01(rms)
            anomaly = frame.novelty >= self.anomaly_novelty
        events.append(self._ev(etype, False, frame, confidence=confidence, intensity=rms, anomaly=anomaly))
        return tuple(events)

    def _ev(self, event_type: str, speech: bool, frame: AudioFrame, *, confidence: float, intensity: float, anomaly: bool = False) -> AudioEvent:
        return AudioEvent(
            event_type=event_type,
            speech=speech,
            confidence=confidence,
            intensity=intensity,
            direction_deg=frame.direction_deg,
            novelty=frame.novelty,
            anomaly=anomaly,
            captured_at=frame.captured_at or datetime.now(timezone.utc).isoformat(),
        )

    # ---- quality monitoring ----
    def quality(self, frame: AudioFrame) -> AudioQuality:
        return AudioQuality(
            clip=frame.peak >= 1.0,
            saturation=frame.rms >= 0.98,
            silence=frame.rms < self.silence_threshold,
            excess_noise=frame.noise_level >= 0.6,
            channel_fault=frame.channel_fault,
        )

    # ---- attention gating ----
    def worth_attention(self, event: AudioEvent, *, threshold: float = 0.4) -> bool:
        if event.anomaly or event.event_type in _ALERT_EVENTS:
            return True
        return event.intensity >= threshold

    def to_modality_observation(self, event: AudioEvent, *, received_at: str = "") -> Any:
        from .fusion import ModalityObservation

        received_at = received_at or datetime.now(timezone.utc).isoformat()
        return ModalityObservation(modality="audio", entity=event.event_type, value="heard", confidence=event.confidence, captured_at=event.captured_at, received_at=received_at, source="audio.sed")
