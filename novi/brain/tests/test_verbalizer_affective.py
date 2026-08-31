"""Tests for the strategy-based extension of novi/brain/verbalizer.py.

Plan 24 Phase 18: the verbalizer receives a strategy rather than raw emotion.
Example: ACKNOWLEDGE + SOLVE, tone calm, length short, certainty moderate →
"Yeah, I see the problem. Let's fix the actual part that's failing."
"""

from __future__ import annotations

import unittest

from novi.brain.verbalizer import Verbalizer


class VerbalizerAffectiveTest(unittest.TestCase):
    def setUp(self) -> None:
        self.verbalizer = Verbalizer()

    def test_acknowledge_strategy_prepends_natural_ack(self) -> None:
        # plan §22: ACKNOWLEDGE + SOLVE → "Yeah, I see the problem. Let's fix..."
        response = self.verbalizer.verbalize(
            "Let's fix the actual part that's failing.",
            strategy=["ACKNOWLEDGE", "SOLVE"],
            tone="calm",
            verbosity="short",
            certainty="moderate",
        )
        self.assertIn("yeah", response.text.lower())
        self.assertIn("fix", response.text.lower())
        self.assertIn("ACKNOWLEDGE", response.controls)

    def test_apologize_strategy_uses_mature_apology(self) -> None:
        response = self.verbalizer.verbalize(
            "I'll focus on the actual issue.",
            strategy=["APOLOGIZE"],
            tone="calm",
            verbosity="short",
            certainty="moderate",
        )
        self.assertIn("you're right", response.text.lower())
        self.assertNotIn("I'm very sorry", response.text.lower())

    def test_give_space_strategy_keeps_minimal(self) -> None:
        response = self.verbalizer.verbalize(
            "I'll give you some space.",
            strategy=["GIVE_SPACE"],
            tone="calm",
            verbosity="short",
            certainty="moderate",
        )
        self.assertLessEqual(len(response.text.split()), 12)

    def test_certainty_low_hedges(self) -> None:
        response = self.verbalizer.verbalize(
            "the sensor reading is ambiguous",
            strategy=["CLARIFY"],
            certainty="low",
        )
        self.assertIn("i think", response.text.lower())

    def test_no_strategy_behaves_as_before(self) -> None:
        response = self.verbalizer.verbalize("hello there", verbosity="short")
        self.assertEqual(response.text, "hello there")
        self.assertNotIn("ACKNOWLEDGE", response.controls)


if __name__ == "__main__":
    unittest.main()
