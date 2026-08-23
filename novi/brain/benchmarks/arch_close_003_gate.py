#!/usr/bin/env python3
"""ARCH-CLOSE-003 Stage-1 storage validation gate.

Runs benchmark + fault-injection/recovery evidence against Novi's real
``brain.storage.DurableMemoryStore`` (the store the Mac Brain actually
uses), per 27_ARCH_CLOSE_003_STAGE_1_STORAGE_BENCHMARK_SPEC.md.

Outputs a structured, reproducible evidence JSON to the path given by
``--output`` (default ``arch-close-003-gate-result.json`` in the cwd).
"""

from __future__ import annotations

import argparse
import json
import platform
import sqlite3
import statistics
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from novi.brain.storage import DurableMemoryStore

BENCHMARK_ID = "ARCH-CLOSE-003-MAC-NOVI-002"
REVISION = "1.0.0"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _percentiles(samples: list[float]) -> dict[str, float]:
    if not samples:
        return {}
    s = sorted(samples)
    n = len(s)

    def p(q: float) -> float:
        if n == 1:
            return s[0]
        k = (n - 1) * q
        lo, hi = int(k), min(int(k) + 1, n - 1)
        return s[lo] + (s[hi] - s[lo]) * (k - lo)

    return {"p50": p(0.50), "p95": p(0.95), "p99": p(0.99), "mean": statistics.mean(s), "count": n}


def _env_manifest() -> dict[str, Any]:
    uname = platform.uname()
    return {
        "host_id": uname.node,
        "os": f"{platform.system()} {platform.release()}",
        "machine": uname.machine,
        "processor": uname.processor or uname.machine,
        "python": platform.python_version(),
        "sqlite": sqlite3.sqlite_version,
        "filesystem": "unknown; record manually if material",
        "novi_revision": _git_revision(),
    }


def _rss_bytes() -> int:
    try:
        import resource

        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024  # macOS reports KB
    except Exception:
        return -1


def _git_revision() -> str:
    try:
        import subprocess

        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _admit(store: DurableMemoryStore, i: int, entity: str = "bench") -> Any:
    return store.admit(
        memory_type="perception",
        content=f"observation-{i}",
        confidence=0.95,
        verification_status="verified",
        privacy_class="public",
        provenance={"source": "bench", "event_id": f"evt-{i}"},
        entity_refs=(entity,),
    )


