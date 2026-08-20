import tempfile
import unittest
from pathlib import Path

from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
from MAC_BRAIN.storage import DurableMemoryStore
from MAC_BRAIN.temporal import TemporalModel
from MAC_BRAIN.tests.test_mac_brain import FakeCamera


class TemporalModelTests(unittest.TestCase):
    def test_sequence_learns_causal_link(self):
        model = TemporalModel(window=3)
        for i in range(1, 9):
            model.record({"door"}, cycle=i)
            model.record({"alice"}, cycle=i)  # alice always follows door within window
        link = model.causal_confidence("door", "alice")
        self.assertIsNotNone(link)
        self.assertGreater(link.confidence, 0.5)
        self.assertIn(link.relation, {"verified", "plausible_cause", "inferred"})

    def test_causal_confidence_respects_occurrence_denominator(self):
        model = TemporalModel(window=1)
        for i in range(1, 5):
            model.record({"signal"}, cycle=i)
            if i <= 2:
                model.record({"lamp"}, cycle=i)  # lamp follows signal only twice of four
        link = model.causal_confidence("signal", "lamp")
        self.assertIsNotNone(link)
        self.assertLess(link.confidence, 1.0)
        self.assertGreater(link.confidence, 0.0)
        self.assertAlmostEqual(link.confidence, 0.5, places=3)

    def test_expected_after_orders_by_confidence(self):
        model = TemporalModel(window=3)
        for i in range(1, 9):
            model.record({"signal"}, cycle=i)
            model.record({"lamp"}, cycle=i)  # frequent effect
        model.record({"signal"}, cycle=10)
        expected = model.expected_after("signal", limit=3)
        self.assertTrue(expected)
        self.assertEqual(expected[0].effect, "lamp")

    def test_window_prevents_links_across_stale_gap(self):
        model = TemporalModel(window=1)
        model.record({"a"}, cycle=1)
        model.record({"b"}, cycle=100)  # far beyond window -> no link
        self.assertIsNone(model.causal_confidence("a", "b"))

    def test_recency_and_stale(self):
        model = TemporalModel()
        model.record({"lamp"}, cycle=1)
        self.assertGreater(model.recency("lamp", 2), 0.9)
        self.assertFalse(model.is_stale("lamp", cycle=5, stale_after=10))
        self.assertTrue(model.is_stale("lamp", cycle=50, stale_after=10))

    def test_timeline_and_top_links(self):
        model = TemporalModel()
        for i in range(1, 7):
            model.record({"x"}, cycle=i)
            model.record({"y"}, cycle=i)
        self.assertEqual(len(model.timeline(limit=2)), 2)
        top = model.top_links(limit=5)
        self.assertGreater(len(top), 0)

    def test_temporal_persists(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "t.db"
            store = DurableMemoryStore(db)
            model = TemporalModel(window=3)
            for i in range(1, 9):
                model.record({"door"}, cycle=i)
                model.record({"alice"}, cycle=i)
            store.save_temporal(model.snapshot())
            store.close()
            reopened = DurableMemoryStore(db)
            loaded = TemporalModel.from_snapshot(reopened.load_temporal())
            link = loaded.causal_confidence("door", "alice")
            self.assertIsNotNone(link)
            self.assertGreater(link.confidence, 0.5)
            reopened.close()


class BrainTemporalTests(unittest.TestCase):
    def test_brain_emits_temporal_and_reports_expected(self):
        from brain.b2_perception import SpecialistPerception
        from MAC_BRAIN.tests.test_mac_brain import PersonBackend
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(PersonBackend()), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        result = None
        for _ in range(4):
            result = brain.step()
        brain.stop()
        self.assertIn("temporal", result)
        self.assertIn("cognition.temporal", [e["event_type"] for e in brain.events])
        self.assertEqual(brain.temporal._last_seen.get("person"), 4)


if __name__ == "__main__":
    unittest.main()
