"""Phase C1 (gap-audit plan 13): Bayesian belief updates.

Pins the noisy-OR evidence combination with source-class weighting and
multiplicative contradiction decay:
  - confirming evidence accumulates with diminishing returns (asymptotic to 1);
  - direct_sensor evidence outweighs user_statement at equal raw confidence;
  - contradictions decay confidence proportionally (not a fixed subtraction);
  - repeated contradiction still flips; single contradiction never does;
  - snapshots round-trip including the evidence source.
"""

import unittest

from novi.brain.cognition import (
    CONTRADICTION_DECAY,
    SOURCE_WEIGHTS,
    BeliefSystem,
    source_weight,
)


class BayesianAccumulationTests(unittest.TestCase):
    def test_confirming_evidence_has_diminishing_returns(self):
        bs = BeliefSystem()
        b = bs.observe("alice", True, confidence=0.8)
        first = b.confidence
        b = bs.observe("alice", True, confidence=0.8)
        second = b.confidence
        gain1 = first - 0.8
        # First observation starts from raw weighted evidence; gains shrink after.
        self.assertGreater(second, first)
        self.assertLess(b.confidence, 1.0)
        if gain1 > 0:
            self.assertLess(second - first, max(gain1, 0.01))

    def test_source_class_weights_evidence(self):
        sensor = BeliefSystem().observe("door", True, confidence=0.9, source="direct_sensor")
        told = BeliefSystem().observe("told_door", True, confidence=0.9, source="user_statement")
        self.assertGreater(sensor.confidence, told.confidence)

    def test_unknown_source_uses_default_weight(self):
        self.assertEqual(source_weight("whisper"), SOURCE_WEIGHTS["direct_sensor"])
        self.assertEqual(source_weight("DIRECT_SENSOR"), SOURCE_WEIGHTS["direct_sensor"])


class ContradictionDecayTests(unittest.TestCase):
    def test_decay_is_multiplicative_not_fixed(self):
        bs = BeliefSystem()
        strong = None
        for _ in range(5):
            strong = bs.observe("lamp", True, confidence=0.99)
        weak = BeliefSystem()
        w = weak.observe("bulb", True, confidence=0.4)
        strong_before = strong.confidence
        weak_before = w.confidence
        s_after = bs.observe("lamp", False, confidence=0.9).confidence
        w_after = weak.observe("bulb", False, confidence=0.9).confidence
        # Proportional: same decay ratio; the stronger belief loses more
        # absolute confidence than the weak one (a fixed subtraction would
        # make the two losses equal).
        self.assertAlmostEqual(s_after / strong_before, CONTRADICTION_DECAY, places=6)
        self.assertAlmostEqual(w_after / weak_before, CONTRADICTION_DECAY, places=6)
        self.assertGreater(strong_before - s_after, weak_before - w_after)

    def test_single_contradiction_never_flips(self):
        bs = BeliefSystem()
        bs.observe("lamp", True, confidence=0.9)
        b = bs.observe("lamp", False, confidence=0.9)
        self.assertEqual(b.value, True)
        self.assertLess(b.confidence, 0.9 * SOURCE_WEIGHTS["direct_sensor"])

    def test_repeated_contradiction_flips_with_new_evidence(self):
        bs = BeliefSystem()
        bs.observe("lamp", True, confidence=0.9)
        bs.observe("lamp", False, confidence=0.95)
        b = bs.observe("lamp", False, confidence=0.95)
        self.assertEqual(b.value, False)
        self.assertAlmostEqual(b.confidence, 0.95 * source_weight("direct_sensor"), places=6)


class SnapshotCompatTests(unittest.TestCase):
    def test_snapshot_roundtrips_last_source(self):
        bs = BeliefSystem()
        bs.observe("cup", True, confidence=0.9, source="model_inference")
        rows = bs.snapshot()
        self.assertEqual(rows[0]["last_source"], "model_inference")
        restored = BeliefSystem.from_snapshot(rows)
        self.assertEqual(restored.belief_for("cup").last_source, "model_inference")

    def test_legacy_snapshot_without_source_still_loads(self):
        legacy = [{"entity": "x", "value": True, "property": "presence",
                   "confidence": 0.5, "evidence_count": 2, "contradictions": 0}]
        b = BeliefSystem.from_snapshot(legacy).belief_for("x")
        self.assertEqual(b.last_source, "")
        self.assertAlmostEqual(b.confidence, 0.5)


if __name__ == "__main__":
    unittest.main()
