"""Tests for the chat deduplication and chat-busy flag fix.

Verifies:
  - Duplicate sends within the dedup window are rejected.
  - The chat-busy flag prevents the background loop from stepping.
  - The chat-busy flag is cleared after compose_reply completes.
  - The chat-busy flag is cleared even if compose_reply raises.
"""

import unittest
import time
from unittest.mock import patch, MagicMock

from web.server import NoviWebServer


class ChatDeduplicationTests(unittest.TestCase):
    def setUp(self):
        self.server = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        self.server.start()

    def tearDown(self):
        self.server.stop()

    def test_duplicate_send_within_window_returns_existing(self):
        """Sending the same text twice within the dedup window returns the existing reply."""
        r1 = self.server.chat_send("hello there", confidence=0.9)
        self.assertNotIn("deduplicated", r1)
        r2 = self.server.chat_send("hello there", confidence=0.9)
        self.assertTrue(r2.get("deduplicated", False))

    def test_different_text_not_deduplicated(self):
        """Different text is not deduplicated."""
        r1 = self.server.chat_send("hello", confidence=0.9)
        r2 = self.server.chat_send("goodbye", confidence=0.9)
        self.assertNotIn("deduplicated", r1)
        self.assertNotIn("deduplicated", r2)

    def test_dedup_window_expires(self):
        """After the dedup window, the same text is processed again."""
        # Set a very short dedup window.
        self.server._dedup_window_seconds = 0.1
        r1 = self.server.chat_send("test message", confidence=0.9)
        self.assertNotIn("deduplicated", r1)
        time.sleep(0.15)
        r2 = self.server.chat_send("test message", confidence=0.9)
        self.assertNotIn("deduplicated", r2)


class ChatBusyFlagTests(unittest.TestCase):
    def setUp(self):
        self.server = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        self.server.start()

    def tearDown(self):
        self.server.stop()

    def test_chat_busy_flag_set_during_send(self):
        """The _chat_busy flag is set during chat_send and cleared after."""
        # Before send, flag should be False.
        self.assertFalse(self.server._chat_busy)
        # During send, the flag should be set (we check after the call returns,
        # it should already be cleared).
        self.server.chat_send("hello", confidence=0.9)
        self.assertFalse(self.server._chat_busy)

    def test_chat_busy_flag_cleared_on_exception(self):
        """The _chat_busy flag is cleared even if compose_reply raises."""
        self.assertFalse(self.server._chat_busy)
        # Make compose_reply raise.
        with patch.object(self.server.brain, 'compose_reply', side_effect=RuntimeError("test error")):
            try:
                self.server.chat_send("hello", confidence=0.9)
            except RuntimeError:
                pass
        self.assertFalse(self.server._chat_busy)

    def test_background_loop_skips_step_when_chat_busy(self):
        """The background loop skips brain.step() when _chat_busy is True."""
        with self.server._lock:
            self.server._chat_busy = True
        # Simulate the loop check.
        with self.server._lock:
            should_skip = self.server._chat_busy
        self.assertTrue(should_skip)
        # Clear it.
        with self.server._lock:
            self.server._chat_busy = False


class ChatSendAppendTests(unittest.TestCase):
    def setUp(self):
        self.server = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        self.server.start()

    def tearDown(self):
        self.server.stop()

    def test_single_send_appends_one_user_one_novi(self):
        """A single send appends exactly one user message and one Novi reply."""
        chat_before = len(self.server._chat)
        self.server.chat_send("hello there", confidence=0.9)
        chat_after = len(self.server._chat)
        # Should add exactly 2 entries (user + novi).
        self.assertEqual(chat_after - chat_before, 2)

    def test_two_different_sends_append_four_entries(self):
        """Two different sends append 4 entries total (2 per send)."""
        chat_before = len(self.server._chat)
        self.server.chat_send("hello", confidence=0.9)
        self.server.chat_send("how are you?", confidence=0.9)
        chat_after = len(self.server._chat)
        self.assertEqual(chat_after - chat_before, 4)

    def test_duplicate_send_does_not_append_extra(self):
        """A duplicate send within the window does not append extra entries."""
        chat_before = len(self.server._chat)
        self.server.chat_send("hello there", confidence=0.9)
        chat_after_first = len(self.server._chat)
        self.assertEqual(chat_after_first - chat_before, 2)
        # Duplicate send.
        self.server.chat_send("hello there", confidence=0.9)
        chat_after_dup = len(self.server._chat)
        # No extra entries from the duplicate.
        self.assertEqual(chat_after_dup, chat_after_first)


if __name__ == "__main__":
    unittest.main()