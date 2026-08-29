"""Per-person conversation threads (phase 2, issue 3).

The remote-app user and each recognized in-home person get their own thread,
so one conversation never derives context from — or corrupts — another.
The web UI pane is the "" thread.
"""

from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
