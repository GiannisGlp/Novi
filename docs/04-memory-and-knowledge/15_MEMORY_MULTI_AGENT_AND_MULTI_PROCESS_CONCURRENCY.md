# 15 — Memory Multi-Agent and Multi-Process Concurrency

## Status

**DESIGN — V1**

## Purpose

Define how Novi safely handles concurrent memory access from perception, cognition, autonomy, voice/audio, the control application, background learning, indexing, consolidation, and future agents or processes.

The objective is not merely database integrity. SQLite can protect physical consistency. Novi must additionally protect **semantic consistency**: the meaning of memory must remain correct when many components observe, propose, update, retrieve, consolidate, delete, and index information concurrently.

---

## 1. Core Decision

Novi uses:

> **Centralized semantic ownership + concurrent reads + serialized authoritative writes + asynchronous background work + explicit concurrency limits.**

Subsystems must not receive unrestricted direct write access to the authoritative memory database.

The Memory Manager is the authoritative gateway for semantic memory mutations.

```text
                    NOVI COMPONENTS
                         │
       ┌─────────────────┼──────────────────┐
       │                 │                  │
   Perception        Cognition          Autonomy
       │                 │                  │
       ├──────────── Voice/Audio ──────────┤
       │                 │                  │
       └──────────── Control App ──────────┘
                         │
                  Memory API
                         │
                 ┌───────▼───────┐
                 │ Memory Manager│
                 └───────┬───────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       SQLite          Index          Files
       Writer         Manager        Manager
```

This does not prohibit optimized read paths. It prohibits bypassing the semantic ownership boundary for mutations.

---

## 2. Why Centralized Semantic Ownership Is Required

SQLite can serialize writes and maintain ACID guarantees, but database-level serialization does not understand Novi's semantics.

For example, these operations can each be individually valid SQL transactions:

```text
A: Vano is in the kitchen
B: Vano left the kitchen
C: consolidate Vano's recent activity
D: delete Vano's recent memory
E: generate embedding for the previous state
```

The database can remain structurally consistent while the resulting cognitive state becomes semantically wrong.

The Memory Manager therefore owns:

- admission
- validation
- version checks
- provenance
- ordering
- supersession
- deletion semantics
- schema changes
- indexing events
- authorization
- privacy policy
- audit events
- recovery

---

## 3. SQLite Concurrency Model

SQLite is the initial authoritative local storage technology.

Novi should use **WAL mode** for the primary memory workload because it permits readers to proceed while a writer operates. WAL does not create unlimited write concurrency: there remains a single writer at a time.

Design consequences:

- transactions must be short;
- write work must be serialized through the Memory Manager;
- long-running read transactions must be avoided;
- busy/locked conditions require bounded retry/backoff;
- checkpointing must be actively managed;
- WAL growth must be monitored;
- database integrity must be periodically verified.

Novi must not assume that WAL makes the database multi-writer.

The application must explicitly enable foreign-key enforcement on every SQLite connection that requires relational integrity.

---

## 4. Process Ownership

### Authoritative writer

The Memory Manager is the preferred owner of authoritative write transactions.

### Readers

Read operations may be served concurrently through read-only connections or APIs where this does not bypass privacy and authorization controls.

### Background workers

Background workers submit jobs to the Memory Manager rather than modifying authoritative state independently.

Examples:

- consolidation worker
- embedding worker
- FTS maintenance
- graph projection worker
- backup worker
- replay worker
- retention worker
- schema migration worker

Workers can prepare derived artifacts independently, but activation of those artifacts must occur through an authoritative commit/version boundary.

---

## 5. Operation Classes

Every memory operation has a class.

### Class A — Critical synchronous

Examples:

- user-confirmed correction
- safety-relevant state mutation
- deletion request
- authorization-sensitive relationship change
- committed schema migration

Properties:

- synchronous acknowledgment
- transactional
- provenance required
- authorization required
- failure must be explicit

