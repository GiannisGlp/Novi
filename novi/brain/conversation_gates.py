"""Release quality gates (plan 03 Phases 21, 28).

Evaluates a replay ``baseline.json`` against the plan's acceptance
thresholds. Thresholds are the plan's calibrated starting targets;
dimensions a run does not cover report UNMEASURED (never a silent
pass, never a false fail). Critical memory/perception failures are
release blockers at any aggregate score (plan §21: a single
catastrophic hallucinated memory blocks release).

Usage: ``conversation_gates check --evidence-dir <baseline-dir>``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# (gate id, kind, key, threshold, comparator). Kinds: dimension rate,
# critical-label absence, aggregate metric, overall pass.
DIMENSION_GATES: list[tuple[str, str, float]] = [
    ("context continuity >= 0.95", "Context continuity", 0.95),
    ("referent resolution >= 0.95", "Referent resolution", 0.95),
    ("memory retrieval >= 0.90", "Memory retrieval", 0.90),
    ("perception grounding >= 0.95", "Perception grounding", 0.95),
    ("capability honesty == 1.0", "Capability honesty", 1.0),
    ("correction recovery >= 0.95", "Correction handling", 0.95),
]

# Any occurrence blocks release regardless of aggregates.
CRITICAL_LABELS = (
    "MEMORY_HALLUCINATED",
    "HALLUCINATION",
    "FALSE_CAPABILITY",
    "PERCEPTION_IGNORED",
)

# Clarification budget: plan target <= 5% is for *unnecessary*
# questions; the measured rate includes necessary ones (C-050...), so
# the machine gate uses a calibrated ceiling and reports both.
CLARIFICATION_CEILING = 0.15


def _rate(cells: dict[str, Any], dimension: str) -> float | None:
    cell = cells.get(dimension)
    if not isinstance(cell, dict) or not cell.get("scenarios"):
        return None
    return float(cell.get("pass_rate", 0.0))


def evaluate_gates(baseline: dict[str, Any]) -> dict[str, Any]:
    """Evaluate gate verdicts for one baseline summary."""
    cells = baseline.get("by_dimension", {}) or {}
    labels = baseline.get("label_counts", {}) or {}
    metrics = baseline.get("metrics", {}) or {}
    totals = baseline.get("totals", {}) or {}
    gates: list[dict[str, Any]] = []

    for gate_id, dimension, threshold in DIMENSION_GATES:
        rate = _rate(cells, dimension)
        if rate is None:
            gates.append({"gate": gate_id, "status": "UNMEASURED",
                          "detail": f"no {dimension} scenarios in run"})
        else:
            gates.append({"gate": gate_id,
                          "status": "PASS" if rate >= threshold else "FAIL",
                          "detail": f"{rate:.3f} vs {threshold}"})
    critical = {label: int(labels.get(label, 0) or 0)
                for label in CRITICAL_LABELS if labels.get(label)}
    gates.append({
        "gate": "no critical memory/perception failures",
        "status": "PASS" if not critical else "FAIL",
        "detail": "clean" if not critical else str(critical),
    })
    clarification = metrics.get("clarification_rate")
    if clarification is None:
        gates.append({"gate": f"clarification rate <= {CLARIFICATION_CEILING}",
                      "status": "UNMEASURED", "detail": "no metrics in run"})
    else:
        gates.append({
            "gate": f"clarification rate <= {CLARIFICATION_CEILING}",
            "status": "PASS" if float(clarification) <= CLARIFICATION_CEILING else "FAIL",
            "detail": f"{clarification} vs {CLARIFICATION_CEILING}",
        })
    overall = totals.get("pass_rate")
    gates.append({
        "gate": "overall pass_rate == 1.0",
        "status": "PASS" if overall == 1.0 else "FAIL",
        "detail": f"pass_rate={overall}",
    })
    measured = [g for g in gates if g["status"] != "UNMEASURED"]
    return {
        "schema": "conversation-gates/v1",
        "git_sha": baseline.get("git_sha", ""),
        "timestamp": baseline.get("timestamp", ""),
        "model": baseline.get("model", ""),
        "gates": gates,
        "status": "PASS" if measured and all(g["status"] == "PASS" for g in measured) else "FAIL",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Release quality gates for conversation baselines (plan 03 Phases 21, 28)")
    parser.add_argument("command", choices=["check"])
    parser.add_argument("--evidence-dir", required=True,
                        help="baseline dir containing baseline.json")
    parser.add_argument("--out", default="",
                        help="write gates.json here (empty = stdout only)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    baseline = json.loads((Path(args.evidence_dir) / "baseline.json").read_text())
    verdict = evaluate_gates(baseline)
    if args.out:
        Path(args.out).write_text(json.dumps(verdict, indent=2))
    print(json.dumps(verdict, indent=2))
    return 0 if verdict["status"] == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
