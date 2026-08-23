"""Tests for the Situation Model.

Verifies:
  - SituationModel derives situations from the WorldModel.
  - Situations have the full field set (situation_id, world_state_version, etc.).
  - Person-present, unfamiliar-object, goal-pursuit, and idle situations are recognized.
  - Situations have confidence, freshness, and provenance.
  - The situation.derived event is emitted in the runtime.
  - Multiple situations can overlap.
"""

import unittest

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.autonomy import Goal
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.situation_model import SituationModel
from novi.brain.tests.test_mac_brain import FakeCamera
from novi.brain.world_model import OBJECT, OBSERVED, PERSON, UNKNOWN, WorldModel


class CupBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)


class PersonBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("alice", 0.95, (0.0, 0.0, 0.3, 0.5)),)


class SituationModelTests(unittest.TestCase):
    def test_derive_produces_situations(self):
        wm = WorldModel()
        wm.add_entity("cup_001", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.85)
        sm = SituationModel()
        situations = sm.derive(wm)
        self.assertGreater(len(situations), 0)

    def test_idle_situation_when_nothing_happening(self):
        wm = WorldModel()
        sm = SituationModel()
        situations = sm.derive(wm)
        self.assertEqual(len(situations), 1)
        self.assertEqual(situations[0].situation_type, "idle")

    def test_person_present_situation(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.95)
        sm = SituationModel()
        situations = sm.derive(wm)
        person_situations = [s for s in situations if s.situation_type == "person_present"]
        self.assertEqual(len(person_situations), 1)
        self.assertIn("Alice", person_situations[0].label)

    def test_unfamiliar_object_situation(self):
        wm = WorldModel()
        wm.add_entity("mystery_001", OBJECT, labels=["mystery"], epistemic_status=UNKNOWN, confidence=0.1)
        sm = SituationModel()
        situations = sm.derive(wm)
        unknown_situations = [s for s in situations if s.situation_type == "unfamiliar_object"]
        self.assertEqual(len(unknown_situations), 1)
        self.assertIn("mystery", unknown_situations[0].label)

    def test_goal_pursuit_situation(self):
        wm = WorldModel()
        sm = SituationModel()
        situations = sm.derive(wm, active_goals=("goal_123",))
        goal_situations = [s for s in situations if s.situation_type == "goal_pursuit"]
        self.assertEqual(len(goal_situations), 1)
        self.assertIn("goal_123", goal_situations[0].active_goals)

    def test_conversation_occurring_situation(self):
        wm = WorldModel()
        sm = SituationModel()
        situations = sm.derive(wm, social_context={"conversation_active": True, "participants": ["Alice"]})
        conv_situations = [s for s in situations if s.situation_type == "conversation_occurring"]
        self.assertEqual(len(conv_situations), 1)

    def test_situations_overlap(self):
        """Multiple situations can be active simultaneously."""
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.95)
        wm.add_entity("mystery_001", OBJECT, labels=["mystery"], epistemic_status=UNKNOWN, confidence=0.1)
        sm = SituationModel()
        situations = sm.derive(wm, active_goals=("goal_1",))
        types = {s.situation_type for s in situations}
        self.assertIn("person_present", types)
        self.assertIn("unfamiliar_object", types)
        self.assertIn("goal_pursuit", types)

    def test_situation_has_full_field_set(self):
        wm = WorldModel()
        wm.add_entity("cup_001", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.85)
        sm = SituationModel()
        situations = sm.derive(wm)
        s = situations[0]
        self.assertTrue(s.situation_id)
        self.assertTrue(s.world_state_version >= 0)
        self.assertIsInstance(s.active_entities, tuple)
        self.assertIsInstance(s.active_events, tuple)
        self.assertIsInstance(s.active_activities, tuple)
        self.assertIsInstance(s.relationships, tuple)
        self.assertIsInstance(s.novi_state, dict)
        self.assertIsInstance(s.active_goals, tuple)
        self.assertIsInstance(s.attention_targets, tuple)
        self.assertIsInstance(s.hazards, tuple)
        self.assertIsInstance(s.opportunities, tuple)
        self.assertIsInstance(s.social_context, dict)
        self.assertIsInstance(s.recent_changes, tuple)
        self.assertIsInstance(s.predictions, tuple)
        self.assertIsInstance(s.uncertainties, tuple)
        self.assertIsInstance(s.provenance, dict)
        self.assertIn(s.freshness, ("fresh", "recent", "stale"))
        self.assertTrue(s.created_at)

    def test_freshness_reflects_world_change(self):
        """Regression: freshness was always 'stale' because the last-seen
        world version was updated before the freshness comparison, so the
        model always compared the version to itself."""
        wm = WorldModel()
        wm.add_entity("cup_001", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.85)
        sm = SituationModel()
        # First derivation: world has advanced from the initial -1 sentinel.
        first = sm.derive(wm)[0]
        self.assertNotEqual(first.freshness, "stale")
        # Second derivation with no world change: now stale.
        second = sm.derive(wm)[0]
        self.assertEqual(second.freshness, "stale")
        # World changes again: no longer stale.
        wm.add_entity("cup_002", OBJECT, labels=["cup2"], epistemic_status=OBSERVED, confidence=0.8)
        third = sm.derive(wm)[0]
        self.assertNotEqual(third.freshness, "stale")

    def test_situation_snapshot(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.95)
        sm = SituationModel()
        situations = sm.derive(wm)
        snap = situations[0].snapshot()
        self.assertIn("situation_id", snap)
        self.assertIn("situation_type", snap)
        self.assertIn("confidence", snap)
        self.assertIn("label", snap)

    def test_uncertainties_surfaced(self):
        wm = WorldModel()
        wm.add_entity("mystery_001", OBJECT, labels=["mystery"], epistemic_status=UNKNOWN, confidence=0.1)
        sm = SituationModel()
        situations = sm.derive(wm)
        # Uncertainties should be surfaced.
        all_uncertainties = []
        for s in situations:
            all_uncertainties.extend(s.uncertainties)
        self.assertTrue(any("mystery" in u for u in all_uncertainties))

    def test_situations_of_type(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.95)
        sm = SituationModel()
        sm.derive(wm)
        person_situations = sm.situations_of_type("person_present")
        self.assertEqual(len(person_situations), 1)


class SituationModelRuntimeIntegrationTests(unittest.TestCase):
    def test_situation_derived_event_emitted(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        event_types = [e["event_type"] for e in brain.events]
        self.assertIn("situation.derived", event_types)

    def test_last_situations_stored(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        self.assertGreater(len(brain._last_situations), 0)

    def test_person_detected_creates_person_situation(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(PersonBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        situation_types = [s["situation_type"] for s in brain._last_situations]
        self.assertIn("person_present", situation_types)

    def test_goal_active_creates_goal_pursuit_situation(self):
        brain = MacBrain(camera=FakeCamera(), perception=SpecialistPerception(CupBackend()),
                         config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.set_goal(Goal.reach(3.0, 0.0, max_steps=60))
        brain.step()
        brain.stop()
        situation_types = [s["situation_type"] for s in brain._last_situations]
        self.assertIn("goal_pursuit", situation_types)


if __name__ == "__main__":
    unittest.main()
