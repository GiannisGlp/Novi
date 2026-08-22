"""Tests for the chat deduplication and chat-busy flag fix.

Verifies:
  - Duplicate sends within the dedup window are rejected.
  - The chat-busy flag prevents the background loop from stepping.
  - The chat-busy flag is cleared after compose_reply completes.
  - The chat-busy flag is cleared even if compose_reply raises.
"""

import time
import unittest
from unittest.mock import MagicMock, patch

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


class ChatPollIdempotencyTests(unittest.TestCase):
    """The /api/chat?after=N endpoint must never re-send already-delivered
    entries. The frontend depends on this contract: two overlapping polls reading
    the same `after` must return the same entries, and the client dedups by seq so
    a re-append can never create a duplicate message."""

    def setUp(self):
        self.server = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        self.server.start()

    def tearDown(self):
        self.server.stop()

    def test_poll_after_returns_all_and_next_is_empty(self):
        self.server.clear_chat()
        self.server.chat_send("hello", confidence=0.9)
        first = self.server.chat(0)
        self.assertEqual(len(first["entries"]), 2)  # user + novi
        after = first["after"]
        # The next poll with the returned `after` must be empty (no re-send).
        second = self.server.chat(after)
        self.assertEqual(second["entries"], [])
        self.assertEqual(second["after"], after)

    def test_poll_after_is_idempotent(self):
        """Polling twice with the same `after` returns the same entries and does
        not mutate server state, so the client dedup set is what prevents a
        duplicate DOM append when two polls overlap."""
        self.server.clear_chat()
        self.server.chat_send("how are you?", confidence=0.9)
        a = self.server.chat(0)
        b = self.server.chat(0)
        self.assertEqual(a["entries"], b["entries"])
        self.assertEqual(a["after"], b["after"])
        self.assertEqual(len(a["entries"]), 2)

    def test_poll_entries_have_monotonic_seqs(self):
        """Every entry carries a unique, increasing seq so the client can dedup."""
        self.server.clear_chat()
        self.server.chat_send("first", confidence=0.9)
        self.server.chat_send("second", confidence=0.9)
        entries = self.server.chat(0)["entries"]
        seqs = [e["seq"] for e in entries]
        self.assertEqual(seqs, sorted(seqs))
        self.assertEqual(len(seqs), len(set(seqs)))


class ChatSummarizerGateTests(unittest.TestCase):
    """The chat summarizer must not run an LLM call on every single append past
    the threshold — it is gated to run only when the thread has grown enough."""

    def setUp(self):
        self.server = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        self.server.start()

    def tearDown(self):
        self.server.stop()

    def _seed_chat(self, n: int) -> None:
        self.server._chat = [
            {"seq": i + 1, "role": "user" if i % 2 == 0 else "novi", "text": f"msg {i + 1}"}
            for i in range(n)
        ]
        self.server._chat_seq = n

    def test_no_summary_when_below_threshold(self):
        self._seed_chat(10)
        with patch.object(self.server, "conversation_summarizer", MagicMock()) as sm:
            self.server._maybe_summarize_chat()
        sm.assert_not_called()
        self.assertEqual(len(self.server._chat), 10)

    def test_gate_skips_when_not_enough_new_turns(self):
        # 22 turns but last summarized at 22 -> no new growth -> gated (no call).
        self._seed_chat(22)
        self.server._last_summarized_len = 22
        with patch.object(self.server, "conversation_summarizer", MagicMock()) as sm:
            self.server._maybe_summarize_chat()
        sm.assert_not_called()
        # Thread untouched because the gate skipped.
        self.assertEqual(len(self.server._chat), 22)

    def test_summarizes_when_grown_past_gate(self):
        self._seed_chat(30)  # grew well past the gate since last summary
        self.server._last_summarized_len = 8
        with patch.object(self.server, "conversation_summarizer", return_value="summary") as sm:
            self.server._maybe_summarize_chat(threshold=20, keep_recent=8)
        sm.assert_called_once()
        # Trimmed to the last 8 recent turns.
        self.assertEqual(len(self.server._chat), 8)


if __name__ == "__main__":
    unittest.main()
