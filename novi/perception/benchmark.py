"""Grounding benchmark runner (plan Phase 10, Steps 10.3/10.4).

Executes a versioned corpus against any SpatialPerceptionBackend and
aggregates the plan's metrics: IoU@0.5/0.75/0.90/0.95, mean IoU, center
error, precision/recall, FP/FN, malformed-output rate, latency
p50/p95/p99, negative-query correctness.

CI runs this with DeterministicLocateAnythingBackend (no model, no GPU);
evidence runs use the real backend (see scripts/mac-locateanything-experiment.py
benchmark section). Cognitive metrics (search success, world-state accuracy,
planner success) are brain-zone and measured separately — this report covers
perception metrics only.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from novi.brain.io import CameraFrame
from novi.perception.benchmark_corpus import BenchmarkCorpus, BenchmarkRecord
from novi.perception.benchmark_metrics import (
    center_error_norm,
    iou_at_thresholds,
    latency_percentiles,
    malformed_rate,
    mean_iou_matched,
    precision_recall_fp_fn,
)
from novi.perception.grounding import (
    GroundingObservation,
    SpatialInferencePolicy,
    SpatialPerceptionBackend,
    SpatialQuery,
)

ImageLoader = Callable[[BenchmarkRecord], CameraFrame]


def _norm_xywh(x1: int, y1: int, x2: int, y2: int) -> tuple[int, int, int, int]:
    return (x1, y1, x2 - x1, y2 - y1)


@dataclass
class RecordResult:
    record_id: str
    query: str
    category: str
    success: bool
    no_object: bool
    n_observations: int
    latency_ms: float | None
    validation_error_count: int
    expected_no_object: bool
    negative_correct: bool | None = None
    iou: dict[str, float] = field(default_factory=dict)
    mean_iou: float = 0.0
    center_error: float | None = None
    precision: float | None = None
    recall: float | None = None
    fp: int = 0
    fn: int = 0


@dataclass
class BenchmarkReport:
    corpus_id: str
    corpus_version: str
    backend_model_id: str
    timestamp: str
    per_record: list[RecordResult]
    aggregate: dict

    def to_dict(self) -> dict:
        return {
            "corpus_id": self.corpus_id,
            "corpus_version": self.corpus_version,
            "backend_model_id": self.backend_model_id,
            "timestamp": self.timestamp,
            "per_record": [r.__dict__ for r in self.per_record],
            "aggregate": self.aggregate,
        }


def _default_loader(repo_root: Path) -> ImageLoader:
    def load(record: BenchmarkRecord) -> CameraFrame:
        payload = (repo_root / record.image_path).read_bytes()
        return CameraFrame(
            frame_id=record.record_id,
            captured_at="bench",
            width=record.image_width,
            height=record.image_height,
            payload=payload,
        )

    return load


def run_grounding_benchmark(
    backend: SpatialPerceptionBackend,
    corpus: BenchmarkCorpus,
    policy: SpatialInferencePolicy,
    *,
    image_loader: ImageLoader | None = None,
    repo_root: Path | None = None,
) -> BenchmarkReport:
    loader = image_loader or _default_loader(repo_root or Path.cwd())
    per_record: list[RecordResult] = []
    latencies: list[float] = []

    for record in corpus.records:
        frame = loader(record)
        if (frame.width, frame.height) != (record.image_width, record.image_height):
            raise ValueError(
                f"{record.record_id}: frame dims {frame.width}x{frame.height} "
                f"do not match record {record.image_width}x{record.image_height}"
            )
        query = SpatialQuery(text=record.query, frame_id=record.record_id, timestamp="bench")
        started = time.perf_counter()
        result = backend.ground(frame, query, policy)
        wall_ms = (time.perf_counter() - started) * 1000.0
        latency = result.latency_ms if result.latency_ms is not None else wall_ms
        latencies.append(latency)

        pred_norm = [
            _norm_xywh(*o.source_box) for o in result.observations if isinstance(o, GroundingObservation)
        ]
        gt_norm = [_norm_xywh(*gt.box) for gt in record.expected_boxes]

        rec = RecordResult(
            record_id=record.record_id,
            query=record.query,
            category=record.category,
            success=result.success,
            no_object=result.no_object,
            n_observations=len(result.observations),
            latency_ms=round(latency, 1),
            validation_error_count=len(result.validation_errors),
            expected_no_object=record.expected_no_object,
        )

        if record.expected_no_object:
            rec.negative_correct = bool(result.no_object or (result.success and not result.observations))
        else:
            rec.iou = iou_at_thresholds(pred_norm, gt_norm)
            rec.mean_iou = mean_iou_matched(pred_norm, gt_norm)
            if pred_norm and gt_norm:
                # center error of the best-IoU pair
                best = max(((p, g) for p in pred_norm for g in gt_norm), key=lambda pg: _pair_iou(*pg))
                rec.center_error = round(center_error_norm(*best), 2)
            p, r, fp, fn = precision_recall_fp_fn(pred_norm, gt_norm)
            rec.precision, rec.recall, rec.fp, rec.fn = p, r, fp, fn
        per_record.append(rec)

    positive = [r for r in per_record if not r.expected_no_object]
    negatives = [r for r in per_record if r.expected_no_object]
    total_tp = sum(1 for r in positive if r.mean_iou >= 0.5)
    total_fp = sum(r.fp for r in positive)
    total_fn = sum(r.fn for r in positive)
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0

    aggregate = {
        "records": len(per_record),
        "positive_records": len(positive),
        "negative_records": len(negatives),
        "iou@0.5": round(sum(r.iou.get("iou@0.5", 0.0) for r in positive) / len(positive), 4) if positive else 0.0,
        "iou@0.75": round(sum(r.iou.get("iou@0.75", 0.0) for r in positive) / len(positive), 4) if positive else 0.0,
        "iou@0.90": round(sum(r.iou.get("iou@0.90", 0.0) for r in positive) / len(positive), 4) if positive else 0.0,
        "iou@0.95": round(sum(r.iou.get("iou@0.95", 0.0) for r in positive) / len(positive), 4) if positive else 0.0,
        "mean_iou": round(sum(r.mean_iou for r in positive) / len(positive), 4) if positive else 0.0,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "false_positives": total_fp,
        "false_negatives": total_fn,
        "negative_correct": round(sum(1 for r in negatives if r.negative_correct) / len(negatives), 4) if negatives else None,
        "malformed_rate": malformed_rate([r.validation_error_count for r in per_record], len(per_record)),
        **{f"latency_{k}": v for k, v in latency_percentiles(latencies).items()},
        "total_observations": sum(r.n_observations for r in per_record),
    }

    caps = backend.capabilities()
    return BenchmarkReport(
        corpus_id=corpus.corpus_id,
        corpus_version=corpus.version,
        backend_model_id=caps.model_id or "unknown",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
        per_record=per_record,
        aggregate=aggregate,
    )


def _pair_iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    from novi.perception.tracking import _iou

    return _iou(a, b)
