"""Tests for continual learning gates (06_AUTONOMY doc 11 Phase 11 / doc 07).

The full learning pipeline: verified experience → candidate lesson → evidence
aggregation → validation → promotion (with regression scenario) → rollback.
A change cannot merge if it causes unverified promotions or knowledge that
regresses (doc 09 Step 9).
"""

from __future__ import annotations

import unittest

from novi.brain.recovery import CounterfactualRecorder, RegressionMemory


class ContinualLearningGateTests(unittest.TestCase):
    def test_full_pipeline_promotes_only_verified_lessons(self):
        """experience -> candidate -> validation -> promotion -> regression."""
        memory = RegressionMemory()
        recorder = CounterfactualRecorder()

        # 1. Verified experience: the failure record is confirmed.
        record = recorder.record(
            failure_ref="act-7", believed={"mug": "kitchen"}, expected={"mug": "kitchen"},
            happened={"mug": "living_room"}, discrepancy_reason="object moved",
            information_that_would_prevent="re-check before pickup",
            policy_should_change=True, cycle=9,
        )

        # 2. Candidate lesson backed by the verified counterfactual.
        lesson = memory.propose(title="re-check location before pickup",
                                evidence_refs=(record.record_id,))
        # 3. Unverified candidates never promote.
        self.assertFalse(memory.promote(lesson, regression_scenario="object_moved_scenario"))

        # 4. Validation passes: the lesson is now backed by aggregated evidence.
        lesson.verified = True
        self.assertTrue(memory.promote(lesson, regression_scenario="object_moved_scenario"))
        self.assertEqual(memory.scenarios_for(lesson.lesson_id), ("object_moved_scenario",))

        # 5. Regression scenario fails -> rollback (doc 11 Phase 11 item 7).
        self.assertTrue(memory.rollback(lesson.lesson_id))
        self.assertFalse(lesson.verified)
        self.assertEqual(lesson.regression_scenarios, [])
        self.assertIn(lesson.lesson_id, memory.rollbacks())

        # 6. The rolled-back lesson cannot be re-promoted without fresh evidence.
        self.assertFalse(memory.promote(lesson, regression_scenario="object_moved_scenario"))
        self.assertEqual(memory.scenarios_for(lesson.lesson_id), ())

    def test_rollback_is_idempotent(self):
        memory = RegressionMemory()
        lesson = memory.propose(title="lesson")
        lesson.verified = True
        memory.promote(lesson, regression_scenario="s1")
        self.assertTrue(memory.rollback(lesson.lesson_id))
        self.assertFalse(memory.rollback(lesson.lesson_id))
        self.assertEqual(len(memory.rollbacks()), 1)

    def test_learning_never_increases_false_knowledge(self):
        """Across many lessons, promoted knowledge is always regression-scenario
        backed; every failed regression rolls the lesson back."""
        memory = RegressionMemory()
        for i in range(50):
            lesson = memory.propose(title=f"lesson-{i}")
            lesson.verified = True
            memory.promote(lesson, regression_scenario=f"scenario-{i}")
            if i % 3 == 0:  # one third regress in the next version
                memory.rollback(lesson.lesson_id)
        promoted = [lesson for lesson in memory.lessons() if lesson.verified]
        rolled_back = memory.rollbacks()
        self.assertEqual(len(promoted), 50 - len(rolled_back))
        for lesson in promoted:
            self.assertTrue(lesson.regression_scenarios,
                            "promoted knowledge always carries a regression scenario")


if __name__ == "__main__":
    unittest.main()
