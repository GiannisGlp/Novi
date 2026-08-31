"""Tests for novi/brain/conflict.py — conflict handling state machine.

Plan 24 Phase 12: NORMAL → CORRECTION → DISAGREEMENT → TENSION → REPAIR →
RESOLUTION. Rules: never become defensive, never blame the user, distinguish
disagreement from hostility, stop arguing when evidence does not justify it,
preserve factual honesty.
"""

from __future__ import annotations

import unittest

from novi.brain.conflict import ConflictState, ConflictStateMachine


class ConflictStateMachineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.machine = ConflictStateMachine()

    def test_starts_normal(self) -> None:
        self.assertEqual(self.machine.state, ConflictState.NORMAL)

    def test_user_correction_moves_to_correction(self) -> None:
        self.machine.transition("user_correction")
        self.assertEqual(self.machine.state, ConflictState.CORRECTION)

    def test_repeated_misunderstanding_escalates_to_tension(self) -> None:
        self.machine.transition("user_correction")
        self.machine.transition("repeated_misunderstanding")
        self.assertEqual(self.machine.state, ConflictState.TENSION)

    def test_successful_clarification_resolves(self) -> None:
        self.machine.transition("user_correction")
        self.machine.transition("successful_clarification")
        self.assertEqual(self.machine.state, ConflictState.RESOLUTION)

    def test_repair_after_tension(self) -> None:
        self.machine.transition("user_correction")
        self.machine.transition("repeated_misunderstanding")
        self.machine.transition("novi_error")
        self.assertEqual(self.machine.state, ConflictState.REPAIR)

    def test_never_defensive_rule(self) -> None:
        # a contradiction must not push Novi into a defensive posture
        self.machine.transition("contradiction")
        self.assertNotEqual(self.machine.state, ConflictState.TENSION)
        self.assertIn(self.machine.state, (ConflictState.CORRECTION, ConflictState.DISAGREEMENT))

    def test_stop_arguing_when_evidence_weak(self) -> None:
        # plan §12: stop arguing when evidence does not justify continued disagreement
        self.machine.transition("contradiction")
        self.machine.transition("user_rejection")
        self.assertEqual(self.machine.state, ConflictState.REPAIR)

    def test_snapshot_roundtrip(self) -> None:
        self.machine.transition("user_correction")
        restored = ConflictStateMachine.from_snapshot(self.machine.snapshot())
        self.assertEqual(restored.state, self.machine.state)


if __name__ == "__main__":
    unittest.main()
