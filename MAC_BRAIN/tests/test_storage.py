import tempfile
import unittest
from pathlib import Path

from brain.b2_perception import Detection, SpecialistPerception, DeterministicPerceptionBackend
from MAC_BRAIN.io import CameraFrame
from MAC_BRAIN.models import DeterministicSTTProvider
from MAC_BRAIN.runtime import MacBrain
from MAC_BRAIN.storage import DurableMemoryStore
from MAC_BRAIN.autonomy import Goal, GoalStatus
from MAC_BRAIN.tests.test_mac_brain import FakeCamera


class AliceBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("alice", 0.95, (0, 0, 1, 1)),)


class DurableMemoryStoreTests(unittest.TestCase):
    def _path(self, tmp):
        return Path(tmp) / "state.db"

    def test_admit_retrieve_persist_across_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db = self._path(td)
            store = DurableMemoryStore(db)
            admission = store.admit(
                memory_type="utterance",
                content="alice said hello",
                confidence=0.9,
                verification_status="verified",
                privacy_class="public",
                provenance={"source": "speech.stt"},
                entity_refs=("alice",),
            )
            self.assertTrue(admission.accepted)
            store.close()

            reopened = DurableMemoryStore(db)
            self.assertEqual(reopened.active_count, 1)
            matches = reopened.retrieve("alice", entity="alice")
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0].content, "alice said hello")
            record = reopened.get(admission.memory_id)
            self.assertIsNotNone(record)
            self.assertEqual(record.entity_refs, ("alice",))
            reopened.close()

    def test_forget_persists_deleted_flag(self):
        with tempfile.TemporaryDirectory() as td:
            db = self._path(td)
            store = DurableMemoryStore(db)
            admission = store.admit(
                memory_type="perception",
                content="alice",
                confidence=0.95,
                verification_status="verified",
                privacy_class="public",
                provenance={"source": "vision"},
                entity_refs=("alice",),
            )
            store.close()
            reopened = DurableMemoryStore(db)
            self.assertTrue(reopened.forget(admission.memory_id))
            self.assertEqual(reopened.active_count, 0)
            self.assertEqual(reopened.deleted_count, 1)
            reopened.close()

    def test_goal_history_persists(self):
        with tempfile.TemporaryDirectory() as td:
            db = self._path(td)
            store = DurableMemoryStore(db)
            store.save_goal(goal_id="g1", kind="reach", target=(8.0, 0.0), priority=1.0, max_steps=30, created_cycle=0, status=GoalStatus.COMPLETED.value, steps_taken=16)
            store.close()
            reopened = DurableMemoryStore(db)
            goals = reopened.goals()
            self.assertEqual(len(goals), 1)
            self.assertEqual(goals[0]["goal_id"], "g1")
            self.assertEqual(goals[0]["target"], [8.0, 0.0])
            self.assertEqual(goals[0]["status"], "completed")
            reopened.close()


class DurableBrainTests(unittest.TestCase):
    def test_brain_memory_survives_restart(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "brain.db"
            brain = MacBrain(camera=FakeCamera(), store_path=str(db))
            brain.start()
            brain.ingest_transcript(DeterministicSTTProvider("alice said hello").transcribe("x.wav"))
            brain.set_goal(Goal.reach(8.0, 0.0, max_steps=30))
            for _ in range(20):
                brain.step()
            brain.stop()

            # reopen against the same store
            brain2 = MacBrain(camera=FakeCamera(), store_path=str(db))
            brain2.start()
            self.assertGreaterEqual(brain2.memory.active_count, 1)
            self.assertEqual(len(brain2.memory.goals()), 1)
            matches = brain2.memory.retrieve("alice", entity="alice")
            self.assertTrue(matches)
            brain2.stop()

    def test_durable_store_is_used_and_closed(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "brain.db"
            brain = MacBrain(camera=FakeCamera(), store_path=str(db))
            self.assertIsInstance(brain.memory, DurableMemoryStore)
            brain.start()
            brain.set_goal(Goal.reach(2.0, 0.0, max_steps=10))
            brain.step()
            brain.stop()
            # store file exists on disk after close
            self.assertTrue(db.exists())


if __name__ == "__main__":
    unittest.main()
