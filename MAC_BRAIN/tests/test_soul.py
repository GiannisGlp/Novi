import tempfile
import unittest
from pathlib import Path

from MAC_BRAIN.runtime import MacBrain
from MAC_BRAIN.soul import Soul
from MAC_BRAIN.storage import DurableMemoryStore
from MAC_BRAIN.tests.test_mac_brain import FakeCamera


class SoulTests(unittest.TestCase):
    def test_identity_and_values_are_stable(self):
        soul = Soul()
        self.assertEqual(soul.identity.name, "Novi")
        self.assertEqual(soul.personality.values["non_harm"], 1.0)
        self.assertIn("honesty", soul.personality.values)
        # traits are bounded
        for v in soul.personality.traits.values():
            self.assertGreaterEqual(v, 0.0)
            self.assertLessEqual(v, 1.0)

    def test_success_raises_satisfaction(self):
        soul = Soul()
        before = soul.affect.dimensions["satisfaction"]
        soul.update({"kind": "task_success"})
        self.assertGreater(soul.affect.dimensions["satisfaction"], before)

    def test_failure_raises_frustration_and_caution(self):
        soul = Soul()
        f0 = soul.affect.dimensions["frustration"]
        c0 = soul.affect.dimensions["caution"]
        soul.update({"kind": "goal_failed"})
        self.assertGreater(soul.affect.dimensions["frustration"], f0)
        self.assertGreater(soul.affect.dimensions["caution"], c0)
        self.assertGreater(soul.motivations["recover"], 0.5)

    def test_affect_decays_toward_baseline(self):
        soul = Soul()
        soul.update({"kind": "task_success"})
        elevated = soul.affect.dimensions["satisfaction"]
        for _ in range(20):
            soul.affect.decay(0.8)
        self.assertLess(soul.affect.dimensions["satisfaction"], elevated)

    def test_tone_is_context_and_affect_aware(self):
        soul = Soul()
        self.assertIn(soul.tone()["tone"], {"warm", "curious"})
        serious = soul.tone({"serious": True})
        self.assertEqual(serious["tone"], "calm")
        self.assertFalse(serious["playful"])

    def test_affect_never_rewrites_personality(self):
        soul = Soul()
        traits = dict(soul.personality.traits)
        for kind in ("goal_failed", "task_failure", "uncertain"):
            soul.update({"kind": kind})
        self.assertEqual(soul.personality.traits, traits)
        self.assertEqual(soul.personality.values, {"honesty": 0.9, "respect": 0.95, "curiosity": 0.9, "care": 0.85, "learning": 0.9, "coherence": 0.9, "humility": 0.85, "non_harm": 1.0})

    def test_soul_persists_durable_state_across_restart(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "soul.db"
            store = DurableMemoryStore(db)
            soul = Soul()
            soul.update({"kind": "goal_completed"})
            store.save_soul(soul.durable_snapshot())
            store.close()
            reopened = DurableMemoryStore(db)
            snap = reopened.load_soul()
            restored = Soul.from_snapshot(snap)
            self.assertEqual(restored.identity.name, "Novi")
            self.assertEqual(restored.personality.traits, soul.personality.traits)
            self.assertEqual(restored.motivations, soul.motivations)
            reopened.close()


class BrainSoulTests(unittest.TestCase):
    def test_brain_updates_soul_and_reports_tone(self):
        brain = MacBrain(camera=FakeCamera())
        brain.start()
        result = brain.step()
        brain.stop()
        self.assertIn("soul", result)
        self.assertIn(result["soul"]["tone"], {"warm", "curious", "calm", "satisfied", "recovering", "cautious"})
        self.assertTrue(any(e["event_type"] == "soul.updated" for e in brain.events))

    def test_soul_persisted_when_durable(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "brain.db"
            brain = MacBrain(camera=FakeCamera(), store_path=str(db))
            brain.start()
            brain.step()
            brain.stop()
            store = DurableMemoryStore(db)
            self.assertIsNotNone(store.load_soul())
            store.close()


if __name__ == "__main__":
    unittest.main()