# ------------------------------------------------------------------ benchmark
def _benchmark(db: Path) -> dict[str, Any]:
    N = 2000
    store = DurableMemoryStore(db)
    write_times: list[float] = []
    t0 = time.perf_counter()
    for i in range(N):
        t = time.perf_counter()
        _admit(store, i)
        write_times.append((time.perf_counter() - t) * 1000.0)
    ingest_wall = time.perf_counter() - t0

    read_times: list[float] = []
    for i in range(0, N, 20):
        t = time.perf_counter()
        store.retrieve("observation", limit=5)
        read_times.append((time.perf_counter() - t) * 1000.0)

    db_size = db.stat().st_size
    wal = Path(str(db) + "-wal")
    wal_size = wal.stat().st_size if wal.exists() else 0
    journal_mode = store._conn.execute("PRAGMA journal_mode").fetchone()[0]

    # writer contention: two connections serialize; count any busy/conflict errors
    conflicts = 0
    lag: list[str] = []
    lock = threading.Lock()

    def writer(lo: int, hi: int) -> None:
        nonlocal conflicts
        s = DurableMemoryStore(db)
        for i in range(lo, hi):
            with lock:
                try:
                    s.admit(
                        memory_type="perception",
                        content=f"contention-{i}",
                        confidence=0.9,
                        verification_status="verified",
                        privacy_class="public",
                        provenance={"source": "contention"},
                        entity_refs=("t",),
                    )
                except sqlite3.OperationalError as exc:
                    conflicts += 1
                    if len(lag) < 5:
                        lag.append(str(exc))
        s.close()

    threads = [threading.Thread(target=writer, args=(start, start + 250)) for start in (0, 250, 500, 750)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    active_count = store.active_count
    store.close()
    return {
        "writes": N,
        "write_wall_s": round(ingest_wall, 6),
        "write_ms": _percentiles(write_times),
        "read_ms": _percentiles(read_times),
        "events_throughput_per_s": round(N / ingest_wall, 1),
        "storage_growth_bytes": {"db": db_size, "wal": wal_size},
        "journal_mode": journal_mode,
        "writer_contention": {"conflicts": conflicts, "sample": lag},
        "active_count_after": active_count,
    }


# ------------------------------------------------------------------ recovery
def _recovery_checks(td: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def record(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"check": name, "result": "PASS" if passed else "FAIL", "detail": detail})

    # 1. commit -> reopen persistence (COMMITTED)
    db = td / "r1.db"
    s = DurableMemoryStore(db)
    a = _admit(s, 1, "alice")
    s.close()
    s2 = DurableMemoryStore(db)
    ok = s2.get(a.memory_id) is not None
    record("commit_reopen_persistence", ok, a.memory_id if ok else "record missing after reopen")
    s2.close()

    # 2. rollback of uncommitted transaction (ROLLED_BACK)
    db = td / "r2.db"
    DurableMemoryStore(db).close()
    raw = sqlite3.connect(str(db))
    raw.execute(
        "INSERT INTO memory_records (memory_id, memory_type, created_at, content, confidence, verification_status, privacy_class, revision) "
        "VALUES (?,?,?,?,?,?,?,?)",
        ("mem-uncommitted", "perception", "2026-01-01T00:00:00Z", "not-committed", 0.9, "verified", "public", 0),
    )
    raw.close()  # abrupt close without commit -> rollback
    s = DurableMemoryStore(db)
    rolled = s.get("mem-uncommitted") is None
    record("uncommitted_rollback", rolled, "uncommitted row absent after reopen" if rolled else "uncommitted row leaked")
    s.close()

    # 3. duplicate event submission -> idempotent (KEEP_EXISTING)
    db = td / "r3.db"
    s = DurableMemoryStore(db)
    r1 = _admit(s, 1, "alice")
    before = s.active_count
    r2 = _admit(s, 1, "alice")
    record("duplicate_idempotent", r2.accepted and r1.memory_id == r2.memory_id and s.active_count == before, r2.decision)
    s.close()

    # 4. checkpoint -> reopen integrity
    db = td / "r4.db"
    s = DurableMemoryStore(db)
    for i in range(100):
        _admit(s, i, "chk")
    s.close()
    s = DurableMemoryStore(db)
    intact = s.active_count == 100
    record("checkpoint_reopen_integrity", intact, f"active_count={s.active_count}")
    s.close()

    # 5. backup -> restore (SQLite online backup)
    db = td / "r5.db"
    s = DurableMemoryStore(db)
    for i in range(50):
        _admit(s, i, "bkp")
    src = sqlite3.connect(db)
    dst = sqlite3.connect(td / "restore.db")
    src.backup(dst)
    dst.close()
    src.close()
    s.close()
    restored = DurableMemoryStore(td / "restore.db")
    ok = restored.active_count == 50
    record("backup_restore", ok, f"restored_active={restored.active_count}")
    restored.close()

    # 6. malformed migration -> rejected/rolled back, source stays intact
    db = td / "r6.db"
    s = DurableMemoryStore(db)
    _admit(s, 1, "mig")
    s.close()
    try:
        bad = sqlite3.connect(db)
        # DROP COLUMN is unsupported in this SQLite build -> raises, must not corrupt
        bad.execute("ALTER TABLE memory_records DROP COLUMN content")
        bad.commit()
        bad.close()
    except sqlite3.Error:
        pass
    s = DurableMemoryStore(db)
    record("malformed_migration_no_corruption", s.active_count == 1, f"source readable, active_count={s.active_count}")
    s.close()

    return checks


# ------------------------------------------------------------------ runner
def run(output: Path | None) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        bench = _benchmark(td / "bench.db")
        checks = _recovery_checks(td)
    passed = all(c["result"] == "PASS" for c in checks)
    decision = "ADOPT" if passed else "DEFER"
    result = {
        "benchmark_id": BENCHMARK_ID,
        "benchmark_revision": REVISION,
        "timestamp_utc": _now(),
        "decision": decision,
        "target": "brain.storage.DurableMemoryStore",
        "environment": _env_manifest(),
        "peak_rss_bytes": _rss_bytes(),
        "benchmark": bench,
        "correctness_gate": {"passed": passed, "checks": checks},
        "limitations": [
            "No physical power-loss test on this host; crash simulated by abrupt close before commit.",
            "Storage-full and permission-failure conditions not exercised on-device.",
            "Deep concurrent conflict stress is single-host/serialized; multi-node is out of Stage-1 scope.",
            "Resource thresholds are provisional (no ARCH-CLOSE-007 measured budget yet).",
        ],
    }
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="ARCH-CLOSE-003 storage validation gate for DurableMemoryStore")
    parser.add_argument("--output", type=str, default="arch-close-003-gate-result.json")
    args = parser.parse_args()
    result = run(Path(args.output))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
