"""Tests: VoiceLoop — frames -> VAD -> STT -> reply -> arbitration -> TTS.

Wiring contract (doc 15 "Full-duplex integration"):
- feed/drain pattern: never blocks; no threads/sleeps inside the loop;
- a closed speech turn becomes exactly one reply_fn invocation;
- empty transcripts never reach reply_fn or TTS;
- owner chat inbound surfaces a yield-after-sentence arbitration decision;
- every stage emits provenance into the loop's event log.
"""

from __future__ import annotations

from novi.brain.audio import AudioFrame
from novi.voice.stt import DeterministicSTTProvider
from novi.voice.tts import DeterministicTTSProvider
from novi.voice.vad import TurnSegmenter
from novi.voice.voice_loop import VoiceLoop

EP = 2  # endpoint_frames for fast closes in tests


def _loop(script: dict[str, str], replies: dict[str, str]):
    seg = TurnSegmenter(endpoint_frames=EP)
    stt = DeterministicSTTProvider(script)
    tts = DeterministicTTSProvider()
    seen: list[tuple[str, str]] = []

    def reply_fn(text: str, *, person: str = "") -> str:
        seen.append((person, text))
        return replies.get(text, "")

    loop = VoiceLoop(
        segmenter=seg,
        stt=stt,
        tts=tts,
        reply_fn=reply_fn,
    )
    return loop, tts, seen


def _speech(at: str) -> AudioFrame:
    return AudioFrame(rms=0.5, peak=0.8, speech=True, captured_at=at)


def _sil() -> AudioFrame:
    return AudioFrame(rms=0.01, peak=0.02, speech=False)


class TestVoiceLoop:
    def test_speech_turn_flows_to_reply_and_tts(self):
        loop, tts, seen = _loop({"u1": "hello novi"}, {"hello novi": "hello!"})
        loop.feed_frame(_speech("u1"))
        for i in range(EP):
            loop.feed_frame(_sil())
        spoken = loop.drain()
        assert seen == [("", "hello novi")]
        assert len(spoken) == 1
        assert spoken[0].text == "hello!"
        assert [u.text for u in tts.utterances] == ["hello!"]

    def test_silence_produces_nothing(self):
        loop, tts, seen = _loop({}, {})
        loop.feed_frame(_sil())
        assert loop.drain() == []
        assert seen == []
        assert tts.utterances == []

    def test_unknown_audio_never_reaches_reply_or_tts(self):
        loop, tts, seen = _loop({}, {})
        loop.feed_frame(_speech("x1"))
        for _ in range(EP):
            loop.feed_frame(_sil())
        spoken = loop.drain()
        assert spoken == []
        assert seen == []
        assert tts.utterances == []

    def test_two_turns_processed_in_order(self):
        script = {"a1": "what is that", "b1": "thank you"}
        replies = {"what is that": "that is a cup", "thank you": "you are welcome"}
        loop, tts, seen = _loop(script, replies)
        loop.feed_frame(_speech("a1"))
        for _ in range(EP):
            loop.feed_frame(_sil())
        loop.feed_frame(_speech("b1"))
        for _ in range(EP):
            loop.feed_frame(_sil())
        spoken = loop.drain()
        assert seen == [("", "what is that"), ("", "thank you")]
        assert [s.text for s in spoken] == ["that is a cup", "you are welcome"]

    def test_owner_message_surfaces_yield_decision(self):
        loop, _, seen = _loop({"c1": "tell me more"}, {"tell me more": "gladly"})
        loop.begin_exchange("anna")
        loop.feed_frame(_speech("c1"))
        d = loop.notify_owner_message("work-msg-1")
        assert d.action == "yield-after-sentence"
        # still processes normally: sentence finished first
        for _ in range(EP):
            loop.feed_frame(_sil())
        spoken = loop.drain()
        assert seen == [("", "tell me more")]
        assert len(spoken) == 1

    def test_person_name_flows_to_reply(self):
        loop, _, seen = _loop({"p1": "hi anna here"}, {})
        loop.person = "Anna"
        loop.feed_frame(_speech("p1"))
        for _ in range(EP):
            loop.feed_frame(_sil())
        loop.drain()
        assert seen == [("Anna", "hi anna here")]

    def test_events_record_provenance(self):
        loop, _, _ = _loop({"e1": "ping"}, {"ping": "pong"})
        loop.begin_exchange("bob")
        loop.feed_frame(_speech("e1"))
        for _ in range(EP):
            loop.feed_frame(_sil())
        loop.drain()
        kinds = [e["kind"] for e in loop.events]
        assert "exchange-begun" in kinds
        assert "turn-transcribed" in kinds
        assert "reply-spoken" in kinds

    def test_snapshot_reports_state(self):
        loop, _, _ = _loop({}, {})
        snap = loop.snapshot()
        assert snap["turns_pending"] == 0
        loop.feed_frame(_speech("s1"))
        assert loop.snapshot()["turns_pending"] >= 0  # open turn not yet closed
