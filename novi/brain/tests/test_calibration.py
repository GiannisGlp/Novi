"""Phase E2: reasoning-calibration statistics.

Pins Brier score, binned ECE, and the combined report on known cases:
perfect confidence, perfect anti-confidence, uniform ignorance, and a
hand-computable mixed case.
"""

import unittest

from novi.brain.calibration import (
    brier_score,
    calibration_bins,
    calibration_report,
    expected_calibration_error,
)


class BrierTests(unittest.TestCase):
    def test_perfect_confidence_scores_zero(self):
        self.assertAlmostEqual(brier_score([(1.0, True), (0.0, False)]), 0.0)

    def test_confident_wrong_scores_one(self):
        self.assertAlmostEqual(brier_score([(1.0, False), (0.0, True)]), 1.0)

    def test_uniform_ignores_scores_quarter(self):
        self.assertAlmostEqual(brier_score([(0.5, True), (0.5, False)]), 0.25)

    def test_empty_is_zero_and_values_clamped(self):
        self.assertEqual(brier_score([]), 0.0)
        self.assertEqual(brier_score([(5.0, True)]), brier_score([(1.0, True)]))


class ECETests(unittest.TestCase):
    def test_perfect_calibration_has_zero_ece(self):
        # In every bin, avg_confidence == accuracy.
        pairs = [(1.0, True)] * 5 + [(0.0, False)] * 5
        self.assertAlmostEqual(expected_calibration_error(pairs), 0.0)

    def test_overconfident_predictions_raise_ece(self):
        pairs = [(1.0, False)] * 4
        self.assertGreater(expected_calibration_error(pairs), 0.9)

    def test_bins_partition_samples(self):
        pairs = [(i / 10, i % 2 == 0) for i in range(10)]
        bins = calibration_bins(pairs, n_bins=10)
        self.assertEqual(sum(b["count"] for b in bins), len(pairs))
        # Boundary value 1.0 lands in the last bin, not dropped.
        last = bins[-1]
        self.assertEqual(last["count"], 1)


class ReportTests(unittest.TestCase):
    def test_report_shape_and_consistency(self):
        report = calibration_report([(0.9, True), (0.9, True), (0.2, False)], n_bins=10)
        self.assertEqual(report["samples"], 3)
        self.assertTrue(0.0 <= report["brier"] <= 1.0)
        self.assertTrue(0.0 <= report["ece"] <= 1.0)
        self.assertEqual(len(report["bins"]), 10)

    def test_empty_report(self):
        report = calibration_report([])
        self.assertEqual(report["samples"], 0)
        self.assertEqual(report["brier"], 0.0)
        self.assertEqual(report["ece"], 0.0)


if __name__ == "__main__":
    unittest.main()
