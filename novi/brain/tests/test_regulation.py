"""Tests for novi/brain/regulation.py — emotional regulation engine.

Plan 24 Phase 9: RegulationDecision maps affective state + social context +
relationship + conversation goal + user availability + recent Novi behavior
into behavior adjustments. Gate E3: emotional signals change behavior
appropriately without causing overreaction.
"""

from __future__ import annotations

import unittest

from novi.brain.regulation import RegulationDecision, RegulationEngine, RegulationInput


class RegulationEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = RegulationEngine()

    def test_high_frustration_reduces_verbosity(self) -> None:
        # plan §13 example: frustration .74, solve technical problem, high availability
        decision = self.engine.decide(
            RegulationInput(
                affective_state={"frustration_likelihood": 0.74},
                social_context={},
                relationship={"preferred_verbosity": "measured"},
                conversation_goal="solve_technical_problem",
                user_availability="high",
                recent_novi_behavior=["repeated_explanation"],
            )
        )
        self.assertEqual(decision.verbosity, "low")
        self.assertEqual(decision.directness, "high")
        self.assertEqual(decision.empathy, "moderate")
        self.assertEqual(decision.humor, "low")
        self.assertEqual(decision.repetition_suppression, "strong")

    def test_calm_state_keeps_measured_behavior(self) -> None:
        decision = self.engine.decide(
            RegulationInput(
                affective_state={"frustration_likelihood": 0.1},
                social_context={"conversation_temperature": "calm"},
                relationship={},
                conversation_goal="chat",
                user_availability="high",
                recent_novi_behavior=[],
            )
        )
        self.assertEqual(decision.verbosity, "measured")
        self.assertEqual(decision.humor, "moderate")
        self.assertEqual(decision.repetition_suppression, "none")

    def test_recent_repetition_suppresses_repetition(self) -> None:
        decision = self.engine.decide(
            RegulationInput(
                affective_state={"frustration_likelihood": 0.3},
                social_context={},
                relationship={},
                conversation_goal="solve_technical_problem",
                user_availability="high",
                recent_novi_behavior=["repeated_explanation", "repeated_explanation"],
            )
        )
        self.assertEqual(decision.repetition_suppression, "strong")

    def test_low_availability_suppresses_initiative(self) -> None:
        decision = self.engine.decide(
            RegulationInput(
                affective_state={"frustration_likelihood": 0.5},
                social_context={},
                relationship={},
                conversation_goal="chat",
                user_availability="low",
                recent_novi_behavior=[],
            )
        )
        self.assertGreater(decision.initiative_suppression, 0.5)
        self.assertGreater(decision.interruption_threshold, 0.5)

    def test_relationship_preference_flows_into_verbosity(self) -> None:
        decision = self.engine.decide(
            RegulationInput(
                affective_state={},
                social_context={},
                relationship={"preferred_verbosity": "concise"},
                conversation_goal="chat",
                user_availability="high",
                recent_novi_behavior=[],
            )
        )
        self.assertEqual(decision.verbosity, "concise")

    def test_repair_strategy_selected_on_tension(self) -> None:
        decision = self.engine.decide(
            RegulationInput(
                affective_state={"frustration_likelihood": 0.8},
                social_context={"conversation_temperature": "tense"},
                relationship={},
                conversation_goal="solve_technical_problem",
                user_availability="high",
                recent_novi_behavior=["repeated_explanation"],
            )
        )
        self.assertIn(decision.repair_strategy, ("apologize", "clarify", "rephrase", "give_space"))

    def test_snapshot_roundtrip(self) -> None:
        decision = self.engine.decide(
            RegulationInput(
                affective_state={"frustration_likelihood": 0.74},
                social_context={},
                relationship={},
                conversation_goal="solve_technical_problem",
                user_availability="high",
                recent_novi_behavior=["repeated_explanation"],
            )
        )
        restored = RegulationDecision.from_snapshot(decision.snapshot())
        self.assertEqual(restored.verbosity, decision.verbosity)
        self.assertEqual(restored.directness, decision.directness)
        self.assertEqual(restored.repair_strategy, decision.repair_strategy)


if __name__ == "__main__":
    unittest.main()
