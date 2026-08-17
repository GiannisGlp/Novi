# 07 — Memory Schema and Storage

## Status

**DESIGN — V1 STORAGE ARCHITECTURE**

## Purpose

Define Novi's local-first memory substrate: canonical structured storage, large artifacts, indexes, provenance, schema evolution, transactions, concurrency, backup/recovery, retention, and Jetson constraints.

The storage layer preserves information deliberately admitted by higher-level memory policy. It does not become the source of reasoning, personality, or authorization.

## 1. Architectural Principles

### 1.1 SQLite first

SQLite is the initial authoritative structured store. It provides transactional persistence, mature tooling, foreign keys, FTS5, JSON support, and crash recovery; WAL provides concurrent readers and writers on the same host. citeturn1search1turn1search2turn0search17turn1search3

SQLite is an implementation choice behind a storage API, not a permanent vendor lock.

### 1.2 Semantics belong to Novi

```text
Cognition / Memory Manager
        ↓ semantic decision
Storage API
        ↓ persistence
SQLite / files / indexes
```

### 1.3 Models never receive unrestricted database authority

Nemotron or another model can propose a memory, update, query, or schema change. It cannot execute arbitrary SQL or choose arbitrary filesystem paths. All mutations pass through typed services and policy validation.

### 1.4 Canonical data vs derived data

Canonical:

- SQLite records
- managed artifact files

Derived:

- FTS indexes
- embeddings/vector indexes
- caches
- retrieval metadata

A derived index must be rebuildable from canonical records.

### 1.5 Protected storage

The immutable/protected area is outside the autonomous memory write path. Learning and schema evolution cannot modify it.

## 2. Storage Layers

```text
                    MEMORY API
                        │
              ┌─────────┴─────────┐
              │                   │
        Structured Store       Artifact Store
              │                   │
           SQLite          filesystem/object abstraction
              │
      ┌───────┼────────┐
      │       │        │
    tables   FTS     metadata
      │
      └───────┬────────┘
              │
       derived indexes
        ┌─────┴─────┐
        │           │
    embeddings   retrieval indexes
```

Ephemeral data such as working context, candidate retrieval sets, and temporary model output should not become durable by accident.

## 3. Database Boundaries

The initial deployment should evaluate three logical databases:

```text
novi_core.db
novi_memory.db
novi_audit.db
```

### `novi_core.db`

Stable operational state:

- entities
- people references
- places
- relationships
- current world-state projections
- configuration references
- schema metadata

### `novi_memory.db`

Evolving cognitive data:

- retained episodes
- memories
- claims
- knowledge candidates
- semantic knowledge
- procedures
- preferences
- predictions
- provenance
- retrieval metadata
- FTS structures

### `novi_audit.db`

Append-oriented audit/operations data:

- admission decisions
- consolidation
- retention/deletion
- schema proposals and migrations
- retrieval traces
- policy outcomes
- integrity events

The physical split remains a benchmark question. The logical ownership boundaries must remain even if the implementation later uses fewer files.

### SQLite concurrency constraint

WAL allows readers and a writer to proceed concurrently, but there is still one writer at a time. WAL also requires processes to share the same host and does not work over a network filesystem. citeturn1search1

Novi therefore must not use SQLite as a distributed database.

## 4. Core Schema

The following is the conceptual V1 schema. Exact SQL migrations belong in the implementation repository.

### 4.1 `memory_items`

```text
memory_id              TEXT PRIMARY KEY
memory_type            TEXT NOT NULL
subject_entity_id      TEXT
content                TEXT
structured_payload     JSON
status                 TEXT NOT NULL
importance             REAL
confidence             REAL
verification_state     TEXT NOT NULL
privacy_class          TEXT NOT NULL
created_at             INTEGER NOT NULL
observed_at            INTEGER
valid_from             INTEGER
valid_until            INTEGER
last_confirmed_at      INTEGER
last_accessed_at       INTEGER
access_count           INTEGER NOT NULL
retention_class        TEXT NOT NULL
source_kind             TEXT NOT NULL
schema_version         INTEGER NOT NULL
```

Stable, frequently queried fields remain columns; flexible domain-specific attributes can use validated JSON. SQLite JSON functions are built in on modern versions, with JSONB available for on-disk internal representations. JSON does not replace relational constraints. citeturn1search3

