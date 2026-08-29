"""Tests for active perception (06_AUTONOMY doc 04).

Covers: strict parsing of grounding-model output, query arbitration, bounded
active search with budget exhaustion, information-gain scoring, the escalation
ladder, and the A-PERCEPT-01 gate (no false positive after budget exhaustion).
"""

from __future__ import annotations

import unittest

from novi.brain.active_perception import (
    ActiveSearch,
    DetectionBox,
    InformationGainScorer,
    LocateResult,
    PerceptionBudget,
    PerceptionEscalator,
    PerceptionQuery,
    QueryArbitrator,
    StrictBoxParser,
)


class StrictParserTests(unittest.TestCase):
    def test_valid_box_parses(self):
        box, error = StrictBoxParser().parse(
            {"label": "mug", "confidence": 0.9, "box": [0.1, 0.2, 0.5, 0.6]},
            model_version="v1",
        )
        self.assertEqual(error, "")
        assert box is not None
        self.assertEqual(box.label, "mug")
        self.assertEqual(box.model_version, "v1")
        self.assertAlmostEqual(box.x1, 0.1)

    def test_malformed_outputs_are_rejected(self):
        parser = StrictBoxParser()
        cases = [
            ("not a dict", "malformed_output"),
            ({"label": "", "confidence": 0.9, "box": [0, 0, 1, 1]}, "malformed_output"),
            ({"label": "mug", "confidence": 1.5, "box": [0, 0, 1, 1]}, "malformed_output"),
            ({"label": "mug", "confidence": 0.9, "box": [0, 0, 1]}, "malformed_output"),
            ({"label": "mug", "confidence": 0.9, "box": ["a", 0, 1, 1]}, "malformed_output"),
            ({"label": "mug", "confidence": 0.9, "box": [0, 0, float("nan"), 1]}, "malformed_output"),
            ({"label": "mug", "confidence": 0.9, "box": [0, 0, 1, float("inf")]}, "malformed_output"),
        ]
        for raw, expected_error in cases:
            box, error = parser.parse(raw)
            self.assertIsNone(box)
            self.assertIn(expected_error, error or "")

    def test_out_of_range_and_inverted_boxes_rejected(self):
        parser = StrictBoxParser()
        self.assertIn("out_of_range", parser.parse({"label": "mug", "confidence": 0.9, "box": [0.1, 0.1, 1.5, 0.9]})[1])
        self.assertIn("inverted_box", parser.parse({"label": "mug", "confidence": 0.9, "box": [0.5, 0.2, 0.1, 0.6]})[1])
        self.assertIn("inverted_box", parser.parse({"label": "mug", "confidence": 0.9, "box": [0.1, 0.6, 0.5, 0.2]})[1])


class QueryArbitrationTests(unittest.TestCase):
    def test_expensive_grounding_only_when_it_can_change_a_decision(self):
        arbitrator = QueryArbitrator()
        self.assertFalse(arbitrator.should_query())
        self.assertTrue(arbitrator.should_query(user_asked_specific=True))
        self.assertTrue(arbitrator.should_query(ssdlite_ambiguous=True))
        self.assertTrue(arbitrator.should_query(identity_uncertain=True))
        self.assertTrue(arbitrator.should_query(prediction_error=True))
        self.assertTrue(arbitrator.should_query(plan_needs_fact=True))
        self.assertTrue(arbitrator.should_query(freshness_insufficient=True))


class InformationGainTests(unittest.TestCase):
    def test_score_is_improvement_over_cost(self):
        scorer = InformationGainScorer()
        high = scorer.score(decision_improvement=1.0, latency_s=1.0, energy=0.1, risk=0.1)
        low = scorer.score(decision_improvement=0.1, latency_s=10.0, energy=1.0, risk=1.0)
        self.assertGreater(high, low)


class FakeLocateBackend:
    """Scripted grounding backend: each call pops the next outcome."""

    def __init__(self, script: list[LocateResult]) -> None:
        self.script = list(script)
        self.calls = 0

    def locate(self, image, query, *, cycle=0) -> LocateResult:
        self.calls += 1
        if not self.script:
            return LocateResult(query.query_id, False, (), 0.1, "v1", not_found_reason="no_match")
        return self.script.pop(0)


