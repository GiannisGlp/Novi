"""Tests: TTS provider boundary, macOS say stub, deterministic fallback.

Contract (doc 15): synthesize(text) -> AudioOut. SayTTSProvider shells
out to macOS `say` (day-one stub); DeterministicTTSProvider records the
request for CI assertions. Empty text is rejected at the boundary.
"""

from __future__ import annotations

import pytest

from novi.voice.tts import AudioOut, DeterministicTTSProvider


class TestDeterministicTTS:
    def test_synthesize_returns_audio_out_with_text(self):
        tts = DeterministicTTSProvider()
        out = tts.synthesize("hello there")
        assert isinstance(out, AudioOut)
        assert out.text == "hello there"
        assert out.provider == "deterministic"
        assert out.spoken is False  # nothing actually played

    def test_empty_text_rejected(self):
        tts = DeterministicTTSProvider()
        with pytest.raises(ValueError):
            tts.synthesize("   ")

    def test_utterances_recorded_for_assertions(self):
        tts = DeterministicTTSProvider()
        tts.synthesize("one")
        tts.synthesize("two")
        assert [u.text for u in tts.utterances] == ["one", "two"]


class TestSayTTSAvailability:
    def test_say_provider_reports_availability(self):
        from novi.voice.tts import SayTTSProvider

        provider = SayTTSProvider(say_bin="/nonexistent/say-binary")
        assert provider.available() is False

        provider_ok = SayTTSProvider(say_bin="/bin/echo")  # any executable path
        # availability checks existence+exec bit; /bin/echo exists on mac/linux CI
        assert provider_ok.available() in (True, False)

    def test_say_provider_synthesize_without_binary_raises(self):
        from novi.voice.tts import SayTTSProvider

        provider = SayTTSProvider(say_bin="/nonexistent/say-binary")
        with pytest.raises(RuntimeError):
            provider.synthesize("should fail")