### 4.2 `entities`

```text
entity_id               TEXT PRIMARY KEY
entity_type             TEXT NOT NULL
canonical_name          TEXT
attributes_json         JSON
status                  TEXT NOT NULL
confidence              REAL
privacy_class           TEXT NOT NULL
created_at              INTEGER NOT NULL
updated_at              INTEGER NOT NULL
schema_version          INTEGER NOT NULL
```

### 4.3 `relationships`

```text
relationship_id         TEXT PRIMARY KEY
subject_entity_id       TEXT NOT NULL
predicate               TEXT NOT NULL
object_entity_id        TEXT NOT NULL
confidence              REAL
status                  TEXT NOT NULL
valid_from              INTEGER
valid_until             INTEGER
provenance_ref           TEXT
created_at              INTEGER NOT NULL
updated_at              INTEGER NOT NULL
```

Foreign keys should be explicitly enabled for every connection. SQLite does not enforce them by default. citeturn1search2turn1search5

### 4.4 `claims`

```text
claim_id                TEXT PRIMARY KEY
subject_entity_id       TEXT
predicate               TEXT NOT NULL
object_value_json       JSON
claim_type              TEXT NOT NULL
epistemic_state         TEXT NOT NULL
confidence              REAL
verification_state      TEXT NOT NULL
valid_from              INTEGER
valid_until             INTEGER
created_at              INTEGER NOT NULL
updated_at              INTEGER NOT NULL
```

A claim can be true, false, uncertain, stale, superseded, or contradicted.

### 4.5 `episodes`

```text
episode_id              TEXT PRIMARY KEY
started_at              INTEGER NOT NULL
ended_at                INTEGER
location_entity_id      TEXT
summary                 TEXT
importance              REAL
status                  TEXT NOT NULL
created_at              INTEGER NOT NULL
```

### 4.6 `procedures`

```text
procedure_id            TEXT PRIMARY KEY
name                    TEXT NOT NULL
version                 INTEGER NOT NULL
steps_json              JSON NOT NULL
preconditions_json      JSON
postconditions_json     JSON
confidence              REAL
verification_state      TEXT NOT NULL
status                  TEXT NOT NULL
created_at              INTEGER NOT NULL
updated_at              INTEGER NOT NULL
```

### 4.7 `preferences`

```text
preference_id           TEXT PRIMARY KEY
subject_entity_id       TEXT NOT NULL
key                     TEXT NOT NULL
value_json              JSON NOT NULL
confidence              REAL
source_memory_id        TEXT
verification_state      TEXT NOT NULL
valid_from              INTEGER
valid_until             INTEGER
updated_at              INTEGER NOT NULL
```

### 4.8 `predictions`

```text
prediction_id           TEXT PRIMARY KEY
subject_entity_id       TEXT
prediction_type         TEXT NOT NULL
prediction_json         JSON NOT NULL
confidence              REAL
predicted_for           INTEGER
expires_at              INTEGER
outcome_state           TEXT NOT NULL
created_at               INTEGER NOT NULL
```

Predictions never become authoritative facts merely because their confidence is high.

## 5. Provenance Schema

Provenance is first-class and independently queryable.

### `evidence_sources`

```text
source_id               TEXT PRIMARY KEY
source_kind             TEXT NOT NULL
source_identifier       TEXT
source_version          TEXT
origin                  TEXT
trust_domain            TEXT
created_at              INTEGER NOT NULL
metadata_json           JSON
```

### `evidence_items`

```text
evidence_id             TEXT PRIMARY KEY
source_id               TEXT NOT NULL
evidence_kind           TEXT NOT NULL
payload_ref             TEXT
observed_at             INTEGER
captured_at             INTEGER
confidence              REAL
content_hash            TEXT
privacy_class           TEXT NOT NULL
metadata_json            JSON
```

### `claim_evidence`

```text
claim_id                TEXT NOT NULL
evidence_id             TEXT NOT NULL
relationship_type       TEXT NOT NULL
weight                  REAL
PRIMARY KEY (claim_id, evidence_id)
```

### `memory_provenance`

