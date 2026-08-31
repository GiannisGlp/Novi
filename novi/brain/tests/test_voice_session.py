"""Tests for the brain-owned voice session (plan 25, Part B).

Wires the voice package's VoiceLoop to the brain: a closed speech turn is
transcribed, handed to brain.respond() (the reply engine — trained data when
enabled), and the reply is synthesized for playback. Deterministic STT/TTS keep
the tests hardware-free.
"""

from __future__ import annotations

import unittest

from novi.brain.audio import AudioFrame
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.voice_session import VoiceSession
from novi.voice.stt import DeterministicSTTProvider
from novi.voice.tts import DeterministicTTSProvider
from novi.voice.vad import TurnSegmenter

EP = 2  # endpoint_frames for fast closes in tests


def _speech(at: str) -> AudioFrame:
    return AudioFrame(rms=0.5, peak=0.8, speech=True, captured_at=at)


def _sil() -> AudioFrame:
    return AudioFrame(rms=0.01, peak=0.02, speech=False)


class VoiceSessionTest(unittest.TestCase):
    def _session(self, script: dict[str, str], **brain_kw) -> tuple[VoiceSession, DeterministicTTSProvider]:
        brain = MacBrain(config=MacBrainConfig(curiosity_enabled=False, **brain_kw))
        tts = DeterministicTTSProvider()
        session = VoiceSession(
            brain,
            stt=DeterministicSTTProvider(script),
            tts=tts,
            segmenter=TurnSegmenter(endpoint_frames=EP),
        )
        return session, tts

    def test_heard_turn_replies_with_brain_text_and_speaks(self) -> None:
        session, tts = self._session({"u1": "hello novi"})
        session.feed_frame(_speech("u1"))
        for _ in range(EP):
            session.feed_frame(_sil())
        spoken = session.drain()
        self.assertEqual(len(spoken), 1)
        # The brain's reply engine produced text (deterministic fallback here —
        # no transport in CI) and the TTS spoke it back.
        self.assertTrue(spoken[0].text)
        self.assertEqual([u.text for u in tts.utterances], [spoken[0].text])

    def test_silence_produces_nothing(self) -> None:
        session, tts = self._session({})
        session.feed_frame(_sil())
        self.assertEqual(session.drain(), [])
        self.assertEqual(tts.utterances, [])

    def test_unknown_audio_never_reaches_reply_or_tts(self) -> None:
        session, tts = self._session({})
        session.feed_frame(_speech("x1"))
        for _ in range(EP):
            session.feed_frame(_sil())
        self.assertEqual(session.drain(), [])
        self.assertEqual(tts.utterances, [])

    def test_person_flows_to_brain_reply(self) -> None:
        seen: dict[str, str] = {}

        class PersonBrain:
            def respond(self, text: str, *, person: str = "") -> dict:
                seen["person"] = person
                return {"text": f"hi {person}"}

        tts = DeterministicTTSProvider()
        session = VoiceSession(
            PersonBrain(),
            stt=DeterministicSTTProvider({"p1": "hi anna here"}),
            tts=tts,
            segmenter=TurnSegmenter(endpoint_frames=EP),
        )
        session.person = "Anna"
        session.feed_frame(_speech("p1"))
        for _ in range(EP):
            session.feed_frame(_sil())
        spoken = session.drain()
        self.assertEqual(len(spoken), 1)
        self.assertEqual(seen["person"], "Anna")
        self.assertEqual(spoken[0].text, "hi Anna")

    def test_events_record_provenance(self) -> None:
        session, _ = self._session({"e1": "ping"})
        session.feed_frame(_speech("e1"))
        for _ in range(EP):
            session.feed_frame(_sil())
        session.drain()
        kinds = [e["kind"] for e in session.events]
        self.assertIn("turn-transcribed", kinds)
        self.assertIn("reply-spoken", kinds)

    def test_hear_delegates_to_brain_listen(self) -> None:
        class StubBrain:
            def listen(self, seconds: float = 3.0) -> dict:
                return {"transcription": type("T", (), {"text": "hello from the mic"})()}

        session = VoiceSession(StubBrain())
        self.assertEqual(session.hear(2.0), "hello from the mic")


if __name__ == "__main__":
    unittest.main()
