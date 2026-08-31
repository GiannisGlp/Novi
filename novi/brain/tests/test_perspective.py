"""Tests for novi/brain/perspective.py — perspective-taking engine.

Plan 24 Phase 5: maintain multiple hypotheses about the user's state rather
than assuming one interpretation, then select behavior robust across likely
interpretations. This is more mature than claiming certainty.
"""

from __future__ import annotations

import unittest

from novi.brain.perspective import PerspectiveEngine, PerspectiveHypothesis


class PerspectiveEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = PerspectiveEngine()

    def test_hypothesize_creates_scored_hypotheses(self) -> None:
        # plan §9 example: "Fine. Whatever."
        hyps = self.engine.hypothesize(
            "Fine. Whatever.",
            interpretations=["frustrated", "tired", "disengaged", "casual"],
            priors=[0.55, 0.20, 0.15, 0.10],
            supporting=[["volume_up", "correction_language"], ["slow_speech"], ["short_responses"], []],
            contradictory=[["neutral_face"], [], [], ["engaged_gaze"]],
            expected=[["sigh", "repeats"], ["yawns"], ["looks_away"], ["continues_topic"]],
            consequences=["reduce_pressure", "reduce_pressure", "give_space", "continue_normally"],
        )
        self.assertEqual(len(hyps), 4)
        self.assertEqual(hyps[0].interpretation, "frustrated")
        self.assertAlmostEqual(hyps[0].probability, 0.55, places=2)
        self.assertIn("volume_up", hyps[0].supporting_evidence)
        self.assertIn("neutral_face", hyps[0].contradictory_evidence)
        self.assertEqual(hyps[0].consequence, "reduce_pressure")

    def test_update_adjusts_probability(self) -> None:
        self.engine.hypothesize(
            "Fine. Whatever.",
            interpretations=["frustrated", "tired"],
            priors=[0.5, 0.5],
        )
        hyp = self.engine.update("frustrated", supports=True, strength=0.8)
        self.assertIsNotNone(hyp)
        self.assertGreater(hyp.probability, 0.5)
        # contradictory evidence lowers it
        hyp = self.engine.update("frustrated", supports=False, strength=0.8)
        self.assertLess(hyp.probability, 0.5 + 0.2)

    def test_robust_action_selects_best_across_hypotheses(self) -> None:
        self.engine.hypothesize(
            "Fine. Whatever.",
            interpretations=["frustrated", "tired", "disengaged", "casual"],
            priors=[0.55, 0.20, 0.15, 0.10],
            consequences=["reduce_pressure", "reduce_pressure", "give_space", "continue_normally"],
        )
        action = self.engine.robust_action()
        self.assertEqual(action, "reduce_pressure")  # 0.75 combined mass

    def test_robust_action_handles_unknown_interpretation(self) -> None:
        self.engine.hypothesize(
            "x",
            interpretations=["frustrated"],
            priors=[0.6],
            consequences=["reduce_pressure"],
        )
        # an interpretation with no consequence maps to the default
        action = self.engine.robust_action(default="continue_normally")
        self.assertEqual(action, "reduce_pressure")

    def test_never_claims_certainty(self) -> None:
        # probabilities are normalized and no single hypothesis is forced
        self.engine.hypothesize(
            "Fine. Whatever.",
            interpretations=["frustrated", "tired", "disengaged", "casual"],
            priors=[0.55, 0.20, 0.15, 0.10],
        )
        total = sum(h.probability for h in self.engine.all())
        self.assertAlmostEqual(total, 1.0, places=2)
        self.assertLess(self.engine.best().probability, 1.0)

    def test_snapshot_roundtrip(self) -> None:
        self.engine.hypothesize(
            "Fine. Whatever.",
            interpretations=["frustrated", "tired"],
            priors=[0.6, 0.4],
            consequences=["reduce_pressure", "give_space"],
        )
        restored = PerspectiveEngine.from_snapshot(self.engine.snapshot())
        self.assertEqual(len(restored.all()), 2)
        self.assertEqual(restored.best().interpretation, self.engine.best().interpretation)
        self.assertAlmostEqual(restored.best().probability, self.engine.best().probability, places=2)


if __name__ == "__main__":
    unittest.main()
