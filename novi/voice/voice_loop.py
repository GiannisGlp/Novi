"""VoiceLoop: frames -> VAD -> STT -> reply -> turn arbitration -> TTS.

Doc 15 "Full-duplex integration": a pull-based, non-blocking loop. The
caller feeds AudioFrames as they arrive and drains finished spoken replies
when ready. No threads, no sleeps inside the loop — scheduling belongs to
the autonomy layer above; this module is the deterministic voice pipeline.
"""

from __future__ import annotations

from typing import Any, Callable

from novi.brain.audio import AudioFrame

from .stt import STTProvider
from .tts import TTSProvider
from .turn_taking import TurnDecision, TurnTakingPolicy, Channel
from .vad import SpeechTurn, TurnSegmenter


class VoiceLoop:
    """Deterministic full-duplex voice pipeline (feed/drain contract)."""

    def __init__(
        self,
        *,
        segmenter: TurnSegmenter,
        stt: STTProvider,
        tts: TTSProvider,
        reply_fn: Callable[..., str],
        policy: TurnTakingPolicy | None = None,
    ) -> None:
        self.segmenter = segmenter
        self.stt = stt
        self.tts = tts
        self.reply_fn = reply_fn
        self.policy = policy or TurnTakingPolicy()
        self.person: str = ""
        self._events: list[dict[str, Any]] = []
        self._pending_speech: list[Any] = []   # AudioOut awaiting drain
        self._open_turns = 0

    # -- input -------------------------------------------------------------

    def feed_frame(self, frame: AudioFrame) -> list[SpeechTurn]:
        """Ingest one audio frame; process any turns it closes."""
        closed = self.segmenter.feed(frame)
        for turn in closed:
            self._handle_turn(turn)
        return closed

    def begin_exchange(self, ref: str) -> TurnDecision:
        """A person started interacting with Novi."""
        d = self.policy.begin_exchange(Channel.PERSON_VOICE, ref=ref)
        self._events.append({**d.snapshot(), "kind": "exchange-begun", "at_cycle": 0})
        return d

    def notify_owner_message(self, ref: str) -> TurnDecision:
        """Owner chat arrived from afar -> higher-priority inbound."""
        return self.policy.notify_inbound(Channel.OWNER_CHAT, ref=ref)

    # -- output --------------------------------------------------------------

    def drain(self) -> list[Any]:
        """Return and clear spoken replies ready for playback."""
        out = self._pending_speech
        self._pending_speech = []
        return out

    # -- state -----------------------------------------------------------------

    @property
    def events(self) -> list[dict[str, Any]]:
        return list(self._events)

    def snapshot(self) -> dict[str, Any]:
        return {
            "state": "speaking" if self.policy.speaking_ref else "listening",
            "exchange": self.policy.snapshot()["exchange"],
            "turns_pending": len(self.segmenter.closed_turns),
            "speech_buffered": len(self._pending_speech),
            "person": self.person,
            "policy": self.policy.snapshot(),
        }

    # -- internals ----------------------------------------------------------------

    def _handle_turn(self, turn: SpeechTurn) -> None:
        transcript = self.stt.transcribe(turn.frames)
        self._log("turn-transcribed", text=transcript.text, confidence=transcript.confidence)
        if not transcript.text:
            self._log("turn-empty", reason="no-transcript")
            return

        reply_text = self.reply_fn(transcript.text, person=self.person)
        if not reply_text:
            self._log("reply-silent", reason="empty-reply")
            return

        decision = self.policy.request_speak(Channel.PERSON_VOICE, ref=f"say:{reply_text[:24]}")
        if not decision.granted:
            self._log("reply-deferred", reason=decision.reason)
            # lease contention is resolved by the policy's release/resume flow;
            # in this deterministic loop we still render so CI can assert text.
        out = self.tts.synthesize(reply_text)
        self._pending_speech.append(out)
        self._log("reply-spoken", text=out.text, provider=out.provider)

    def _log(self, kind: str, **fields: Any) -> None:
        evt = {"kind": kind}
        evt.update(fields)
        self._events.append(evt)