### Class B — Normal synchronous

Examples:

- current world-state memory
- durable user preference
- confirmed relationship update

Properties:

- short transaction
- normal priority
- idempotency required

### Class C — Asynchronous

Examples:

- candidate memory admission
- consolidation
- routine detection
- graph enrichment
- embedding generation

Properties:

- queued
- retryable
- eventually consistent
- lower priority than live cognition/autonomy

### Class D — Bulk/background

Examples:

- full re-indexing
- historical replay
- archival maintenance
- benchmark preparation

Properties:

- interruptible
- throttled
- resource-aware
- never allowed to starve critical workloads

---

## 6. Memory Command Model

Mutations should be represented as typed commands rather than arbitrary SQL.

Example:

```json
{
  "command_id": "cmd_123",
  "type": "MEMORY_CANDIDATE_CREATE",
  "actor": "perception_service",
  "subject": "person:123",
  "payload": {},
  "source_event_ids": ["evt_456"],
  "expected_version": 17,
  "priority": "normal",
  "created_at": "..."
}
```

The Memory Manager validates the command before creating or modifying state.

The model must never be able to submit raw SQL as a memory command.

---

## 7. Idempotency

Every externally generated mutation requires an idempotency key or stable command/event ID.

If the same command arrives twice:

```text
command X
   ↓
commit
   ↓
retry command X
   ↓
recognized duplicate
   ↓
return previous result
```

This is essential because sensors, processes, queues, and network clients can retry after timeouts without knowing whether the original operation committed.

Idempotency records must survive process restarts for the retention period required by the operation.

---

## 8. Optimistic Versioning

Important mutable entities should carry a monotonically increasing version.

Example:

```text
Memory M
version = 17
```

A worker reads version 17 and proposes an update:

```text
UPDATE ... WHERE id = M AND version = 17
```

If another operation has already changed it to version 18, the update fails as stale rather than silently overwriting newer state.

The worker must then:

1. reload current state;
2. reevaluate its proposal;
3. retry only if still valid;
4. otherwise discard or create a new candidate.

---

## 9. Event Ordering

Concurrent observations require ordering metadata.

Every event should contain, where available:

- event ID
- source ID
- source sequence
- observed timestamp
- received timestamp
- processing timestamp
- causal/parent references

Timestamps alone are insufficient to establish a total order across independent sensors.

Novi should preserve partial ordering rather than inventing certainty.

For example:

```text
Camera event A
Audio event B
IoT event C
```

may be concurrent observations of the same real-world situation.

The World Model and Memory Manager can later establish relationships between them.

---

## 10. Conflict Handling

Concurrent semantic updates must not automatically overwrite each other.

Example:

```text
A: device is in kitchen
B: device is in bedroom
```

Possible explanations include:

- device moved;
- one observation is stale;
- one sensor is wrong;
- two devices were confused;
- identity resolution changed.

The Memory Manager records the conflict and invokes appropriate consolidation/verification rather than selecting whichever transaction committed last.

**Last-write-wins is not an acceptable general semantic policy.**

It may only be used for explicitly defined state where latest observation is the intended semantics.

---

## 11. Live State vs Durable Memory

Live world state and historical memory have different consistency requirements.

```text
Live state
→ freshness prioritized
→ may be replaced by newer observation

Historical memory
→ provenance prioritized
→ previous states preserved
```

The same event may update both:

```text
current_state: Vano = kitchen

historical_event:
  Vano entered kitchen at T1
```

A later event can change current state without destroying the historical event.

---

## 12. Consolidation Concurrency

Consolidation must never process a memory snapshot while assuming it is permanently unchanged.

A consolidation job records:

- source memory IDs
- source versions
- snapshot time
- consolidation algorithm/version
- model/version if used

Before committing the result, it verifies that relevant source versions have not changed.

If they have changed, the result is:

```text
stale consolidation
```

and must be recomputed or safely rebased.

---

## 13. Embedding Concurrency

