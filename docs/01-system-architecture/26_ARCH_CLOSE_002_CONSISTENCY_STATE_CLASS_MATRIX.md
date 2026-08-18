# 26 — ARCH-CLOSE-002 Consistency and State-Class Matrix

**Status:** P0 closure artifact — normative Stage-1 mapping
**Priority:** P0
**Authority:** System Architecture
**Scope:** Stage-1 local consistency, durability, transaction, concurrency, conflict, replication, recovery and deletion requirements
**Depends on:** 107 Durable State, 108 Transactions/Concurrency/Consistency, 109 Replication/Synchronization, 110 Recovery, 111 Privacy/Data Lifecycle, canonical contracts and contract implementation standards

## 1. Purpose

This document closes the ARCH-CLOSE-002 requirement by assigning explicit state classes and operational guarantees to Novi's major durable and runtime state categories.

It does not select a database technology. Storage remains governed by the Stage-1 storage ADR and its benchmark/adoption gate.

The central rule from the consistency architecture is:

> Consistency is a contract attached to state and operations; Novi must not maximize consistency uniformly across the system.

The durable-state architecture likewise distinguishes authoritative history, materialized state, derived views, checkpoints and ephemeral state. These distinctions are preserved here rather than collapsed into a single database consistency policy.

## 2. Consistency vocabulary

The matrix uses the consistency classes established by document 108:

| Class | Meaning | Typical use |
|---|---|---|
| C0 | Ephemeral / best effort | transient buffers, UI/runtime context |
| C1 | Eventual | rebuildable derived indexes, analytics |
| C2 | Session / causal | semantic memory and causally dependent derived state |
| C3 | Transactionally consistent | authoritative local state requiring atomic transitions |
| C4 | Linearizable / strong | consequential authority and real-time control state where required |
| C5 | Strict-serializable | only where transaction + real-time ordering is demonstrably required |

These are architectural contracts, not claims about what a specific storage engine automatically provides.

## 3. Stage-1 boundary

Stage 1 is a single-device/local-first architecture.

Therefore:

- replication is not a Stage-1 dependency;
- distributed consensus is not required for ordinary local state;
- future distributed behavior must preserve the state-class contracts defined here;
- local state must remain valid when disconnected;
- a future replica must not weaken an existing safety or governance guarantee.

The Stage-1 storage ADR explicitly treats SQLite as a candidate rather than an adopted technology and requires benchmark/fault-injection evidence before adoption.

## 4. State-class matrix

