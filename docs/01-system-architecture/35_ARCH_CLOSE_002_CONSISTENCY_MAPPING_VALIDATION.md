# 35 — ARCH-CLOSE-002 Consistency Mapping Validation

**Status:** VALIDATED — architecture evidence recorded
**Priority:** P0
**Authority:** System Architecture

## 1. Purpose

Validate that the canonical state-class matrix gives each important Novi state class an explicit owner, durability, consistency, transaction, concurrency, conflict, replication, recovery and lifecycle policy.

## 2. Required matrix dimensions

Every durable or safety-relevant state class must define:

- source-of-truth owner;
- durability requirement;
- consistency class;
- transaction boundary;
- concurrency model;
- conflict policy;
- replication requirement;
- recovery requirement;
- deletion/erasure behavior;
- Stage-1 local versus future distributed scope.

## 3. Canonical state classes

| State class | Owner | Durability | Consistency | Transaction | Concurrency | Conflict | Replication | Recovery | Lifecycle |
|---|---|---|---|---|---|---|---|---|---|
| Authoritative event | Event/contract subsystem | Durable | Strong append ordering | Atomic append | Serialized append | Reject/diagnose | Optional future | Replay | Retention policy |
| Observation | Perception | Short/durable by provenance policy | Ordered-by-time semantics | Event append | Concurrent producers | Preserve provenance | Optional | Replay | Retention policy |
| Evidence | Validation/knowledge | Durable | Immutable | Atomic append | Append-only | Reject mutation | Future replicated | Replay | Retention/erasure policy |
| World state | World-model owner | Durable checkpoint + reconstructable events | Versioned | State transition transaction | Controlled | Version/conflict policy | Future | Event replay + checkpoint | Snapshot/retention |
| Memory record | Memory | Durable | Strong identity, governed updates | Atomic record transaction | Controlled | Versioned/authorized | Future | Backup + replay | Retention/erasure |
| Knowledge record | Knowledge | Durable | Versioned | Atomic update | Controlled | Provenance/version conflict | Future | Backup | Retention/erasure |
| Goal | Autonomy | Durable when committed | Strong identity | Atomic lifecycle transition | Single owner | Explicit replacement/termination | Future | Checkpoint/replay | Lifecycle policy |
| Plan | Autonomy | Durable while active | Versioned | Atomic publication | Single active revision | Supersede | Future | Reconstruct | Expire/archive |
| Action proposal | Autonomy | Auditable | Immutable | Atomic append | Concurrent proposals allowed | Reject stale/duplicate | Optional | Replay | Retention |
| Authorization | Governance/safety | Durable audit record | Strong | Atomic decision | Serialized per authority scope | Reject ambiguity | Future | Replay | Audit retention |
| Safety decision | Safety | Durable audit record | Strong | Atomic decision | Serialized per action | Fail-safe/reject | Future | Replay | Audit retention |
| Action execution | Control | Durable audit + live state | Strong for lifecycle | Atomic transition | Single execution owner | Reject duplicate | Future | Reconcile/replay | Retention |
| Action outcome | Control/evidence | Durable | Immutable | Atomic append | Append-only | Reject mutation | Future | Replay | Retention |
| Model invocation | Brain/model runtime | Durable audit, payload policy-dependent | Versioned | Atomic invocation record | Concurrent | Correlate by invocation ID | Future | Replay metadata | Retention/privacy |
| Hardware health | Hardware/health | Current + durable fault history | Strong for safety fields | Atomic snapshot | Concurrent sensors, single reducer | Sensor arbitration | Future | Last-known + fault state | Current + history |
| Deployment manifest | Deployment | Durable, immutable by revision | Strong/versioned | Atomic publication | Single publisher | Reject conflicting revision | Future | Reinstall/reproduce | Version retention |
| Configuration | Configuration authority | Durable | Strong/versioned | Atomic commit | Controlled | Explicit version conflict | Future | Backup/restore | Versioned/erasure policy |
| Embedding/index | Derived memory/knowledge | Rebuildable | Eventual | Batch transaction | Parallel workers | Rebuild from source | Optional | Rebuild | Rebuild/replace |
| Cache | Owning subsystem | Ephemeral | Eventual | None/atomic local update | Concurrent | Drop/recompute | No | Recompute | TTL/eviction |
| Work queue | Owning runtime | Bounded; class-dependent | Ordered where required | Enqueue/dequeue transaction | Controlled workers | Reject duplicate/stale | No Stage-1 | Drain/restart policy | TTL/drop/coalesce |

## 4. Architectural rules validated

1. **One authoritative owner:** derived state cannot silently become a second source of truth.
2. **Safety state is strong:** authorization, safety decisions and execution lifecycle cannot use eventual consistency as their authoritative semantics.
3. **Historical records are immutable:** evidence, decisions and outcomes are appended/versioned rather than rewritten.
4. **Derived state is rebuildable:** caches, indexes and embeddings must not be required to recover authoritative state.
5. **Queues are bounded:** queue growth cannot become an implicit durability mechanism.
6. **Stage-1 is local-first:** replication is not required for correctness in the first local runtime, but interfaces must not prevent later distributed operation.
7. **Privacy lifecycle is explicit:** deletion/erasure policies must be defined for persisted observations, memory, knowledge, model records and derived artifacts.
8. **Recovery is source-driven:** recovery uses authoritative events/checkpoints rather than reconstructing truth from caches.

## 5. Consistency classes

Novi uses four practical classes:

- **Strong:** authoritative safety/governance/control lifecycle and identity-sensitive state.
- **Ordered/event:** append-only records whose correctness depends on causal/temporal ordering.
- **Versioned:** durable mutable state where readers must identify the revision.
- **Eventual/rebuildable:** derived caches, indexes and embeddings where authoritative source state remains available.

The class is attached to the state semantics, not selected merely for database convenience.

## 6. Stage-1 versus future distributed behavior

Stage-1 assumes a local Novi runtime. This does **not** mean all state is treated as one transaction or one consistency domain. State ownership and transaction boundaries remain explicit.

Future distributed operation may introduce replication, partition handling and conflict resolution, but distributed complexity must not be introduced into Stage-1 unless required by a measured use case.

## 7. Validation method

Validation was performed against the closure requirements and the canonical contract boundaries. Each state class has a defined source of truth, lifecycle and recovery path. No class relies on a cache/index/embedding as authoritative truth.

The matrix is an architecture baseline; implementation-specific transaction and performance behavior remains subject to the storage benchmark and runtime validation gates.

## 8. Evidence and limitations

This document establishes **architecture-level consistency mapping evidence**. It does not claim that SQLite, another database, or a distributed implementation has already demonstrated the stated guarantees under physical load.

ARCH-CLOSE-003 remains responsible for empirical storage/concurrency/recovery evidence. ARCH-CLOSE-006 remains responsible for timing semantics. ARCH-CLOSE-009 remains responsible for mapping each invariant to executable validation.

## 9. Closure decision

**ARCH-CLOSE-002: VALIDATED at the architecture-definition level.**

Remaining implementation evidence is explicitly delegated to the corresponding closure workstreams rather than blocking this architecture mapping itself.
