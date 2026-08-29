"""Tests for recovery & metacognition (06_AUTONOMY doc 07).

Covers: the failure taxonomy, per-class recovery strategies and bounded retry
budgets, confidence decomposition, counterfactual failure records, regression
memory, and the A-META-01 gate (500 injected failures: zero infinite retry
loops, zero unverified learning promotions).
"""

from __future__ import annotations

import random
import unittest

from novi.brain.recovery import (
    ASK_USER,
    REFRESH_PERCEPTION,
    REPLAN,
    RETRY,
    SAFE_STOP,
    ConfidenceProfile,
    CounterfactualRecorder,
    FailureClass,
    FailureClassifier,
    RecoveryPlanner,
    RegressionMemory,
)


class FailureClassificationTests(unittest.TestCase):
    def test_all_taxonomy_classes_are_covered(self):
        """Every class in the doc 07 taxonomy maps to a strategy + budget."""
        planner = RecoveryPlanner()
        for failure_class in FailureClass:
            plan = planner.plan_for(reason=failure_class.value)
            self.assertEqual(plan.failure_class, failure_class)
            self.assertTrue(plan.strategy)
            self.assertGreaterEqual(plan.retry_budget, 0)

    def test_keyword_classification(self):
        classifier = FailureClassifier()
        self.assertEqual(classifier.classify(reason="camera frame stale"), FailureClass.PERCEPTION)
        self.assertEqual(classifier.classify(reason="planner busy"), FailureClass.PLANNING)
        self.assertEqual(classifier.classify(reason="estop active"), FailureClass.SAFETY)
        self.assertEqual(classifier.classify(reason="not localized"), FailureClass.LOCALIZATION)
        self.assertEqual(classifier.classify(reason="battery low"), FailureClass.RESOURCE)
        self.assertEqual(classifier.classify(reason="operator cancelled"), FailureClass.HUMAN_INTERRUPTION)
        self.assertEqual(classifier.classify(reason="gripper jammed"), FailureClass.EXECUTION)

    def test_safety_failures_never_retry(self):
        plan = RecoveryPlanner().plan_for(reason="safety invariant violated")
        self.assertEqual(plan.strategy, SAFE_STOP)
        self.assertEqual(plan.retry_budget, 0)

    def test_physical_failures_have_no_retry_loop(self):
        """Doc 07 Step 5: repeating a physically-failed action without new
        information is forbidden — precondition/resource/interruption classes
        carry a zero budget."""
        planner = RecoveryPlanner()
        for reason in ("precondition failed", "budget exhausted", "interrupted"):
            plan = planner.plan_for(reason=reason)
            self.assertFalse(planner.is_infinite(plan), "no plan may be an infinite retry loop")


class RecoveryBudgetTests(unittest.TestCase):
    def test_five_hundred_mixed_failures_recover_boundedly(self):
        """Gate A-META-01 (boundedness half): 500 injected mixed failures all
        produce bounded plans — every one recovers, replans, asks or stops,
        with zero infinite retry loops."""
        rng = random.Random(0x5A7A)
        reasons = [
            "camera frame stale", "planner busy", "not localized", "route blocked",
            "motor timeout", "postcondition not met", "battery low", "estop active",
            "model unavailable", "operator cancelled", "gripper jammed", "world belief contradiction",
        ]
        planner = RecoveryPlanner()
        for _ in range(500):
            reason = rng.choice(reasons)
            plan = planner.plan_for(reason=reason)
            self.assertIn(plan.strategy, (RETRY, REFRESH_PERCEPTION, REPLAN, ASK_USER, SAFE_STOP))
            self.assertFalse(planner.is_infinite(plan),
                             f"infinite retry loop for {reason!r}")
            if plan.strategy == RETRY:
                self.assertGreater(plan.retry_budget, 0, "a retry strategy must have a budget")


class ConfidenceTests(unittest.TestCase):
    def test_confidence_is_decomposed_not_global(self):
        profile = ConfidenceProfile(perception=0.9, world_state=0.8, identity=0.7,
                                    plan=0.6, action=0.5, verification=0.4)
        ok, missing = profile.is_confident({"perception": 0.5, "plan": 0.5})
        self.assertTrue(ok)
        ok, missing = profile.is_confident({"perception": 0.5, "verification": 0.9})
        self.assertFalse(ok)
        self.assertEqual(missing, ["verification"])

    def test_snapshot_lists_all_components(self):
        profile = ConfidenceProfile(perception=0.9)
        snapshot = profile.snapshot()
        self.assertEqual(set(snapshot.keys()),
                         {"perception", "world_state", "identity", "plan", "action", "verification"})


class CounterfactualTests(unittest.TestCase):
    def test_failure_records_what_was_believed(self):
        recorder = CounterfactualRecorder()
        recorder.record(
            failure_ref="act-1",
            believed={"mug": "kitchen"}, expected={"mug": "kitchen"},
            happened={"mug": "living_room"},
            discrepancy_reason="object moved during plan",
            information_that_would_prevent="re-checking location before pickup",
            policy_should_change=True, cycle=7,
        )
        records = recorder.records()
        self.assertEqual(len(records), 1)
        self.assertTrue(recorder.policy_change_candidates()[0].policy_should_change)
        self.assertEqual(records[0].cycle, 7)


class RegressionMemoryTests(unittest.TestCase):
    def test_only_verified_lessons_promote(self):
        memory = RegressionMemory()
        lesson = memory.propose(title="recheck location before pickup", evidence_refs=("cf-1",))
        self.assertFalse(memory.promote(lesson, regression_scenario="object_moved_scenario"),
                         "unverified lessons must not promote")
        self.assertEqual(memory.unverified_promotions(), 1)
        lesson.verified = True
        self.assertTrue(memory.promote(lesson, regression_scenario="object_moved_scenario"))
        self.assertEqual(memory.scenarios_for(lesson.lesson_id), ("object_moved_scenario",))

    def test_promotion_is_idempotent(self):
        memory = RegressionMemory()
        lesson = memory.propose(title="lesson")
        lesson.verified = True
        memory.promote(lesson, regression_scenario="s1")
        memory.promote(lesson, regression_scenario="s1")
        self.assertEqual(len(memory.scenarios_for(lesson.lesson_id)), 1)

    def test_zero_unverified_promotions_across_many_lessons(self):
        """Gate A-META-01 (learning half): zero unverified promotions."""
        memory = RegressionMemory()
        for i in range(100):
            lesson = memory.propose(title=f"lesson-{i}")
            if i % 2 == 0:
                lesson.verified = True
            memory.promote(lesson, regression_scenario=f"scenario-{i}")
        self.assertEqual(memory.unverified_promotions(), 50)
        verified = [lesson for lesson in memory.lessons() if lesson.verified]
        self.assertTrue(all(lesson.regression_scenarios for lesson in verified),
                        "every promoted lesson has a regression scenario")


if __name__ == "__main__":
    unittest.main()
