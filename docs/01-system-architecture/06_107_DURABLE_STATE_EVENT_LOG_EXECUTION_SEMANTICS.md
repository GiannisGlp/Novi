# 107 — Durable State, Event Log & Execution Semantics Architecture

**Status:** Proposed / Architecture Foundation  
**Priority:** P1 — prerequisite for distributed Novi  
**Document class:** Detailed system architecture  
**Depends on:** 00–106 architecture, memory, knowledge, provenance, schema/model evolution, governance, and human-oversight decisions  
**Enables:** 108 consistency and concurrency, 109 replication and distributed memory, 110 recovery, 111 privacy lifecycle, 112 observability/evaluation, 113 resource governance, 114 multi-agent coordination

---

## 1. Purpose

This document defines the durable state and execution substrate required for Novi to operate as a continuously running autonomous cognitive system.

The purpose is not to select a particular database or message broker. The purpose is to define the **semantic contract** that storage, event processing, memory, knowledge, autonomy, governance, and future distributed runtimes must implement.

Novi must be able to answer, after restart or failure:

- What state did Novi have?
- What changed that state?
- In what order did relevant changes occur?
- Which observation, memory, model, policy, or human decision caused a change?
- Which version of each dependency was active?
- Which action was proposed, authorized, executed, and observed?
- Can the state be reconstructed or verified?
- Can an invalid change be isolated or rolled back without corrupting unrelated state?

The architectural principle is:

> **Durable state is derived from an authoritative, typed history of state-changing events, while materialized state and snapshots provide efficient access.**

This creates a separation between **what happened**, **what state is currently materialized**, and **what can be reconstructed**.

---

## 2. Why This Layer Exists Before Replication

Distributed replication must not be the first P1 implementation layer.

Before Novi can safely replicate memory or cognitive state, it must define:

```text
EVENT
STATE
VERSION
TRANSACTION
COMMIT
CHECKPOINT
SNAPSHOT
DERIVATION
RECOVERY
```

Otherwise a distributed system would replicate ambiguous semantics and make conflicts harder to reason about.

The dependency chain is therefore:

```text
95–106
Semantics + provenance + governance
        ↓
107 Durable state + event semantics
        ↓
108 Consistency + concurrency
        ↓
109 Replication + distributed memory
        ↓
110 Recovery + resilience
```

107 is consequently a **platform contract**, not merely a persistence implementation.

---

## 3. Architectural Model

Novi maintains three related representations:

```text
                    ┌─────────────────────┐
                    │   AUTHORITATIVE     │
                    │     EVENT LOG       │
                    └──────────┬──────────┘
                               │
                         deterministic
                            reducers
                               │
                ┌──────────────┴──────────────┐
                ↓                             ↓
       MATERIALIZED STATE              DERIVED VIEWS
                │                             │
                ↓                             ↓
        current world/cognitive         indexes, retrieval,
        state and subsystem state       analytics, projections
                │
                ↓
            SNAPSHOTS
```

The event log preserves the durable history. Materialized state is optimized for normal runtime access. Derived views are disposable/rebuildable where possible.

No disposable cache may become the sole authoritative representation of a critical state.

---

## 4. Core Invariants

### 4.1 Every durable state mutation is attributable

A durable mutation must identify at least:

- event ID
- event type
- creation timestamp
- logical/causal ordering information
- producer/component identity
- actor/authority context where applicable
- subject/entity affected
- previous state/version reference where applicable
- resulting state/version reference where applicable
- provenance references
- policy/governance context where relevant

### 4.2 Events are immutable

Once committed, an event is not edited in place.

Corrections are represented as new events that supersede, invalidate, retract, or compensate for prior events according to domain rules.

### 4.3 State is versioned

Critical durable state must have an explicit version or revision identity.

A consumer must be able to determine whether it is operating against the state it expected.

### 4.4 Derived data is distinguishable from authoritative data

Novi must distinguish:

```text
AUTHORITATIVE
DERIVED
CACHED
EPHEMERAL
```

A vector index, UI cache, model context cache, or generated summary must not silently become authoritative memory.

### 4.5 Provenance survives projection

When an event becomes memory, knowledge, a world-model fact, a decision, or an action record, its provenance chain must remain addressable.

### 4.6 Safety and governance state cannot be bypassed

The event substrate must not allow an adaptive subsystem to rewrite immutable safety constraints or manufacture authority through ordinary state mutation.

