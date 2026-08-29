"""Grounding benchmark metrics (plan Phase 10, Step 10.3).

Pure, deterministic metric computation over predicted/ground-truth boxes and
latency samples. Boxes are `(x, y, w, h)`; functions are scale-agnostic, so
they work on both pixel boxes and [0,1000]-normalized boxes as long as both
sides of a comparison use the same space (the runner normalizes once).

Matching is greedy best-IoU (one prediction per ground-truth box), matching
the ObjectTracker convention. `_iou` is reused from tracking.
"""

from __future__ import annotations

import statistics
from typing import Sequence

from novi.perception.tracking import _iou

Box = tuple[int, int, int, int]


def _best_matches(pred_boxes: Sequence[Box], gt_boxes: Sequence[Box]) -> tuple[list[float], int, int]:
    """Greedy best-IoU matching. Returns (best_iou_per_gt, tp, fp)."""
    used: set[int] = set()
    best_per_gt: list[float] = []
    for gt in gt_boxes:
        best, best_idx = 0.0, None
        for i, pred in enumerate(pred_boxes):
            if i in used:
                continue
            iou = _iou(pred, gt)
            if iou > best:
                best, best_idx = iou, i
        if best_idx is not None:
            used.add(best_idx)
        best_per_gt.append(best)
    tp = len(used)
    fp = len(pred_boxes) - tp
    return best_per_gt, tp, fp


_IOU_KEYS = {0.5: "iou@0.5", 0.75: "iou@0.75", 0.9: "iou@0.90", 0.95: "iou@0.95"}


def iou_at_thresholds(
    pred_boxes: Sequence[Box],
    gt_boxes: Sequence[Box],
    thresholds: Sequence[float] = (0.5, 0.75, 0.90, 0.95),
) -> dict[str, float]:
    """Fraction of ground-truth boxes matched at each IoU threshold."""
    if not gt_boxes:
        return {_IOU_KEYS.get(t, f"iou@{t}"): 0.0 for t in thresholds}
    best_per_gt, _, _ = _best_matches(pred_boxes, gt_boxes)
    return {
        _IOU_KEYS.get(t, f"iou@{t}"): round(sum(1.0 for b in best_per_gt if b >= t) / len(gt_boxes), 4)
        for t in thresholds
    }


def mean_iou_matched(pred_boxes: Sequence[Box], gt_boxes: Sequence[Box]) -> float:
    """Mean of best-IoU per ground-truth box (0.0 when no GT)."""
    if not gt_boxes:
        return 0.0
    best_per_gt, _, _ = _best_matches(pred_boxes, gt_boxes)
    return round(sum(best_per_gt) / len(gt_boxes), 4)


def center_error_norm(pred: Box, gt: Box) -> float:
    """Euclidean distance between box centers (same space as the boxes)."""
    px, py = pred[0] + pred[2] / 2, pred[1] + pred[3] / 2
    gx, gy = gt[0] + gt[2] / 2, gt[1] + gt[3] / 2
    return round(((px - gx) ** 2 + (py - gy) ** 2) ** 0.5, 4)


def precision_recall_fp_fn(
    pred_boxes: Sequence[Box],
    gt_boxes: Sequence[Box],
    iou_threshold: float = 0.5,
) -> tuple[float, float, int, int]:
    """(precision, recall, false_positives, false_negatives) at a threshold.

    A prediction counts as TP only when its best GT match is >= the IoU
    threshold (the greedy matching itself stays threshold-free so the same
    pairing is used for IoU@k curves).
    """
    best_per_gt, _, _ = _best_matches(pred_boxes, gt_boxes)
    tp = sum(1.0 for b in best_per_gt if b >= iou_threshold)
    fp = len(pred_boxes) - tp
    fn = len(gt_boxes) - tp
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return precision, recall, int(fp), int(fn)


def latency_percentiles(
    samples: Sequence[float], ps: Sequence[float] = (50, 95, 99)
) -> dict[str, float | None]:
    """Linear-interpolated percentiles (numpy-style). None when empty."""
    if not samples:
        return {f"p{p}": None for p in ps}
    ordered = sorted(samples)

    def _pct(p: float) -> float:
        pos = (p / 100.0) * (len(ordered) - 1)
        lo = int(pos)
        hi = min(lo + 1, len(ordered) - 1)
        frac = pos - lo
        return ordered[lo] + frac * (ordered[hi] - ordered[lo])

    return {f"p{p}": round(_pct(p), 1) for p in ps}


def malformed_rate(validation_error_counts: Sequence[int], total: int) -> float:
    """Fraction of results carrying validation errors (0.0 when total == 0)."""
    if total <= 0:
        return 0.0
    return round(sum(1 for c in validation_error_counts if c > 0) / total, 4)
