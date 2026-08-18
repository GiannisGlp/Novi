# 18 — Stage-1 Durable State Storage ADR

**Decision ID:** ADR-DATA-001  
**Status:** PROPOSED — NOT YET ADOPTED  
**Owner:** System Architecture  
**Scope:** Novi single-device / Stage-1 durable state  
**Depends on:** `06_107_DURABLE_STATE_EVENT_LOG_EXECUTION_SEMANTICS.md`, `07_108_TRANSACTIONS_CONCURRENCY_CONSISTENCY_AND_CONFLICT_RESOLUTION.md`, `16_CANONICAL_SYSTEM_CONTRACTS.md`, `17_CONTRACT_IMPLEMENTATION_AND_SCHEMA_STANDARD.md`

---

## 1. Purpose

Define the decision process and candidate baseline for Novi's first local durable-state implementation without prematurely committing Novi to a distributed database, cloud service, vector database, or NVIDIA-specific storage technology.

This ADR deliberately does **not** decide the final production backend until the required benchmark and fault-injection evidence exists.

---

## 2. Problem

Novi requires durable local state for at least:

- event history;
- operational state;
- checkpoints;
- recovery metadata;
- contract/version metadata;
- provenance references;
- configuration state;
- memory/knowledge indexes where the selected architecture permits local storage.

The Stage-1 backend must support the semantic guarantees already defined by documents 107 and 108 without becoming the semantic authority itself.

---

## 3. Constraints

The Stage-1 implementation should:

- run fully locally;
- operate offline;
- have no mandatory cloud dependency;
- support crash recovery;
- support atomic transactions;
- support explicit concurrency semantics;
- support deterministic backups/checkpoints;
- expose predictable failure behavior;
- be portable across development and edge environments;
- have a small operational footprint;
- preserve canonical contract/version metadata;
- support schema migrations;
- be observable and testable;
- avoid locking Novi's semantic architecture to one storage engine.

The initial robot is expected to be a single primary physical node, so distributed replication is not a Stage-1 requirement.

---

## 4. Candidate technologies

### Candidate A — SQLite

SQLite is the primary Stage-1 candidate because it is embedded, local, transactional and operationally simple. Its official documentation describes atomic transactions and crash/power-failure recovery, while WAL mode provides concurrent readers and a single serialized writer. https://sqlite.org/atomiccommit.html https://sqlite.org/wal.html

Relevant strengths:

- embedded;
- no separate database server;
- mature transactional semantics;
- single-file deployment;
- WAL mode;
- strong local portability;
- straightforward backup/recovery workflows;
- suitable for single-device Stage-1 architecture.

Known constraints:

- WAL requires participating processes to share the same host and does not work over a network filesystem;
- there is one writer at a time in normal WAL operation;
- high-write/concurrent workloads may require careful batching and scheduling;
- SQLite must not be assumed to satisfy future multi-node requirements.

The SQLite documentation explicitly states that WAL permits readers and writers to proceed concurrently but still serializes writers. https://sqlite.org/wal.html

### Candidate B — RocksDB

RocksDB is a serious alternative if Novi's workload becomes dominated by very high write throughput, key-value access, large append-heavy state, or storage patterns better suited to an embedded LSM engine.

Its documentation describes WAL-based crash recovery and transaction support with pessimistic and optimistic concurrency control. https://github.com/facebook/rocksdb/wiki/Write-Ahead-Log-%28WAL%29 https://github.com/facebook/rocksdb/wiki/Transactions

Relevant strengths:

- embedded;
- high-throughput key-value workloads;
- WAL recovery;
- optimistic/pessimistic transaction support;
- column-family organization;
- good fit for append-heavy workloads.

Known constraints:

- significantly more operational/engineering complexity than SQLite for a relational semantic state layer;
- application-level schema/index/query semantics are more involved;
- relational queries and ad-hoc state inspection are less convenient;
- it must not be selected merely for theoretical throughput.

