"""Memory 2.0: importance-weighted retrieval + episodic narrative.

Verifies that recall scores memories by relevance × recency × importance and
that a short episodic narrative is reconstructed from recent memories.
"""

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from brain.b1_memory import MemoryRecord
from MAC_BRAIN.models.stt import TranscriptionResult
from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
from MAC_BRAIN.tests.test_mac_brain import FakeCamera


def _record(mid: str, created_at: str, confidence: float, mtype: str = "utterance", content: str = "x") -> MemoryRecord:
    return MemoryRecord(mid, mtype, created_at, content, confidence, "verified", "public", 0, {}, entity_refs=("alice",))


class MemoryScoreTests(unittest.TestCase):
    def test_score_prefers_recent_high_confidence(self):
        now = datetime.now(timezone.utc)
        old = _record("old", (now - timedelta(minutes=10)).isoformat(), 0.5)
        new = _record("new", now.isoformat(), 0.9)
        self.assertGreater(MacBrain._memory_score(new, 0, now), MacBrain._memory_score(old, 0, now))

    def test_score_prefers_higher_relevance(self):
        now = datetime.now(timezone.utc)
        a = _record("a", now.isoformat(), 0.8)
        b = _record("b", now.isoformat(), 0.8)
        # same recency/importance, but a is more relevant (lower FTS rank index)
        self.assertGreater(MacBrain._memory_score(a, 0, now), MacBrain._memory_score(b, 5, now))


class Memory2RuntimeTests(unittest.TestCase):
    def _brain(self, store_path):
        return MacBrain(camera=FakeCamera(), store_path=store_path, config=MacBrainConfig())

    def _hear(self, brain, text, confidence=0.9):
        return brain.ingest_transcript(
            TranscriptionResult(text=text, language="en", confidence=confidence, audio_path="", provider="web", model_id="web")
        )

    def test_episodic_narrative_reconstructs_recent_memories(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "m.db")
            brain = self._brain(db)
            brain.start()
            try:
                self._hear(brain, "alice moved the door")
                self._hear(brain, "alice said hello")
                narrative = brain._episodic_narrative()
                self.assertTrue(any("alice moved the door" in n for n in narrative), narrative)
                self.assertTrue(any("alice said hello" in n for n in narrative), narrative)
            finally:
                brain.stop()

    def test_recall_context_returns_weighted_memories(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "m2.db")
            brain = self._brain(db)
            brain.start()
            try:
                self._hear(brain, "alice moved the door")
                self._hear(brain, "alice likes jazz")
                # recall for the salient entity alice
                from brain.b1_cognition import Situation
                sit = Situation(cycle=1, entities=(), salient_entities=("alice",), recent_events=(), uncertainty=(), evidence=())
                result = brain._recall_context(sit, ())
                self.assertTrue(result["memories"])
                self.assertIn("alice", result["query"])
            finally:
                brain.stop()


if __name__ == "__main__":
    unittest.main()
