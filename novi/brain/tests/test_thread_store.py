"""Unit tests: conversation thread persistence + routine tracker.

Deterministic, socket-free, stdlib-only. The tracker is exercised against
a tiny in-memory store double; table/trim behavior against real SQLite.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from novi.brain.conversation.thread_store import (
    MAX_STORED_THREADS,
    ROUTINE_MIN_OCCURRENCES,
    ROUTINE_MIN_SESSIONS,
    load_thread,
    matched_routine,
    observe_routine,
    routine_signature,
    save_thread,
)
from novi.brain.storage import DurableMemoryStore


class _FakeStore:
    """Minimal store double with the conversation-table surface."""

    def __init__(self) -> None:
        self.threads: dict[str, dict] = {}
        self.routines: dict[str, dict] = {}

    def save_conversation_thread(self, speaker: str, data: dict) -> None:
        self.threads[speaker] = data

    def load_conversation_thread(self, speaker: str) -> dict:
        return self.threads.get(speaker) or {}

    def trim_conversation_threads(self, keep: int) -> None:
        for speaker in list(self.threads)[:-keep] if len(self.threads) > keep else []:
            del self.threads[speaker]

    def save_conversation_routine(self, signature: str, data: dict) -> None:
        self.routines[signature] = data

    def load_conversation_routine(self, signature: str) -> dict:
        return self.routines.get(signature) or {}


class SignatureTests(unittest.TestCase):
    def test_identical_requests_match(self) -> None:
        a = routine_signature("RECOMMENDATION", "Recommend an interior for my car.")
        b = routine_signature("RECOMMENDATION", "Recommend an interior for my car.")
        self.assertIsNotNone(a)
        self.assertEqual(a, b)

    def test_distinct_behaviors_differ(self) -> None:
        a = routine_signature("RECOMMENDATION", "Recommend an interior for my car.")
        b = routine_signature("INFORMATION_REQUEST", "What colors does the Model Y come in?")
        self.assertNotEqual(a, b)

    def test_non_behavioral_intents_skipped(self) -> None:
        for intent in ("GREETING", "FAREWELL", "CONFIRMATION",
                       "DISCONFIRMATION", "CORRECTION"):
            self.assertIsNone(routine_signature(intent, "Hello there friend."),
                              intent)

    def test_empty_text_skipped(self) -> None:
        self.assertIsNone(routine_signature("RECOMMENDATION", "   "))


class RoutineSupportTests(unittest.TestCase):
    def _observe(self, store: _FakeStore, session: str, n: int = 1) -> dict:
        record: dict = {}
        for _ in range(n):
            record = observe_routine(
                store, speaker="user", session_id=session,
                intent="RECOMMENDATION",
                text="Recommend an interior for my car.")
        return record

    def test_single_session_never_supported(self) -> None:
        store = _FakeStore()
        record = self._observe(store, "s1", n=10)
        self.assertFalse(record["supported"])
        self.assertEqual(record["sessions"], ["s1"])

    def test_supported_across_sessions(self) -> None:
        store = _FakeStore()
        self._observe(store, "s1", n=ROUTINE_MIN_OCCURRENCES - 1)
        record = self._observe(store, "s2", n=1)
        self.assertTrue(record["supported"])
        self.assertEqual(len(record["sessions"]), ROUTINE_MIN_SESSIONS)
        self.assertEqual(record["occurrences"], ROUTINE_MIN_OCCURRENCES)

    def test_match_returns_only_supported(self) -> None:
        store = _FakeStore()
        self.assertEqual(matched_routine(
            store, speaker="user", intent="RECOMMENDATION",
            text="Recommend an interior for my car."), {})
        self._observe(store, "s1", n=ROUTINE_MIN_OCCURRENCES - 1)
        self._observe(store, "s2", n=1)
        hit = matched_routine(store, speaker="user",
                              intent="RECOMMENDATION",
                              text="Recommend an interior for my car.")
        self.assertTrue(hit["supported"])

    def test_match_is_per_speaker(self) -> None:
        store = _FakeStore()
        self._observe(store, "s1", n=ROUTINE_MIN_OCCURRENCES - 1)
        self._observe(store, "s2", n=1)
        self.assertEqual(matched_routine(
            store, speaker="bob", intent="RECOMMENDATION",
            text="Recommend an interior for my car."), {})

    def test_corrupt_record_fails_closed(self) -> None:
        store = _FakeStore()
        store.routines["k"] = "not-a-dict"
        record = observe_routine(store, speaker="user", session_id="s1",
                                 intent="RECOMMENDATION",
                                 text="Recommend an interior for my car.")
        self.assertIsInstance(record, dict)


class ThreadRoundtripTests(unittest.TestCase):
    def test_save_load_roundtrip(self) -> None:
        store = _FakeStore()
        snapshot = {"topic": "Tesla", "turn_count": 3,
                    "recent_turns": [{"user": "hi", "novi": "hey"}],
                    "anchor": {"topic": "Tesla"}}
        save_thread(store, "user", snapshot)
        self.assertEqual(load_thread(store, "user")["topic"], "Tesla")

    def test_load_missing_is_empty(self) -> None:
        self.assertEqual(load_thread(_FakeStore(), "nobody"), {})

    def test_load_corrupt_is_empty(self) -> None:
        store = _FakeStore()
        store.threads["user"] = "not-a-dict"
        self.assertEqual(load_thread(store, "user"), {})

    def test_thread_count_bounded(self) -> None:
        store = _FakeStore()
        for i in range(MAX_STORED_THREADS + 5):
            save_thread(store, f"speaker-{i}", {"turn_count": i})
        self.assertLessEqual(len(store.threads), MAX_STORED_THREADS)


class ConversationTableTests(unittest.TestCase):
    def test_tables_survive_roundtrip_on_real_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = DurableMemoryStore(Path(tmp) / "c.db")
            try:
                store.save_conversation_thread("user", {"turn_count": 2})
                self.assertEqual(
                    store.load_conversation_thread("user")["turn_count"], 2)
                store.save_conversation_routine("sig", {"supported": True})
                self.assertTrue(
                    store.load_conversation_routine("sig")["supported"])
                for i in range(MAX_STORED_THREADS + 3):
                    store.save_conversation_thread(f"s-{i}", {"turn_count": i})
                store.trim_conversation_threads(MAX_STORED_THREADS)
                store.save_conversation_thread("user", {"turn_count": 2})
            finally:
                store.close()
            reopened = DurableMemoryStore(Path(tmp) / "c.db")
            try:
                self.assertEqual(
                    reopened.load_conversation_thread("user")["turn_count"], 2)
                self.assertTrue(
                    reopened.load_conversation_routine("sig")["supported"])
            finally:
                reopened.close()


if __name__ == "__main__":
    unittest.main()
