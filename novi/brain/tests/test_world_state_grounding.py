"""Tests for grounded world state (06_AUTONOMY doc 03).

Covers: freshness/TTL expiry, belief revision with evidence tiers (the
model-inference-vs-direct-observation rule), prediction-error records, and an
A-WORLD-01-style 30-minute simulated scenario with object movement, missing
observations and contradictory sensors.
"""

from __future__ import annotations

import unittest

from novi.brain.belief_revision import (
    DIRECT_OBSERVATION,
    MODEL_INFERENCE,
    MULTI_SENSOR_FUSION,
    PREDICTION,
    RELIABLE_MEMORY,
    USER_ASSERTION,
    BeliefClaim,
    BeliefRevisionPolicy,
    classify_evidence,
)
from novi.brain.prediction import PredictionErrorTracker
from novi.brain.world_model import OBSERVED, PREDICTED, STALE, VERIFIED, WorldModel


class FreshnessTests(unittest.TestCase):
    def test_freshness_policy_expires_stale_facts(self):
        world = WorldModel()
        world.add_entity("mug-1", "object", labels=["mug"])
        world.update_entity_state("mug-1", "location", "kitchen",
                                  epistemic_status=OBSERVED, confidence=0.9, source="camera", timestamp="t0")
        world.set_field_ttl("mug-1", "location", ttl_cycles=10, observed_cycle=0)

        self.assertEqual(world.freshness_of("mug-1", "location", cycle=5), "fresh")
        self.assertEqual(world.freshness_of("mug-1", "location", cycle=11), "stale")

        expired = world.expire_stale(cycle=15)
        self.assertIn(("mug-1", "location"), expired)
        entity = world.get_entity("mug-1")
        assert entity is not None
        self.assertEqual(entity.lifecycle, STALE, "expired facts mark their entity STALE")

    def test_freshness_without_policy_is_unknown(self):
        world = WorldModel()
        world.add_entity("mug-1", "object", labels=["mug"])
        self.assertEqual(world.freshness_of("mug-1", "location", cycle=0), "unknown")

    def test_expire_is_idempotent(self):
        world = WorldModel()
        world.add_entity("mug-1", "object", labels=["mug"])
        world.update_entity_state("mug-1", "location", "kitchen",
                                  epistemic_status=OBSERVED, confidence=0.9, source="camera", timestamp="t0")
        world.set_field_ttl("mug-1", "location", ttl_cycles=5, observed_cycle=0)
        first = world.expire_stale(cycle=10)
        second = world.expire_stale(cycle=11)
        self.assertEqual(first, [("mug-1", "location")])
        self.assertEqual(second, [])