### 4.7 Replay must be deterministic within the declared boundary

Given the same event history and compatible reducer/schema versions, Novi should reproduce the same materialized state.

When exact determinism is impossible because an external dependency is involved, the event must preserve the external result and relevant dependency identity so the historical execution remains explainable.

---

## 5. Event Taxonomy

Events should be typed by semantic domain rather than represented as arbitrary application logs.

### Observation events

Examples:

- `ObservationRecorded`
- `SensorReadingCaptured`
- `PerceptionResultProduced`
- `HumanInteractionObserved`

### Cognitive-state events

Examples:

- `WorldEntityCreated`
- `WorldEntityUpdated`
- `RelationshipChanged`
- `TemporalStateAdvanced`
- `SpatialStateUpdated`

### Memory and knowledge events

Examples:

- `MemoryCreated`
- `MemoryRevised`
- `MemoryInvalidated`
- `KnowledgeCandidateCreated`
- `KnowledgeVerified`
- `KnowledgeRetracted`
- `EmbeddingMaterialized`

### Autonomy and decision events

Examples:

- `AttentionChanged`
- `GoalCreated`
- `GoalPrioritized`
- `PlanCreated`
- `ActionProposed`
- `ActionAuthorized`
- `ActionRejected`
- `ActionExecuted`
- `ActionOutcomeObserved`

### Model and capability events

Examples:

- `ModelSelected`
- `ModelInvocationCompleted`
- `SkillRegistered`
- `SkillVersionActivated`
- `SchemaVersionActivated`

### Governance events

Examples:

- `PolicyChanged`
- `AuthorityGranted`
- `AuthorityRevoked`
- `HumanApprovalRecorded`
- `RetentionRuleChanged`
- `DeletionRequested`
- `DeletionVerified`

The taxonomy must remain extensible, but new event types require ownership, schema definition, versioning, and compatibility rules.

---

## 6. Canonical Event Envelope

The exact serialization format is implementation-specific, but every durable event must semantically contain:

```text
EventEnvelope
├── event_id
├── event_type
├── event_schema_version
├── occurred_at
├── recorded_at
├── producer_id
├── actor_context
├── authority_context
├── subject_refs[]
├── causation_id
├── correlation_id
├── parent_event_refs[]
├── state_revision
├── payload
├── provenance_refs[]
├── policy_context
├── model_context (optional)
├── schema_context
└── integrity_metadata
```

`occurred_at` describes when the event happened in the represented world/runtime. `recorded_at` describes when Novi durably recorded it. These timestamps must not be conflated.

`causation_id` identifies the direct event or request that caused the event. `correlation_id` groups a larger workflow or execution.

---

## 7. State Model

Novi state is divided into four durability classes.

### Class A — Critical durable state

Examples:

- identity
- safety configuration
- governance state
- authorization state
- durable memory
- verified knowledge
- world-model state required for continuity
- active goals/plans where continuity is required

Requirements:

- durable persistence
- versioning
- provenance
- recovery support
- auditability

### Class B — Reconstructable durable state

Examples:

- search indexes
- derived summaries
- embeddings
- materialized analytics
- secondary graph projections

These may be rebuilt from authoritative history and source records.

### Class C — Recoverable runtime state

Examples:

- current task queues
- in-flight workflow state
- temporary context
- retry metadata

These require explicit recovery semantics but do not necessarily become permanent memory.

### Class D — Ephemeral state

Examples:

- transient model context
- temporary buffers
- UI state
- sensor frame caches

Ephemeral state must never be assumed to survive restart.

---

## 8. Transaction and Commit Semantics

107 defines the vocabulary; 108 will define the complete consistency model.

For 107, the minimum contract is:

```text
BEGIN
  ↓
READ expected state/version
  ↓
VALIDATE
  ↓
CREATE events
  ↓
DURABLY COMMIT
  ↓
APPLY / MATERIALIZE
  ↓
PUBLISH derived notifications
```

A state transition must not be externally reported as committed before its authoritative durable record satisfies the configured durability guarantee.

External side effects require a stronger boundary:

```text
intent event
   ↓
authorization
   ↓
side-effect execution
   ↓
outcome event
```

The system must never claim successful physical action solely because an action request was created.

---

## 9. Idempotency

Autonomous systems retry. Therefore durable commands and side effects must support idempotency where technically possible.

Every retryable operation must have a stable operation identity.