| State class | Examples | Source of truth | Durability | Consistency | Transaction requirement | Concurrency | Conflict policy | Stage-1 replication | Recovery | Deletion/erasure |
|---|---|---|---|---|---|---|---|---|---|---|
| Authoritative event history | committed EventEnvelope records | durable event log | permanent/retention governed | C3; stronger if operation semantics require | atomic append + commit | serialized/optimistic by partition | reject duplicate; preserve immutable history; explicit correction events | none required | replayable from last valid position/checkpoint | retention/tombstone policy; immutable history handled by lifecycle rules |
| Critical governance state | safety policy, authority grants/revocations, protected configuration | governed authority store | durable | C4/C5 where real-time/transaction semantics require | atomic policy transition + authorization revalidation | serialized or strongly coordinated | reject unsafe conflict; explicit authority precedence; escalate | none | restore only from validated authoritative state | governed deletion; protected records may have retention constraints |
| Authorization state | capability grants, revocations, execution permissions | authorization authority | durable | C4; freshness bounded for consequential actions | atomic grant/revoke; stale approval rejection | serialized/compare-and-set | newest policy is not sufficient; authority and effective-time rules decide | none | restore with policy/version validation | lifecycle-controlled; revocation must not be undone by ordinary replay |
| Safety/control state | emergency-stop state, safety interlocks, hardware safety state | independent safety/control authority | durable where continuity requires; physical safety path independent | C4/C5 as justified by deployment | atomic safety transition | serialized/independent safety controller | fail-safe/reject; never generic last-write-wins | none | safe-stop/reinitialize according to hardware safety architecture | controlled; safety history retained as required |
| Current world state | entities, relationships, temporal/spatial state used for continuity | world-state materialization derived from authoritative events | durable | C2/C3 depending on decision impact | transactional state transition | optimistic versioning; stronger for consequential invariants | domain-specific merge/reject; preserve provenance | none | rebuild from event history/checkpoint | dependency-aware lifecycle |
| Durable episodic memory | MemoryRecord and revisions | memory authority/event history | durable | C2/C3 | transactional promotion/revision/deletion | optimistic concurrency + revision checks | provenance/evidence-aware conflict resolution; manual review when unresolved | none | reconstruct from history/checkpoints | privacy/retention/dependency-aware erasure |
| Verified knowledge | KnowledgeRecord, verification/retraction state | knowledge authority + provenance | durable | C2/C3; stronger for policy-critical knowledge | atomic promotion/retraction | optimistic; evidence-aware | never generic last-write-wins; retain competing claims when unresolved | none | reconstructible with provenance | lifecycle and dependency-aware erasure |
| Goals | active/persistent goals | autonomy authority | durable while active/retained | C2/C3 | goal transition transaction | optimistic revision control | policy/priority/authority rules; reject invalid transition | none | restore valid active-goal state | goal lifecycle/retention rules |
| Plans | active plans and plan revisions | autonomy planner/state authority | durable when continuity required | C2/C3 | transactional plan revision/activation | optimistic with version checks | supersede/replan; never silently overwrite executed history | none | recover active plan or replan from durable state | lifecycle-controlled; executed history retained |
| Action proposals | proposed actions | autonomy subsystem | durable when needed for audit/traceability | C2/C3 | atomic proposal creation | optimistic | duplicate proposal deduplication; stale proposal invalidation | none | recover pending proposals and reconcile | lifecycle + audit retention |
| Action authorization decisions | Authorization + SafetyDecision associated with action | authorization/safety authority | durable | C4/C5 where consequential | atomic decision with relevant state/policy snapshot | serialized/revalidated | reject stale or conflicting authorization | none | restore only if authority/policy versions remain valid | governed audit retention |
| Action execution state | execution attempts/status | execution subsystem + durable event history | durable | C3; stronger where physical safety requires | execution-state transitions atomic | serialized per physical actuator/resource | explicit state machine; unknown outcome requires reconciliation | none | reconcile in-flight/unknown effects | audit/retention rules |
| Action outcomes | observed result of execution | event history / observation authority | durable for audit and learning | C2/C3 | append-only outcome event | append/idempotent | preserve all observations; reconcile contradictions | none | replayable | retention/privacy rules |
| Model invocation records | model/version/configuration/result metadata | event history / model execution authority | durable for consequential invocations | C3 | atomic invocation/result recording | idempotent by invocation ID | preserve lineage; never overwrite model history | none | reconstruct execution lineage | retention/privacy policy |
| Hardware health | health/fault/degradation status | hardware/control authority | durable enough for diagnostics and safe recovery | C3/C4 depending on safety impact | atomic state transition for fault state | serialized per device/resource | fail-safe; retain fault evidence | none | safe-stop/reinitialize; diagnostics retained | hardware/service lifecycle |
| Configuration | runtime configuration, feature flags, thresholds | configuration authority | durable | C3; C4 when authorization/safety affected | transactional configuration change | compare-and-set/versioned | explicit precedence; reject stale update | none | restore validated version | configuration lifecycle/audit |
| Contract/version metadata | schema versions, compatibility manifest | contract registry/deployment authority | durable | C3 | atomic manifest/migration update | serialized/versioned | reject incompatible deployment | none | restore exact compatible tuple | retain versions needed for historical interpretation |
| Checkpoint metadata | snapshot position, reducer/schema versions | recovery subsystem | durable | C3 | atomic checkpoint commit | serialized per checkpoint scope | reject incomplete/invalid checkpoint | none | validate then replay suffix | retention policy |
| Derived search indexes | inverted indexes, retrieval projections | rebuildable projection from canonical state | rebuildable; persistence optional | C1/C2 | batch/transactional index update | concurrent projection workers | rebuild/reconcile from source; no semantic authority | future optional | delete/rebuild from authoritative state | delete with source lifecycle |
| Embeddings / derived representations | vector indexes, feature projections | model/materialization pipeline | rebuildable where practical | C1/C2 | versioned projection update | concurrent workers | rebuild on model/version conflict | future optional | regenerate from source | dependency-aware deletion |
| Analytics/metrics | aggregate counters, dashboards | derived analytics pipeline | rebuildable | C1 | batch/transactional aggregation as needed | concurrent/partitioned | recompute from source | future optional | recompute | retention policy |
| Runtime queues | task/event queues, retry state | execution/runtime subsystem | recoverable while relevant | C1/C2 | enqueue/dequeue semantics defined per queue | concurrent consumers with idempotency | deduplicate/retry/dead-letter | none | replay/reconcile pending work | expiry/dead-letter lifecycle |
| Transient sensor buffers | recent frames, short-lived samples | local sensor process | ephemeral | C0 | no durable transaction unless promoted | producer-local | drop/overwrite according to buffer policy | none | discarded on restart | automatic expiry |
| Temporary model context | inference context not promoted to durable memory | local cognition runtime | ephemeral | C0/C1 | none unless promoted | process-local | discard | none | discarded | automatic expiry |
| Local caches | cached state/indexes | derived from authoritative source | optional/rebuildable | C0/C1 | no authority transaction | concurrent cache access | invalidate/rebuild; never authoritative by default | none | invalidate/repopulate | cache TTL/clear |

