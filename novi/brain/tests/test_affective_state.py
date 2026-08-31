"""Tests for novi/brain/affective_state.py — transient affective state.

Plan 24 Phase 2: a transient state with dimensions (valence, arousal,
engagement, frustration/fatigue/stress/enthusiasm/confusion/comfort
likelihood, social_availability). Every dimension carries value, confidence,
source, last_updated and decay. These are *estimates from observable
evidence*, never clinical measurements or definitive emotional diagnoses.
"""

from __future__ import annotations

import unittest

from novi.brain.affective_state import AffectiveDimension, AffectiveState


class AffectiveDimensionTest(unittest.TestCase):
    def test_dimension_carries_value_confidence_source_decay(self) -> None:
        d = AffectiveDimension(value=0.72, confidence=0.78, source="fusion", decay_seconds=90)
        self.assertEqual(d.value, 0.72)
        self.assertEqual(d.confidence, 0.78)
        self.assertEqual(d.source, "fusion")
        self.assertEqual(d.decay_seconds, 90)
        self.assertTrue(d.last_updated)

    def test_values_clamped(self) -> None:
        d = AffectiveDimension(value=1.7, confidence=-0.2, source="x")
        self.assertLessEqual(d.value, 1.0)
        self.assertGreaterEqual(d.confidence, 0.0)

    def test_snapshot_roundtrip(self) -> None:
        d = AffectiveDimension(value=0.5, confidence=0.6, source="voice", decay_seconds=60)
        restored = AffectiveDimension.from_snapshot(d.snapshot())
        self.assertEqual(restored, d)


class AffectiveStateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.state = AffectiveState()

    def test_default_state_has_all_dimensions(self) -> None:
        for name in AffectiveState.DIMENSIONS:
            self.assertIn(name, self.state.dimensions)
            dim = self.state.dimensions[name]
            self.assertEqual(dim.value, 0.0)
            self.assertEqual(dim.confidence, 0.0)

    def test_update_sets_dimension(self) -> None:
        self.state.update("frustration_likelihood", value=0.72, confidence=0.78, source="fusion")
        dim = self.state.dimensions["frustration_likelihood"]
        self.assertEqual(dim.value, 0.72)
        self.assertEqual(dim.confidence, 0.78)
        self.assertEqual(dim.source, "fusion")

    def test_update_unknown_dimension_is_ignored(self) -> None:
        self.state.update("not_a_dimension", value=0.9, confidence=0.9, source="x")
        self.assertNotIn("not_a_dimension", self.state.dimensions)

    def test_decay_lowers_value_without_evidence(self) -> None:
        self.state.update("frustration_likelihood", value=0.8, confidence=0.8, source="fusion")
        self.state.decay(elapsed_seconds=90)
        self.assertLess(self.state.dimensions["frustration_likelihood"].value, 0.8)
        self.assertGreaterEqual(self.state.dimensions["frustration_likelihood"].value, 0.0)

    def test_decay_never_goes_below_zero(self) -> None:
        self.state.update("frustration_likelihood", value=0.1, confidence=0.8, source="fusion")
        for _ in range(20):
            self.state.decay(elapsed_seconds=90)
        self.assertEqual(self.state.dimensions["frustration_likelihood"].value, 0.0)

    def test_fresh_evidence_resists_decay(self) -> None:
        # A just-updated dimension decays only slightly.
        self.state.update("stress_likelihood", value=0.7, confidence=0.7, source="fusion")
        self.state.decay(elapsed_seconds=1)
        self.assertGreater(self.state.dimensions["stress_likelihood"].value, 0.6)

    def test_snapshot_shape(self) -> None:
        self.state.update("frustration_likelihood", value=0.72, confidence=0.78, source="fusion", decay_seconds=90)
        snap = self.state.snapshot()
        self.assertIn("frustration_likelihood", snap)
        dim = snap["frustration_likelihood"]
        self.assertEqual(dim["value"], 0.72)
        self.assertEqual(dim["confidence"], 0.78)
        self.assertEqual(dim["decay_seconds"], 90)
        self.assertIn("last_updated", dim)
        self.assertIn("source", dim)

    def test_from_snapshot_restores(self) -> None:
        self.state.update("enthusiasm_likelihood", value=0.6, confidence=0.5, source="voice")
        restored = AffectiveState.from_snapshot(self.state.snapshot())
        self.assertEqual(
            restored.dimensions["enthusiasm_likelihood"].value,
            self.state.dimensions["enthusiasm_likelihood"].value,
        )

    def test_peak_dimension(self) -> None:
        self.state.update("frustration_likelihood", value=0.3, confidence=0.5, source="a")
        self.state.update("fatigue_likelihood", value=0.8, confidence=0.6, source="b")
        name, dim = self.state.peak()
        self.assertEqual(name, "fatigue_likelihood")
        self.assertEqual(dim.value, 0.8)


if __name__ == "__main__":
    unittest.main()
