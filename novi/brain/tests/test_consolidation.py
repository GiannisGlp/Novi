import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from novi.brain.consolidation import ConsolidationConfig, MemoryConsolidator
from novi.brain.models import DeterministicSTTProvider
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.storage import DurableMemoryStore
from novi.brain.tests.test_mac_brain import FakeCamera


def _admit(store, memory_type, content, confidence, entity_refs=()):
    return store.admit(
        memory_type=memory_type,
        content=content,
        confidence=confidence,
        verification_status="verified",
        privacy_class="public",
        provenance={"source": "test"},
        entity_refs=tuple(entity_refs),
    )


def _future_iso(created_at: str, seconds: float) -> str:
    t = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    return (t + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


class MemoryConsolidatorTests(unittest.TestCase):
    def test_expiry_sets_expired_state_and_hides_from_retrieval(self):
        with tempfile.TemporaryDirectory() as td:
            store = DurableMemoryStore(Path(td) / "s.db")
            admission = _admit(store, "perception", "stale", confidence=0.9, entity_refs=("x",))
            cfg = ConsolidationConfig(ttl_by_type={"perception": 100}, contradiction_types=())
            cons = MemoryConsolidator(store, cfg)
            rec = store.get(admission.memory_id)
            report = cons.consolidate(now=_future_iso(rec.created_at, 200))
            self.assertEqual(report.expired, 1)
            self.assertEqual(store.get_state(admission.memory_id), "expired")
            self.assertEqual(store.active_count, 0)
            self.assertEqual(store.retrieve("stale"), ())

    def test_confidence_decay_archives_below_min(self):
        with tempfile.TemporaryDirectory() as td:
            store = DurableMemoryStore(Path(td) / "s.db")
            admission = _admit(store, "perception", "decaying", confidence=0.9, entity_refs=("x",))
            cfg = ConsolidationConfig(
                decay_start_seconds=0.0,
                decay_period_seconds=10.0,
                decay_factor=0.5,
                min_confidence=0.3,
                contradiction_types=(),
            )
            cons = MemoryConsolidator(store, cfg)
            rec = store.get(admission.memory_id)
            # mild decay: confidence stays above min -> decayed, still active
            report1 = cons.consolidate(now=_future_iso(rec.created_at, 10))
            self.assertEqual(report1.decayed, 1)
            self.assertEqual(store.get_state(admission.memory_id), "active")
            self.assertAlmostEqual(store.get(admission.memory_id).confidence, 0.45, places=3)
            # deeper decay: confidence below min -> archived
            report2 = cons.consolidate(now=_future_iso(rec.created_at, 40))
            self.assertEqual(report2.archived, 1)
            self.assertEqual(store.get_state(admission.memory_id), "archived")
            self.assertEqual(store.active_count, 0)

    def test_contradiction_resolution_supersedes_stale_fact(self):
        with tempfile.TemporaryDirectory() as td:
            store = DurableMemoryStore(Path(td) / "s.db")
            cfg = ConsolidationConfig(contradiction_types=("fact",))
            cons = MemoryConsolidator(store, cfg)
            old = _admit(store, "fact", "height is 5", confidence=0.6, entity_refs=("tree",))
            new = _admit(store, "fact", "height is 9", confidence=0.9, entity_refs=("tree",))
            cons.consolidate()
            # newer/higher-confidence fact survives; older superseded
            self.assertEqual(store.get_state(new.memory_id), "active")
            self.assertEqual(store.get_state(old.memory_id), "superseded")
            results = store.retrieve("height", entity="tree", memory_type="fact")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].content, "height is 9")


class BrainConsolidationTests(unittest.TestCase):
    def test_consolidator_attached_with_durable_store_and_emits_event(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "brain.db"
            cfg = MacBrainConfig(
                consolidation_config=ConsolidationConfig(
                    decay_start_seconds=0.0,
                    decay_period_seconds=1.0,
                    decay_factor=0.1,
                    min_confidence=0.5,
                )
            )
            brain = MacBrain(camera=FakeCamera(), store_path=str(db), config=cfg)
            self.assertIsNotNone(brain.consolidator)
            brain.start()
            brain.ingest_transcript(DeterministicSTTProvider("alice said hello").transcribe("x.wav"))
            # find the stored utterance record to compute a future timestamp
            records = brain.memory.retrieve("alice", entity="alice")
            self.assertTrue(records)
            future = _future_iso(records[0].created_at, 10)
            brain.consolidate(now=future)
            brain.stop()
            events = [e for e in brain.events if e["event_type"] == "memory.consolidated"]
            self.assertTrue(events)
            self.assertGreaterEqual(events[-1]["payload"]["archived"], 0)


if __name__ == "__main__":
    unittest.main()
