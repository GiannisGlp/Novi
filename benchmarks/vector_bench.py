#!/usr/bin/env python3
"""Vector retrieval benchmark for the Novi Mac Brain (gap-audit plan Phase E2).

Seeds a durable memory store with N records, then measures the latency
distribution of indexed (FTS) and semantic (embedding) retrieval. Acceptance:
p99 retrieve < 50 ms at 5k records on the local development host.

Results are written to ``mac_test_results/vector_bench/<run-id>/result.json``
following the same evidence convention as scripts/storage_benchmark.py.

Usage:
    .venv/bin/python benchmarks/vector_bench.py            # 5k records
    .venv/bin/python benchmarks/vector_bench.py --records 500
"""
from __future__ import annotations

import argparse
import contextlib
import json
import platform
import statistics
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TARGET_P99_MS = 50.0

WORDS = ("cup", "plant", "kitchen", "table", "window", "door", "lamp", "chair",
         "room", "morning", "water", "book", "light", "shadow", "coffee", "rain")


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * p))))
    return ordered[index]


def environment() -> dict[str, str]:
    return {
        "host": platform.node(),
        "os": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
    }


def _seed_sentence(i: int) -> str:
    w1 = WORDS[i % len(WORDS)]
    w2 = WORDS[(i * 7 + 3) % len(WORDS)]
    w3 = WORDS[(i * 13 + 1) % len(WORDS)]
    return f"the {w1} was {w2} beside the {w3} in cycle {i}"


def run_vector_bench(records: int = 5000, queries: int = 200) -> dict[str, object]:
    """Seed, query, and score the durable store. Deterministic content."""
    from novi.brain.storage import DurableMemoryStore

    fts_latencies: list[float] = []
    sem_latencies: list[float] = []

    with tempfile.TemporaryDirectory(prefix="novi-vector-bench-") as temp:
        store = DurableMemoryStore(Path(temp) / "bench.sqlite3")
        seed_start = time.perf_counter()
        for i in range(records):
            store.admit(
                memory_type="perception",
                content=_seed_sentence(i),
                confidence=0.6 + (i % 4) * 0.1,
                verification_status="verified",
                privacy_class="public",
                provenance={"source": "benchmark", "memory_class": "episodic"},
                entity_refs=(WORDS[i % len(WORDS)],),
                temporal_context={"cycle": i},
            )
        seed_s = time.perf_counter() - seed_start

        query_terms = [WORDS[(i * 5) % len(WORDS)] for i in range(queries)]
        for term in query_terms:
            start = time.perf_counter()
            store.retrieve_indexed(term, limit=5)
            fts_latencies.append((time.perf_counter() - start) * 1000.0)

        for term in query_terms[: max(1, queries // 2)]:
            start = time.perf_counter()
            store.retrieve_semantic(term, limit=5)
            sem_latencies.append((time.perf_counter() - start) * 1000.0)

    def dist(values: list[float]) -> dict[str, float]:
        if not values:
            return {"n": 0}
        return {
            "n": len(values),
            "mean_ms": round(statistics.fmean(values), 3),
            "p50_ms": round(percentile(values, 0.50), 3),
            "p95_ms": round(percentile(values, 0.95), 3),
            "p99_ms": round(percentile(values, 0.99), 3),
            "max_ms": round(max(values), 3),
        }

    overall_p99 = max(
        percentile(fts_latencies, 0.99) if fts_latencies else 0.0,
        percentile(sem_latencies, 0.99) if sem_latencies else 0.0,
    )
    return {
        "target": {"metric": "p99_retrieve_ms", "threshold": TARGET_P99_MS},
        "records_seeded": records,
        "seed_seconds": round(seed_s, 3),
        "indexed_retrieval": dist(fts_latencies),
        "semantic_retrieval": dist(sem_latencies),
        "overall_p99_ms": round(overall_p99, 3),
        "pass": bool(overall_p99 < TARGET_P99_MS),
        "environment": environment(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def persist(result: dict[str, object]) -> Path:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "mac_test_results" / "vector_bench" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "result.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    latest = ROOT / "mac_test_results" / "vector_bench" / "latest"
    if latest.is_symlink() or latest.exists():
        with contextlib.suppress(IsADirectoryError):
            latest.unlink()
    with contextlib.suppress(OSError):
        latest.symlink_to(out_dir.name)
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=int, default=5000)
    parser.add_argument("--queries", type=int, default=200)
    args = parser.parse_args()

    result = run_vector_bench(records=args.records, queries=args.queries)
    out_path = persist(result)
    status = "PASS" if result["pass"] else "FAIL"
    print(f"[{status}] vector bench: records={args.records} "
          f"p99={result['overall_p99_ms']}ms (target<{TARGET_P99_MS}ms)")
    print(f"results: {out_path}")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
