"""Baseline vs +grounding comparison harness (plan Step 26).

"Baseline Novi vs Novi + LocateAnything" is the plan's most important
experiment. Both sides run on the SAME corpus:

- baseline: ObjectDetector (SSDLite) detections vs ground truth — SSDLite has
  no language queries, so matching is IoU-based and label-agnostic (its
  categories are COCO classes, not semantic descriptions);
- with-grounding: LocateAnything grounding vs ground truth (reuses
  `run_grounding_benchmark` as the single source of truth).

Aggregates report recall/precision/FP/FN per side plus a delta. CI runs the
deterministic detector + deterministic grounding backend; evidence runs use
the real SSDLite-on-MPS and LocateAnything backends.

Cognitive metrics (search success, world-state accuracy, planner success)
are brain-zone and out of scope here.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from novi.brain.io import CameraFrame
from novi.perception.benchmark import run_grounding_benchmark
from novi.perception.benchmark_corpus import BenchmarkCorpus, BenchmarkRecord
from novi.perception.benchmark_metrics import precision_recall_fp_fn
from novi.perception.detection import ObjectDetector
from novi.perception.grounding import SpatialInferencePolicy, SpatialPerceptionBackend

ImageLoader = Callable[[BenchmarkRecord], CameraFrame]


@dataclass
class ComparisonReport:
    corpus_id: str
    timestamp: str
    baseline: dict
    with_grounding: dict
    delta: dict
    per_record: list[dict]

    def to_dict(self) -> dict:
        return {
            "corpus_id": self.corpus_id,
            "timestamp": self.timestamp,
            "baseline": self.baseline,
            "with_grounding": self.with_grounding,
            "delta": self.delta,
            "per_record": self.per_record,
        }


def _det_pixel_to_norm(box: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    x, y, w, h = box
    x1 = min(x * 1000 // width, 1000)
    y1 = min(y * 1000 // height, 1000)
    x2 = min((x + w) * 1000 // width, 1000)
    y2 = min((y + h) * 1000 // height, 1000)
    return (x1, y1, x2 - x1, y2 - y1)


def compare_baseline_vs_grounding(
    corpus: BenchmarkCorpus,
    detector: ObjectDetector,
    grounding_backend: SpatialPerceptionBackend,
    policy: SpatialInferencePolicy,
    *,
    image_loader: ImageLoader | None = None,
    repo_root: Path | None = None,
) -> ComparisonReport:
    g_report = run_grounding_benchmark(
        grounding_backend, corpus, policy, image_loader=image_loader, repo_root=repo_root
    )
    loader = image_loader or (lambda rec: _default_load(rec, repo_root or Path.cwd()))

    baseline_tp = baseline_fp = baseline_fn = 0
    baseline_gt = 0
    per_record: list[dict] = []

    for i, record in enumerate(corpus.records):
        frame = loader(record)
        dets = detector.detect(frame)
        pred_norm = [_det_pixel_to_norm(d.bbox, frame.width, frame.height) for d in dets]
        gt_norm = [(gt.box[0], gt.box[1], gt.box[2] - gt.box[0], gt.box[3] - gt.box[1]) for gt in record.expected_boxes]
        p, r, fp, fn = precision_recall_fp_fn(pred_norm, gt_norm)
        baseline_tp += round(r * len(gt_norm)) if gt_norm else 0
        baseline_fp += fp
        baseline_fn += fn
        baseline_gt += len(gt_norm)

        g_rec = g_report.per_record[i]
        per_record.append(
            {
                "record_id": record.record_id,
                "query": record.query,
                "category": record.category,
                "ssdlite_detections": len(dets),
                "ssdlite_recall@0.5": r,
                "ssdlite_precision": p,
                "ssdlite_fp": fp,
                "ssdlite_fn": fn,
                "grounding_recall@0.5": g_rec.recall,
                "grounding_precision": g_rec.precision,
                "grounding_iou@0.5": g_rec.iou.get("iou@0.5"),
                "grounding_negative_correct": g_rec.negative_correct,
                "grounding_latency_ms": g_rec.latency_ms,
            }
        )

    baseline_recall = baseline_tp / baseline_gt if baseline_gt else 0.0
    baseline_precision = baseline_tp / (baseline_tp + baseline_fp) if (baseline_tp + baseline_fp) else 0.0
    baseline = {
        "recall@0.5": round(baseline_recall, 4),
        "precision": round(baseline_precision, 4),
        "false_positives": baseline_fp,
        "false_negatives": baseline_fn,
        "total_gt_boxes": baseline_gt,
    }
    with_grounding = {
        "recall@0.5": g_report.aggregate["recall"],
        "precision": g_report.aggregate["precision"],
        "false_positives": g_report.aggregate["false_positives"],
        "false_negatives": g_report.aggregate["false_negatives"],
        "iou@0.5": g_report.aggregate["iou@0.5"],
        "mean_iou": g_report.aggregate["mean_iou"],
        "negative_correct": g_report.aggregate["negative_correct"],
        "latency_p50": g_report.aggregate["latency_p50"],
    }
    delta = {
        "recall@0.5": round(with_grounding["recall@0.5"] - baseline["recall@0.5"], 4),
        "precision": round(with_grounding["precision"] - baseline["precision"], 4),
        "false_positives": with_grounding["false_positives"] - baseline["false_positives"],
        "false_negatives": with_grounding["false_negatives"] - baseline["false_negatives"],
    }
    return ComparisonReport(
        corpus_id=corpus.corpus_id,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
        baseline=baseline,
        with_grounding=with_grounding,
        delta=delta,
        per_record=per_record,
    )


def _default_load(record: BenchmarkRecord, repo_root: Path) -> CameraFrame:
    payload = (repo_root / record.image_path).read_bytes()
    return CameraFrame(
        frame_id=record.record_id,
        captured_at="bench",
        width=record.image_width,
        height=record.image_height,
        payload=payload,
    )
