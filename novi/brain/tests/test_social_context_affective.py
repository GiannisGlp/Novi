"""Tests for the affective extension of novi/brain/social_context.py.

Plan 24 Phase 6: SocialContext gains emotional_signal, confidence,
recent_social_events, current_topic, user_goal and boundary_state. The
context stays short-lived and continuously recomputed from observable
evidence.
"""

from __future__ import annotations

import unittest

from novi.brain.social_context import SocialContextBuilder, SocialEvidence


class SocialContextAffectiveTest(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = SocialContextBuilder()

    def test_affective_state_flows_into_context(self) -> None:
        evidence = SocialEvidence(
            person_present=True,
            affective_state={"frustration_likelihood": {"value": 0.72, "confidence": 0.78}},
        )
        ctx = self.builder.build(evidence)
        self.assertIn("frustration_likelihood", ctx.emotional_signal)
        self.assertEqual(ctx.emotional_signal["frustration_likelihood"]["value"], 0.72)

    def test_boundary_state_flows_into_context(self) -> None:
        evidence = SocialEvidence(person_present=True, boundary_state="DO_NOT_PROBE")
        ctx = self.builder.build(evidence)
        self.assertEqual(ctx.boundary_state, "DO_NOT_PROBE")

    def test_topic_and_goal_flow_into_context(self) -> None:
        evidence = SocialEvidence(person_present=True, current_topic="camera", user_goal="solve_problem")
        ctx = self.builder.build(evidence)
        self.assertEqual(ctx.current_topic, "camera")
        self.assertEqual(ctx.user_goal, "solve_problem")

    def test_recent_social_events_flow_into_context(self) -> None:
        evidence = SocialEvidence(person_present=True, recent_social_events=["user_correction", "user_thanks"])
        ctx = self.builder.build(evidence)
        self.assertIn("user_correction", ctx.recent_social_events)

    def test_confidence_rises_with_evidence(self) -> None:
        ctx1 = self.builder.build(SocialEvidence(person_present=True))
        ctx2 = self.builder.build(
            SocialEvidence(person_present=True, speech_tempo_ratio=1.6, speech_volume_ratio=1.4)
        )
        self.assertGreater(ctx2.confidence, ctx1.confidence)
        self.assertLessEqual(ctx2.confidence, 1.0)

    def test_absent_person_has_low_confidence(self) -> None:
        ctx = self.builder.build(SocialEvidence(person_present=False))
        self.assertEqual(ctx.confidence, 0.0)

    def test_snapshot_includes_new_fields(self) -> None:
        evidence = SocialEvidence(
            person_present=True,
            boundary_state="NORMAL",
            current_topic="camera",
            user_goal="solve_problem",
            recent_social_events=["user_correction"],
        )
        snap = self.builder.build(evidence).snapshot()
        self.assertIn("emotional_signal", snap)
        self.assertIn("boundary_state", snap)
        self.assertIn("current_topic", snap)
        self.assertIn("user_goal", snap)
        self.assertIn("recent_social_events", snap)
        self.assertIn("confidence", snap)
        self.assertEqual(snap["boundary_state"], "NORMAL")
        self.assertEqual(snap["current_topic"], "camera")


if __name__ == "__main__":
    unittest.main()
