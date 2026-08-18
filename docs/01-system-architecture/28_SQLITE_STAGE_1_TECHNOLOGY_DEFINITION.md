# 28 — SQLite Stage-1 Technology Definition

**Status:** Candidate baseline — adoption pending benchmark evidence  
**Priority:** P0  
**Authority:** System Architecture / ADR-DATA-001  
**Scope:** Novi Stage-1 local durable state

## 1. Purpose

Define exactly what Novi means by **SQLite** as its Stage-1 durable-state candidate. This document constrains the technology choice, runtime configuration, ownership boundary, and validation requirements without declaring SQLite adopted before the benchmark gate is satisfied.

## 2. Current upstream baseline

As of 2026-08-18, the official SQLite website identifies **SQLite 3.53.3**, released 2026-06-26, as the latest release. Novi must pin the exact SQLite version used by a tested runtime rather than depend on an unqualified system `sqlite3`. urlSQLite official release pagehttps://sqlite.org/index.html?lang=en

## 3. Role in Novi

SQLite is a **durable persistence mechanism**, not a semantic authority.

```text
Canonical contracts / domain authorities
                ↓
        Novi persistence layer
                ↓
             SQLite
                ↓
       durable local storage
```

SQLite must not own:

- cognition;
- memory semantics;
- knowledge semantics;
- autonomy;
- authorization;
- safety decisions;
- provenance policy;
- contract meaning;
- privacy policy.

## 4. Stage-1 topology

Stage-1 assumes one primary physical Novi node and local/offline operation.

```text
Novi process(es)
      │
      ▼
Persistence service
      │
      ├── canonical event log
      ├── durable state
      ├── checkpoints
      ├── provenance metadata
      ├── contract/version metadata
      └── configuration state
             │
             ▼
        SQLite database
             │
             ├── main database
             ├── WAL
             └── backup/checkpoint artifacts
```

Network-mounted SQLite databases are outside the Stage-1 target. SQLite's WAL documentation requires the participating processes to share the same host and notes that WAL is not supported over network filesystems. citeturn0search3

## 5. Version policy

The runtime must record at minimum:

- SQLite library version;
- SQLite source/build identity where custom-built;
- compile-time options;
- Python/runtime binding version;
- operating-system version;
- Novi revision;
- schema/contract versions;
- database format/migration version.

At startup, Novi should expose the SQLite library version and compile options through diagnostics and persist the runtime compatibility tuple in deployment metadata.

## 6. Threading model

Novi must **not** assume that any SQLite build is thread-safe merely because SQLite supports threading.

The required Stage-1 baseline is:

- serialized SQLite threading mode;
- no sharing of a single connection across unrelated execution contexts unless the persistence layer explicitly serializes access;
- application-level connection ownership/pooling rules;
- no `SQLITE_THREADSAFE=0` custom build for the multi-component Novi runtime.

SQLite documents serialized mode as the default threading mode and distinguishes it from multi-thread and single-thread modes. citeturn0search2

## 7. Journal mode

**Baseline:** WAL.

WAL is selected because Stage-1 requires concurrent reads while writes are occurring and because SQLite's WAL design separates reading, writing and checkpointing. SQLite documents that WAL permits readers and writers to proceed concurrently while writers remain serialized. citeturn0search3

Required validation:

- WAL remains enabled after database reopen;
- checkpoint behavior is measured;
- WAL growth is bounded by policy;
- recovery after interrupted writes is tested;
- backup procedures correctly handle WAL state.

## 8. Durability and synchronous policy

The durability policy must be explicit rather than inherited accidentally from a host default.

For safety-critical or authoritative state, the initial benchmark baseline should test:

```text
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
```

`NORMAL` may be benchmarked as an optimization for non-safety-critical state, but it must not become the default for authoritative state without evidence and an explicit ADR decision.

SQLite's official compile-time documentation notes that `FULL` provides the strongest power-loss durability behavior, while `NORMAL` in WAL mode protects database integrity but can allow recent changes to be rolled back after power loss. citeturn0search0

## 9. Transaction boundary

Novi must define transaction boundaries above SQL statements.

Required pattern:

```text
validate contract
      ↓
validate authority / policy
      ↓
begin transaction
      ↓
append authoritative record
      ↓
update required durable state
      ↓
write provenance/revision metadata
      ↓
COMMIT
```

Derived indexes should be rebuildable where practical and must not be allowed to become the sole authority for canonical state.

## 10. Concurrency policy

SQLite provides one serialized writer in WAL operation. Novi therefore must avoid uncontrolled write contention. citeturn0search3

The persistence layer should provide:

- one controlled write path or explicit write scheduling;
- short transactions;
- bounded queues/backpressure;
- deterministic conflict detection;
- retry policy for transient busy/locked conditions;
- idempotency keys for retried events;
- stale revision rejection.

