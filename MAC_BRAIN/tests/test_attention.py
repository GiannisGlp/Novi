"""Tests for AttentionCandidates (PERFECTING_PLAN Step 1).

Covers:
  - Cognition supplies ranked candidates; Autonomy decides.
  - Scoring across salience, novelty, urgency, social, relevance, uncertainty.
  - Suggested actions: observe, orient, ask, ignore.
  - Uncertainty-driven attention gaps.
"""

import unittest

from MAC_BRAIN.world_model import (
    WorldModel,
    OBSERVED,
    INFERRED,
    PREDICTED,
    UNKNOWN,
    PERSON,
    OBJECT,
    ROOM,
)
from MAC_BRAIN.attention import (
    AttentionCandidate,
    AttentionRanker,
    SALIENCE,
    NOVELTY,
    URGENCY,
    SOCIAL,
    RELEVANCE,
    UNCERTAINTY,
)


class AttentionRankerTests(unittest.TestCase):
    def test_rank_produces_candidates(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.9)
        wm.add_entity("cup_001", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.8)
        ranker = AttentionRanker()
        candidates = ranker.rank(wm)
        self.assertEqual(len(candidates), 2)
        for c in candidates:
            self.assertIsInstance(c, AttentionCandidate)
            self.assertGreater(c.overall, 0.0)

    def test_person_gets_social_boost(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.5)
        wm.add_entity("cup_001", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.5)
        ranker = AttentionRanker()
        candidates = ranker.rank(wm)
        alice = next(c for c in candidates if c.target_id == "alice_001")
        cup = next(c for c in candidates if c.target_id == "cup_001")
        self.assertGreater(alice.scores[SOCIAL], cup.scores[SOCIAL])

    def test_unknown_entity_gets_uncertainty_boost(self):
        wm = WorldModel()
        wm.add_entity("known_001", OBJECT, labels=["known"], epistemic_status=OBSERVED, confidence=0.8)
        wm.add_entity("unknown_001", OBJECT, labels=["unknown"], epistemic_status=UNKNOWN, confidence=0.1)
        ranker = AttentionRanker()
        candidates = ranker.rank(wm)
        unknown = next(c for c in candidates if c.target_id == "unknown_001")
        known = next(c for c in candidates if c.target_id == "known_001")
        self.assertGreater(unknown.scores[UNCERTAINTY], known.scores[UNCERTAINTY])
        self.assertEqual(unknown.suggested_action, "observe")

    def test_novel_entity_gets_novelty_score(self):
        wm = WorldModel()
        wm.add_entity("new_001", OBJECT, labels=["new thing"], epistemic_status=UNKNOWN, confidence=0.2)
        ranker = AttentionRanker()
        candidates = ranker.rank(wm, known_entities={"new_001"})  # already known -> not novel
        # Now test with empty known set -> novel
        candidates2 = ranker.rank(wm, known_entities=set())
        novel_cand = next(c for c in candidates2 if c.target_id == "new_001")
        self.assertGreater(novel_cand.scores[NOVELTY], 0.5)

    def test_relevance_to_goal_target(self):
        wm = WorldModel()
        wm.add_entity("cup_001", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.8)
        wm.add_entity("door_001", OBJECT, labels=["door"], epistemic_status=OBSERVED, confidence=0.8)
        ranker = AttentionRanker()
        candidates = ranker.rank(wm, active_goal_target="cup")
        cup = next(c for c in candidates if c.target_id == "cup_001")
        door = next(c for c in candidates if c.target_id == "door_001")
        self.assertGreater(cup.scores[RELEVANCE], door.scores[RELEVANCE])

    def test_urgency_boost_for_alert_state(self):
        wm = WorldModel()
        wm.add_entity("door_001", OBJECT, labels=["door"], epistemic_status=OBSERVED, confidence=0.8)
        wm.update_entity_state("door_001", "state", "open", epistemic_status=OBSERVED, confidence=0.9, source="sensor")
        wm.add_entity("chair_001", OBJECT, labels=["chair"], epistemic_status=OBSERVED, confidence=0.8)
        wm.update_entity_state("chair_001", "state", "stationary", epistemic_status=OBSERVED, confidence=0.9, source="sensor")
        ranker = AttentionRanker()
        candidates = ranker.rank(wm)
        door = next(c for c in candidates if c.target_id == "door_001")
        chair = next(c for c in candidates if c.target_id == "chair_001")
        self.assertGreater(door.scores[URGENCY], chair.scores[URGENCY])

    def test_ranked_by_overall_score(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.9)
        wm.add_entity("cup_001", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.8)
        wm.add_entity("unknown_001", OBJECT, labels=["mystery"], epistemic_status=UNKNOWN, confidence=0.1)
        ranker = AttentionRanker()
        candidates = ranker.rank(wm)
        # Candidates are sorted by overall descending.
        for i in range(len(candidates) - 1):
            self.assertGreaterEqual(candidates[i].overall, candidates[i + 1].overall)

    def test_suggested_actions(self):
        wm = WorldModel()
        wm.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.9)
        wm.add_entity("mystery_001", OBJECT, labels=["mystery"], epistemic_status=UNKNOWN, confidence=0.1)
        ranker = AttentionRanker()
        candidates = ranker.rank(wm)
        alice = next(c for c in candidates if c.target_id == "alice_001")
        mystery = next(c for c in candidates if c.target_id == "mystery_001")
        self.assertEqual(alice.suggested_action, "ask")  # person -> social invitation
        self.assertEqual(mystery.suggested_action, "observe")  # unknown -> observe

    def test_snapshot(self):
        c = AttentionCandidate(
            candidate_id="att:x", target_type="entity", target_id="x", target_label="X",
            scores={"salience": 0.8}, overall=0.5, reason="test", suggested_action="observe",
        )
        snap = c.snapshot()
        self.assertEqual(snap["candidate_id"], "att:x")
        self.assertEqual(snap["overall"], 0.5)
        self.assertEqual(snap["suggested_action"], "observe")

    def test_top_n(self):
        wm = WorldModel()
        for i in range(10):
            conf = 0.1 * (i + 1)
            wm.add_entity(f"obj_{i}", OBJECT, labels=[f"obj{i}"], epistemic_status=OBSERVED, confidence=conf)
        ranker = AttentionRanker()
        candidates = ranker.rank(wm)
        top3 = ranker.top_n(candidates, n=3)
        self.assertEqual(len(top3), 3)
        self.assertGreaterEqual(top3[0].overall, top3[1].overall)

    def test_archived_entities_excluded(self):
        from MAC_BRAIN.world_model import ARCHIVED
        wm = WorldModel()
        wm.add_entity("active_001", OBJECT, labels=["active"], epistemic_status=OBSERVED, confidence=0.8)
        wm.add_entity("old_001", OBJECT, labels=["old"], epistemic_status=OBSERVED, confidence=0.8)
        wm.set_entity_lifecycle("old_001", ARCHIVED)
        ranker = AttentionRanker()
        candidates = ranker.rank(wm)
        ids = {c.target_id for c in candidates}
        self.assertIn("active_001", ids)
        self.assertNotIn("old_001", ids)


if __name__ == "__main__":
    unittest.main()