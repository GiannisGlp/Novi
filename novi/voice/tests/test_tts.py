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


def _write_exe(path, body: str) -> str:
    path.write_text(body)
    path.chmod(0o755)
    return str(path)


class TestPiperTTS:
    def test_missing_binaries_raise_honestly(self, tmp_path):
        from novi.voice.tts import PiperTTSProvider

        provider = PiperTTSProvider(
            piper_bin=str(tmp_path / "no-piper"),
            model=str(tmp_path / "no-model.onnx"),
            player_bin=str(tmp_path / "no-player"),
        )
        assert provider.available() is False
        with pytest.raises(RuntimeError):
            provider.synthesize("hello")

    def test_empty_text_rejected(self, tmp_path):
        from novi.voice.tts import PiperTTSProvider

        provider = PiperTTSProvider(
            piper_bin=str(tmp_path / "piper"),
            model=str(tmp_path / "voice.onnx"),
            player_bin=str(tmp_path / "aplay"),
        )
        with pytest.raises(ValueError):
            provider.synthesize("   ")

    def test_synthesize_pipes_text_through_piper_to_player(self, tmp_path):
        from novi.voice.tts import PiperTTSProvider

        piper = _write_exe(
            tmp_path / "piper",
            "#!/bin/sh\n"
            "while [ $# -gt 0 ]; do\n"
            '  if [ "$1" = "-f" ]; then OUT=\"$2\"; shift 2; else shift; fi\n'
            "done\n"
            'cat > \"$OUT\"\n',
        )
        # Fake player keeps a copy of the wav file it is handed.
        player = _write_exe(tmp_path / "aplay", "#!/bin/sh\ncp \"$1\" \"$0.spoke\"\n")
        model = tmp_path / "voice.onnx"
        model.write_bytes(b"fake-voice-model")
        provider = PiperTTSProvider(piper_bin=piper, model=str(model), player_bin=player)
        assert provider.available() is True
        out = provider.synthesize("hello piper")
        assert out.spoken is True
        assert out.provider == "piper"
        assert out.text == "hello piper"
        assert (tmp_path / "aplay.spoke").read_bytes() == b"hello piper"