class BeliefRevisionTests(unittest.TestCase):
    def test_direct_observation_beats_model_inference_regardless_of_confidence(self):
        """Doc 03: a hallucinated model statement must never outrank direct
        contradictory sensor evidence — even at 0.95 vs 0.7 confidence."""
        policy = BeliefRevisionPolicy()
        old = BeliefClaim("living_room", DIRECT_OBSERVATION, 0.7, cycle=5, source="camera")
        new = BeliefClaim("bedroom", MODEL_INFERENCE, 0.95, cycle=6, source="llm")
        decision = policy.revise(new=new, old=old)
        self.assertFalse(decision.accepted, "model inference must lose to direct observation")
        self.assertEqual(decision.winner, "old")
        self.assertEqual(decision.basis, "tier")

    def test_user_assertion_beats_reliable_memory(self):
        policy = BeliefRevisionPolicy()
        old = BeliefClaim("desk", RELIABLE_MEMORY, 0.9, cycle=1, source="memory")
        new = BeliefClaim("kitchen", USER_ASSERTION, 0.8, cycle=2, source="user")
        decision = policy.revise(new=new, old=old)
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.basis, "tier")

    def test_same_tier_confidence_decides(self):
        policy = BeliefRevisionPolicy()
        old = BeliefClaim("a", MULTI_SENSOR_FUSION, 0.6, cycle=1)
        new = BeliefClaim("b", MULTI_SENSOR_FUSION, 0.9, cycle=1)
        self.assertTrue(policy.revise(new=new, old=old).accepted)
        new_low = BeliefClaim("c", MULTI_SENSOR_FUSION, 0.5, cycle=1)
        self.assertFalse(policy.revise(new=new_low, old=old).accepted)

    def test_same_tier_confidence_recency_decides(self):
        policy = BeliefRevisionPolicy()
        old = BeliefClaim("a", DIRECT_OBSERVATION, 0.8, cycle=10)
        newer = BeliefClaim("b", DIRECT_OBSERVATION, 0.8, cycle=12)
        self.assertTrue(policy.revise(new=newer, old=old).accepted)

    def test_perfect_tie_keeps_current_belief(self):
        policy = BeliefRevisionPolicy()
        old = BeliefClaim("a", DIRECT_OBSERVATION, 0.8, cycle=10)
        same = BeliefClaim("a", DIRECT_OBSERVATION, 0.8, cycle=10)
        decision = policy.revise(new=same, old=old)
        self.assertFalse(decision.accepted, "no churn on identical claims")
        self.assertEqual(decision.basis, "tie")

    def test_first_observation_accepted(self):
        policy = BeliefRevisionPolicy()
        decision = policy.revise(new=BeliefClaim("kitchen", DIRECT_OBSERVATION, 0.9), old=None)
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.basis, "first_observation")

    def test_classify_evidence_maps_transformations(self):
        self.assertEqual(classify_evidence(source="camera", transformation="direct"), DIRECT_OBSERVATION)
        self.assertEqual(classify_evidence(source="fusion", transformation="fusion"), MULTI_SENSOR_FUSION)
        self.assertEqual(classify_evidence(source="llm", transformation="inference"), MODEL_INFERENCE)
        self.assertEqual(classify_evidence(source="user", transformation="direct"), USER_ASSERTION)
        self.assertEqual(classify_evidence(source="predictor", transformation="prediction"), PREDICTION)

    def test_decisions_are_auditable(self):
        policy = BeliefRevisionPolicy()
        policy.revise(new=BeliefClaim("a", DIRECT_OBSERVATION, 0.9, cycle=1), old=None)
        policy.revise(new=BeliefClaim("b", MODEL_INFERENCE, 0.95, cycle=2),
                      old=BeliefClaim("a", DIRECT_OBSERVATION, 0.9, cycle=1))
        self.assertEqual(len(policy.decisions()), 2)
        for decision in policy.decisions():
            self.assertTrue(decision.explanation)
            self.assertIn("evidence_class", decision.new_claim.__dict__)


class PredictionErrorTests(unittest.TestCase):
    def test_error_records_accumulate_with_stats(self):
        tracker = PredictionErrorTracker(error_threshold=0.2)
        tracker.record(prediction_ref="p1", expected={"mug": "kitchen"}, actual={"mug": "living_room"},
                       cycle=5, magnitude=0.8, cause_hypothesis="moved")
        tracker.record(prediction_ref="p2", expected={"book": "desk"}, actual={"book": "desk"},
                       cycle=6, magnitude=0.0)
        self.assertEqual(tracker.count(), 2)
        self.assertAlmostEqual(tracker.mean_magnitude(), 0.4)
        self.assertEqual(tracker.high_error_count(), 1)
        record = tracker.errors()[0]
        self.assertTrue(record.should_update_model)
        self.assertTrue(record.warrants_perception)
        self.assertEqual(record.cause_hypothesis, "moved")

    def test_low_error_does_not_warrant_perception(self):
        tracker = PredictionErrorTracker(error_threshold=0.2)
        tracker.record(prediction_ref="p1", expected=1, actual=1, cycle=1, magnitude=0.1)
        self.assertFalse(tracker.errors()[0].warrants_perception)


