#!/usr/bin/env python3
"""Collect Step-5 NVIDIA no-hardware experiment evidence (roadmap item 28).

Runs the three no-hardware NVIDIA experiments on the Mac with deterministic
mocks (Exp 1 context-aware reference resolution, Exp 2 skill contract,
Exp 3 NoviEpisode demo dataset + adapters), then writes an evidence record
into IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/ with:

  - one evidence file per experiment, each labeled with a validation evidence
    class (docs/01-system-architecture/10_ARCHITECTURE_VALIDATION_AND_TRACEABILITY.md
    E0-E5) — deterministic cross-component no-hardware tests are E2/E3; the
    epistemic status of episode *content* (OBSERVED/SIMULATED) is preserved
    separately so simulations never become facts;
  - commit_sha.txt and collection_time.txt (matching archive convention);
  - an INDEX.md subsection appended with one row per experiment.

No NVIDIA hardware, no CUDA/TensorRT, no ROS2 — these validate the architecture
seams the docs require on the Mac alone.

Usage:
    python scripts/mac/nvidia_evidence.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = ROOT / "IMPLEMENTATION_PLAN" / "EVIDENCE" / "mac"
INDEX = EVIDENCE_ROOT / "INDEX.md"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


# Validation evidence classes come from the experiment module itself
# (MAC_BRAIN.nvidia_experiments.VALIDATION_CLASS_BY_EXPERIMENT), labelling each
# run with E0-E5 per docs/01-system-architecture/10_ARCHITECTURE_VALIDATION_AND_TRACEABILITY.md.

def main() -> int:
    from MAC_BRAIN.nvidia_experiments import run_nvidia_experiments

    stamp = utc_stamp()
    dest = EVIDENCE_ROOT / stamp
    dest.mkdir(parents=True, exist_ok=True)

    results = run_nvidia_experiments()
    env = {
        "python": sys.version,
        "platform": sys.platform,
        "nvidia_hardware": False,
        "backend": "deterministic-mock",
        "note": "No-hardware Mac experiment; validates architecture seams only "
                "(PERFECTING_PLAN/09_GAP_ANALYSIS_NVIDIA_INTEGRATION.md).",
    }

    manifest_rows: list[dict] = []
    for r in results:
        cls = r.validation_class or "E2"
        record = {
            "run_id": f"{stamp}-{r.experiment_id}",
            "experiment_id": r.experiment_id,
            "name": r.name,
            "status": "PASS" if r.passed else "FAIL",
            "evidence_class": cls,
            "epistemic_class": r.evidence_class,  # OBSERVED/SIMULATED on episode content
            "input_config": env,
            "start_time": stamp,
            "metrics": {},
            "failures": [] if r.passed else [r.reason],
            "conclusion": r.reason,
            "evidence": r.evidence_file,
        }
        fname = f"{r.experiment_id}.json"
        (dest / fname).write_text(json.dumps(record, indent=2, default=str) + "\n")
        manifest_rows.append({
            "experiment_id": r.experiment_id,
            "file": fname,
            "passed": r.passed,
            "evidence_class": cls,
        })

    (dest / "manifest.json").write_text(json.dumps({
        "run_id": stamp,
        "experiment_count": len(results),
        "all_passed": all(r.passed for r in results),
        "evidence_classes": [r.validation_class or "E2" for r in results],
        "environment": env,
        "experiments": manifest_rows,
    }, indent=2) + "\n")

    (dest / "commit_sha.txt").write_text(git_sha() + "\n")
    (dest / "collection_time.txt").write_text(f"Collected UTC: {stamp}\n")

    # Append rows to the archive index.
    rows = []
    for r in results:
        cls = r.validation_class or "E2"
        fname = f"{r.experiment_id}.json"
        rows.append(
            f"| NVIDIA no-hardware {r.experiment_id} | `{stamp}/{fname}` | "
            f"{r.name} — [E-class {cls}] {'PASS' if r.passed else 'FAIL'}: {r.reason} |"
        )
    with INDEX.open("a", encoding="utf-8") as fh:
        fh.write("\n## Step 5 — NVIDIA no-hardware experiments (roadmap item 28)\n")
        fh.write("\n".join(rows) + "\n")

    print(f"Written {len(results)} experiment evidence records to {dest}")
    for r in results:
        cls = r.validation_class or "E2"
        print(f"  {r.experiment_id}: {'PASS' if r.passed else 'FAIL'} [evidence {cls}] {r.name}")
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
