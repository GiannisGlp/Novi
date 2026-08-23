"""Incremental knowledge persistence: triples are written to the durable store
immediately (not only at shutdown), so a crash cannot lose learned knowledge,
and a fresh brain reloads them on start."""

import tempfile
import unittest
from pathlib import Path

from novi.brain.models.stt import TranscriptionResult
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.tests.test_mac_brain import FakeCamera


class IncrementalKnowledgePersistenceTests(unittest.TestCase):
    def _brain(self, store_path):
        return MacBrain(camera=FakeCamera(), store_path=store_path, config=MacBrainConfig())

    def _hear(self, brain, text, confidence=0.9):
        return brain.ingest_transcript(
            TranscriptionResult(text=text, language="en", confidence=confidence, audio_path="", provider="web", model_id="web")
        )

    def test_triple_persisted_before_stop(self):
        """The triple must be in the store as soon as it is learned — before stop()."""
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "k.db")
            brain = self._brain(db)
            brain.start()
            try:
                self._hear(brain, "alice moved the door")
                # Without calling stop(), the durable store must already hold the triple.
                snap = brain.memory.load_knowledge()
                self.assertIsNotNone(snap)
                triples = snap["triples"]
                self.assertTrue(any(t["subject"] == "alice" and t["predicate"] == "moved" and t["object"] == "door" for t in triples), triples)
            finally:
                brain.stop()

    def test_reload_on_start(self):
        """A fresh brain on the same store recalls the triple from the previous run."""
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "k.db")
            b1 = self._brain(db)
            b1.start()
            self._hear(b1, "alice moved the door")
            b1.stop()  # graceful (also covers the normal save path)

            b2 = self._brain(db)
            b2.start()
            try:
                ctx = b2.knowledge.context("alice")
                self.assertTrue(any(t.predicate == "moved" and t.object == "door" for t in ctx), ctx)
            finally:
                b2.stop()

    def test_graph_on_change_hook_fires_on_add(self):
        from novi.brain.kgraph import EntityKnowledgeGraph

        calls = []
        g = EntityKnowledgeGraph(on_change=lambda: calls.append(1))
        g.add("alice", "moved", "door", confidence=0.9, cycle=1)
        self.assertEqual(len(calls), 1)
        # re-adding (evidence bump) also fires
        g.add("alice", "moved", "door", confidence=0.8, cycle=2)
        self.assertEqual(len(calls), 2)

    def test_identity_persists_before_stop(self):
        """Person-name bindings are written to the store immediately (not only on stop)."""
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "id.db")
            b1 = self._brain(db)
            b1.start()
            self._hear(b1, "Hi novi, its me Vano")
            snap = b1.memory.load_identity()  # must already be persisted, before stop()
            self.assertIsNotNone(snap)
            names = {n for binds in snap.get("bindings", {}).values() for n in binds}
            self.assertIn("vano", names)
            b1.stop()

    def test_identity_reloads_on_start(self):
        """A fresh brain on the same store recognizes the person from a prior run."""
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "id2.db")
            b1 = self._brain(db)
            b1.start()
            self._hear(b1, "Hi novi, its me Vano")
            b1.stop()
            b2 = self._brain(db)
            b2.start()
            try:
                belief = b2.identity.identity_for("person")
                self.assertIsNotNone(belief)
                binds = b2.identity.snapshot()["bindings"].get("person", {})
                self.assertIn("vano", binds)
            finally:
                b2.stop()


if __name__ == "__main__":
    unittest.main()
