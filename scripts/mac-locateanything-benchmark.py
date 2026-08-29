#!/usr/bin/env python3
"""Real-model benchmark evidence run (plan Step 25/26).

Runs the versioned corpus against the REAL backends:
- baseline side: TorchvisionSSDLiteDetector on MPS (SSDLite320 MobileNetV3)
- grounding side: LocateAnything-3B on MPS (bf16, pinned revision)

Usage:  HF_HOME=~/.cache/novi/models/locateanything-hf \\
        .venv-locateanything/bin/python scripts/mac-locateanything-benchmark.py

Writes docs/07-locate-anything/evidence/benchmark-compare-<ts>.json and prints
the comparison summary. CI stand-in: novi/perception/tests/test_benchmark_compare.py.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
os.environ.setdefault("HF_HOME", os.path.expanduser("~/.cache/novi/models/locateanything-hf"))

from novi.perception.benchmark_corpus import BenchmarkCorpus  # noqa: E402
from novi.perception.benchmark_compare import compare_baseline_vs_grounding  # noqa: E402
from novi.perception.grounding import SpatialInferencePolicy  # noqa: E402
from novi.perception.locate_anything import LocateAnythingBackend  # noqa: E402
from novi.perception.locate_anything_runtime import LocateAnythingRuntime  # noqa: E402
from novi.perception.real_backends import TorchvisionPerceptionDetector  # noqa: E402

CORPUS = REPO_ROOT / "docs" / "07-locate-anything" / "benchmark" / "corpus-v1.json"


def main() -> int:
    corpus = BenchmarkCorpus.load(CORPUS)
    print(f"[corpus] {corpus.corpus_id} v{corpus.version} — {len(corpus.records)} records")

    detector = TorchvisionPerceptionDetector(device="mps")
    runtime = LocateAnythingRuntime()
    backend = LocateAnythingBackend()
    backend.attach_runtime(runtime)
    caps = backend.capabilities()
    print(f"[backend] grounding state={caps.state.value} device={caps.device}")

    started = time.perf_counter()
    report = compare_baseline_vs_grounding(
        corpus,
        detector,
        backend,
        SpatialInferencePolicy(),
        repo_root=REPO_ROOT,
    )
    wall = round(time.perf_counter() - started, 1)

    out_dir = REPO_ROOT / "docs" / "07-locate-anything" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"benchmark-compare-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(report.to_dict(), indent=2))

    print(f"[wall] {wall}s")
    print(f"[baseline  ssdlite]   {report.baseline}")
    print(f"[grounding locateany] {report.with_grounding}")
    print(f"[delta]               {report.delta}")
    print(f"[evidence] {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