```text
request_id
   ↓
operation_id
   ↓
execution attempt 1
execution attempt 2
execution attempt 3
```

Multiple delivery attempts must not accidentally create multiple logical state transitions.

For inherently non-idempotent physical actions, Novi must use explicit execution state and reconciliation rather than pretending retries are safe.

---

## 10. Causality and Ordering

Wall-clock timestamps alone are insufficient to establish causal order.

Novi should preserve:

```text
occurred_at
recorded_at
causation_id
correlation_id
parent_event_refs
logical revision / sequence
```

Where distributed execution is later introduced, 108/109 may add stronger causal mechanisms such as logical clocks, vector clocks, or equivalent revision metadata.

The architecture must never infer causality solely from timestamps.

---

## 11. Snapshots and Checkpoints

Snapshots exist to reduce replay cost, not to replace history.

A snapshot must identify:

- snapshot ID
- state scope
- state revision
- source event position/range
- reducer/schema versions
- creation timestamp
- integrity metadata
- dependency versions where required

```text
EVENT 1 ─ EVENT 2 ─ ... ─ EVENT N
                         │
                      SNAPSHOT
                         │
EVENT N+1 ─ EVENT N+2 ─ ...
```

Recovery may load the latest valid snapshot and replay subsequent events.

Snapshots may be discarded and regenerated if the authoritative history remains intact.

---

## 12. Schema and Reducer Evolution

Event schemas and state reducers evolve.

Every durable event therefore carries a schema version, and every materialized state identifies the reducer/schema versions used to produce it.

Supported evolution mechanisms may include:

- backward-compatible schema extension
- versioned event handlers
- explicit migration events
- projection rebuilds
- snapshot migration

Migration must not silently alter historical meaning.

When a historical event cannot be interpreted by the current runtime, Novi must either retain a compatible historical interpreter or preserve enough information to migrate the representation without changing its semantic meaning.

This directly connects 107 to schema evolution and model/memory co-evolution defined earlier.

---

## 13. Provenance and Dependency Graph

Durable state must support dependency-aware provenance.

A typical chain is:

```text
SOURCE OBSERVATION
      ↓
PERCEPTION RESULT
      ↓
MEMORY / KNOWLEDGE
      ↓
WORLD MODEL
      ↓
DECISION
      ↓
ACTION
      ↓
OUTCOME
```

Each derived object should be able to reference the records from which it was derived.

This enables:

- explanation
- audit
- correction
- model evaluation
- privacy impact analysis
- dependency-aware deletion
- historical reconstruction

The provenance graph may be implemented separately from the event log, but the two must remain referentially consistent.

---

## 14. Failure Semantics

107 must explicitly distinguish:

```text
NOT STARTED
IN PROGRESS
COMMITTED
FAILED
ABORTED
UNKNOWN
RECONCILING
COMPENSATED
```

`UNKNOWN` is important. After a crash during an external side effect, Novi may not know whether the physical operation completed.

The system must not convert uncertainty into false success.

Recovery therefore follows:

```text
failure detected
      ↓
identify last durable state
      ↓
identify in-flight operations
      ↓
reconcile external side effects
      ↓
recover / compensate
      ↓
resume
```

110 will define the full recovery and disaster-resilience architecture.

---

## 15. Offline-First Requirement

The durable substrate must operate without Wi-Fi, Bluetooth, or external network access.

Connectivity-dependent synchronization is an optional downstream capability.

```text
LOCAL EVENT LOG
      ↓
LOCAL STATE
      ↓
LOCAL AUTONOMY

optional later:
LOCAL HISTORY ↔ REMOTE HISTORY
```

Reconnection must never bypass:

- authorization
- safety policy
- provenance
- privacy/retention rules
- deletion requirements
- conflict handling

This preserves Novi's existing offline-first architectural rule.

---

## 16. Storage Selection Requirements

This document does not mandate a database technology.

The eventual implementation must evaluate candidate local/open-source technologies against:

| Requirement | Must support |
|---|---|
| Durable local writes | Yes |
| Transactional semantics | Yes for critical state |
| Ordered/event history | Yes |
| Crash recovery | Yes |
| Embedded/edge operation | Yes |
| Mac development | Yes |
| Jetson deployment | Yes or via supported deployment architecture |
| Offline operation | Yes |
| Backup/export | Yes |
| Encryption support | Required at system level |
| Schema evolution | Required |
| Efficient projections | Required |
| Replication path | Must not block future 109 |

