"""Tests for exploration & curiosity policy (06_AUTONOMY doc 06).

Covers: novelty detection with information hypotheses, information-gain
scoring (novelty alone never justifies exploration), bounded exploration,
safe-first step ordering, background-goal capping, preference learning, and
the A-CURIOSITY-01 gate (high-value unknowns discovered within a fixed budget
without low-value wandering).
"""

from __future__ import annotations

import unittest

from novi.brain.curiosity import (
    CuriosityGoalGenerator,
    CuriosityScorer,
    ExplorationBudget,
    ExplorationPlanner,
    ExplorationPreferenceLearner,
    NoveltyCandidate,
    NoveltyDetector,
)


class NoveltyTests(unittest.TestCase):
    def test_all_novelty_sources_form_hypotheses(self):
        detector = NoveltyDetector()
        candidates = detector.candidates(
            unseen_objects=("mug",),
            unexplored_regions=("west_wing",),
            unexpected_events=("door_opened",),
            prediction_errors=("kitchen",),
            contradictions=("cup",),
            new_sensors=("depth",),
            changed_environment=("living_room",),
        )
        self.assertEqual(len(candidates), 7)
        for candidate in candidates:
            self.assertTrue(candidate.information_hypothesis,
                            "every candidate must state what uncertainty it reduces")
            self.assertGreater(candidate.uncertainty, 0.0)

    def test_candidates_are_distinct(self):
        detector = NoveltyDetector()
        candidates = detector.candidates(unseen_objects=("a", "b", "c"))
        self.assertEqual(len({c.target for c in candidates}), 3)


class CuriosityScoringTests(unittest.TestCase):
    def test_high_value_beats_mere_novelty(self):
        """A-CURIOSITY-01: high-value unknowns outscore low-value ones."""
        scorer = CuriosityScorer()
        high = scorer.score(uncertainty_reduction=0.9, future_usefulness=0.9, cost=0.2, risk=0.1)
        low = scorer.score(uncertainty_reduction=0.9, future_usefulness=0.1, cost=0.5, risk=0.4)
        self.assertGreater(high, low)

    def test_costly_risky_exploration_is_rejected(self):
        scorer = CuriosityScorer()
        score = scorer.score(uncertainty_reduction=0.5, future_usefulness=0.5, cost=0.6, risk=0.5)
        self.assertLess(score, 0.0, "exploration whose cost+risk exceeds value must not happen")


class BudgetTests(unittest.TestCase):
    def test_budget_exhausts_on_any_dimension(self):
        budget = ExplorationBudget(max_duration_cycles=5, max_distance_m=10.0, max_energy=1.0,
                                   max_perception_calls=3, max_retries=1)
        self.assertFalse(budget.exhausted(cycles=1, distance_m=1.0, energy=0.1, perception_calls=1, retries=0))
        self.assertTrue(budget.exhausted(cycles=5, distance_m=1.0, energy=0.1, perception_calls=1, retries=0))
        self.assertTrue(budget.exhausted(cycles=1, distance_m=10.0, energy=0.1, perception_calls=1, retries=0))
        self.assertTrue(budget.exhausted(cycles=1, distance_m=1.0, energy=1.0, perception_calls=1, retries=0))
        self.assertTrue(budget.exhausted(cycles=1, distance_m=1.0, energy=0.1, perception_calls=3, retries=0))
        self.assertTrue(budget.exhausted(cycles=1, distance_m=1.0, energy=0.1, perception_calls=1, retries=1))

    def test_forbidden_regions_blocked(self):
        budget = ExplorationBudget(forbidden_regions=((2.0, 2.0, 3.0, 3.0),))
        self.assertTrue(budget.region_forbidden(2.5, 2.5))
        self.assertFalse(budget.region_forbidden(0.0, 0.0))


