# 41 — ARCH-CLOSE-003 SQLite Recovery Validation

**Status:** P0 execution gate  
**Authority:** System Architecture  
**Closure item:** ARCH-CLOSE-003 — Stage-1 durable storage

## Objective

Validate the SQLite candidate against the recovery/correctness requirements that remain open after the Mac performance benchmark.

## Current evidence

`storage-benchmark-result.json` demonstrates a strong SQLite Mac baseline: write p99 0.121 ms, read p99 0.00417 ms, 10,000 events, zero conflicts, and successful durability/reopen validation.

The benchmark itself records that fault injection, migration, backup/restore and fuller concurrency testing remain open.

## Validation harness

Run:

```bash
python3 scripts/sqlite_recovery_validation.py --output sqlite-recovery-validation-result.json
```

The harness validates:

- committed data survives close/reopen;
- uncommitted work is rolled back;
- duplicate event IDs are rejected without changing committed state;
- stale revision attempts are rejected;
- checkpoint followed by reopen preserves state;
- SQLite online backup restores committed state;
- malformed migration failure does not silently alter the source state.

## Interpretation

A passing harness is **necessary but not sufficient** for final ARCH-CLOSE-003 closure. It does not emulate every arbitrary process kill or storage-device failure.

Remaining environment-level tests are required for:

- storage-full condition;
- permission failure;
- concurrent conflict stress;
- interrupted backup;
- arbitrary process termination during commit/checkpoint;
- migration against real Novi contract schemas.

## Gate

SQLite can be recommended as the Stage-1 backend only when correctness, recovery, migration, backup/restore, concurrency governance and resource requirements all pass. The simplest passing candidate remains preferred.