```text
memory_id               TEXT NOT NULL
source_type             TEXT NOT NULL
source_id               TEXT NOT NULL
transformation          TEXT
model_id                TEXT
model_version           TEXT
created_at              INTEGER NOT NULL
PRIMARY KEY (memory_id, source_id, transformation)
```

This lets Novi answer **why it believes something** without asking the LLM to reconstruct provenance.

## 6. Supersession and Contradiction

### `claim_relations`

```text
from_claim_id           TEXT NOT NULL
to_claim_id             TEXT NOT NULL
relation_type            TEXT NOT NULL
created_at               INTEGER NOT NULL
PRIMARY KEY (from_claim_id, to_claim_id, relation_type)
```

Relations include:

- supports
- contradicts
- supersedes
- derived_from
- refines
- duplicates
- invalidates

Historical claims remain available unless retention/privacy policy requires deletion.

## 7. Full-Text Search

SQLite FTS5 is the initial candidate for local lexical search. It supports token-based indexing and configurable prefix indexes. citeturn0search17

Searchable material may include:

- memory text
- summaries
- entity names
- tags
- document titles
- selected knowledge fields

The FTS index references canonical IDs and is rebuildable.

```text
memory_items → memory_fts → memory_id
```

## 8. Vector Storage

Embeddings are derived indexes, never canonical memory.

Conceptual metadata:

```text
embedding_id
subject_type
subject_id
model_id
model_version
dimensions
vector_store
content_hash
created_at
```

The vector implementation remains replaceable and should initially be local/embedded if benchmarks support it.

When an embedding model changes:

```text
canonical memory
      ↓
content hash
      ↓
new embedding model
      ↓
new index
```

Old and new indexes may coexist during migration and evaluation.

## 9. File and Artifact Storage

Large images, audio, video, documents, and generated artifacts belong in a managed artifact layer rather than being unnecessarily embedded in SQLite.

```text
storage/
├── objects/
│   ├── images/
│   ├── audio/
│   ├── video/
│   ├── documents/
│   └── generated/
├── indexes/
└── temporary/
```

SQLite stores metadata such as:

```text
artifact_id
relative_path
content_hash
media_type
size_bytes
created_at
privacy_class
retention_class
source_id
```

The artifact service resolves paths. Models never provide arbitrary filesystem paths directly.

## 10. Schema Evolution

Novi is expected to learn new concepts, but learning does not imply unrestricted DDL.

A model may propose:

```text
new entity type
new attribute
new relation
new table
new index
```

The Schema Manager validates the proposal.

### Lifecycle

```text
proposal
  ↓
semantic validation
  ↓
security validation
  ↓
compatibility analysis
  ↓
resource analysis
  ↓
migration plan
  ↓
approval policy
  ↓
transactional migration
  ↓
verification
```

### Existing representation first

Before creating a table, Novi must determine whether an existing entity/attribute/relation model is sufficient.

A new physical table is justified only when the concept has stable semantics, significant scale/query requirements, meaningful relational constraints, or lifecycle/indexing requirements that cannot be represented cleanly otherwise.

Every migration is versioned, deterministic, tested, audited, and recoverable.

## 11. SQLite Type Discipline

Use SQLite `STRICT` tables for core structured data where practical. STRICT tables enforce declared types and allow integrity checks to validate type correctness. citeturn1search0

Use flexible JSON only where extensibility is intentional.

```text
stable core fields → strict relational schema
variable attributes → validated JSON
large artifacts → files
semantic search → vectors
exact search → FTS
```

## 12. Constraints and Indexing

Use database-enforced:

- primary keys
- unique constraints
- NOT NULL
- CHECK constraints
- foreign keys

Likely indexes, subject to workload benchmarks:

```text
memory_items(subject_entity_id)
memory_items(memory_type, status)
memory_items(observed_at)
memory_items(valid_from, valid_until)
memory_items(last_accessed_at)
claims(subject_entity_id, predicate)
relationships(subject_entity_id, predicate)
relationships(object_entity_id, predicate)
provenance(source_id)
```

Foreign-key child columns should be indexed where joins or parent updates/deletes require it. citeturn1search2

## 13. Transactions and Idempotency

Memory admission, canonical memory creation, and provenance creation should normally be atomic.