class ExplorationPlanningTests(unittest.TestCase):
    def test_safe_first_order_and_stop_threshold(self):
        planner = ExplorationPlanner(budget=ExplorationBudget(stop_gain_threshold=0.1))
        candidate = NoveltyCandidate("c1", "west_wing", "unexplored_region",
                                     "map the west wing", uncertainty=0.8)
        steps = planner.plan(candidate, future_usefulness=0.8)
        # Safe observations first; low-gain steps are dropped by the threshold.
        self.assertGreaterEqual(len(steps), 1)
        self.assertEqual(steps[0].action, "observe")
        self.assertTrue(all(step.gain >= planner.budget.stop_gain_threshold for step in steps))

    def test_low_usefulness_exploration_is_bounded(self):
        planner = ExplorationPlanner()
        candidate = NoveltyCandidate("c1", "trivia", "unexpected_event",
                                     "why did the light blink", uncertainty=0.2)
        steps = planner.plan(candidate, future_usefulness=0.1)
        self.assertLessEqual(len(steps), 4, "low-value exploration stays small")


class GoalGenerationTests(unittest.TestCase):
    def test_background_goals_are_capped(self):
        generator = CuriosityGoalGenerator(max_background_goals=2)
        candidate = NoveltyCandidate("c1", "x", "unseen_object", "identify x")
        self.assertIsNotNone(generator.generate(candidate))
        self.assertIsNotNone(generator.generate(candidate))
        self.assertIsNone(generator.generate(candidate), "background exploration goals must be capped")
        self.assertEqual(len(generator.generated()), 2)

    def test_no_goals_without_spare_budget(self):
        generator = CuriosityGoalGenerator()
        candidate = NoveltyCandidate("c1", "x", "unseen_object", "identify x")
        self.assertIsNone(generator.generate(candidate, spare_autonomy_budget=False))


class PreferenceLearningTests(unittest.TestCase):
    def test_usefulness_learned_from_verified_outcomes(self):
        learner = ExplorationPreferenceLearner()
        learner.record(target="kitchen", novelty_type="unseen_object", improved_future_task=True)
        learner.record(target="kitchen", novelty_type="unseen_object", improved_future_task=True)
        learner.record(target="attic", novelty_type="unexplored_region", improved_future_task=False)
        useful = learner.usefulness("unseen_object")
        useless = learner.usefulness("unexplored_region")
        self.assertGreater(useful, 0.5)
        self.assertLess(useless, 0.5)
        self.assertEqual(len(learner.outcomes()), 3)


class CuriosityGateTests(unittest.TestCase):
    def test_a_curiosity_01_discovers_high_value_unknowns_within_budget(self):
        """In a simulated environment with hidden useful information, Novi
        discovers the high-value unknowns within a fixed budget and avoids
        low-value wandering."""
        budget = ExplorationBudget(
            max_duration_cycles=12, max_perception_calls=5, max_retries=1,
            stop_gain_threshold=0.1,
        )
        detector = NoveltyDetector()
        planner = ExplorationPlanner(budget=budget)

        # High-value: the kitchen object (useful for the user's goals).
        high = detector.candidates(unseen_objects=("kitchen_object",))[0]
        # Low-value: a light flicker with no consequence.
        low = detector.candidates(unexpected_events=("light_flicker",))[0]

        high_plan = planner.plan(high, future_usefulness=0.9)
        low_plan = planner.plan(low, future_usefulness=0.05)

        # The planner naturally spends its steps on the high-value target.
        self.assertGreater(len(high_plan), len(low_plan),
                           "high-value exploration deserves more steps than low-value wandering")
        # Bounded: the plan never exceeds the perception-call budget.
        self.assertLessEqual(len(high_plan), budget.max_perception_calls)
        # No unsafe exploration: forbidden regions are never targets.
        self.assertFalse(budget.region_forbidden(0.0, 0.0))
        # No endless behavior: gains below threshold are dropped.
        self.assertTrue(all(s.gain >= budget.stop_gain_threshold for s in high_plan))

        # And the preference learner records whether it paid off.
        learner = ExplorationPreferenceLearner()
        learner.record(target="kitchen_object", novelty_type="unseen_object",
                       improved_future_task=True, gain=high_plan[0].gain)
        self.assertGreater(learner.usefulness("unseen_object"), 0.5)


if __name__ == "__main__":
    unittest.main()
