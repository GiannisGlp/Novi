# 40 — ARCH-CLOSE-003 Storage Benchmark Execution

**Status:** P0 evidence record — SQLite selected for Stage 1, residual fault testing open  
**Authority:** System Architecture  
**Closure item:** ARCH-CLOSE-003 — Stage-1 durable storage

## Objective

Produce and preserve real Novi storage evidence on the Mac development host. This is an evidence-driven architecture decision.

## Performance evidence

The committed `storage-benchmark-result.json` establishes the Mac SQLite baseline using Novi-shaped event/state transactions:

- write p50: 0.033 ms;
- write p95: 0.0515 ms;
- write p99: 0.121 ms;
- read p50: 0.00271 ms;
- read p95: 0.00329 ms;
- read p99: 0.00417 ms;
- 10,000 events;
- zero conflicts;
- successful durability/reopen validation.

## Recovery/correctness evidence

The committed `sqlite-recovery-validation-result.json` reports **PASS** for all seven executed checks:

1. commit → reopen persistence;
2. rollback of uncommitted transaction;
3. duplicate-event rejection;
4. stale-revision rejection;
5. checkpoint → reopen integrity;
6. backup → restore;
7. malformed-migration isolation.

The recovery run used SQLite 3.53.4 and Python 3.14.6 and completed at `2026-08-19T05:27:07Z`. fileciteturn389file0

## Stage-1 decision

**SQLite is selected as Novi's Stage-1 durable-state backend.**

This decision is based on measured performance plus the executed correctness/recovery gate. There is currently no measured requirement that justifies adding RocksDB or PostgreSQL complexity for Stage 1.

This is a Stage-1 decision, not a claim that SQLite will satisfy every future distributed, high-volume or robot-scale workload.

## Residual validation

ARCH-CLOSE-003 remains technically open for the following environment-level evidence:

- arbitrary live-process termination during commit/checkpoint;
- storage-full behavior;
- permission/failure behavior;
- deeper concurrent conflict stress;
- interrupted backup testing;
- long-duration growth/soak against the final Novi workload;
- final robot hardware resource validation.

The recovery harness explicitly records these limitations. fileciteturn389file0

## Evidence handling

Benchmark numbers are generated artifacts and must not be hand-edited. Evidence should retain the exact Novi revision, benchmark revision, host/runtime identity and configuration where appropriate.

## Interpretation rule

A fast SQLite result alone does not prove SQLite is universally superior. The current adoption is justified because the measured Stage-1 workload is comfortably within the Mac envelope and the executed recovery/correctness checks pass. Remaining fault and robot-environment evidence is tracked explicitly rather than hidden.
