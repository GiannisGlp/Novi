"""Tests for the emotional-memory extension of novi/brain/interaction_outcome.py.

Plan 24 Phase 8: interaction records gain episode, social_context,
affective_signals and learned_implication. This is an interaction-learning
record, not a diagnosis.
"""

from __future__ import annotations

import unittest

from novi.brain.interaction_outcome import InteractionOutcome, OutcomeRecorder


class InteractionOutcomeAffectiveTest(unittest.TestCase):
    def setUp(self) -> None:
        self.recorder = OutcomeRecorder()

    def _make_outcome(self, **overrides: object) -> InteractionOutcome:
        base: dict[str, object] = {
            "interaction_id": "i1",
            "input_text": "explain the camera again",
            "person": "Vano",
            "response_text": "continued detailed explanation",
            "user_reaction": "correction",
            "correction": "shorter answer",
            "outcome": "corrected",
            "episode": "camera debugging",
            "social_context": "user became frustrated after repeated explanation",
            "affective_signals": {"frustration_likelihood": 0.72},
            "learned_implication": "reduce verbosity under similar conditions",
            "confidence": 0.91,
        }
        base.update(overrides)
        return InteractionOutcome(**base)

    def test_new_fields_default(self) -> None:
        o = InteractionOutcome(interaction_id="i0", input_text="hi", person="Vano")
        self.assertEqual(o.episode, "")
        self.assertEqual(o.social_context, "")
        self.assertEqual(o.affective_signals, {})
        self.assertEqual(o.learned_implication, "")

    def test_affective_signals_recorded(self) -> None:
        o = self._make_outcome()
        self.assertEqual(o.episode, "camera debugging")
        self.assertEqual(o.social_context, "user became frustrated after repeated explanation")
        self.assertEqual(o.affective_signals["frustration_likelihood"], 0.72)
        self.assertEqual(o.learned_implication, "reduce verbosity under similar conditions")

    def test_snapshot_includes_new_fields(self) -> None:
        snap = self._make_outcome().snapshot()
        self.assertIn("episode", snap)
        self.assertIn("social_context", snap)
        self.assertIn("affective_signals", snap)
        self.assertIn("learned_implication", snap)
        self.assertEqual(snap["episode"], "camera debugging")

    def test_snapshot_roundtrip(self) -> None:
        o = self._make_outcome()
        restored = InteractionOutcome.from_snapshot(o.snapshot())
        self.assertEqual(restored.episode, o.episode)
        self.assertEqual(restored.social_context, o.social_context)
        self.assertEqual(restored.affective_signals, o.affective_signals)
        self.assertEqual(restored.learned_implication, o.learned_implication)
        self.assertAlmostEqual(restored.confidence, o.confidence, places=2)

    def test_derive_implication_from_correction(self) -> None:
        o = self._make_outcome()
        implication = OutcomeRecorder.derive_implication(o)
        self.assertIn("reduce verbosity", implication)
        self.assertIn("similar conditions", implication)

    def test_derive_implication_empty_without_correction(self) -> None:
        o = self._make_outcome(user_reaction="thanks", correction="", outcome="acknowledged")
        self.assertEqual(OutcomeRecorder.derive_implication(o), "")

    def test_learned_implications_from_recorder(self) -> None:
        self.recorder.record(self._make_outcome())
        self.recorder.record(
            self._make_outcome(
                interaction_id="i2",
                user_reaction="thanks",
                correction="",
                outcome="acknowledged",
                learned_implication="",
            )
        )
        implications = self.recorder.learned_implications()
        self.assertEqual(len(implications), 1)
        self.assertIn("reduce verbosity", implications[0])


if __name__ == "__main__":
    unittest.main()
