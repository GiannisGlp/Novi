import tempfile
import unittest
from pathlib import Path

from novi.brain.b2_perception import SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.social import RelationshipCategory, Relationships, SocialIntelligence
from novi.brain.storage import DurableMemoryStore
from novi.brain.tests.test_mac_brain import PersonBackend


class SocialRelationshipTests(unittest.TestCase):
    def test_interactions_build_familiarity_and_category(self):
        reg = Relationships()
        self.assertEqual(reg.category_for("alice"), RelationshipCategory.UNKNOWN)
        rel = reg.note_interaction("alice", quality=0.9, now="t0")
        self.assertEqual(rel.category, RelationshipCategory.FIRST_MEETING)
        for i in range(10):
            reg.note_interaction("alice", quality=0.9, now=f"t{i+1}")
        self.assertGreaterEqual(reg.get("alice").familiarity, 0.7)
        self.assertEqual(reg.get("alice").category, RelationshipCategory.FRIEND)

    def test_one_interaction_does_not_redefine_relationship(self):
        reg = Relationships()
        reg.note_interaction("alice")
        self.assertEqual(reg.category_for("alice"), RelationshipCategory.FIRST_MEETING)
        self.assertLess(reg.get("alice").familiarity, 0.3)

    def test_relationship_dims_independent(self):
        reg = Relationships()
        reg.get("bob").trust = 0.1  # know well but not trusted yet
        reg.get("bob").familiarity = 0.9
        # familiarity does not imply trust or permission
        self.assertGreater(reg.get("bob").familiarity, 0.7)
        self.assertLess(reg.get("bob").trust, 0.3)
        snap = reg.get("bob").snapshot()
        self.assertNotIn("authorized", snap)  # relationship is not permission

    def test_expression_differs_by_tier(self):
        reg = Relationships()
        social = SocialIntelligence()
        stranger = social.expression("stranger", reg, {"caution": 0.3})
        for i in range(12):
            reg.note_interaction("friend", quality=0.9, now=f"t{i}")
        friend = social.expression("friend", reg, {"caution": 0.3})
        self.assertIn(stranger["tone"], {"polite", "friendly"})
        self.assertTrue(stranger["reserved"])
        self.assertEqual(friend["tone"], "warm")
        self.assertTrue(friend["playful"])
        self.assertFalse(friend["reserved"])
        self.assertGreater(friend["warmth"], stranger["warmth"])

    def test_serious_context_suppresses_playfulness(self):
        reg = Relationships()
        social = SocialIntelligence()
        for i in range(12):
            reg.note_interaction("friend", quality=0.9, now=f"t{i}")
        serious = social.expression("friend", reg, {"caution": 0.3}, {"serious": True})
        self.assertEqual(serious["tone"], "calm")
        self.assertFalse(serious["playful"])

    def test_participation_gate_enforces_cooldown_and_discipline(self):
        reg = Relationships()
        social = SocialIntelligence(cooldown_cycles=4)
        d = social.participation_decision("alice", reg, direct_confidence=0.9, cycle=1)
        self.assertEqual(d["action"], "participate")
        # immediate repeat, not clearly addressed -> silence
        d2 = social.participation_decision("alice", reg, direct_confidence=0.3, relevance=0.5, cycle=2)
        self.assertEqual(d2["action"], "observe")
        # after cooldown, direct address again participates
        d3 = social.participation_decision("alice", reg, direct_confidence=0.9, cycle=10)
        self.assertEqual(d3["action"], "participate")
        # stranger needs higher confidence than familiar
        for i in range(12):
            reg.note_interaction("friend", quality=0.9, now=f"t{i}")
        social.participation_decision("stranger", reg, direct_confidence=0.5, cycle=20)
        d_friend = social.participation_decision("friend", reg, direct_confidence=0.5, cycle=21)
        self.assertEqual(d_friend["action"], "participate")

    def test_relationships_persist_durably(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "rel.db"
            store = DurableMemoryStore(db)
            reg = Relationships()
            for i in range(12):
                reg.note_interaction("alice", quality=0.9, now=f"t{i}")
            store.save_relationships(reg.snapshot())
            store.close()
            reopened = DurableMemoryStore(db)
            loaded = Relationships.from_snapshot(reopened.load_relationships())
            self.assertEqual(loaded.get("alice").category, RelationshipCategory.FRIEND)
            self.assertEqual(loaded.get("alice").interaction_count, 12)
            reopened.close()


class BrainSocialTests(unittest.TestCase):
    def test_brain_notes_person_relationship_and_emits_social(self):
        camera = __import__("novi.brain.tests.test_mac_brain", fromlist=["FakeCamera"]).FakeCamera()
        brain = MacBrain(camera=camera, perception=SpecialistPerception(PersonBackend()), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        self.assertIn("social.interaction", [e["event_type"] for e in brain.events])
        self.assertEqual(brain.relationships.get("person").interaction_count, 1)


if __name__ == "__main__":
    unittest.main()