class WorldStateScenarioTests(unittest.TestCase):
    """A-WORLD-01-style: 30-minute simulated scenario (1 cycle = 1 minute)."""

    def test_thirty_minute_scenario_maintains_grounding(self):
        world = WorldModel()
        policy = BeliefRevisionPolicy()
        world.add_entity("mug-1", "object", labels=["mug"])
        world.add_entity("book-1", "object", labels=["book"])

        current_mug: str | None = None
        # 1. Object movement with direct observations.
        world.update_entity_state("mug-1", "location", "kitchen",
                                  epistemic_status=OBSERVED, confidence=0.9, source="camera", timestamp="t00")
        world.set_field_ttl("mug-1", "location", ttl_cycles=10, observed_cycle=0)
        current_mug = "kitchen"

        # 2. Contradictory sensor event: mug now in living_room (it moved).
        world.update_entity_state("mug-1", "location", "living_room",
                                  epistemic_status=OBSERVED, confidence=0.9, source="camera", timestamp="t05")
        # Fresh observation renews the freshness anchor (caller's contract).
        world.set_field_ttl("mug-1", "location", ttl_cycles=10, observed_cycle=5)
        # Belief revision agrees: same tier, fresher wins.
        decision = policy.revise(
            new=BeliefClaim("living_room", DIRECT_OBSERVATION, 0.9, cycle=5),
            old=BeliefClaim("kitchen", DIRECT_OBSERVATION, 0.9, cycle=0),
        )
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.basis, "recency")
        current_mug = "living_room"

        # 3. Missing observations: no data for the book for 20 minutes.
        world.update_entity_state("book-1", "location", "desk",
                                  epistemic_status=OBSERVED, confidence=0.9, source="camera", timestamp="t00")
        world.set_field_ttl("book-1", "location", ttl_cycles=5, observed_cycle=0)

        # 4. A hallucinated model inference claims mug is in the bedroom at 0.95.
        world.update_entity_state("mug-1", "location", "bedroom",
                                  epistemic_status=PREDICTED, confidence=0.95, source="llm", timestamp="t20")
        # The world model itself refuses to let a hypothetical overwrite the real value.
        mug_entity = world.get_entity("mug-1")
        assert mug_entity is not None
        self.assertEqual(mug_entity.state_value("location"), "living_room")
        # And the revision policy rejects the inference on tier grounds.
        hallucination = policy.revise(
            new=BeliefClaim("bedroom", MODEL_INFERENCE, 0.95, cycle=20, source="llm"),
            old=BeliefClaim("living_room", DIRECT_OBSERVATION, 0.7, cycle=5, source="camera"),
        )
        self.assertFalse(hallucination.accepted)
        self.assertEqual(hallucination.basis, "tier")

        # 5. Time passes; the book's stale fact expires.
        expired = world.expire_stale(cycle=30)
        self.assertIn(("book-1", "location"), expired)
        book = world.get_entity("book-1")
        assert book is not None
        self.assertEqual(book.lifecycle, STALE)

        # 6. Provenance is preserved: the contradiction is recorded, not erased.
        self.assertTrue(world._contradictions, "contradictions must be preserved as history")

        # 7. No unverified inference is presented as verified.
        entity = world.get_entity("mug-1")
        assert entity is not None
        self.assertEqual(entity.state_status("location"), OBSERVED)
        self.assertNotEqual(entity.state_status("location"), VERIFIED, "unverified inference never becomes verified")
        self.assertEqual(entity.state_value("location"), current_mug)

        # 8. The mug's location was fresh mid-scenario; after 30 minutes of
        # silence both facts are correctly expired (the world went quiet).
        self.assertEqual(world.freshness_of("mug-1", "location", cycle=15), "fresh")
        resolved = world.resolve("mug")
        assert resolved is not None
        self.assertEqual(resolved.entity_id, "mug-1")
        self.assertEqual(world.freshness_of("mug-1", "location", cycle=30), "stale")
        self.assertEqual(resolved.lifecycle, STALE)


if __name__ == "__main__":
    unittest.main()