class ActiveSearchTests(unittest.TestCase):
    def test_found_on_first_attempt(self):
        query = PerceptionQuery.for_goal("mug", goal_id="g1", confidence_threshold=0.5)
        box = DetectionBox("mug", 0.9, 0.1, 0.1, 0.5, 0.5, source="locate_anything")
        backend = FakeLocateBackend([LocateResult(query.query_id, True, (box,), 0.2, "v1")])
        outcome = ActiveSearch(backend).search(query, image="frame")
        self.assertTrue(outcome.found)
        self.assertEqual(outcome.reason, "found")
        assert outcome.best is not None
        self.assertEqual(outcome.best.label, "mug")

    def test_raw_model_output_passes_through_strict_parser(self):
        query = PerceptionQuery.for_goal("mug", goal_id="g1")
        raw = LocateResult(query.query_id, True, ({"label": "mug", "confidence": 0.85, "box": [0.1, 0.2, 0.4, 0.6]},), 0.3, "v2")
        backend = FakeLocateBackend([raw])
        outcome = ActiveSearch(backend).search(query, image="frame")
        self.assertTrue(outcome.found)
        assert outcome.best is not None
        self.assertEqual(outcome.best.model_version, "v2")

    def test_malformed_output_retries_then_finds(self):
        query = PerceptionQuery.for_goal("mug", goal_id="g1")
        malformed = LocateResult(query.query_id, False, ({"label": "mug", "confidence": 0.9, "box": [0.9, 0.1, 0.1, 0.6]},), 0.2, "v1")
        box = DetectionBox("mug", 0.8, 0.1, 0.1, 0.5, 0.5)
        backend = FakeLocateBackend([
            malformed,
            LocateResult(query.query_id, True, (box,), 0.2, "v1"),
        ])
        outcome = ActiveSearch(backend).search(query, image="frame")
        self.assertTrue(outcome.found)
        self.assertEqual(outcome.attempts, 2)

    def test_model_unavailable_retries_within_budget(self):
        query = PerceptionQuery.for_goal("mug", goal_id="g1")
        box = DetectionBox("mug", 0.8, 0.1, 0.1, 0.5, 0.5)
        backend = FakeLocateBackend([
            LocateResult(query.query_id, False, (), 5.0, "v1", failure_reason="model_unavailable"),
            LocateResult(query.query_id, True, (box,), 0.2, "v1"),
        ])
        outcome = ActiveSearch(backend).search(query, image="frame")
        self.assertTrue(outcome.found)
        self.assertEqual(outcome.attempts, 2)

    def test_budget_exhaustion_never_hallucinates_success(self):
        """Gate A-PERCEPT-01: after the budget is exhausted, the search reports
        not-found uncertainty — no false-positive claim."""
        query = PerceptionQuery.for_goal("mug", goal_id="g1", confidence_threshold=0.9)
        # Backend always returns nothing / malformed output.
        backend = FakeLocateBackend([
            LocateResult(query.query_id, False, (), 0.2, "v1", not_found_reason="no_match"),
            LocateResult(query.query_id, False, ({"label": "mug", "confidence": 0.99, "box": [0.8, 0.8, 0.2, 0.2]},), 0.2, "v1"),
            LocateResult(query.query_id, False, (), 0.2, "v1", not_found_reason="no_match"),
            LocateResult(query.query_id, False, (), 0.2, "v1", not_found_reason="no_match"),
        ])
        budget = PerceptionBudget(max_vlm_queries=3, max_camera_search_cycles=10, max_retries=1)
        outcome = ActiveSearch(backend, budget=budget).search(query, image="frame")
        self.assertFalse(outcome.found, "budget exhaustion must never produce a false positive")
        self.assertEqual(outcome.reason, "budget_exhausted")
        self.assertLess(outcome.uncertainty, 1.0, "uncertainty must be reported")
        self.assertGreaterEqual(backend.calls, 1)

    def test_low_confidence_match_keeps_searching(self):
        query = PerceptionQuery.for_goal("mug", goal_id="g1", confidence_threshold=0.9)
        weak = DetectionBox("mug", 0.6, 0.1, 0.1, 0.5, 0.5)
        strong = DetectionBox("mug", 0.95, 0.1, 0.1, 0.5, 0.5)
        backend = FakeLocateBackend([
            LocateResult(query.query_id, True, (weak,), 0.2, "v1"),
            LocateResult(query.query_id, True, (strong,), 0.2, "v1"),
        ])
        outcome = ActiveSearch(backend).search(query, image="frame")
        self.assertTrue(outcome.found)
        assert outcome.best is not None
        self.assertAlmostEqual(outcome.best.confidence, 0.95)


class EscalationTests(unittest.TestCase):
    def test_ladder_stops_when_satisfied(self):
        escalator = PerceptionEscalator(confidence_threshold=0.5)
        result = escalator.escalate(detector_confidence=0.8, tracked=False, vlm_confidence=None, budget_left=True)
        self.assertEqual(result.step, "ssdlite")
        self.assertTrue(result.satisfied)

    def test_ladder_descends_monotonically(self):
        escalator = PerceptionEscalator(confidence_threshold=0.5)
        r1 = escalator.escalate(detector_confidence=0.2, tracked=False, vlm_confidence=None, budget_left=True)
        self.assertEqual(r1.step, "viewpoint")
        r2 = escalator.escalate(detector_confidence=0.2, tracked=False, vlm_confidence=None, budget_left=False)
        self.assertEqual(r2.step, "human")
        self.assertFalse(r2.satisfied)

    def test_vlm_stage_used_when_detector_weak(self):
        escalator = PerceptionEscalator(confidence_threshold=0.5)
        result = escalator.escalate(detector_confidence=0.3, tracked=False, vlm_confidence=0.9, budget_left=True)
        self.assertEqual(result.step, "vlm")
        self.assertTrue(result.satisfied)


if __name__ == "__main__":
    unittest.main()
