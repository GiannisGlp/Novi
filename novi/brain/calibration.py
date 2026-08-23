"""Reasoning-calibration statistics (gap-audit plan Phase E2).

Measures whether the brain's stated confidence predicts correctness: a
well-calibrated reasoner that says 0.8 is right ~80% of the time.

Pure, deterministic statistics — Brier score and binned Expected Calibration
Error — with no external dependencies, so the calibration harness runs
offline in CI exactly like every other brain capability.
"""

from __future__ import annotations

from typing import Any, Iterable


def brier_score(pairs: Iterable[tuple[float, bool]]) -> float:
    """Mean squared error of confidence against outcome: lower is better (0..1)."""
    pairs = list(pairs)
    if not pairs:
        return 0.0
    total = sum((max(0.0, min(1.0, c)) - (1.0 if ok else 0.0)) ** 2 for c, ok in pairs)
    return total / len(pairs)


def calibration_bins(pairs: Iterable[tuple[float, bool]], *, n_bins: int = 10) -> list[dict[str, Any]]:
    """Bin confidences into ``n_bins`` equal-width buckets over [0, 1]."""
    pairs = [(max(0.0, min(1.0, c)), bool(ok)) for c, ok in pairs]
    width = 1.0 / n_bins
    bins: list[dict[str, Any]] = []
    for i in range(n_bins):
        lo, hi = i * width, (i + 1) * width
        members = [(c, ok) for c, ok in pairs if (lo <= c < hi) or (i == n_bins - 1 and c == hi)]
        count = len(members)
        avg_conf = sum(c for c, _ in members) / count if count else 0.0
        accuracy = sum(1 for _, ok in members if ok) / count if count else 0.0
        bins.append({
            "bin": i,
            "range": [round(lo, 4), round(hi, 4)],
            "count": count,
            "avg_confidence": round(avg_conf, 6),
            "accuracy": round(accuracy, 6),
        })
    return bins


def expected_calibration_error(pairs: Iterable[tuple[float, bool]], *, n_bins: int = 10) -> float:
    """ECE: weighted |avg_confidence − accuracy| across bins (0 perfect .. 1 worst)."""
    pairs = list(pairs)
    if not pairs:
        return 0.0
    bins = calibration_bins(pairs, n_bins=n_bins)
    total = len(pairs)
    return sum(b["count"] / total * abs(b["avg_confidence"] - b["accuracy"]) for b in bins)


def calibration_report(pairs: Iterable[tuple[float, bool]], *, n_bins: int = 10) -> dict[str, Any]:
    """One auditable object: Brier, ECE, per-bin table."""
    rows = list(pairs)
    well_formed = [(max(0.0, min(1.0, c)), bool(ok)) for c, ok in rows]
    return {
        "samples": len(well_formed),
        "brier": round(brier_score(well_formed), 6),
        "ece": round(expected_calibration_error(well_formed, n_bins=n_bins), 6),
        "bins": calibration_bins(well_formed, n_bins=n_bins),
    }
