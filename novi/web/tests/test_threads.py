"""Per-person conversation threads (phase 2, issue 3).

The remote-app user and each recognized in-home person get their own thread,
so one conversation never derives context from — or corrupts — another.
The web UI pane is the "" thread.
"""

from __future__ import annotations

import unittest

from novi.web.runtime_budgets import WebRuntimeBudgets
from novi.web.server import NoviWebServer


class PersonThreadTests(unittest.TestCase):
    def _server(self, **kw) -> NoviWebServer:
        defaults = {"port": 0, "store_path": None, "auto_step": False, "chat_llm": False}
        defaults.update(kw)
        s = NoviWebServer(**defaults)
        s.start()
        return s

    def test_threads_are_separate_per_person(self) -> None:
        s = self._server()
        try:
            s.chat_send("hello alice", person="alice")
            s.chat_send("hello bob", person="bob")
            alice = s._chat_thread("alice")
            bob = s._chat_thread("bob")
            self.assertTrue(alice, "alice's thread must have her turns")
            self.assertTrue(bob, "bob's thread must have his turns")
            self.assertFalse(any("bob" in c["text"].lower() for c in alice))
            self.assertFalse(any("alice" in c["text"].lower() for c in bob))
            # The web UI pane is untouched by person-thread traffic.
            self.assertEqual(s._chat_thread(""), [])
        finally:
            s.stop()

    def test_history_is_person_scoped(self) -> None:
        s = self._server()
        try:
            s.chat_send("hi alice", person="alice")
            s.chat_send("hi bob", person="bob")
            s.chat_send("how are you alice", person="alice")
            hist = s._build_history(6, "alice")
            self.assertTrue(all("bob" not in e["text"].lower() for e in hist))
            self.assertTrue(any("how are you alice" in e["text"].lower() for e in hist))
            self.assertNotEqual(s._last_novi_text("alice"), "")
            self.assertEqual(s._last_novi_text("nobody"), "")
        finally:
            s.stop()

    def test_chat_api_after_is_person_scoped(self) -> None:
        s = self._server()
        try:
            s.chat_send("hey alice", person="alice")
            s.chat_send("hey bob", person="bob")
            entries = s.chat(0, "alice")["entries"]
            self.assertTrue(entries)
            self.assertFalse(any("bob" in e["text"].lower() for e in entries))
        finally:
            s.stop()

    def test_clear_chat_is_person_scoped(self) -> None:
        s = self._server()
        try:
            s.chat_send("hi alice", person="alice")
            s.chat_send("hi bob", person="bob")
            s.clear_chat("alice")
            self.assertEqual(s._chat_thread("alice"), [])
            self.assertTrue(s._chat_thread("bob"), "bob's thread must survive alice's clear")
        finally:
            s.stop()


class ThreadBoundTests(unittest.TestCase):
    """Memory stability: distinct person threads are LRU-bounded ("" pinned)."""

    def _server(self, **kw) -> NoviWebServer:
        defaults = {
            "port": 0,
            "store_path": None,
            "auto_step": False,
            "chat_llm": False,
            "budgets": WebRuntimeBudgets(max_chat_threads=4),
        }
        defaults.update(kw)
        return NoviWebServer(**defaults)

    def test_distinct_persons_stay_bounded_and_pin_ui_thread(self) -> None:
        s = self._server()
        try:
            for i in range(20):
                s._chat_thread(f"p{i}")
            self.assertLessEqual(len(s._threads), 4)
            self.assertIn("", s._threads, "the web UI pane must never be evicted")
            self.assertIn("p19", s._threads, "most-recently-used threads survive")
            self.assertNotIn("p0", s._threads, "least-recently-used threads are evicted")
        finally:
            s.stop()

    def test_lru_touch_protects_active_thread(self) -> None:
        s = self._server()
        try:
            for i in range(3):
                s._chat_thread(f"p{i}")  # threads: "", p0, p1, p2
            s._chat_thread("p0")  # p0 becomes most-recently-used
            s._chat_thread("p3")  # over budget: evicts p1, not p0
            self.assertIn("p0", s._threads)
            self.assertNotIn("p1", s._threads)
            self.assertIn("", s._threads)
        finally:
            s.stop()

    def test_seq_stays_monotonic_across_eviction(self) -> None:
        s = self._server()
        try:
            s._append_chat({"role": "user", "text": "hi"}, "alice")
            first = s._seq_for("alice")
            for i in range(10):
                s._chat_thread(f"other{i}")
            self.assertNotIn("alice", s._threads, "alice's turn data was evicted")
            s._append_chat({"role": "user", "text": "again"}, "alice")
            # Seq continues (never reuses 1..N): the client's rendered-seq
            # dedup set must not swallow the new generation as duplicates.
            self.assertGreater(s._seq_for("alice"), first)
        finally:
            s.stop()

    def test_evicted_thread_resumes_delivery(self) -> None:
        s = self._server()
        try:
            s._append_chat({"role": "user", "text": "before"}, "alice")
            cursor = s.chat(0, "alice")["after"]
            for i in range(10):
                s._chat_thread(f"other{i}")
            stored = s._append_chat({"role": "novi", "text": "after eviction"}, "alice")
            chunk = s.chat(cursor, "alice")
            self.assertIn(stored["seq"], [e["seq"] for e in chunk["entries"]])
        finally:
            s.stop()


if __name__ == "__main__":
    unittest.main()