Candidate technologies must be compared objectively rather than selected because they are familiar or vendor-branded.

---

## 17. Boundary Rules

### Cognitive systems may

- create proposed state transitions
- create observations
- create memory candidates
- request transactions
- request authorized actions

### Cognitive systems may not

- rewrite committed history
- modify immutable safety policy directly
- fabricate authority context
- bypass durable recording for critical state
- treat a cache as authoritative without an explicit contract

### Infrastructure may

- persist events
- materialize state
- rebuild projections
- checkpoint
- recover
- enforce durability and integrity guarantees

Infrastructure must not silently reinterpret cognitive semantics.

---

## 18. Security and Integrity

Critical event/state records require integrity protection appropriate to their risk.

The architecture should support:

- authenticated writers
- least-privilege access
- integrity checks
- tamper-evident audit records where required
- encrypted storage
- secure key management
- access audit
- protected deletion workflows

Security metadata must not become a mechanism for adaptive intelligence to grant itself authority.

---

## 19. Performance Targets

Exact production numbers belong in implementation-specific performance specifications. The architectural targets are:

- local critical state writes must be bounded and measurable
- event append must not become the dominant latency of ordinary cognition
- replay time must remain bounded through snapshots/checkpoints
- projection rebuild must be independently measurable
- storage growth must be observable
- retention policies must be enforceable
- Jetson memory/storage constraints must be considered from the beginning

Performance optimization must not weaken durability, provenance, safety, or audit guarantees without an explicit architectural decision.

---

## 20. Testing and Validation

107 requires tests at four levels.

### Unit

- event validation
- schema compatibility
- reducer behavior
- version checks
- idempotency
- causation/correlation handling

### Integration

- append → commit → materialize
- snapshot → replay
- restart recovery
- failed transaction handling
- projection rebuild

### Failure-mode

- process crash during write
- storage failure
- duplicate delivery
- delayed delivery
- corrupted projection
- incompatible schema
- unknown external side effect

### Long-running

- sustained event throughput
- storage growth
- snapshot cadence
- replay performance
- repeated restarts
- memory/knowledge revision over long lifetimes

A test that only verifies the happy path is insufficient for this layer.

---

## 21. Acceptance Criteria

107 is architecturally complete when the implementation plan can demonstrate:

1. A canonical typed event model exists.
2. Critical state has an explicit durability class.
3. Critical mutations have stable identity and provenance.
4. Committed events are immutable.
5. Materialized state can be rebuilt from authoritative history.
6. Snapshots identify the exact history/reducer/schema boundary they represent.
7. Restart recovery semantics are defined.
8. Duplicate/retry behavior is defined.
9. Unknown external side effects are explicitly represented.
10. Schema/reducer evolution is versioned.
11. Offline operation is preserved.
12. Safety/governance state cannot be bypassed through ordinary cognitive writes.
13. The design leaves a clean contract for 108 consistency/concurrency.
14. The design leaves a clean contract for 109 replication.
15. The design supports dependency-aware provenance needed by privacy and governance.

---

## 22. Next Documents

The recommended P1 sequence is now:

```text
107 Durable State, Event Log & Execution Semantics   ← THIS DOCUMENT
        ↓
108 Transactions, Concurrency, Consistency & Conflicts
        ↓
109 Replication, Synchronization & Distributed Memory
        ↓
110 Failure Recovery, Checkpointing & Disaster Resilience
        ↓
111 Privacy, Retention, Dependency-Aware Erasure & Data Lifecycle
        ↓
112 Observability, Evaluation, Drift & Agent Lifespan Reliability
        ↓
113 Resource Governance, Scheduling, Budgets & Quotas
        ↓
114 Multi-Agent Coordination, Delegation & Shared Memory
```

107 is intentionally implementation-neutral. Technology selection should happen after the semantic contract is accepted, not before.

---

## 23. Architectural Decision Summary

**Decision:** Make the durable event/state substrate the first P1 dependency after the 95–106 semantic/governance foundation.

**Rationale:** Replication, recovery, privacy, observability, and multi-agent coordination all require a precise definition of durable state, event identity, causality, versions, commits, and reconstruction.

**Consequence:** Novi's next engineering work should establish the event/state contract and evaluate storage implementations before introducing distributed replication.

**Status:** Proposed. Requires review against the existing 95–106 documents before implementation contracts are frozen.
