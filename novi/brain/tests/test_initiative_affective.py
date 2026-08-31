"""Tests for the affective extension of novi/brain/initiative_scoring.py.

Plan 24 Phase 15: the initiative score gains relationship_fit (multiplicative)
and emotional_pressure (penalty). Examples: highly frustrated user + non-urgent
observation → suppress initiative; calm + engaged + important task → allowed;
safety event → overrides normal social suppression.
"""

from __future__ import annotations

import unittest

from novi.brain.initiative_scoring import InitiativeGate, InitiativeScorer


class InitiativeAffectiveTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scorer = InitiativeScorer()

    def test_emotional_pressure_suppresses_initiative(self) -> None:
        # plan §19: user highly frustrated + non-urgent observation → suppress
        low = self.scorer.score(
            relevance=0.6, confidence=0.7, social_opportunity=0.6,
            novelty=0.6, expected_value=0.5, urgency=0.2, emotional_pressure=0.8,
        )
        high = self.scorer.score(
            relevance=0.6, confidence=0.7, social_opportunity=0.6,
            novelty=0.6, expected_value=0.5, urgency=0.2, emotional_pressure=0.0,
        )
        self.assertLess(low.score, high.score)
        self.assertIn("emotional_pressure", low.penalties)

    def test_relationship_fit_raises_score(self) -> None:
        low = self.scorer.score(
            relevance=0.8, confidence=0.8, social_opportunity=0.8,
            novelty=0.8, expected_value=0.8, urgency=0.5, relationship_fit=0.3,
        )
        high = self.scorer.score(
            relevance=0.8, confidence=0.8, social_opportunity=0.8,
            novelty=0.8, expected_value=0.8, urgency=0.5, relationship_fit=0.9,
        )
        self.assertGreater(high.score, low.score)
        self.assertIn("relationship_fit", high.components)

    def test_calm_engaged_important_task_allows_initiative(self) -> None:
        # plan §19: user calm + engaged + important task completion → allowed
        result = self.scorer.score(
            relevance=0.9, confidence=0.9, social_opportunity=0.9,
            novelty=0.9, expected_value=0.9, urgency=0.8, relationship_fit=0.9,
            emotional_pressure=0.1,
        )
        self.assertGreaterEqual(result.score, 0.7)  # CONSIDER or INITIATE

    def test_frustrated_non_urgent_stays_silent(self) -> None:
        # plan §19: highly frustrated + non-urgent observation → suppress
        result = self.scorer.score(
            relevance=0.5, confidence=0.6, social_opportunity=0.5,
            novelty=0.5, expected_value=0.4, urgency=0.1, relationship_fit=0.5,
            emotional_pressure=0.9,
        )
        self.assertLess(result.score, 0.25)  # SILENCE

    def test_safety_overrides_social_suppression(self) -> None:
        # plan §19: possible safety event → safety policy overrides suppression
        gate = InitiativeGate()
        allowed, reason = gate.allow(
            person="Vano", cycle=0, user_speaking=True, safety=True
        )
        self.assertTrue(allowed)
        self.assertEqual(reason, "safety_override")


if __name__ == "__main__":
    unittest.main()