No application component should bypass the persistence service to write the database directly.

## 11. SQLite configuration baseline

The tested Stage-1 candidate should explicitly record and validate:

| Setting | Baseline |
|---|---|
| journal mode | WAL |
| synchronous | FULL for authoritative state |
| foreign keys | ON |
| busy timeout | explicit, measured |
| temp storage | explicit policy |
| trusted schema | explicit security decision |
| auto checkpoint | explicit/observed policy |
| threading | serialized |
| database path | local persistent filesystem |
| network filesystem | prohibited |
| extensions | disabled unless explicitly required |

SQLite's compile-time documentation recommends careful control of compile options and notes that `trusted_schema` should be considered for applications using application-defined SQL functions or virtual tables. citeturn0search0

## 12. Security boundary

The database file must be treated as sensitive durable state.

Required controls include:

- filesystem permissions owned by the Novi service account;
- secrets never stored as ordinary configuration values in the database;
- encryption-at-rest decision owned by Security;
- controlled backup/export;
- integrity verification;
- audit metadata;
- privacy classification on records where required.

SQLite does not replace the Novi security architecture.

## 13. Backup and recovery

Backups must use a SQLite-aware mechanism and be validated by restoration tests.

The recovery procedure must prove:

1. database integrity after clean shutdown;
2. recovery after process crash;
3. recovery after interrupted transaction;
4. restoration from backup;
5. schema migration after restoration;
6. preservation of event IDs, revisions, provenance and contract versions.

## 14. Failure semantics

Persistence errors must never be silently converted to successful state transitions.

The persistence API must distinguish at minimum:

```text
COMMITTED
ROLLED_BACK
CONFLICT
RETRYABLE_FAILURE
RECOVERABLE_UNKNOWN
CORRUPTED
UNSAFE
```

Unknown external-side-effect outcomes remain governed by the action/recovery architecture; SQLite cannot determine whether an external physical action occurred.

## 15. Migration policy

SQLite schema migrations are application-controlled artifacts.

Each migration must have:

- unique migration ID;
- source schema version;
- target schema version;
- deterministic migration procedure;
- preconditions;
- postconditions;
- rollback/recovery strategy where feasible;
- validation fixture;
- backup requirement;
- Novi revision reference.

Contract versioning and database schema versioning must remain distinct identifiers.

## 16. Observability

Novi must record enough telemetry to diagnose:

- transaction latency;
- busy/locked events;
- rollback rate;
- WAL size;
- checkpoint duration;
- database size;
- storage I/O;
- recovery duration;
- migration duration;
- integrity-check results.

The database itself must not become the only location where operational evidence exists.

## 17. Build policy

The first implementation should prefer a **known, tested SQLite build** supplied by the selected runtime rather than introducing a custom SQLite compilation.

If a custom build becomes necessary, the build must pin:

- exact SQLite source release;
- compiler/toolchain;
- compile-time options;
- platform architecture;
- build flags;
- cryptographic/source artifact identity;
- test-suite result.

SQLite explicitly documents that non-standard compile-time configurations should be tested with the SQLite test suite. citeturn0search0turn0search1

## 18. Explicit non-goals

This definition does not claim that SQLite is suitable for:

- distributed multi-primary state;
- network-shared database operation;
- unlimited concurrent writers;
- cloud-scale persistence;
- safety-authoritative control loops;
- future multi-robot replication without architectural review.

Those are separate architecture decisions.

## 19. Adoption gate

SQLite remains **CANDIDATE** until ARCH-CLOSE-003 benchmark evidence proves the following:

```text
Correctness                 ✓
Crash recovery              ✓
Power-loss behavior         ✓
Concurrency                 ✓
Latency                     ✓
Throughput                  ✓
Resource budget             ✓
Backup/restore              ✓
Migration                   ✓
Security controls           ✓
Operational observability   ✓
```

Only then may ADR-DATA-001 change from `PROPOSED` to `ADOPTED`.

## 20. Primary sources

- SQLite official homepage/release information. urlSQLitehttps://sqlite.org/index.html?lang=en
- SQLite WAL documentation. urlSQLite WAL documentationhttps://www.sqlite.org/wal.html
- SQLite threading documentation. urlSQLite threading documentationhttps://sqlite.org/threadsafe.html
- SQLite compile-time options. urlSQLite compile-time optionshttps://www.sqlite.org/compile.html
- SQLite compilation guidance. urlSQLite compilation guidancehttps://www.sqlite.org/howtocompile.html

## 21. Decision statement

> **Novi Stage-1 defines SQLite as the primary durable-state candidate, with WAL, explicit durability, serialized threading, controlled writes, SQLite-aware backup/recovery, and pinned runtime/build metadata. SQLite is not considered adopted until the ARCH-CLOSE-003 evidence gate passes.**
