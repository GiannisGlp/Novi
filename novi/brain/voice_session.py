"""Voice session — hear + talk back (plan 25, Part B).

Wires the voice package's deterministic full-duplex ``VoiceLoop`` to the brain:
frames → VAD → STT → ``brain.respond()`` (talk with the trained data) → TTS.
The brain is the reply engine, so whatever transport the brain owns — the
trained-adapter transport when enabled, the Ollama transport, or the
deterministic fallback — is what Novi talks back with.

Providers are injectable so tests use the deterministic STT/TTS. The default
wiring uses the macOS ``say`` TTS for audible talk-back. Real Whisper STT plugs
in through the voice package's ``STTProvider`` protocol; today the brain's
``listen()`` path records the microphone and transcribes with Whisper (the
``hear()`` convenience below), and a frame-based Whisper provider slots in when
the capture frontend supplies raw audio frames.
"""

from __future__ import annotations

from typing import Any

from novi.voice.stt import DeterministicSTTProvider, STTProvider
from novi.voice.tts import SayTTSProvider, TTSProvider
from novi.voice.vad import SpeechTurn, TurnSegmenter
from novi.voice.voice_loop import VoiceLoop


class VoiceSession:
    """Brain-owned full-duplex voice session (feed/drain contract).

    Feed ``AudioFrame`` feature descriptors as they arrive; drain finished
    spoken replies when ready. A closed speech turn is transcribed, handed to
    ``brain.respond()``, and the reply is synthesized for playback.
    """

    def __init__(
        self,
        brain: Any,
        *,
        stt: STTProvider | None = None,
        tts: TTSProvider | None = None,
        segmenter: TurnSegmenter | None = None,
        person: str = "",
    ) -> None:
        self.brain = brain
        self.loop = VoiceLoop(
            segmenter=segmenter or TurnSegmenter(),
            stt=stt or DeterministicSTTProvider(),
            tts=tts or SayTTSProvider(),
            reply_fn=self._reply_fn,
        )
        self.person = person

    @property
    def person(self) -> str:
        return self.loop.person

    @person.setter
    def person(self, value: str) -> None:
        # Keep the session and the loop in sync so a later assignment to
        # session.person is what the reply path actually uses.
        self.loop.person = value

    def _reply_fn(self, text: str, *, person: str = "") -> str:
        """The brain's reply engine: respond with the trained data, return text."""
        result = self.brain.respond(text, person=person or self.person)
        return result.get("text") or ""

    # -- input -------------------------------------------------------------

    def feed_frame(self, frame: Any) -> list[SpeechTurn]:
        """Ingest one audio frame; process any speech turns it closes."""
        return self.loop.feed_frame(frame)

    def hear(self, seconds: float = 3.0) -> str:
        """Real hear path: record the microphone and transcribe with Whisper.

        Delegates to ``brain.listen()`` (mic → local Whisper → memory/cognition)
        and returns the transcript text. The caller can then feed it to the
        loop's reply path or to ``brain.respond()`` directly.
        """
        result = self.brain.listen(seconds)
        return result["transcription"].text

    # -- output --------------------------------------------------------------

    def drain(self) -> list[Any]:
        """Return and clear spoken replies ready for playback."""
        return self.loop.drain()

    # -- state -----------------------------------------------------------------

    @property
    def events(self) -> list[dict[str, Any]]:
        return self.loop.events

    def snapshot(self) -> dict[str, Any]:
        return self.loop.snapshot()
