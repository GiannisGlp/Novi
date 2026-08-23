import tempfile
import unittest
from pathlib import Path

from novi.brain.contracts import utc_now
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.storage import DurableMemoryStore
from novi.brain.tests.test_mac_brain import FakeCamera
from novi.brain.vector import HashingEmbedding, cosine


def admit(store, content, entity_refs=()):
    return store.admit(
        memory_type="episode", content=content, confidence=0.8, verification_status="pending",
        privacy_class="private", provenance={"source": "test", "captured_at": utc_now()}, entity_refs=entity_refs,
    )


class EmbeddingTests(unittest.TestCase):
    def test_deterministic_same_text_same_vector(self):
        e = HashingEmbedding()
        a = e.embed("alice moved the red lamp")
        b = e.embed("alice moved the red lamp")
        self.assertEqual(a, b)

    def test_shared_tokens_score_higher(self):
        e = HashingEmbedding()
        base = e.embed("alice moved the lamp")
        similar = e.embed("alice moved the lamp today")
        unrelated = e.embed("the cat sat on the mat")
        self.assertGreater(cosine(base, similar), cosine(base, unrelated))

    def test_cosine_normalized(self):
        a = HashingEmbedding().embed("hello world")
        self.assertAlmostEqual(sum(v * v for v in a), 1.0, places=6)


class SemanticRetrievalTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = DurableMemoryStore(Path(self._tmp.name) / "mem.db")

    def tearDown(self):
        try:
            self.store.close()
        except Exception:
            pass

    def test_retrieve_semantic_returns_relevant(self):
        admit(self.store, "alice watered the green plants")
        admit(self.store, "the cat chased the mouse")
        admit(self.store, "alice moved the lamp")
        got = self.store.retrieve_semantic("alice lamp", limit=5)
        self.assertGreater(len(got), 0)
        # highest shared-token overlap ranks first
        self.assertEqual(got[0].content, "alice moved the lamp")

    def test_retrieve_semantic_respects_entity_and_type(self):
        admit(self.store, "alice watered plants", entity_refs=("alice", "plant"))
        admit(self.store, "bob watered plants", entity_refs=("bob", "plant"))
        got = self.store.retrieve_semantic("plants", entity="alice", limit=5)
        self.assertTrue(all("alice" in r.entity_refs for r in got))

    def test_vectors_persist_across_reopen(self):
        admit(self.store, "alice moved the red lamp")
        path = Path(self._tmp.name) / "mem.db"
        self.store.close()
        reopened = DurableMemoryStore(path)
        got = reopened.retrieve_semantic("alice lamp", limit=5)
        self.assertGreater(len(got), 0)
        reopened.close()
        self.store = reopened  # avoid double-close in tearDown

    def test_forget_removes_from_vector_index(self):
        adm = admit(self.store, "alice moved the red lamp")
        before = self.store.retrieve_semantic("alice", limit=10)
        self.assertGreater(len(before), 0)
        self.assertTrue(self.store.forget(adm.memory_id))
        after = self.store.retrieve_semantic("alice", limit=10)
        self.assertNotIn(adm.memory_id, [r.memory_id for r in after])


class BrainSemanticTests(unittest.TestCase):
    def test_brain_recall_semantic_emits_event(self):
        from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception

        class LampBackend(DeterministicPerceptionBackend):
            def detect(self, frame):
                return (Detection("lamp", 0.8, (0, 0, 1, 1)),)

        with tempfile.TemporaryDirectory() as td:
            brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(LampBackend()), store_path=str(Path(td) / "b.db"), config=MacBrainConfig(curiosity_enabled=False))
            brain.start()
            for _ in range(3):
                brain.step()
            result = brain.recall_semantic("lamp")
            brain.stop()
            self.assertIn("memory.semantic_recall", [e["event_type"] for e in brain.events])
            self.assertGreater(len(result["memories"]), 0)


class FakeBrainCamera(FakeCamera):
    pass


if __name__ == "__main__":
    unittest.main()
