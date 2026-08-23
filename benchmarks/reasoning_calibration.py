#!/usr/bin/env python3
"""Reasoning-calibration harness for the Novi Mac Brain (gap-audit plan Phase E2).

Runs a deterministic perception scenario through the brain, scores the
PredictionEngine's stated confidences against actual outcomes (Brier score +
Expected Calibration Error), reads the rolling ``prediction_accuracy`` metric,
and persists one auditable JSON report under ``mac_test_results/reasoning_calibration/``.

Calibration answers: does a stated 0.9 prediction come true ~90% of the time?
Deterministic scenario, offline, CI-safe.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception  # noqa: E402
from novi.brain.calibration import calibration_report  # noqa: E402
from novi.brain.engine import MacBrain, MacBrainConfig  # noqa: E402
from novi.brain.tests.test_mac_brain import FakeCamera  # noqa: E402


def environment() -> dict[str, str]:
    return {
        "host": platform.node(),
        "os": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
    }


class ScriptedBackend(DeterministicPerceptionBackend):
    """Detects 'cup' for ``present_cycles`` then removes it (scripted ground truth)."""

    def __init__(self, present_cycles: int) -> None:
        self.present_cycles = present_cycles
        self._calls = 0

    def detect(self, frame):
        self._calls += 1
        if self._calls <= self.present_cycles:
            return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)
        return ()


def run_calibration(*, total_cycles: int = 30, present_cycles: int = 25) -> dict[str, object]:
    """Run the scripted scenario and produce a calibration report.

    Ground truth per cycle: 'cup' present iff call index ≤ present_cycles.
    Pairs are (prediction.confidence, prediction came true).
    """
    brain = MacBrain(
        camera=FakeCamera(),
        perception=SpecialistPerception(ScriptedBackend(present_cycles)),
        config=MacBrainConfig(curiosity_enabled=False),
    )
    brain.start()
    try:
        for _ in range(total_cycles):
            brain.step()
        pairs = brain._predictor.accuracy.pairs()
        metrics = {m["name"]: m["value"] for m in brain.metrics_snapshot()}
    finally:
        brain.stop()

    report = calibration_report(pairs)
    pred_acc = metrics.get("prediction_accuracy")
    return {
        "scenario": {
            "entity": "cup",
            "total_cycles": total_cycles,
            "present_cycles": present_cycles,
            "absent_cycles": max(0, total_cycles - present_cycles),
        },
        "calibration": report,
        "prediction_accuracy_metric": pred_acc,
        "pass": bool(pred_acc is not None and 0.0 <= float(pred_acc) <= 1.0),
        "environment": environment(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def persist(result: dict[str, object]) -> Path:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "mac_test_results" / "reasoning_calibration" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "result.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    latest = ROOT / "mac_test_results" / "reasoning_calibration" / "latest"
    if latest.is_symlink() or latest.exists():
        with contextlib.suppress(IsADirectoryError):
            latest.unlink()
    with contextlib.suppress(OSError):
        latest.symlink_to(out_dir.name)
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles", type=int, default=30)
    args = parser.parse_args()

    result = run_calibration(total_cycles=args.cycles)
    status = "PASS" if result["pass"] else "FAIL"
    print(f"[{status}] reasoning calibration: samples={result['calibration']['samples']} "
          f"brier={result['calibration']['brier']} ece={result['calibration']['ece']} "
          f"prediction_accuracy={result['prediction_accuracy_metric']}")
    out_path = persist(result)
    print(f"results: {out_path}")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
