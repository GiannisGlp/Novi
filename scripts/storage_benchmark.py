#!/usr/bin/env python3
"""Run the Novi Stage-1 storage benchmark on the local development host.

The benchmark is intentionally local: its evidence must describe the machine
where Novi will actually run. SQLite is implemented with the Python stdlib.
RocksDB/PostgreSQL are reported as optional candidates until their adapters are
added/configured; this prevents an unavailable dependency from being mistaken
for a failed storage backend.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sqlite3
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
        "processor": platform.processor(),
        "python": platform.python_version(),
        "sqlite": sqlite3.sqlite_version,
        "filesystem": "unknown; record manually if material",
        "novi_revision": os.environ.get("NOVI_REVISION", "unknown"),
    }


def sqlite_benchmark(iterations: int, readers: int) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="novi-storage-") as temp:
        db = Path(temp) / "novi.sqlite3"
        con = sqlite3.connect(db)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=FULL")
        con.execute("PRAGMA foreign_keys=ON")
        con.execute(
            "CREATE TABLE events (event_id TEXT PRIMARY KEY, revision INTEGER NOT NULL, "
            "event_type TEXT NOT NULL, payload TEXT NOT NULL, provenance TEXT NOT NULL)"
        )
        con.execute("CREATE TABLE state (key TEXT PRIMARY KEY, revision INTEGER NOT NULL, value TEXT NOT NULL)")
        con.commit()

        writes: list[float] = []
        reads: list[float] = []
        conflicts = 0

        for i in range(iterations):
            started = time.perf_counter()
            try:
                con.execute("BEGIN IMMEDIATE")
                revision = i + 1
                con.execute(
                    "INSERT INTO events VALUES (?, ?, ?, ?, ?)",
                    (f"evt-{i}", revision, "world_state_change", '{"value":1}', "benchmark"),
                )
                con.execute(
                    "INSERT INTO state(key, revision, value) VALUES ('world', ?, '{\"value\":1}') "
                    "ON CONFLICT(key) DO UPDATE SET revision=excluded.revision, value=excluded.value",
                    (revision,),
                )
                con.commit()
            except Exception:
                con.rollback()
                conflicts += 1
                raise
            writes.append((time.perf_counter() - started) * 1000)

            started = time.perf_counter()
            row = con.execute("SELECT revision, value FROM state WHERE key='world'").fetchone()
            if row is None:
                raise RuntimeError("state read returned no row")
            reads.append((time.perf_counter() - started) * 1000)

        con.close()

        # Re-open to prove durable state survives process/connection close.
        verify = sqlite3.connect(db)
        count = verify.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        revision = verify.execute("SELECT revision FROM state WHERE key='world'").fetchone()[0]
        verify.close()

        return {
            "candidate": "sqlite",
            "version": sqlite3.sqlite_version,
            "iterations": iterations,
            "readers_requested": readers,
            "write_ms": {"p50": percentile(writes, .50), "p95": percentile(writes, .95), "p99": percentile(writes, .99), "mean": statistics.mean(writes)},
            "read_ms": {"p50": percentile(reads, .50), "p95": percentile(reads, .95), "p99": percentile(reads, .99), "mean": statistics.mean(reads)},
            "event_count": count,
            "final_revision": revision,
            "conflicts": conflicts,
            "durability_reopen_pass": count == iterations and revision == iterations,
            "db_size_bytes": db.stat().st_size,
        }


def candidate_availability() -> dict[str, object]:
    return {
        "sqlite": {"available": True, "reason": "Python standard library"},
        "rocksdb": {
            "available": shutil.which("ldb") is not None,
            "reason": "RocksDB CLI (ldb) detected" if shutil.which("ldb") else "Install/configure a reproducible RocksDB adapter before comparison",
        },
        "postgresql": {
            "available": shutil.which("psql") is not None,
            "reason": "psql detected" if shutil.which("psql") else "Install/configure a reproducible PostgreSQL instance before comparison",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=10_000)
    parser.add_argument("--readers", type=int, default=4)
    parser.add_argument("--output", type=Path, default=Path("novi/storage-benchmark-result.json"))
    args = parser.parse_args()

    if args.iterations <= 0:
        parser.error("--iterations must be positive")

    result = {
        "benchmark_id": "ARCH-CLOSE-003-MAC-001",
        "benchmark_revision": "1.0.0",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": environment(),
        "candidate_availability": candidate_availability(),
        "sqlite": sqlite_benchmark(args.iterations, args.readers),
        "limitations": [
            "This first harness measures the local SQLite baseline only.",
            "RocksDB/PostgreSQL are not comparable until reproducible adapters and configurations are provided.",
            "Power/thermal measurements require the target hardware and are not inferred from this Mac run.",
            "Fault-injection, migration and backup/restore remain separate closure gates.",
        ],
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"\nWrote evidence: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