Embedding generation is derived work.

```text
memory commit
     ↓
embedding job
     ↓
model inference
     ↓
vector artifact
     ↓
activation check
     ↓
index update
```

The embedding worker must record the source memory version and embedding-model version.

If the memory changed while embedding was generated, the result must not overwrite the newer embedding.

Old embeddings can remain temporarily as stale derived data until replaced.

---

## 14. Indexing Concurrency

FTS, vector indexes and graph projections are derived indexes, not authoritative truth.

A temporary indexing failure must therefore not corrupt the canonical memory record.

The system should support:

```text
canonical data committed
        ↓
index job queued
        ↓
index succeeds → current
        ↓
index fails → retry/degraded
```

Retrieval must be able to detect when an index is stale.

The system should support deterministic full rebuilds from canonical storage.

---

## 15. Deletion Concurrency

Deletion is a high-priority semantic operation.

If deletion occurs while an embedding, consolidation, or replay job is running, the deletion must win.

Example:

```text
T1: embedding job reads memory M
T2: user requests deletion of M
T3: deletion commits
T4: embedding finishes
T5: activation check sees tombstone/version mismatch
T6: embedding discarded
```

No background worker may resurrect deleted information.

Deletion tombstones or equivalent durable deletion state may be required until all derived work that could reproduce the data has been invalidated.

---

## 16. Schema Migration Concurrency

Schema migrations are exclusive administrative operations.

Before migration:

- stop or drain incompatible writers;
- pause background jobs that depend on the affected schema;
- create backup/checkpoint as appropriate;
- verify database integrity;
- validate migration plan.

After migration:

- verify schema version;
- verify integrity;
- restart compatible workers;
- rebuild affected indexes;
- record migration audit event.

A normal cognitive component cannot request an immediate arbitrary production schema migration.

---

## 17. Control Application Access

The control/monitoring application must use the Memory API or read-only interfaces.

It must not open the production memory database with unrestricted administrative credentials merely to display data.

Administrative operations such as deletion, retention changes, restore, migration or protected-data access require explicit privileged APIs and audit events.

---

## 18. Multiple Agents

Future Novi deployments may contain multiple specialized agents or autonomous workers.

They must not receive implicit shared write authority.

Each agent has:

- identity
- capability set
- authorization scope
- resource budget
- operation priority
- provenance identity

The Memory Manager treats an agent as an actor, not as an owner of the database.

Agent-generated claims remain proposals until admitted under memory policy.

---

## 19. Priority and Backpressure

Memory work must be prioritized.

Suggested order:

```text
SAFETY / LIVE WORLD STATE
        ↓
USER INTERACTION
        ↓
CRITICAL MEMORY OPERATIONS
        ↓
NORMAL MEMORY
        ↓
CONSOLIDATION
        ↓
EMBEDDINGS
        ↓
BULK REINDEX / REPLAY
```

When queues grow, Novi should apply backpressure rather than allowing unlimited memory jobs.

Low-priority work may be deferred, sampled, coalesced, or cancelled.

It must never starve autonomy or safety-critical processing.

---

## 20. Jetson Resource Awareness

On Jetson AGX Orin 64GB, concurrency must account for:

- GPU memory
- CPU utilization
- RAM
- thermal state
- power mode
- storage I/O
- inference queues
- sensor throughput

The Memory Manager should consume resource-health signals and dynamically reduce background concurrency.

Example:

```text
thermal pressure high
       ↓
reduce embedding workers
       ↓
pause bulk replay
       ↓
keep live memory writes
       ↓
keep cognition/autonomy
```

Memory maintenance is subordinate to the robot's operational needs.

---

## 21. Failure Recovery

The system must tolerate:

- process crash
- power loss
- queue interruption
- database busy/locked errors
- partially completed background work
- index corruption
- stale workers
- duplicate commands
- network/control-app disconnect

Transactions must be atomic.

Background jobs must be restartable and idempotent.

