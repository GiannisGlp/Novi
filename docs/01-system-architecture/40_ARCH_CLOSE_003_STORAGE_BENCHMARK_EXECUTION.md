# 40 — ARCH-CLOSE-003 Storage Benchmark Execution

**Status:** P0 execution procedure  
**Authority:** System Architecture  
**Closure item:** ARCH-CLOSE-003 — Stage-1 durable storage

## Objective

Produce the first real Novi storage evidence on the Mac development host. This is an evidence run, not an architecture decision by assumption.

## Run

From the repository root:

```bash
python3 scripts/storage_benchmark.py --iterations 10000 --readers 4 --output storage-benchmark-result.json
```

The command records the host/runtime environment and measures the SQLite baseline using Novi-shaped event/state transactions. It also records whether RocksDB/PostgreSQL tooling is available.

## First decision point

SQLite may be recommended as the Stage-1 authority only after the complete closure evidence demonstrates:

- durable commit/reopen correctness;
- acceptable p50/p95/p99 latency;
- acceptable throughput;
- governed concurrency/conflict behavior;
- recovery correctness;
- migration correctness;
- backup/restore correctness;
- acceptable resource envelope;
- acceptable operational complexity.

The first script run intentionally does **not** close these additional gates. It establishes the Mac baseline.

## Evidence handling

Do not hand-edit benchmark numbers. Commit the generated result only after verifying that it contains the actual machine identity, Novi revision and benchmark revision. If the result contains sensitive host information, retain the full result locally and commit a redacted evidence record instead.

## Interpretation rule

A fast SQLite result does not prove SQLite is universally superior. It answers a narrower question: whether the embedded Stage-1 candidate is comfortably within Novi's measured Mac workload envelope. The final adoption decision remains governed by the full ARCH-CLOSE-003 specification.

## Current state

`ARCH-CLOSE-003 = OPEN / empirical evidence pending.`
