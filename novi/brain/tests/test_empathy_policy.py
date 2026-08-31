"""Tests for novi/brain/empathy_policy.py — empathy as behavioral strategy.

Plan 24 Phase 10: the policy selects one or more behavioral strategies based
on evidence. Empathy is never a claim about private feelings — it is a
behavioral response to observable signals.
"""

from __future__ import annotations

import unittest

from novi.brain.empathy_policy import EmpathyPolicy, EmpathyEvidence


class EmpathyPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = EmpathyPolicy()

    def test_frustration_novi_caused_problem(self) -> None:
        # plan §14: frustration + Novi caused problem → ACKNOWLEDGE + APOLOGIZE + SOLVE
        strategies = self.policy.select(
            EmpathyEvidence(frustration=0.8, novi_caused_problem=True)
        )
        self.assertIn("ACKNOWLEDGE", strategies)
        self.assertIn("APOLOGIZE", strategies)
        self.assertIn("SOLVE", strategies)

    def test_frustration_novi_not_cause(self) -> None:
        # plan §14: frustration + Novi did not cause → ACKNOWLEDGE + SOLVE
        strategies = self.policy.select(
            EmpathyEvidence(frustration=0.8, novi_caused_problem=False)
        )
        self.assertIn("ACKNOWLEDGE", strategies)
        self.assertIn("SOLVE", strategies)
        self.assertNotIn("APOLOGIZE", strategies)

    def test_disengagement_gives_space(self) -> None:
        # plan §14: disengagement → GIVE_SPACE
        strategies = self.policy.select(EmpathyEvidence(disengagement=0.7))
        self.assertIn("GIVE_SPACE", strategies)

    def test_success_celebrates_proportionally(self) -> None:
        # plan §14: success → CELEBRATE, proportionally
        strategies = self.policy.select(EmpathyEvidence(success=0.9))
        self.assertIn("CELEBRATE", strategies)

    def test_high_success_does_not_overcelebrate(self) -> None:
        # Gate E6: no overreaction — celebration is proportional, not gushing
        strategies = self.policy.select(EmpathyEvidence(success=0.9))
        self.assertNotIn("GIVE_SPACE", strategies)
        self.assertNotIn("APOLOGIZE", strategies)

    def test_no_evidence_selects_listen(self) -> None:
        strategies = self.policy.select(EmpathyEvidence())
        self.assertIn("LISTEN", strategies)

    def test_priority_order(self) -> None:
        # when multiple apply, the most relevant strategies come first
        strategies = self.policy.select(
            EmpathyEvidence(frustration=0.8, novi_caused_problem=True, disengagement=0.6)
        )
        self.assertEqual(strategies[0], "ACKNOWLEDGE")
        self.assertIn("APOLOGIZE", strategies)


if __name__ == "__main__":
    unittest.main()