Derived indexes must be rebuildable.

Canonical memory must not depend on an index being available.

---

## 22. Queue Durability

Operations whose loss would cause unacceptable semantic loss require durable queues or durable command records.

Ephemeral queues may be used for disposable derived work such as a best-effort embedding refresh, provided the canonical record remains intact and the job can be regenerated.

The queue policy must therefore distinguish:

```text
must survive restart
vs
safe to regenerate
```

---

## 23. Consistency Classes

Not every memory operation requires identical consistency.

### Strong consistency

Use for:

- deletion
- authorization-sensitive changes
- schema version changes
- user-confirmed corrections
- immutable/protected metadata

### Read-your-writes

Useful for interactive user operations so Novi immediately reflects a confirmed change to the same requester.

### Eventual consistency

Acceptable for:

- embeddings
- FTS updates
- graph projections
- analytics
- background consolidation

The API must communicate when derived state is temporarily stale.

---

## 24. Semantic Transactions

A semantic transaction can involve multiple records and derived state.

Example:

```text
Create relationship
+ create provenance claim
+ create audit event
+ schedule embedding
+ schedule graph projection
```

The canonical semantic mutation should commit atomically. Derived work may happen asynchronously after the authoritative commit.

This creates a reliable boundary:

```text
AUTHORITATIVE COMMIT
        ↓
DERIVED WORK
```

rather than attempting to make every GPU/index/file operation part of one giant database transaction.

---

## 25. Read Isolation

Read operations must specify their consistency requirement.

Examples:

- `CURRENT_STATE` → freshest available committed state
- `HISTORICAL_SNAPSHOT` → stable snapshot
- `USER_CONFIRMED` → only verified claims
- `RETRIEVAL` → may use eventually consistent indexes

Cognition must not accidentally combine data from incompatible snapshots when a coherent state is required.

---

## 26. Deadlock and Lock Avoidance

The architecture should minimize application-level locks.

Preferred strategy:

1. short SQLite transactions;
2. deterministic operation ordering;
3. optimistic versioning for semantic conflicts;
4. queues for serialized mutation classes;
5. bounded retries;
6. no lock held while waiting for model inference, network calls, or GPU work.

Never hold a database transaction open while waiting for an LLM, VLM, remote service, filesystem operation, or long-running computation unless explicitly justified.

---

## 27. No Model Inside a Transaction

A critical rule:

> **Never keep an authoritative database transaction open while asking a generative model to reason.**

Instead:

```text
read snapshot
    ↓
close transaction
    ↓
model reasoning
    ↓
structured proposal
    ↓
revalidate current versions
    ↓
short transaction
    ↓
commit if still valid
```

This avoids long locks and prevents stale model decisions from blindly overwriting current state.

---

## 28. Concurrency Observability

Every operation should be traceable through:

- command ID
- actor ID
- request ID
- transaction ID where available
- source event IDs
- entity/version IDs
- queue/job ID
- retry count
- latency
- result
- conflict status
- fallback status

Metrics should include:

- write queue depth
- write latency
- busy/locked rate
- transaction duration
- retry rate
- conflict rate
- stale proposal rate
- duplicate command rate
- index lag
- embedding lag
- consolidation lag
- deletion propagation lag
- WAL size
- checkpoint duration
- database integrity failures

---

## 29. Testing Strategy

Concurrency testing must include deterministic and stress scenarios.

### Required scenarios

- two simultaneous observations of the same entity;
- duplicate sensor event;
- stale update after newer update;
- simultaneous correction and consolidation;
- deletion during embedding generation;
- deletion during replay;
- schema migration while workers are queued;
- database busy/locked conditions;
- process crash during transaction;
- power-loss simulation;
- queue replay after restart;
- index failure after canonical commit;
- multiple control-app readers;
- high-frequency sensor bursts;
- GPU pressure during embedding jobs;
- thermal throttling during background work.

### Invariants

Tests must verify:

