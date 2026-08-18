# 27 — ARCH-CLOSE-003 Stage-1 Storage Benchmark & Fault-Injection Specification

**Status:** P0 validation specification
**Priority:** P0
**Authority:** System Architecture
**Closure item:** ARCH-CLOSE-003 — Stage-1 durable storage
**Depends on:** `18_STAGE_1_DURABLE_STATE_STORAGE_ADR.md`, `06_107_DURABLE_STATE_EVENT_LOG_EXECUTION_SEMANTICS.md`, `07_108_TRANSACTIONS_CONCURRENCY_CONSISTENCY_AND_CONFLICT_RESOLUTION.md`, `26_ARCH_CLOSE_002_CONSISTENCY_STATE_CLASS_MATRIX.md`

## 1. Purpose

This document defines the executable evidence required before Novi adopts a Stage-1 durable storage backend.

The existing storage ADR intentionally leaves the decision **PROPOSED / NOT YET ADOPTED** and requires benchmark, fault-injection, recovery and resource evidence. This document turns that requirement into a reproducible validation gate.

## 2. Decision rule

No storage technology becomes architectural truth merely because it is convenient for the prototype.

The selected backend must demonstrate that it satisfies Novi's measured Stage-1 requirements for:

- durable event/state persistence;
- transactional integrity;
- consistency guarantees;
- recovery after failure;
- predictable concurrency behavior;
- backup/restore;
- schema migration;
- resource limits;
- offline/local operation.

## 3. Candidate set

The initial benchmark compares:

1. **SQLite** — primary embedded candidate;
2. **RocksDB** — embedded high-throughput alternative;
3. **PostgreSQL** — server-based alternative retained as a control/future candidate.

Vector databases and retrieval indexes are excluded from the durable-state authority comparison because they are projections rather than semantic authorities.

## 4. Test environment

Every benchmark result MUST record:

```text
host_id
OS/version
CPU
GPU
RAM/unified-memory size
storage device/filesystem
runtime/language version
database version
configuration
Novi revision
schema/contract versions
benchmark revision
```

Results from different environments must not be compared without declaring the environmental difference.

## 5. Novi workload model

The benchmark must use representative Novi operations rather than generic database operations.

### 5.1 Event ingestion

Generate realistic `EventEnvelope` records containing:

- event identity;
- event type;
- timestamps;
- producer/actor context;
- subject references;
- causation/correlation identifiers;
- state revision;
- payload;
- provenance references;
- schema metadata;
- integrity metadata.

Measure append latency and sustained throughput.

### 5.2 State transition

Execute:

```text
read expected revision
→ validate
→ append event(s)
→ commit
→ materialize state
```

Verify that externally visible committed state cannot precede the configured durable commit boundary.

### 5.3 Mixed workload

Run concurrent workloads representing:

```text
perception/event writes
world-state updates
memory reads
knowledge/provenance reads
autonomy queries
checkpointing
```

The test must expose writer contention and queue/backpressure behavior.

### 5.4 Recovery workload

Create a known event history, checkpoint it, append additional events, terminate the process at controlled points, restart, recover and verify the reconstructed state against the expected state hash/revision.

## 6. Required metrics

Collect at minimum:

| Metric | Required |
|---|---|
| write p50/p95/p99 | Yes |
| read p50/p95/p99 | Yes |
| event throughput | Yes |
| transaction throughput | Yes |
| writer contention | Yes |
| retry/conflict rate | Yes |
| checkpoint latency | Yes |
| recovery time | Yes |
| storage growth | Yes |
| WAL/log growth | Yes |
| CPU | Yes |
| RAM | Yes |
| storage I/O | Yes |
| peak queue depth | Yes |
| backup duration | Yes |
| restore duration | Yes |

Thermal/power measurements should be collected on the target edge hardware when available.

## 7. Correctness gates

Performance alone cannot produce adoption.

The backend fails the gate if any test demonstrates:

- lost committed event;
- duplicate logical state transition caused by retry;
- stale state accepted where rejection is required;
- impossible state revision;
- broken provenance reference;
- corruption after a supported failure mode;
- false success after an unknown external-side-effect boundary;
- inability to restore an internally consistent state;
- silent semantic change during migration.

