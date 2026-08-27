"""Web `listen()` thin-client property (plan 19, Phase 1).

The north-star R1/R3 contract: web handlers contain no addressee/topic/learning/
composition logic. `chat_send` already routes through `brain.respond()`. The
voice path (`listen()`) must do the same — it must NOT re-implement addressee
resolution, topic tracking, learning, or call `compose_reply` directly.

Pins:
  - `listen()` calls `brain.respond()` (the single brain-owned reply path);
  - `listen()` does NOT call `brain.compose_reply` directly;
  - the reply is appended to chat and returned.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from novi.web.server import NoviWebServer


class ListenThinClientTests(unittest.TestCase):
    def setUp(self):
        # camera_mode="real" so listen() passes the real-sensing guard; the
        # brain's listen() is patched to return a scripted transcription.
        self.server = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False, camera="real")
        self.server.start()

    def tearDown(self):
        self.server.stop()

    def _fake_listen(self, seconds=None):
        from novi.brain.models.stt import TranscriptionResult

        return {
            "transcription": TranscriptionResult(
                text="alice moved the door", language="en", confidence=0.9,
                audio_path="", provider="test", model_id="test",
            ),
            "reasoning": "human_speech_observed",
            "confidence": 0.9,
        }

    def test_listen_routes_through_respond_not_compose_reply(self):
        """listen() uses the single brain-owned respond() path, not compose_reply."""
        calls = {"respond": 0, "compose_reply": 0}

        def fake_respond(*args, **kwargs):
            calls["respond"] += 1
            return {"text": "I remember that alice moved the door.", "reply_source": "dialogue", "addressee": "alice", "reason": "r", "grounding": {}}

        def fake_compose(*args, **kwargs):
            calls["compose_reply"] += 1
            return {"text": "should not be used", "fallback": False, "reason": "r", "grounding": {}}

        with patch.object(self.server.brain, "listen", side_effect=self._fake_listen), \
             patch.object(self.server.brain, "respond", side_effect=fake_respond), \
             patch.object(self.server.brain, "compose_reply", side_effect=fake_compose):
            r = self.server.listen(1.0)

        self.assertEqual(calls["respond"], 1, "listen() must call brain.respond()")
        self.assertEqual(calls["compose_reply"], 0, "listen() must NOT call compose_reply directly")
        self.assertEqual(r["novi"]["text"], "I remember that alice moved the door.")
        self.assertTrue(r["accepted"])


if __name__ == "__main__":
    unittest.main()
