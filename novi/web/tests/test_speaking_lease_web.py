"""Web server speaking-lease integration (plan 19, Phase 1 + 2).

The web server previously froze the whole background loop with a `_chat_busy`
flag while a reply was being composed, so a concurrent step could not fire a
duplicate initiative. The north-star fix keeps the loop ticking and instead
holds the brain's *speaking lease* during composition: the lease gates
spontaneous initiative, so the loop never stalls (SCENARIO-V1) and no
duplicate remark can fire.

Pins:
  - `_chat_busy` is gone from the server (the loop no longer skips on it);
  - the speaking lease is held during `chat_send` composition and released after;
  - the background auto-step loop keeps ticking while a reply is composing.
"""

from __future__ import annotations

import contextlib
import time
import unittest

from novi.web.server import NoviWebServer


class WebSpeakingLeaseTests(unittest.TestCase):
    def setUp(self):
        self.server = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        self.server.start()

    def tearDown(self):
        self.server.stop()

    def test_chat_busy_flag_removed(self):
        """The `_chat_busy` loop-freeze is gone; the lease replaces it."""
        self.assertFalse(hasattr(self.server, "_chat_busy"), "_chat_busy must be removed")

    def test_speaking_lease_held_during_send_and_released(self):
        """chat_send holds the brain's speaking lease while composing, then releases."""
        from unittest.mock import patch

        self.assertFalse(self.server.brain.speaking_lease)
        seen: dict = {}

        def fake_compose(*args, **kwargs):
            seen["lease_during"] = self.server.brain.speaking_lease
            return {"text": "hi", "fallback": False, "reason": "r", "grounding": {}}

        with patch.object(self.server.brain, "compose_reply", side_effect=fake_compose):
            self.server.chat_send("hello", confidence=0.9)
        self.assertTrue(seen.get("lease_during"), "lease must be held while composing")
        self.assertFalse(self.server.brain.speaking_lease, "lease must be released after send")

    def test_speaking_lease_released_on_exception(self):
        """The lease is released even if compose_reply raises."""
        from unittest.mock import patch

        self.assertFalse(self.server.brain.speaking_lease)
        with patch.object(self.server.brain, "compose_reply", side_effect=RuntimeError("test error")), contextlib.suppress(RuntimeError):
            self.server.chat_send("hello", confidence=0.9)
        self.assertFalse(self.server.brain.speaking_lease, "lease must be released on exception")

    def test_background_loop_keeps_stepping_while_lease_held(self):
        """The auto-step loop does NOT skip while the speaking lease is held."""
        s = NoviWebServer(port=0, store_path=None, auto_step=True, chat_llm=False, tick=0.1)
        s.start()
        try:
            s.brain.acquire_speaking_lease()
            # Give the loop a few ticks.
            time.sleep(0.4)
            self.assertGreater(s.brain._cycle, 0, "loop must keep stepping while the lease is held")
        finally:
            s.brain.release_speaking_lease()
            s.stop()


if __name__ == "__main__":
    unittest.main()
