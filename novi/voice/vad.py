"""VAD-gated turn segmentation over the AudioFrame stream.

Spec: docs/plans/01_BRAIN/15_VOICE_CONTINUOUS_DIALOG.md ("Full-duplex
integration"). Continuous listening means continuous *ingestion*, not
continuous decoding: frames flow in every cycle, but only closed speech
turns are handed to STT.

End-of-turn = trailing silence held for ``endpoint_frames`` consecutive
non-speech frames. A hard ``max_utterance_frames`` cap forces a boundary
so long speech cannot starve the STT/brain path.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from novi.brain.audio import AudioFrame


@dataclass
class SpeechTurn:
    """One closed speech turn, ready for transcription."""

    frames: list[AudioFrame] = field(default_factory=list)
    first_captured_at: str = ""
    last_captured_at: str = ""
    duration_frames: int = 0
    peak_rms: float = 0.0
    forced_by_cap: bool = False


class TurnSegmenter:
    """Accumulates speech frames into turns; closes turns on trailing silence.

    Deterministic and hardware-free: operates on whatever AudioFrame stream
    the capture frontend provides (real mic or scripted test frames alike).
    """

    def __init__(
        self,
        *,
        endpoint_frames: int = 5,
        max_utterance_frames: int = 250,
    ) -> None:
        if endpoint_frames < 1:
            raise ValueError("endpoint_frames must be >= 1")
        if max_utterance_frames < 1:
            raise ValueError("max_utterance_frames must be >= 1")
        self.endpoint_frames = endpoint_frames
        self.max_utterance_frames = max_utterance_frames
        self._open: list[AudioFrame] = []
        self._trailing_silence = 0
        self._closed: list[SpeechTurn] = []

    # -- state -----------------------------------------------------------

    @property
    def pending(self) -> bool:
        """True while a turn is open (speech seen, boundary not reached)."""
        return bool(self._open)

    @property
    def closed_turns(self) -> list[SpeechTurn]:
        """Closed turns waiting to be drained."""
        return list(self._closed)

    def drain_closed(self) -> list[SpeechTurn]:
        """Return and clear accumulated closed turns."""
        out = self._closed
        self._closed = []
        return out

    def reset(self) -> None:
        self._open.clear()
        self._trailing_silence = 0
        self._closed.clear()

    # -- streaming -------------------------------------------------------

    def feed(self, frame: AudioFrame) -> list[SpeechTurn]:
        """Ingest one frame; return any turns closed by this frame."""
        closed_now: list[SpeechTurn] = []

        if frame.speech:
            self._open.append(frame)
            self._trailing_silence = 0
            if len(self._open) >= self.max_utterance_frames:
                closed_now.append(self._close(forced=True))
            return closed_now

        # Non-speech frame.
        if not self._open:
            return closed_now

        self._trailing_silence += 1
        if self._trailing_silence >= self.endpoint_frames:
            closed_now.append(self._close(forced=False))
        return closed_now

    # -- internals ---------------------------------------------------------

    def _close(self, *, forced: bool) -> SpeechTurn:
        turn = SpeechTurn(
            frames=list(self._open),
            first_captured_at=self._open[0].captured_at,
            last_captured_at=self._open[-1].captured_at,
            duration_frames=len(self._open),
            peak_rms=max(f.rms for f in self._open),
            forced_by_cap=forced,
        )
        self._open.clear()
        self._trailing_silence = 0
        self._closed.append(turn)
        return turn
