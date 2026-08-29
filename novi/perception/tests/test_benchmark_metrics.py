"""Tests: grounding benchmark metrics (plan Phase 10, Step 10.3).

Pure metric computation over predicted/ground-truth pixel boxes and
latency samples. Everything is deterministic and hardware-free.
"""

from __future__ import annotations

import pytest

from novi.perception.benchmark_metrics import (
    center_error_norm,
    iou_at_thresholds,
    latency_percentiles,
    mean_iou_matched,
    precision_recall_fp_fn,
)

# pixel boxes (x, y, w, h) on a 640x480 image
GT = [(100, 100, 200, 200), (400, 300, 100, 100)]
PERFECT = [(100, 100, 200, 200), (400, 300, 100, 100)]
SLIGHT = [(110, 110, 180, 180), (401, 300, 100, 100)]  # IoU ~0.81 vs first GT
MISSED = [(100, 100, 200, 200)]  # second GT not predicted
SPURIOUS = [(100, 100, 200, 200), (400, 300, 100, 100), (10, 10, 20, 20)]


class TestIouAtThresholds:
    def test_perfect_match_passes_all_thresholds(self):
        res = iou_at_thresholds(PERFECT, GT)
        assert res["iou@0.5"] == 1.0
        assert res["iou@0.75"] == 1.0
        assert res["iou@0.90"] == 1.0
        assert res["iou@0.95"] == 1.0

    def test_slight_offset_passes_05_but_may_fail_095(self):
        res = iou_at_thresholds(SLIGHT, GT)
        assert res["iou@0.5"] == 1.0
        assert res["iou@0.90"] < 1.0

    def test_missing_gt_drops_recall(self):
        res = iou_at_thresholds(MISSED, GT)
        assert res["iou@0.5"] == 0.5

    def test_empty_predictions_yield_zero(self):
        res = iou_at_thresholds([], GT)
        assert res["iou@0.5"] == 0.0


class TestMeanIou:
    def test_perfect_is_one(self):
        assert mean_iou_matched(PERFECT, GT) == 1.0

    def test_partial_match(self):
        val = mean_iou_matched(MISSED, GT)
        assert 0.0 < val < 1.0

    def test_no_gt_is_zero(self):
        assert mean_iou_matched(PERFECT, []) == 0.0


class TestCenterError:
    def test_identical_boxes_zero_error(self):
        assert center_error_norm((100, 100, 200, 200), (100, 100, 200, 200)) == 0.0

    def test_known_offset(self):
        # centers (200,200) vs (210,220) in [0,1000]-normalized box space
        # -> sqrt(10^2 + 20^2) = 22.36 (resolution-independent)
        err = center_error_norm((150, 150, 100, 100), (160, 170, 100, 100))
        assert err == pytest.approx(22.36, abs=0.05)


class TestPrecisionRecall:
    def test_perfect(self):
        p, r, fp, fn = precision_recall_fp_fn(PERFECT, GT)
        assert (p, r, fp, fn) == (1.0, 1.0, 0, 0)

    def test_spurious_prediction_raises_fp(self):
        p, r, fp, fn = precision_recall_fp_fn(SPURIOUS, GT)
        assert fp == 1
        assert p == pytest.approx(2 / 3)

    def test_missed_gt_raises_fn(self):
        p, r, fp, fn = precision_recall_fp_fn(MISSED, GT)
        assert fn == 1
        assert r == pytest.approx(0.5)

    def test_no_predictions(self):
        p, r, fp, fn = precision_recall_fp_fn([], GT)
        assert (p, r, fp, fn) == (0.0, 0.0, 0, 2)

    def test_below_threshold_overlap_is_false_positive(self):
        # pred overlaps GT but IoU < 0.5: must count as FP, not TP
        p, r, fp, fn = precision_recall_fp_fn([(160, 160, 80, 80)], [(100, 100, 200, 200)])
        assert (p, r, fp, fn) == (0.0, 0.0, 1, 1)


class TestLatencyPercentiles:
    def test_percentiles(self):
        samples = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
        res = latency_percentiles(samples)
        assert res["p50"] == pytest.approx(55.0)
        assert res["p95"] == pytest.approx(95.5)
        assert res["p99"] == pytest.approx(99.1)

    def test_empty_samples(self):
        assert latency_percentiles([]) == {"p50": None, "p95": None, "p99": None}