```text
BEGIN
  insert memory
  insert provenance
  insert claim
  insert relationships
  enqueue derived-index update
COMMIT
```

Derived vector/FTS updates should not make canonical persistence depend on an external index being available unless strict consistency is explicitly required.

Every external write should carry an idempotency key. Retried admission must not create duplicate durable memories.

## 14. WAL and Connection Management

WAL is the preferred starting mode for mixed read/write memory workloads because readers can proceed while a writer commits. There remains one writer, and long-running readers can delay checkpoints. citeturn1search1

Monitor:

- WAL size
- checkpoint latency
- busy/locked events
- transaction duration
- long-running readers
- write queue depth

The WAL file is part of persistent database state while active and must remain consistent with its database file. citeturn1search1turn0search1

Use controlled connections. Each connection initializes required pragmas, including foreign-key enforcement. Avoid long transactions for ordinary memory operations.

## 15. Backup and Recovery

Use consistent live-database backup mechanisms rather than copying a database file blindly during active writes.

Candidates:

- SQLite Online Backup API
- `VACUUM INTO`
- `sqlite3_rsync` where appropriate

SQLite documents the Online Backup API and `VACUUM INTO` for consistent snapshots of live databases. citeturn0search5turn0search6

Backup classes:

```text
operational recovery
      ↓
daily local snapshot
      ↓
periodic encrypted archival snapshot
      ↓
user-controlled export
```

Backups are not trusted until restoration is periodically tested.

## 16. Integrity Verification

Scheduled maintenance should perform:

- schema version verification
- foreign-key checks
- `PRAGMA quick_check`
- periodic `PRAGMA integrity_check`
- artifact hash verification
- embedding/content-hash consistency checks
- orphan-reference detection

SQLite documents integrity checks, including additional type checking for STRICT tables. citeturn1search0

## 17. Retention and Deletion

Memory lifecycle remains policy-driven:

```text
ACTIVE → STALE → ARCHIVED → EXPIRED → PURGED
```

Deletion must account for canonical records plus:

- FTS
- embeddings
- artifacts
- caches
- applicable backups
- provenance

Privacy deletion can require stronger guarantees than ordinary expiration.

## 18. Jetson AGX Orin 64GB

Storage competes with inference, perception, navigation, thermal headroom, and power. The Jetson profile should therefore:

- minimize unnecessary writes
- batch consolidation
- defer embedding generation under resource pressure
- bound temporary storage
- monitor disk capacity/health
- prevent unbounded WAL growth
- retain sufficient recovery space
- prioritize safety-critical state

High-volume raw sensor recordings must not be retained automatically forever.

Mac development can use larger datasets and heavier indexing, but the semantic storage APIs must remain identical across Mac, simulation, and Jetson.

## 19. Multi-Process Architecture

Multiple Novi services may exist:

```text
perception
memory manager
cognition
autonomy
retrieval
consolidation
app/audit
```

They must not all write arbitrary SQLite tables.

```text
services
   ↓
Memory API / Memory Manager
   ↓
controlled storage worker
   ↓
SQLite
```

This reduces lock contention and creates one enforcement point for storage policy.

## 20. Distributed Storage

Distributed storage is not a V1 requirement. Novi is a local physical robot and SQLite WAL is explicitly not designed for network filesystems. Future fleet synchronization should be a separate replication layer over canonical records. citeturn1search1

## 21. NVIDIA / NeMo Integration

NVIDIA NeMo Agent Toolkit exposes pluggable memory interfaces/providers and structured memory models. Current documentation lists providers including Mem0, Redis and Zep. citeturn0search0turn0search2

NVIDIA also separates low-level memory editing from higher-level memory management, which is a useful boundary for Novi. citeturn0search4

Novi therefore owns its semantic storage contract:

```text
Novi Memory API
      ↓
provider adapter
      ↓
optional NeMo / other local provider
```

A NeMo provider is adopted only if local benchmarks show that it improves the required workload. It must not replace Novi's canonical schema or provenance model.

## 22. Cloud and External Stores

Cloud memory/storage is exceptional. It requires:

- demonstrated local insufficiency
- permitted data classification
- acceptable latency/availability
- justified cost
- fallback behavior
- export/migration path

