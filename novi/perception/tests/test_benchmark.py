"""Tests: grounding benchmark runner (plan Phase 10, Step 10.3/10.4).

Executes a corpus against any SpatialPerceptionBackend and produces a
BenchmarkReport. CI runs it with the deterministic backend; evidence runs
use the real LocateAnything backend on the Mac.
"""

from __future__ import annotations

import pytest

from novi.brain.io import CameraFrame
from novi.perception.benchmark import BenchmarkReport, run_grounding_benchmark
from novi.perception.benchmark_corpus import BenchmarkCorpus
from novi.perception.grounding import SpatialInferencePolicy
from novi.perception.locate_anything import DeterministicLocateAnythingBackend

W, H = 4112, 2658


def _corpus() -> BenchmarkCorpus:
    return BenchmarkCorpus.from_dict(
        {
            "corpus_id": "test-corpus",
            "version": "t",
            "records": [
                {
                    "record_id": "r-menu",
                    "image_path": "novi/assets/test-image.png",
                    "image_sha256": "0" * 64,
                    "image_width": W,
                    "image_height": H,
                    "query": "locate the menu bar",
                    "category": "novel descriptions",
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


def _backend() -> DeterministicLocateAnythingBackend:
    # near-perfect menu bar + correct negative
    return DeterministicLocateAnythingBackend(
        scripted={
            ("r-menu", "locate the menu bar"): [("menu bar", (1, 0, 999, 23))],
            ("r-neg", "locate a unicorn"): ["none"],
        }
    )


def _run(backend, corpus=None, loader=None) -> BenchmarkReport:
    return run_grounding_benchmark(
        backend,
        corpus or _corpus(),
        SpatialInferencePolicy(),
        image_loader=loader or (lambda rec: _frame(rec)),
    )


class TestRunner:
    def test_report_shape_and_positive_accuracy(self):
        report = _run(_backend())
        assert isinstance(report, BenchmarkReport)
        assert report.corpus_id == "test-corpus"
        assert len(report.per_record) == 2
        assert report.aggregate["iou@0.5"] >= 0.9  # near-perfect menu bar
        assert report.aggregate["mean_iou"] >= 0.9
        assert report.aggregate["negative_correct"] == 1.0

    def test_negative_record_flagged_when_model_invents_box(self):
        backend = DeterministicLocateAnythingBackend(
            scripted={
                ("r-menu", "locate the menu bar"): [("menu bar", (0, 0, 500, 500))],
                ("r-neg", "locate a unicorn"): [("unicorn", (100, 100, 200, 200))],
            }
        )
        report = _run(backend)
        assert report.aggregate["negative_correct"] == 0.0
        neg = report.per_record[1]
        assert neg.negative_correct is False

    def test_wrong_boxes_lower_iou(self):
        backend = DeterministicLocateAnythingBackend(
            scripted={
                ("r-menu", "locate the menu bar"): [("menu bar", (500, 500, 800, 800))],
                ("r-neg", "locate a unicorn"): ["none"],
            }
        )
        report = _run(backend)
        assert report.aggregate["iou@0.5"] == 0.0

    def test_latency_and_malformed_aggregates(self):
        report = _run(_backend())
        agg = report.aggregate
        assert agg["latency_p50"] is not None
        assert agg["malformed_rate"] == 0.0
        assert agg["total_observations"] == 1

    def test_frame_dims_mismatch_rejected(self):
        def bad_loader(record):
            return CameraFrame(frame_id=record.record_id, captured_at="t0", width=10, height=10, payload=b"")

        with pytest.raises(ValueError, match="dims"):
            _run(_backend(), loader=bad_loader)

    def test_report_to_dict_json_serializable(self):
        import json

        payload = json.dumps(_run(_backend()).to_dict())
        assert "iou@0.5" in payload
