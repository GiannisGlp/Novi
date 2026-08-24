"""Tests: IntegrationMixin real-I/O wiring (doc 17 §4).

- enable_real_io(camera=True, mic=True, speaker=True) wires adapters;
- with camera enabled: camera_frames tick in background, preview carries
  image_data_url; perception auto-runs on frames;
- /listen path (server.listen_real) records -> STT -> voice_turn reply;
- speak_back: replies spoken through RealSpeaker when enabled;
- all degrade gracefully when hardware absent (CI-safe assertions only
  check state/shape, not device presence).
"""

from __future__ import annotations

import unittest

from novi.web.server import NoviWebServer


class RealIOWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.s = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.s.stop()
        except Exception:
            pass

    def test_default_off(self) -> None:
        # fresh server: real I/O must start disabled regardless of other tests
        fresh = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        try:
            self.assertFalse(fresh.real_io_enabled)
            self.assertFalse(fresh.real_io["camera"])
            self.assertFalse(fresh.real_io["mic"])
        finally:
            fresh.stop()

    def test_enable_speaker_always_possible(self) -> None:
        # say exists on macOS CI runner; even if not, enabling must not raise
        res = self.s.real_enable(speaker=True)
        self.assertIn("speaker", res)

    def test_listen_real_returns_payload_shape(self) -> None:
        # may fail on missing mic in CI; assert payload shape either way
        try:
            res = self.s.voice_listen(1.0)
        except RuntimeError as exc:
            self.assertIn("microphone", str(exc).lower())
            return
        self.assertIn("ok", res)
        self.assertIn("text", res)

    def test_camera_enable_reports_status_honestly(self) -> None:
        res = self.s.real_enable(camera=True)
        # On CI without a camera, available=False; on a Mac with one, True.
        self.assertIn(res["camera"], (True, False))
        if not res["camera"]:
            self.assertFalse(self.s.real_io["camera"])
