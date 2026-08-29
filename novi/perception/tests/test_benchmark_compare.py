"""Tests: baseline vs grounding comparison (plan Step 26).

"Baseline Novi vs Novi + LocateAnything" is the plan's most important
experiment. This harness computes both sides on the same corpus:
- baseline: ObjectDetector (SSDLite) detections vs ground truth;
- with-grounding: LocateAnything grounding vs ground truth;
and reports recall/precision/FP/FN per side. CI runs it with the
deterministic detector + deterministic grounding backend; evidence runs use
the real models.
"""

from __future__ import annotations

import pytest

from novi.brain.io import CameraFrame
from novi.perception.benchmark_corpus import BenchmarkCorpus
from novi.perception.benchmark_compare import ComparisonReport, compare_baseline_vs_grounding
from novi.perception.detection import DeterministicObjectDetector
from novi.perception.grounding import SpatialInferencePolicy
from novi.perception.locate_anything import DeterministicLocateAnythingBackend

W, H = 4112, 2658


def _corpus() -> BenchmarkCorpus:
    return BenchmarkCorpus.from_dict(
        {
            "corpus_id": "cmp-corpus",
            "version": "t",
            "records": [
                {
                    "record_id": "r-menu",
                    "image_path": "novi/assets/test-image.png",
                    "image_sha256": "0" * 64,
                    "image_width": W,
                    "image_height": H,
                    "query": "locate the menu bar",
                    "category": "novel",
                    "source": "test",
                    "license": "test",
                    "expected_boxes": [{"label": "menu bar", "box": [0, 0, 1000, 24]}],
                },
                {
                    "record_id": "r-neg",
                    "image_path": "novi/assets/test-image.png",
                    "image_sha256": "0" * 64,
                    "image_width": W,
                    "image_height": H,
                    "query": "locate a unicorn",
                    "category": "negative queries",
                    "source": "test",
                    "license": "test",
                    "expected_no_object": True,
                },
            ],
        }
    )


def _frame(record) -> CameraFrame:
    return CameraFrame(frame_id=record.record_id, captured_at="t0", width=W, height=H, payload=b"x")


def _loader(record):
    return _frame(record)


def _detector(hits: bool = True) -> DeterministicObjectDetector:
    # menu bar at pixel (0,0)-(4112,64) == normalized (0,0,1000,16)
    scripted = {"r-menu": [("menu bar", 0.9, (0, 0, 4112, 64))]} if hits else {}
    return DeterministicObjectDetector(scripted=scripted, confidence_floor=0.6)


def _grounding(hits: bool = True) -> DeterministicLocateAnythingBackend:
    scripted = {
        ("r-menu", "locate the menu bar"): [("menu bar", (1, 0, 999, 23))],
        ("r-neg", "locate a unicorn"): ["none"],
    } if hits else {
        ("r-menu", "locate the menu bar"): [("menu bar", (500, 500, 600, 600))],
        ("r-neg", "locate a unicorn"): ["none"],
    }
    return DeterministicLocateAnythingBackend(scripted=scripted)


class TestComparison:
    def test_report_shape(self):
        report = compare_baseline_vs_grounding(
            _corpus(), _detector(), _grounding(), SpatialInferencePolicy(), image_loader=_loader
        )
        assert isinstance(report, ComparisonReport)
        assert set(report.baseline) >= {"recall@0.5", "precision", "false_positives", "false_negatives"}
        assert set(report.with_grounding) >= {"recall@0.5", "negative_correct"}
        assert len(report.per_record) == 2

    def test_grounding_hits_when_ssdlite_misses(self):
        report = compare_baseline_vs_grounding(
            _corpus(), _detector(hits=False), _grounding(), SpatialInferencePolicy(), image_loader=_loader
        )
        assert report.baseline["recall@0.5"] == 0.0
        assert report.with_grounding["recall@0.5"] == 1.0
        assert report.delta["recall@0.5"] == pytest.approx(1.0)

    def test_both_hit(self):
        report = compare_baseline_vs_grounding(
            _corpus(), _detector(hits=True), _grounding(), SpatialInferencePolicy(), image_loader=_loader
        )
        assert report.baseline["recall@0.5"] == 1.0
        assert report.with_grounding["recall@0.5"] == 1.0

    def test_negative_handling_per_side(self):
        report = compare_baseline_vs_grounding(
            _corpus(), _detector(hits=True), _grounding(), SpatialInferencePolicy(), image_loader=_loader
        )
        # SSDLite has no concept of the negative query: it simply reports no
        # detections on that frame; grounding must answer no_object.
        assert report.per_record[1]["grounding_negative_correct"] is True

    def test_to_dict_json_serializable(self):
        import json

        report = compare_baseline_vs_grounding(
            _corpus(), _detector(), _grounding(), SpatialInferencePolicy(), image_loader=_loader
        )
        assert "recall@0.5" in json.dumps(report.to_dict())
