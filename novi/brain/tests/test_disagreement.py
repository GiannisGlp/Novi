"""Tests for novi/brain/disagreement.py — disagreement maturity.

Plan 24 Phase 13: Novi disagrees without "You're wrong." When uncertain it
says "I might be missing something, but..."; when evidence is strong it says
"I don't think that's correct based on what I can see." Then it provides
evidence rather than escalating.
"""

from __future__ import annotations

import unittest

from novi.brain.disagreement import DisagreementBuilder


class DisagreementTest(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = DisagreementBuilder()

    def test_strong_evidence_disagreement(self) -> None:
        text = self.builder.build(
            claim="the camera is broken",
            evidence_strength=0.9,
            uncertainty=0.1,
            evidence="the sensor reports a normal reading",
        )
        self.assertIn("I don't think that's correct", text)
        self.assertIn("the sensor reports a normal reading", text)
        self.assertNotIn("You're wrong", text)

    def test_uncertain_disagreement(self) -> None:
        text = self.builder.build(
            claim="the camera is broken",
            evidence_strength=0.4,
            uncertainty=0.7,
            evidence="the sensor reading is ambiguous",
        )
        self.assertIn("I might be missing something", text)
        self.assertNotIn("You're wrong", text)

    def test_mild_disagreement(self) -> None:
        text = self.builder.build(
            claim="the camera is broken",
            evidence_strength=0.6,
            uncertainty=0.3,
            evidence="the data shows a different pattern",
        )
        self.assertIn("slightly different", text)
        self.assertNotIn("You're wrong", text)

    def test_never_escalates(self) -> None:
        # plan §13: provide evidence rather than escalating
        text = self.builder.build(
            claim="x", evidence_strength=0.95, uncertainty=0.05, evidence="data"
        )
        self.assertNotIn("You're wrong", text)
        self.assertNotIn("You don't understand", text)
        self.assertNotIn("That's stupid", text)

    def test_evidence_always_included(self) -> None:
        text = self.builder.build(
            claim="x", evidence_strength=0.8, uncertainty=0.2, evidence="the log shows a timeout"
        )
        self.assertIn("the log shows a timeout", text)


if __name__ == "__main__":
    unittest.main()
