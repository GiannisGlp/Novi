"""Tests for novi/brain/hypothesis_manager.py — predictive alternatives.

Plan 22 Phase 9 (Tasks 9.2–9.3):
- prediction error → hypothesis generation → evidence → updated belief
  (never a direct jump from error to speech);
- alternatives are real candidates scored by probability / expected evidence
  / risk / cost / relevance (plan §9.3);
- ambiguity is preserved — belief revision never forces a choice.
"""

from __future__ import annotations

import unittest

from novi.brain.hypothesis_manager import HypothesisManager


class HypothesisManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mgr = HypothesisManager()

    def test_generate_creates_scored_alternatives(self) -> None:
        hyps = self.mgr.generate(
            "vano closes laptop and picks up keys",
            ["vano is leaving", "vano is taking a break", "vano is changing location"],
            prior=[0.7, 0.2, 0.1],
            evidence=[["walking toward door"], ["making coffee"], ["moving to another desk"]],
            risks=[0.5, 0.1, 0.2],
            costs=[0.2, 0.1, 0.1],
        )
        self.assertEqual(len(hyps), 3)
        self.assertEqual(self.mgr.observation, "vano closes laptop and picks up keys")
        # probability ordering survives into scores
        best = self.mgr.best()
        self.assertEqual(best.label, "vano is leaving")  # type: ignore[union-attr]
        self.assertGreater(best.probability, 0.5)  # type: ignore[union-attr]
        # risk discounts the leader: A risk .5 vs B .1
        self.assertLessEqual(best.risk, 0.5)  # type: ignore[union-attr]

    def test_evidence_updates_belief(self) -> None:
        self.mgr.generate("mug moved", ["mug carried away", "mug slid", "mug disappeared"],
                          prior=[0.4, 0.3, 0.3])
        before = self.mgr.best()
        before_prob = before.probability if before is not None else 0.0
        self.mgr.update_belief(label="mug carried away", supports=True, strength=1.0)
        self.mgr.update_belief(label="mug carried away", supports=True, strength=1.0)
        after = self.mgr.best()
        self.assertEqual(after.label, "mug carried away")  # type: ignore[union-attr]
        self.assertGreater(after.probability, before_prob)  # type: ignore[union-attr]
        self.assertEqual(after.evidence_for, 2)  # type: ignore[union-attr]

    def test_contradicting_evidence_lowers_belief(self) -> None:
        self.mgr.generate("mug moved", ["mug carried away", "mug slid"], prior=[0.9, 0.1])
        self.mgr.update_belief(label="mug carried away", supports=False, strength=1.0)
        self.mgr.update_belief(label="mug carried away", supports=False, strength=1.0)
        hyp = self.mgr.best()
        self.assertLess(hyp.probability, 0.9)  # type: ignore[union-attr]

    def test_ambiguity_is_preserved_not_forced(self) -> None:
        self.mgr.generate("vano moves", ["vano is leaving", "vano is taking a break"],
                          prior=[0.55, 0.5])
        self.assertIsNone(self.mgr.resolve())  # too close — no forced choice
        self.mgr.update_belief(label="vano is leaving", supports=True, strength=1.0)
        self.mgr.update_belief(label="vano is leaving", supports=True, strength=1.0)
        self.mgr.update_belief(label="vano is leaving", supports=True, strength=1.0)
        resolved = self.mgr.resolve()
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.label, "vano is leaving")  # type: ignore[union-attr]

    def test_bounded_alternatives(self) -> None:
        self.mgr.generate("x", [f"alt-{i}" for i in range(12)])
        self.assertLessEqual(len(self.mgr.all()), self.mgr.max_alternatives)

    def test_explainable_snapshot(self) -> None:
        self.mgr.generate("x", ["a", "b"], prior=[0.8, 0.2])
        snap = self.mgr.snapshot()
        self.assertEqual(snap["observation"], "x")
        self.assertEqual(len(snap["alternatives"]), 2)
        for entry in snap["alternatives"]:
            for key in ("probability", "risk", "cost", "relevance", "score", "expected_evidence"):
                self.assertIn(key, entry)

    def test_unknown_evidence_label_ignored(self) -> None:
        self.mgr.generate("x", ["a", "b"])
        self.assertIsNone(self.mgr.update_belief(label="nope", supports=True))


if __name__ == "__main__":
    unittest.main()