### Candidate C — PostgreSQL

PostgreSQL remains a future candidate if Novi evolves into a multi-process/multi-node architecture where a database server, richer relational queries, stronger concurrent workloads and network access become justified.

It is **not the default Stage-1 candidate** because the initial requirement is local embedded operation with minimal infrastructure.

### Candidate D — specialized/vector databases

Vector databases are **not durable-state authorities**.

They may become specialized indexes for retrieval, but they must remain projections of canonical Memory/Knowledge state.

They are therefore outside the Stage-1 durable-state authority decision.

---

## 5. Preliminary decision

**PROPOSED:** benchmark SQLite as the default Stage-1 candidate.

This is a candidate decision, not an adoption.

The architecture should proceed under the following assumption until evidence disproves it:

```text
canonical semantic state
        ↓
SQLite-backed Stage-1 local persistence candidate
        ↓
WAL + transactional state transitions
        ↓
checkpoint / backup / recovery
```

RocksDB and PostgreSQL remain explicit alternatives until the benchmark gate is closed.

---

## 6. What the database does NOT own

The storage engine does not own:

- meaning of `MemoryRecord`;
- meaning of `KnowledgeRecord`;
- world-model semantics;
- authorization semantics;
- safety semantics;
- cognitive state semantics;
- autonomy semantics;
- contract version meaning;
- provenance policy;
- privacy policy.

Those remain owned by the appropriate canonical architecture domains.

---

## 7. Required Stage-1 storage boundaries

The implementation should separate at minimum:

```text
CANONICAL EVENTS
CURRENT DURABLE STATE
CHECKPOINTS
PROVENANCE / LINEAGE
CONTRACT METADATA
CONFIGURATION
RECOVERY METADATA
DERIVED INDEXES
```

Derived indexes must be rebuildable from authoritative state where practical.

---

## 8. Event/state relationship

The Stage-1 implementation must preserve the semantics of document 107:

```text
EVENT
  ↓
VALIDATE
  ↓
STATE TRANSITION
  ↓
COMMIT
  ↓
CHECKPOINT / INDEX
```

The implementation must make it possible to determine which events produced a durable state revision where the relevant domain requires reconstruction.

---

## 9. Transaction requirements

The Stage-1 backend must demonstrate:

- atomic commit;
- rollback;
- optimistic conflict detection where required;
- idempotent retry support;
- stale-version rejection;
- explicit transaction boundaries;
- durable commit semantics;
- crash recovery;
- unknown external-side-effect outcomes.

SQLite's official documentation confirms atomic transaction behavior and WAL semantics; these properties still require Novi-specific integration tests. https://sqlite.org/atomiccommit.html https://sqlite.org/wal.html

---

## 10. Consistency mapping gate

Before adoption, every Stage-1 state class must be assigned the consistency class defined by document 108.

At minimum evaluate:

| State | Candidate requirement |
|---|---|
| telemetry cache | C0/C1 |
| derived search index | C1/C2 |
| semantic memory metadata | C2/C3 |
| event log | C3+ according to event semantics |
| configuration | C3/C4 as required |
| authorization state | C4 or stronger where required |
| safety state | governed independently; storage cannot replace safety authority |
| checkpoint metadata | C3+ |
| migration metadata | C3+ |

These are **benchmark/test starting points**, not final guarantees.

---

## 11. Required benchmark workload

The benchmark must use realistic Novi workloads rather than generic database benchmarks.

### Write workloads

- sensor-derived event ingestion;
- world-state updates;
- memory admission;
- provenance writes;
- checkpoint creation;
- configuration updates.

### Read workloads

- current-state reads;
- recent-event queries;
- entity lookup;
- provenance lookup;
- recovery reconstruction;
- memory-context retrieval.

### Mixed workload

Simultaneous:

```text
perception writes
+
world-state updates
+
memory reads
+
autonomy queries
+
checkpointing
```

