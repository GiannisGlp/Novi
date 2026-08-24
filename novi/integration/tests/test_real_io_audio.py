"""Tests: real microphone + TTS bridges (doc 17 §2/§3).

- RealMicrophone wraps brain.io.MacMicrophone: record -> wav path;
- RealSpeaker wraps voice.tts.SayTTSProvider: speak + availability;
- listen_and_transcribe: mic record -> STT provider -> Transcript dict;
  graceful RuntimeError when hardware missing (CI-safe);
- speak_reply(text): never raises to caller when TTS unavailable
  (returns spoken=False), speaks when available.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock


class TestRealMicrophone(unittest.TestCase):
    def test_record_returns_wav_path_via_mac_microphone(self):
        from novi.integration.real_io import RealMicrophone

        with tempfile.TemporaryDirectory() as tmp:
            mic = RealMicrophone.__new__(RealMicrophone)
            # inject a fake underlying recorder instead of real sounddevice
            fake_recording = mock.Mock()
            fake_recording.path = Path(tmp) / "mac-mic-00001.wav"
            fake_recording.duration_s = 1.0
            fake_recording.sample_rate = 16000
            inner = mock.Mock()
            inner.record.return_value = fake_recording
            mic._mic = inner
            rec = mic.record(1.0, output_dir=Path(tmp))
            self.assertEqual(rec["path"], str(fake_recording.path))
            self.assertEqual(rec["duration_s"], 1.0)

    def test_missing_sounddevice_raises_actionable_error(self):
        from novi.integration.real_io import RealMicrophone

        mic = RealMicrophone.__new__(RealMicrophone)
        inner = mock.Mock()
        inner.record.side_effect = RuntimeError("sounddevice is required for MacMicrophone")
        mic._mic = inner
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError):
                mic.record(1.0, output_dir=Path(tmp))


class TestListenAndTranscribe(unittest.TestCase):
    def _rstt(self, stt_mock):
        from novi.integration.real_io import RealMicrophone, RealSTT

        mic = mock.Mock(spec=RealMicrophone)
        mic.record.return_value = {"path": "/tmp/x.wav", "duration_s": 2.0, "sample_rate": 16000}
        return RealSTT(stt_mock, mac_microphone=mic)

    def test_listen_then_stt_produces_transcript(self):
        from novi.integration.real_io import RealSTT

        stt = mock.Mock()
        stt.transcribe.return_value = mock.Mock(
            text="hello novi", confidence=0.93, language="en", provider="whisper", model_id="fw:base"
        )
        rstt = self._rstt(stt)
        out = rstt.listen_and_transcribe(2.0, output_dir="/tmp")
        self.assertEqual(out["text"], "hello novi")
        self.assertEqual(out["provider"], "whisper")
        stt.transcribe.assert_called_once_with("/tmp/x.wav")

    def test_silence_yields_empty_text_ok(self):
        from novi.integration.real_io import RealSTT

        stt = mock.Mock()
        stt.transcribe.return_value = mock.Mock(text="", confidence=0.4, provider="whisper", model_id="m")
        rstt = self._rstt(stt)
        out = rstt.listen_and_transcribe(2.0, output_dir="/tmp")
        self.assertEqual(out["text"], "")
        self.assertEqual(out["ok"], True)


class TestRealSpeaker(unittest.TestCase):
    def test_speak_when_available(self):
        from novi.voice.tts import SayTTSProvider

        from novi.integration.real_io import RealSpeaker

        speaker = RealSpeaker(SayTTSProvider(say_bin="/bin/echo"))
        if not speaker.available():
            self.skipTest("no say binary")
        out = speaker.speak("hello there")
        self.assertTrue(out["spoken"])

    def test_speak_when_unavailable_degrades_not_raises(self):
        from novi.voice.tts import SayTTSProvider

        from novi.integration.real_io import RealSpeaker

        speaker = RealSpeaker(SayTTSProvider(say_bin="/nonexistent/say"))
        out = speaker.speak("should degrade")
        self.assertEqual(out["spoken"], False)
        self.assertIn("reason", out)


if __name__ == "__main__":
    unittest.main()