## 5. Required source-of-truth rules

The following ownership rules are normative for Stage 1:

1. **Committed event history is authoritative for historical state-changing events.**
2. **Materialized state is authoritative only where the relevant domain explicitly declares it as a current-state authority; otherwise it is a projection.**
3. **Derived indexes, caches, embeddings and analytics are never authoritative merely because they are persistent.**
4. **Safety and protected authorization state cannot be made subordinate to adaptive cognition or a general-purpose cache.**
5. **A storage engine is an implementation mechanism, not a semantic authority.**
6. **Every promoted durable object must retain a resolvable provenance relationship to its source records where the domain requires provenance.**

## 6. Transaction boundaries

Transactions must be attached to semantic state transitions rather than database convenience.

Examples:

### Memory promotion

```text
candidate memory
    ↓
evidence/provenance validation
    ↓
policy/privacy check
    ↓
transaction commit
    ↓
authoritative MemoryRecord revision
```

### Authorization

```text
request
  ↓
read relevant policy/state versions
  ↓
authorize
  ↓
revalidate before commit when required
  ↓
commit authorization decision
```

### Physical action

```text
ActionProposal
      ↓
Authorization
      ↓
SafetyDecision
      ↓
ActionExecution
      ↓
ActionOutcome
```

Creating an `ActionProposal` is never equivalent to executing the action.

## 7. Concurrency rules

Stage-1 default:

- use optimistic versioning for mutable cognitive/memory state where conflicts are expected to be uncommon;
- use compare-and-set/revision checks to prevent lost updates;
- serialize transitions that affect a single physical actuator/resource;
- use stronger coordination for safety/authorization state when required;
- never use a global lock as a substitute for semantic conflict rules;
- every retryable operation must have explicit idempotency semantics.

Future distributed deployments may introduce stronger coordination or merge mechanisms, but they must preserve the state-class guarantee.

## 8. Conflict policy

Conflict handling is state-specific:

```text
invalid / unsafe state       → reject
stale optimistic write       → retry / rebase / reject
duplicate event              → deduplicate
critical authority conflict → reject + escalate
memory/knowledge conflict   → preserve provenance + evidence-aware resolution
mergeable derived state      → domain-approved merge/rebuild
cache conflict               → invalidate/rebuild
```

`last-write-wins` is not a universal Novi conflict policy and is prohibited for critical semantic, authorization or safety state unless a future explicit architecture decision proves it safe for a narrowly defined state.

## 9. Replication policy

Replication is not required for Stage 1.

If later introduced:

- C0/C1 projections may tolerate bounded staleness;
- C2 state must preserve causal dependencies;
- C3 state must preserve its transactional commit semantics;
- C4/C5 authority and safety state require explicit freshness/coordination rules;
- no replica may manufacture authority while disconnected;
- deletion/tombstone semantics must propagate according to privacy requirements;
- replicated records must preserve identity, provenance, version and integrity metadata.