Core memory should remain locally usable without cloud connectivity.

## 23. Security Requirements

Storage must enforce:

- parameterized SQL
- schema allowlists
- no arbitrary model SQL
- artifact path validation
- service/capability access control
- privacy classification
- audit logging for privileged mutation
- protected-storage isolation
- migration authorization
- backup protection

The model cannot choose an arbitrary path and cause arbitrary bytes to be written there.

## 24. Performance and Benchmarking

Do not invent final limits before workload testing.

Measure:

- write latency
- transaction latency
- read latency
- FTS latency
- vector retrieval latency
- provenance traversal
- consolidation throughput
- checkpoint duration
- WAL growth
- disk write volume
- memory footprint
- CPU utilization
- Jetson power/thermal impact

The objective is predictable storage behavior without interfering with perception, autonomy, safety, or inference.

## 25. Test Matrix

### Correctness

- constraints
- relationships
- migrations
- duplicate prevention
- provenance integrity
- temporal validity

### Failure

- process crash during write
- simulated power loss
- disk full
- corrupted artifact
- interrupted migration
- unavailable vector index
- failed FTS rebuild
- lock contention

### Recovery

- WAL recovery
- backup restoration
- migration recovery
- derived-index reconstruction

### Security

- SQL injection
- path traversal
- unauthorized writes
- malicious schema proposals
- prompt-injection-derived storage requests

### Performance

- high event rates
- burst writes
- concurrent reads
- consolidation during inference
- long-running operation
- Jetson resource pressure

## 26. V1 Decision Summary

| Area | V1 decision |
|---|---|
| Canonical structured store | SQLite |
| Core schema | relational + STRICT where practical |
| Flexible attributes | validated JSON |
| Exact search | SQLite FTS5 |
| Semantic search | replaceable local vector index |
| Large artifacts | managed local filesystem/object abstraction |
| Provenance | first-class relational data |
| Transactions | SQLite transactions |
| Concurrency | WAL + controlled writers |
| Schema evolution | proposal → validation → migration |
| Backups | SQLite-consistent snapshots |
| Cloud | exception only |
| NVIDIA NeMo | optional adapter/provider |
| Vendor lock-in | prohibited |
| Model database access | typed API only |
| Protected core | outside autonomous write authority |

## 27. Open Benchmark Questions

1. How many durable memory records will a typical year generate?
2. How much artifact storage is actually required?
3. Which local vector index gives the best Jetson trade-off?
4. Is SQLite FTS5 sufficient at target scale?
5. Does one database outperform the proposed three-database split?
6. Which WAL/checkpoint policy minimizes inference interference?
7. Should embeddings be synchronous or asynchronous?
8. What storage medium gives adequate endurance and latency?
9. At what workload is a specialized local store justified?
10. Does a NeMo memory component provide measurable value over a Novi-native implementation?

These questions require representative benchmarks before the V1 architecture is changed.

## 28. Design Rule

The durable memory layer should be **boring, deterministic, inspectable, recoverable, and replaceable**.

The intelligence belongs above it.

```text
          NOVI COGNITION
                 │
          intelligent policy
                 │
          MEMORY MANAGER
                 │
       typed storage contracts
                 │
      ┌──────────┼───────────┐
      ▼          ▼           ▼
   SQLite      Files       Indexes
      │          │           │
      └──────────┴───────────┘
              local state
```

The storage layer should not need to understand Novi's personality or reasoning. It should reliably preserve what the higher-level system deliberately decided is worth keeping.

## References

- NVIDIA NeMo Agent Toolkit — memory subsystem/providers. citeturn0search0turn0search4
- NVIDIA NeMo Agent Toolkit — memory data models/plugin architecture. citeturn0search2turn0search7
- SQLite — WAL and concurrency. citeturn1search1
- SQLite — foreign-key constraints. citeturn1search2
- SQLite — STRICT tables. citeturn1search0
- SQLite — JSON/JSONB. citeturn1search3
- SQLite — FTS5. citeturn0search17
- SQLite — Online Backup API. citeturn0search5
- SQLite — VACUUM/VACUUM INTO. citeturn0search6
- SQLite — corruption and safe copying. citeturn0search1