- no deleted memory is resurrected;
- stale proposals cannot overwrite newer versions;
- duplicate commands do not duplicate durable state;
- canonical data survives derived-index failure;
- schema migration is atomic;
- provenance remains attached to mutations;
- protected data cannot be modified by normal workers;
- low-priority work cannot starve critical operations.

---

## 30. Security Boundary

Concurrency does not grant authority.

A process that can write to a queue does not automatically gain permission to write arbitrary memory.

Every command is evaluated for:

```text
identity
→ capability
→ authorization
→ privacy scope
→ policy
→ schema validity
→ provenance
→ semantic conflict
→ commit
```

The immutable/protected core remains outside autonomous write authority regardless of concurrency model.

---

## 31. Recommended V1 Architecture

```text
                    SENSOR / APP / AGENT EVENTS
                              │
                              ▼
                     Event / Command API
                              │
                              ▼
                    ┌───────────────────┐
                    │  Memory Manager   │
                    │                   │
                    │ admission        │
                    │ authorization     │
                    │ version checks    │
                    │ provenance       │
                    │ ordering          │
                    │ prioritization    │
                    └─────────┬─────────┘
                              │
                 ┌────────────┴────────────┐
                 │                         │
           Authoritative             Background
             mutation                  queues
                 │                         │
                 ▼              ┌──────────┼──────────┐
              SQLite            ▼          ▼          ▼
               WAL          consolidate embeddings indexing
                 │
                 └────────────┬────────────┘
                              ▼
                       Derived indexes
                              │
                              ▼
                         Retrieval API
                              │
                              ▼
                           Cognition
```

## 32. Explicit Non-Goals

V1 does not require:

- distributed consensus;
- multi-node shared SQLite;
- unrestricted multi-writer databases;
- arbitrary agent-to-database SQL;
- graph database deployment by default;
- distributed event sourcing for every operation;
- speculative database transactions around LLM inference.

These may be evaluated later if actual deployment requirements justify them.

---

## 33. Decision Summary

| Decision | V1 choice |
|---|---|
| Authoritative storage | SQLite |
| Journal mode | WAL |
| Semantic write owner | Memory Manager |
| Direct arbitrary SQL for models | Prohibited |
| Concurrent reads | Supported |
| Authoritative writes | Serialized/controlled |
| Semantic versioning | Optimistic version checks |
| Duplicate protection | Idempotency keys |
| Derived indexes | Asynchronous |
| Embeddings | Asynchronous |
| Consolidation | Asynchronous/priority controlled |
| Deletion | High-priority authoritative operation |
| Schema migration | Exclusive controlled operation |
| Model inside DB transaction | Prohibited |
| Background pressure control | Required |
| Index rebuild | Deterministic from canonical data |
| Protected core | Outside autonomous authority |
| Multi-agent writes | Via Memory API |

---

## 34. Final Principle

The most important distinction in this document is:

> **SQLite protects the database. The Memory Manager protects the meaning.**

Novi is a continuously operating cognitive system. Perception, cognition, autonomy, learning, indexing and user interaction will naturally operate concurrently. The architecture must therefore treat concurrency as a semantic systems problem, not merely as a database locking problem.

The V1 design deliberately favors correctness, recoverability, auditability and resource-aware degradation over maximum theoretical write throughput. If future measurements demonstrate that SQLite or the centralized Memory Manager is a bottleneck, the abstraction boundaries allow another storage or concurrency implementation to be introduced without changing the cognitive memory contracts.

## 35. References and Research Basis

Primary implementation references to validate during engineering include:

- SQLite WAL and transaction documentation
- SQLite locking/concurrency documentation
- SQLite foreign-key enforcement documentation
- NVIDIA NeMo Agent Toolkit concurrency/session controls
- NVIDIA NeMo Agent Toolkit memory architecture

The implementation must re-check current upstream documentation and benchmark the chosen versions before deployment because runtime capabilities and APIs evolve.