## 8. Fault-injection matrix

At minimum execute:

| Failure | Expected classification |
|---|---|
| crash before commit | ROLLED_BACK |
| crash during commit | COMMITTED or ROLLED_BACK, never ambiguous silently |
| crash immediately after commit | COMMITTED |
| interrupted checkpoint | recover from prior valid state/history |
| duplicate event submission | idempotent logical result |
| stale transaction | explicit conflict/rejection |
| concurrent conflicting update | deterministic governed conflict outcome |
| storage-full condition | governed failure; no silent corruption |
| permission failure | explicit failure |
| malformed migration | migration rejected/rolled back |
| interrupted backup | invalid/incomplete backup detectable |
| restore failure | explicit failure; source remains protected |

Where physical power-loss testing is unsafe or unavailable on development hardware, use an explicitly documented crash simulation and schedule physical validation for the target device.

## 9. Recovery verification

Every recovery test must verify:

```text
last durable event position
state revision
state integrity/hash
provenance reachability
checkpoint validity
schema/reducer compatibility
absence of impossible duplicate transitions
```

Recovery must distinguish at least:

```text
COMMITTED
ROLLED_BACK
RECOVERABLE_UNKNOWN
CORRUPTED
UNSAFE
```

`UNKNOWN` must never be converted to `SUCCESS` without reconciliation evidence.

## 10. Backup and restore gate

The implementation must demonstrate:

1. creation of a consistent backup/checkpoint;
2. integrity verification;
3. restoration into an isolated environment;
4. state/event verification after restore;
5. compatibility with the recorded schema/reducer versions;
6. repeatability of the restore procedure.

A backup is not valid merely because a file was copied successfully.

## 11. Migration gate

At least one forward-compatible schema/state migration and one intentionally incompatible migration must be tested.

The migration test must verify preservation of:

- event IDs;
- state revisions;
- canonical contract IDs;
- semantic versions;
- provenance;
- timestamps and temporal meaning;
- privacy classification;
- deletion/tombstone semantics.

## 12. Resource-budget gate

Results must be compared with the resource budgets established under ARCH-CLOSE-007.

Until measured budgets exist, benchmark reports must label resource thresholds as provisional rather than claiming architecture closure.

A backend that meets correctness requirements but violates the target runtime resource envelope does not pass adoption.

## 13. Reproducibility

Benchmark code, fixtures, configuration and result metadata must be version controlled.

A result record must identify:

```text
benchmark_id
candidate
revision
environment
configuration
workload
sample_count
metrics
failure_tests
result
limitations
```

Raw measurements must be retained where practical so summary statistics can be independently recomputed.

## 14. Adoption decision

The benchmark produces one of:

```text
ADOPT
REJECT
DEFER
```

### ADOPT

All mandatory correctness/recovery gates pass and measured resource/performance behavior is acceptable for Stage-1.

### REJECT

A mandatory requirement cannot be satisfied within the Stage-1 constraints.

### DEFER

Evidence is incomplete or the result is inconclusive; no architectural adoption occurs.

## 15. Required evidence artifact

The final closure evidence should be stored under a dedicated validation path and include:

- benchmark implementation;
- workload fixtures;
- fault-injection tests;
- raw results;
- summarized results;
- environment manifest;
- recovery verification output;
- backup/restore evidence;
- migration evidence;
- final ADR decision.

## 16. Closure criterion

ARCH-CLOSE-003 may be marked complete only when:

```text
ADR decision
    +
benchmark evidence
    +
fault-injection evidence
    +
recovery evidence
    +
backup/restore evidence
    +
resource validation
    +
review
    ↓
STAGE-1 STORAGE ADOPTED
```

Until then, `18_STAGE_1_DURABLE_STATE_STORAGE_ADR.md` remains **PROPOSED — NOT YET ADOPTED**.

## 17. Architectural invariant

> **The Stage-1 storage engine is an implementation of Novi's durability semantics; measured evidence, not familiarity or convenience, determines adoption.**
