# 39 — ARCH-CLOSE-003 Storage Validation Runbook

**Status:** P0 execution runbook
**Authority:** System Architecture
**Closure item:** ARCH-CLOSE-003 — Stage-1 durable storage
**Current decision:** No backend adopted yet

## 1. Objective

Turn the existing ARCH-CLOSE-003 benchmark specification into an executable, reproducible validation campaign on the Mac-first development environment.

The goal is not to prove that a particular database is universally best. The goal is to select the simplest backend that satisfies Novi's actual correctness, durability, recovery, concurrency and resource requirements.

## 2. Candidate policy

Benchmark the following candidates where their runtimes can be installed reproducibly:

1. SQLite — primary embedded candidate.
2. RocksDB — embedded high-throughput alternative.
3. PostgreSQL — server-based control/future candidate.

A candidate that cannot be reproduced on the Mac profile is recorded as **environmentally incompatible**, not silently excluded.

## 3. Novi workload

The benchmark must exercise Novi-shaped operations:

- EventEnvelope append;
- revisioned state transition;
- concurrent reads and writes;
- provenance lookup;
- checkpoint creation;
- recovery/replay;
- duplicate event submission;
- stale revision/conflict handling;
- backup and restore;
- schema migration.

Synthetic data is acceptable for the first run, provided the fixture schema matches the canonical Novi contracts.

## 4. Required environment record

Every run records:

```text
host
OS/version
CPU
GPU
RAM/unified memory
storage device/filesystem
runtime versions
candidate/version
configuration
Novi commit
schema/contract versions
benchmark revision
```

## 5. Required measurements

At minimum:

- write p50/p95/p99;
- read p50/p95/p99;
- event/transaction throughput;
- contention/conflict rate;
- checkpoint latency;
- recovery time;
- storage growth;
- WAL/log growth where applicable;
- CPU/RAM/I/O;
- backup and restore duration;
- failure-test outcomes.

## 6. Correctness gate

Performance does not compensate for correctness failure.

A candidate fails if it loses a committed event, accepts an invalid stale transition, silently corrupts state, breaks provenance, produces an unrecoverable supported failure, or silently changes semantics during migration.

## 7. Fault injection

The execution campaign must cover at least:

- crash before commit;
- crash during commit;
- crash immediately after commit;
- interrupted checkpoint;
- duplicate event submission;
- stale transaction;
- concurrent conflict;
- storage-full condition;
- permission failure;
- malformed migration;
- interrupted backup;
- restore failure.

The result must classify outcomes as `COMMITTED`, `ROLLED_BACK`, `RECOVERABLE_UNKNOWN`, `CORRUPTED`, or `UNSAFE` where applicable.

## 8. Adoption gate

A candidate can be recommended only when:

```text
correctness passes
+ recovery passes
+ migration passes
+ backup/restore passes
+ concurrency is governed
+ resource envelope is acceptable
+ Mac reproduction is documented
+ operational complexity is justified
```

The simplest passing candidate is preferred for Stage 1.

## 9. Evidence outputs

The campaign must produce:

- machine-readable benchmark results;
- human-readable benchmark report;
- failure-injection results;
- environment manifest;
- candidate comparison;
- adoption recommendation or explicit defer decision;
- remaining risks.

## 10. Closure rule

ARCH-CLOSE-003 remains **OPEN** until benchmark and recovery evidence exist. The specification and runbook alone do not close the workstream.
