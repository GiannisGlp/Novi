import tempfile
import unittest
from pathlib import Path

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.kgraph import EntityKnowledgeGraph, infer_entity_type
from novi.brain.models.stt import TranscriptionResult
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.storage import DurableMemoryStore
from novi.brain.tests.test_mac_brain import FakeCamera


class KnowledgeGraphTests(unittest.TestCase):
    def test_add_and_query_triple(self):
        g = EntityKnowledgeGraph()
        g.add("alice", "moved", "door", confidence=0.8, source="s1", cycle=1)
        triples = g.triples(subject="alice")
        self.assertEqual(len(triples), 1)
        self.assertEqual(triples[0].predicate, "moved")
        self.assertEqual(triples[0].evidence_count, 1)

    def test_contradiction_preserves_evidence(self):
        g = EntityKnowledgeGraph()
        g.add("alice", "located_near", "kitchen", confidence=0.9, source="s1", cycle=1)
        g.add("alice", "located_near", "garden", confidence=0.8, source="s2", cycle=2)
        self.assertTrue(g.has_conflict("alice", "located_near"))
        # Phase P3: rivals are now SUPERSEDED (window closed, successor linked),
        # not merely 'contradicted' — evidence is still preserved and queryable.
        history = g.history(subject="alice", predicate="located_near")
        self.assertEqual(len(history), 1)
        lead = g.leading("alice", "located_near")
        self.assertEqual(lead.object, "kitchen")  # highest-weighted object stays active
        self.assertEqual(lead.status, "active")
        superseded = history[0]
        self.assertEqual(superseded.object, "garden")
        self.assertEqual(superseded.status, "superseded")
        # temporal window closed at the cycle the rival lost + succession link
        self.assertEqual(superseded.valid_until_cycle, 2)
        self.assertEqual(superseded.superseded_by, ("alice", "located_near", "kitchen"))

    def test_extraction_from_text(self):
        g = EntityKnowledgeGraph()
        triples = g.extract_from_text("alice moved the door", ("alice", "door"))
        self.assertEqual(len(triples), 1)
        s, p, o = triples[0]
        self.assertEqual((s, o), ("alice", "door"))
        self.assertEqual(p, "moved")

    def test_infer_entity_type(self):
        self.assertEqual(infer_entity_type("alice"), "person")
        self.assertEqual(infer_entity_type("kitchen"), "place")
        self.assertEqual(infer_entity_type("lamp"), "object")

    def test_context_query(self):
        g = EntityKnowledgeGraph()
        g.add("alice", "moved", "door", confidence=0.8, source="s", cycle=1)
        g.add("alice", "located_near", "garden", confidence=0.7, source="s", cycle=2)
        ctx = g.context("alice")
        self.assertEqual(len(ctx), 2)
        self.assertTrue(all(t.subject == "alice" or t.object == "alice" for t in ctx))

    def test_durability(self):
        with tempfile.TemporaryDirectory() as td:
            store = DurableMemoryStore(Path(td) / "k.db")
            g = EntityKnowledgeGraph()
            g.add("alice", "moved", "door", confidence=0.9, source="s", cycle=1)
            store.save_knowledge(g.snapshot())
            store.close()
            reopened = DurableMemoryStore(Path(td) / "k.db")
            loaded = EntityKnowledgeGraph.from_snapshot(reopened.load_knowledge())
            self.assertEqual(len(loaded.triples()), 1)
            self.assertEqual(loaded.leading("alice", "moved").object, "door")
            reopened.close()


class BrainKnowledgeTests(unittest.TestCase):
    class PersonBackend(DeterministicPerceptionBackend):
        def detect(self, frame):
            return (Detection("person", 0.8, (0, 0, 1, 1)),)

    def _brain(self):
        return MacBrain(camera=FakeCamera(), perception=SpecialistPerception(self.PersonBackend()), config=MacBrainConfig(curiosity_enabled=False))

    def test_speech_builds_knowledge_triples(self):
        brain = self._brain()
        brain.start()
        tr = TranscriptionResult(text="alice moved the door", language="en", confidence=0.9, audio_path="", provider="test", model_id="test")
        brain.ingest_transcript(tr)
        brain.stop()
        self.assertEqual(brain.knowledge.counts()["triples"], 1)
        self.assertIn("knowledge.updated", [e["event_type"] for e in brain.events])
        self.assertGreater(len(brain.knowledge.triples()), 0)

    def test_retrieve_knowledge_emits_event(self):
        brain = self._brain()
        brain.start()
        tr = TranscriptionResult(text="alice moved the door", language="en", confidence=0.9, audio_path="", provider="test", model_id="test")
        brain.ingest_transcript(tr)
        result = brain.retrieve_knowledge("alice")
        brain.stop()
        self.assertGreater(len(result["triples"]), 0)
        self.assertIn("knowledge.recalled", [e["event_type"] for e in brain.events])

    def test_knowledge_reported_in_step(self):
        brain = self._brain()
        brain.start()
        result = brain.step()
        brain.stop()
        self.assertIn("knowledge", result)
        self.assertIn("triples", result["knowledge"])


if __name__ == "__main__":
    unittest.main()