---

## 12. Benchmark metrics

Record at minimum:

- p50/p95/p99 write latency;
- p50/p95/p99 read latency;
- transactions/second;
- sustained event throughput;
- checkpoint latency;
- recovery time;
- database growth rate;
- WAL growth;
- CPU usage;
- RAM usage;
- storage I/O;
- power impact on edge hardware where measurable;
- thermal impact where measurable;
- contention rate;
- conflict/retry rate.

Measurements must identify hardware, OS, runtime, database version and configuration.

---

## 13. Fault-injection tests

Before adoption, test at minimum:

- process crash during transaction;
- process crash immediately after commit;
- power-loss simulation during write;
- interrupted checkpoint;
- corrupted/incomplete temporary state;
- stale transaction retry;
- duplicate event submission;
- concurrent conflicting updates;
- storage-full condition;
- permission failure;
- malformed schema migration;
- backup/restore interruption.

The recovery result must be classified as:

```text
COMMITTED
ROLLED_BACK
RECOVERABLE_UNKNOWN
CORRUPTED
UNSAFE
```

No ambiguous outcome may be silently treated as success.

---

## 14. Migration requirements

The storage abstraction must permit migration without changing canonical semantics.

Migration must preserve:

- contract IDs;
- schema versions;
- event IDs;
- state revisions;
- provenance;
- temporal semantics;
- privacy classifications;
- deletion/tombstone semantics.

A database migration must be replayable and verifiable.

---

## 15. Backup and recovery

Stage-1 backup must define:

```text
what is backed up
when
where
how integrity is verified
how restoration is tested
how schema versions are handled
how WAL/checkpoint state is handled
```

For SQLite WAL deployments, the WAL is part of persistent state while connections are active and must be handled correctly during copy/backup procedures. https://sqlite.org/wal.html

---

## 16. Security

The storage layer must support:

- filesystem permissions;
- secrets separation;
- encryption strategy where required;
- integrity verification;
- audit metadata;
- privacy classifications;
- controlled export/backup.

Encryption requirements belong to the security architecture; the storage ADR only evaluates implementation compatibility.

---

## 17. Privacy

Storage selection must not bypass Memory/Knowledge privacy requirements.

Retention, erasure, dependency-aware deletion and training-data boundaries remain governed by the privacy/data-lifecycle architecture.

---

## 18. Exit criteria for adoption

SQLite may be **ADOPTED** only if benchmark and fault-injection evidence demonstrates that it satisfies all Stage-1 requirements within measured resource budgets.

Otherwise:

```text
SQLite fails requirement
        ↓
identify failing workload
        ↓
benchmark alternative
        ↓
RocksDB / PostgreSQL / other candidate
        ↓
ADR revision
```

No technology may be selected because it is familiar or popular.

---

## 19. Decision status

Current status:

```text
PROPOSED
  ↓
BENCHMARK REQUIRED
  ↓
FAULT INJECTION REQUIRED
  ↓
RESOURCE VALIDATION REQUIRED
  ↓
REVIEW
  ↓
ADOPT / REJECT / DEFER
```

**SQLite is currently a candidate, not an adopted Novi technology.**

---

## 20. Sources

Primary technology references used for this ADR:

- SQLite atomic commit: https://sqlite.org/atomiccommit.html
- SQLite WAL: https://sqlite.org/wal.html
- SQLite isolation/concurrency: https://sqlite.org/isolation.html
- RocksDB WAL: https://github.com/facebook/rocksdb/wiki/Write-Ahead-Log-%28WAL%29
- RocksDB transactions: https://github.com/facebook/rocksdb/wiki/Transactions

These sources establish technology capabilities. Novi adoption still requires Novi-specific evidence.

---

## 21. Final rule

> **Stage 1 should prefer the simplest local durable-state technology that demonstrably satisfies Novi's measured workload, recovery, consistency and resource requirements.**
