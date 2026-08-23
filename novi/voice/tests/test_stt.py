"""Tests: STT provider protocol + deterministic implementation.

Contract (doc 15): transcribe(turn) -> Transcript{text, confidence,
provenance}. DeterministicSTTProvider maps scripted per-turn payloads so
CI never needs audio models; a real Whisper-class provider implements the
same protocol later.
"""

from __future__ import annotations

import pytest

from novi.brain.audio import AudioFrame
from novi.voice.stt import DeterministicSTTProvider, Transcript


def _turn(text_hint: str = "hello novi"):
    frames = [AudioFrame(rms=0.5, peak=0.8, speech=True, captured_at="t1")]
    return frames, text_hint


class TestDeterministicSTT:
    def test_transcribes_scripted_payload(self):
        stt = DeterministicSTTProvider({"t1": "hello novi"})
        tr = stt.transcribe(_turn()[0])
        assert isinstance(tr, Transcript)
        assert tr.text == "hello novi"
        assert tr.confidence == 1.0
        assert tr.provider == "deterministic"

    def test_unknown_audio_transcribes_empty_with_zero_confidence(self):
        stt = DeterministicSTTProvider({})
        tr = stt.transcribe(_turn()[0])
        assert tr.text == ""
        assert tr.confidence == 0.0

    def test_provenance_records_frame_span(self):
        stt = DeterministicSTTProvider({"t1": "hi", "t2": "there"})
        f1 = AudioFrame(rms=0.5, speech=True, captured_at="t1")
        f2 = AudioFrame(rms=0.5, speech=True, captured_at="t2")
        tr = stt.transcribe([f1, f2])
        assert tr.audio_first == "t1"
        assert tr.audio_last == "t2"

    def test_protocol_satisfied(self):
        from novi.voice.stt import STTProvider

        stt = DeterministicSTTProvider({})
        assert isinstance(stt, STTProvider)

    def test_empty_turn_rejected(self):
        stt = DeterministicSTTProvider({})
        with pytest.raises(ValueError):
            stt.transcribe([])
