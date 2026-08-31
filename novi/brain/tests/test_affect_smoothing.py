"""Tests for novi/brain/affect_smoothing.py — temporal affect smoothing.

Plan 24 Phase 4: avoid reacting to single frames or words. Use a short-term
window, exponential decay, minimum evidence count, hysteresis, confidence
threshold and cooldowns so noisy sensor readings cannot cause
calm → tense → calm → tense oscillation.
"""

from __future__ import annotations

import unittest

from novi.brain.affect_smoothing import AffectSmoother


class AffectSmootherTest(unittest.TestCase):
    def setUp(self) -> None:
        self.smoother = AffectSmoother(min_evidence=2, confidence_threshold=0.5, hysteresis=0.15, cooldown_cycles=3)

    def test_single_observation_does_not_transition(self) -> None:
        # one loud word → no major emotional transition
        sig = self.smoother.observe("frustration", value=0.9, confidence=0.9, cycle=1)
        self.assertEqual(sig.state, "low")

    def test_repeated_evidence_transitions_to_high(self) -> None:
        self.smoother.observe("frustration", value=0.8, confidence=0.8, cycle=1)
        sig = self.smoother.observe("frustration", value=0.8, confidence=0.8, cycle=2)
        self.assertEqual(sig.state, "high")

    def test_low_confidence_evidence_does_not_transition(self) -> None:
        self.smoother.observe("frustration", value=0.9, confidence=0.2, cycle=1)
        sig = self.smoother.observe("frustration", value=0.9, confidence=0.2, cycle=2)
        self.assertEqual(sig.state, "low")

    def test_hysteresis_prevents_oscillation(self) -> None:
        # reach high, then a small drop must NOT flip back to low
        self.smoother.observe("frustration", value=0.8, confidence=0.8, cycle=1)
        self.smoother.observe("frustration", value=0.8, confidence=0.8, cycle=2)
        sig = self.smoother.observe("frustration", value=0.55, confidence=0.8, cycle=3)
        self.assertEqual(sig.state, "high")  # 0.55 > 0.5 - 0.15 = 0.35

    def test_cooldown_blocks_immediate_re_transition(self) -> None:
        # high → drop below hysteresis → low, but cooldown prevents instant flip
        self.smoother.observe("frustration", value=0.8, confidence=0.8, cycle=1)
        self.smoother.observe("frustration", value=0.8, confidence=0.8, cycle=2)
        # strong drop below low threshold
        sig = self.smoother.observe("frustration", value=0.1, confidence=0.8, cycle=3)
        self.assertEqual(sig.state, "low")
        # immediately re-observed high during cooldown → stays low
        sig = self.smoother.observe("frustration", value=0.9, confidence=0.9, cycle=4)
        self.assertEqual(sig.state, "low")
        # after cooldown expires, repeated evidence can transition again
        sig = self.smoother.observe("frustration", value=0.9, confidence=0.9, cycle=8)
        sig = self.smoother.observe("frustration", value=0.9, confidence=0.9, cycle=9)
        self.assertEqual(sig.state, "high")

    def test_value_decays_without_evidence(self) -> None:
        self.smoother.observe("fatigue", value=0.8, confidence=0.8, cycle=1)
        sig = self.smoother.observe("fatigue", value=0.8, confidence=0.8, cycle=2)
        self.assertGreater(sig.value, 0.7)
        # no evidence for many cycles → decay
        sig = self.smoother.observe("fatigue", value=0.0, confidence=0.0, cycle=20)
        self.assertLess(sig.value, 0.3)

    def test_evidence_count_resets_after_decay_gap(self) -> None:
        self.smoother.observe("stress", value=0.8, confidence=0.8, cycle=1)
        self.smoother.observe("stress", value=0.8, confidence=0.8, cycle=2)
        # long gap resets the window
        sig = self.smoother.observe("stress", value=0.8, confidence=0.8, cycle=30)
        self.assertEqual(sig.evidence_count, 1)

    def test_snapshot_roundtrip(self) -> None:
        self.smoother.observe("frustration", value=0.8, confidence=0.8, cycle=1)
        self.smoother.observe("frustration", value=0.8, confidence=0.8, cycle=2)
        restored = AffectSmoother.from_snapshot(self.smoother.snapshot())
        self.assertEqual(
            restored.get("frustration").state,
            self.smoother.get("frustration").state,
        )
        self.assertEqual(
            restored.get("frustration").evidence_count,
            self.smoother.get("frustration").evidence_count,
        )


if __name__ == "__main__":
    unittest.main()
