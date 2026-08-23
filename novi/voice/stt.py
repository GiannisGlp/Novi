"""STT provider boundary and deterministic implementation.

Doc 15 contract: an STTProvider turns one closed SpeechTurn into a
Transcript. Real Whisper-class backends implement the protocol; CI uses
the deterministic provider keyed on frame timestamps so behavior is
reproducible without audio models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from novi.brain.audio import AudioFrame


@dataclass(frozen=True)
class Transcript:
    """Text result for one speech turn, with provenance."""

    text: str
    confidence: float
    provider: str
    language: str = "en"
    audio_first: str = ""
    audio_last: str = ""


@runtime_checkable
class STTProvider(Protocol):
    def transcribe(self, frames: list[AudioFrame]) -> Transcript: ...


class DeterministicSTTProvider:
    """Scripted STT: maps first-frame timestamp -> text.

    Unknown turns transcribe to empty text with zero confidence (fail
    quiet, never invent). Matches the brain's DeterministicSTTProvider
    role but operates on closed turn frame lists.
    """

    def __init__(self, scripted: dict[str, str] | None = None) -> None:
        self._scripted = dict(scripted or {})

    def transcribe(self, frames: list[AudioFrame]) -> Transcript:
        if not frames:
            raise ValueError("cannot transcribe an empty turn")
        key = frames[0].captured_at
        text = self._scripted.get(key, "")
        return Transcript(
            text=text,
            confidence=1.0 if text else 0.0,
            provider="deterministic",
            audio_first=frames[0].captured_at,
            audio_last=frames[-1].captured_at,
        )
