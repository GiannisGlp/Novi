"""Memory consolidation into higher-level summaries (Memory 3.0).

Verifies the SummaryConsolidator: groups episodic memories by entity and distills
them into a single higher-level summary memory, idempotently, and wired into the
runtime consolidate() pass.
"""

import tempfile
import unittest
from pathlib import Path

from novi.brain.consolidation import SummaryConsolidator
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.models.stt import TranscriptionResult
from novi.brain.storage import DurableMemoryStore
from novi.brain.tests.test_mac_brain import FakeCamera


class SummaryConsolidatorTests(unittest.TestCase):
    def _store(self, td):
        return DurableMemoryStore(str(Path(td) / "m.db"))

    def _admit(self, store, text, entity):
        return store.admit(
            memory_type="utterance",
            content=text,
            confidence=0.9,
            verification_status="verified",
            privacy_class="public",
            provenance={"source": "test"},
            entity_refs=(entity,),
        )

    def test_consolidates_episodic_memories_into_summary(self):
        with tempfile.TemporaryDirectory() as td:
            store = self._store(td)
            self._admit(store, "alice moved the door", "alice")
            self._admit(store, "alice likes jazz", "alice")
            c = SummaryConsolidator(store)
            report = c.consolidate()
            self.assertEqual(report.created, 1)
            summaries = [r for r in store.active_rows() if r["record"].memory_type == "summary"]
            self.assertEqual(len(summaries), 1)
            self.assertIn("alice", summaries[0]["record"].content)
            self.assertIn("moved the door", summaries[0]["record"].content)
            self.assertIn("likes jazz", summaries[0]["record"].content)

    def test_idempotent_across_runs(self):
        with tempfile.TemporaryDirectory() as td:
            store = self._store(td)
            self._admit(store, "alice moved the door", "alice")
            self._admit(store, "alice likes jazz", "alice")
            c = SummaryConsolidator(store)
            c.consolidate()
            second = c.consolidate()
            self.assertEqual(second.created, 0)
            summaries = [r for r in store.active_rows() if r["record"].memory_type == "summary"]
            self.assertEqual(len(summaries), 1)

    def test_below_min_group_size_no_summary(self):
        with tempfile.TemporaryDirectory() as td:
            store = self._store(td)
            self._admit(store, "alice moved the door", "alice")
            c = SummaryConsolidator(store, min_group_size=2)
            report = c.consolidate()
            self.assertEqual(report.created, 0)


class SummaryRuntimeTests(unittest.TestCase):
    def test_consolidate_emits_summary_memory(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "m.db")
            brain = MacBrain(camera=FakeCamera(), store_path=db, config=MacBrainConfig())
            brain.start()
            try:
                for text in ("alice moved the door", "alice likes jazz"):
                    brain.ingest_transcript(TranscriptionResult(text=text, language="en", confidence=0.9, audio_path="", provider="web", model_id="web"))
                brain.consolidate()
                summaries = [r for r in brain.memory.active_rows() if r["record"].memory_type == "summary"]
                self.assertTrue(summaries, "expected a summary memory to be created")
                self.assertIn("alice", summaries[0]["record"].content)
                events = [e for e in brain.events if e["event_type"] == "memory.summarized"]
                self.assertTrue(events)
            finally:
                brain.stop()


if __name__ == "__main__":
    unittest.main()