These rules align with the existing distributed-memory architecture, which requires explicit consistency classes and prohibits treating all replicated state as equally authoritative.

## 10. Recovery policy

Recovery follows the authoritative state class:

```text
C0 → discard / reinitialize
C1 → rebuild projection
C2 → restore valid state + causal reconciliation
C3 → restore last valid commit/checkpoint + replay
C4/C5 → restore only validated authoritative state and re-establish safety/authority before consequential operation
```

An unknown external side-effect outcome must remain `UNKNOWN` until reconciled. Recovery must never manufacture success from absence of an error.

## 11. Deletion and erasure

Deletion semantics are part of the state contract.

For privacy-sensitive state, deletion must account for:

- authoritative record;
- replicas when later introduced;
- derived indexes;
- embeddings and projections;
- caches;
- provenance/dependency records;
- tombstones required to prevent resurrection.

Not every audit or safety record can necessarily be deleted immediately; retention obligations must be determined by the dedicated privacy and governance authorities.

## 12. Stage-1 implementation requirements

Before storage adoption, implementation evidence must demonstrate at minimum:

- atomic commit for C3+ state;
- stale-version rejection;
- idempotent retries;
- crash recovery;
- deterministic checkpoint/replay behavior where applicable;
- conflict detection for concurrent writes;
- projection rebuild from authoritative state;
- dependency-aware deletion behavior;
- preservation of contract/version/provenance metadata.

The storage ADR remains **PROPOSED — NOT YET ADOPTED** until its benchmark and fault-injection gate is satisfied.

## 13. Validation plan

ARCH-CLOSE-002 validation must eventually include:

| Validation | Evidence type |
|---|---|
| state-class matrix completeness | static/document validation |
| source-of-truth ownership | architecture review + cross-reference audit |
| transaction semantics | integration tests |
| concurrent update conflicts | concurrency tests |
| idempotency | retry tests |
| recovery mapping | crash/restart tests |
| projection rebuild | integration/replay tests |
| deletion/erasure | lifecycle tests |
| future replication rules | simulation/distributed tests |

No state class should be marked fully implemented merely because its row exists in this document.

## 14. Evidence and closure status

This document provides the required architectural state-class mapping for ARCH-CLOSE-002.

**Current state:** architectural mapping defined; implementation and empirical validation pending.

The closure item must not be marked fully complete until the required state-class guarantees are implemented and tested, and the evidence is recorded in the architecture closure register.

## 15. Authoritative dependencies and research basis

Internal authoritative dependencies:

- `06_107_DURABLE_STATE_EVENT_LOG_EXECUTION_SEMANTICS.md` — durable history, state classes, commit, replay and provenance.
- `07_108_TRANSACTIONS_CONCURRENCY_CONSISTENCY_AND_CONFLICT_RESOLUTION.md` — consistency classes, transactions, concurrency and conflict semantics.
- `07_109_REPLICATION_SYNCHRONIZATION_AND_DISTRIBUTED_MEMORY_ARCHITECTURE.md` — future distributed consistency and replication requirements.
- `08_110_RECOVERY_CHECKPOINTING_AND_DISASTER_RESILIENCE_ARCHITECTURE.md` — recovery and resilience.
- `09_111_PRIVACY_RETENTION_DEPENDENCY_AWARE_ERASURE_AND_DATA_LIFECYCLE_ARCHITECTURE.md` — deletion and lifecycle semantics.
- `17_CONTRACT_IMPLEMENTATION_AND_SCHEMA_STANDARD.md` — contract/version/provenance implementation requirements.
- `18_STAGE_1_DURABLE_STATE_STORAGE_ADR.md` — Stage-1 storage selection and evidence gate.

External research basis is maintained by the authoritative architecture documents. Technology capabilities must be validated against primary vendor/standards sources before becoming a P0 technology decision.

## 16. Architectural invariant

> **Every meaningful Novi state has an explicit owner, durability class, consistency guarantee, transaction boundary, concurrency model, conflict policy, recovery path and lifecycle rule.**
