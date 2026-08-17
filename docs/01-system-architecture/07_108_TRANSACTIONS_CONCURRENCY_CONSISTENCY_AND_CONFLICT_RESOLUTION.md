# 108 — Transactions, Concurrency, Consistency & Conflict Resolution Architecture

## Status

**NORMATIVE ARCHITECTURE — P1 / CRITICAL FOUNDATION**

## Purpose

Define how Novi safely coordinates concurrent reads, writes, state transitions, memory corrections, model updates, policy changes, human interventions and future distributed operations on top of the durable state and event semantics established by document 107.

This document deliberately does **not** assume that every Novi state requires the strongest possible consistency. Instead, each state class must declare the weakest consistency and concurrency guarantees that preserve its semantic correctness, safety and governance requirements.

## 1. Core Principle

> **Consistency is a contract attached to state and operations, not a property that should be maximized uniformly across the entire system.**

Distributed-systems literature distinguishes multiple consistency models with different safety, availability and coordination costs. Linearizability constrains single-object operations according to real-time order; serializability constrains concurrent transactions to histories equivalent to a serial execution; stronger combinations such as strict serializability impose both transaction ordering and real-time constraints. citeturn0search0turn0search1

## 2. Why 108 Follows 107

107 defines:

```text
EVENT
STATE
VERSION
COMMIT
SNAPSHOT
CHECKPOINT
```

108 defines when concurrent transitions are valid:

```text
CONCURRENT OPERATIONS
        ↓
CONFLICT ANALYSIS
        ↓
CONSISTENCY CONTRACT
        ↓
COMMIT / ABORT / RETRY / MERGE
```

Without this layer, replication and multi-agent coordination would distribute undefined conflict semantics.

## 3. Transaction

A transaction is a bounded logical unit of state transitions with explicit success, failure and visibility semantics.

A transaction should define:

- transaction ID;
- actor/principal;
- read set;
- write set;
- preconditions;
- consistency requirement;
- isolation requirement;
- authorization context;
- idempotency key where applicable;
- commit result;
- provenance.

## 4. Atomicity

Where a transaction is declared atomic:

```text
ALL REQUIRED EFFECTS
      ↓
COMMIT

OR

NO COMMITTED EFFECTS
      ↓
ABORT
```

Atomicity must be scoped. External side effects cannot automatically be rolled back merely because an internal transaction aborts.

## 5. Internal vs External Effects

Novi must distinguish:

```text
DURABLE INTERNAL STATE
        ≠
EXTERNAL SIDE EFFECT
```

Examples of external effects include sending a message, moving a physical device, charging a payment instrument, or invoking an irreversible external API.

Compensation, confirmation and authorization semantics must be explicit for such effects.

## 6. Commit Boundary

A commit establishes which state changes become durable and visible under the applicable consistency contract.

```text
PREPARE
 ↓
VALIDATE
 ↓
AUTHORIZE
 ↓
COMMIT
 ↓
PUBLISH / OBSERVE
```

The exact ordering is operation-specific but must be defined rather than implied.

## 7. Isolation

Isolation describes what concurrent transactions can observe about one another.

Novi must not use the word "transactional" as if it implied one universal isolation guarantee.

## 8. Common Isolation Levels

Where relational semantics are relevant, the architecture may expose:

```text
READ UNCOMMITTED
READ COMMITTED
REPEATABLE READ
SNAPSHOT ISOLATION
SERIALIZABLE
```

Their actual guarantees and anomalies must be documented for the implementation used.

## 9. Serializability

Serializable execution means the concurrent history is equivalent to some serial execution.

Classical database theory establishes serialization as a central correctness criterion for concurrent database systems. citeturn0search4

Novi should use serializability when invariants require transaction-level ordering across multiple objects and weaker guarantees cannot preserve correctness.

## 10. Linearizability

Linearizability applies to operations whose externally visible behavior must appear atomic and consistent with real-time ordering.

It is a strong guarantee and can reduce availability during network partitions. citeturn0search1

It should therefore be reserved for state where real-time semantics materially matter.

## 11. Strict Serializability

For operations requiring both serializable transactions and real-time ordering, Novi may require strict serializability.

This is stronger than either ordinary serializability or ordinary linearizability alone. citeturn0search0

## 12. Causal Consistency

Causal consistency preserves causal ordering without requiring one global real-time order for all unrelated operations.

It may be appropriate for some memory and knowledge flows where causal dependencies matter but global serialization is unnecessarily expensive.

## 13. Session Guarantees

Where appropriate, Novi may provide session-level guarantees such as:

```text
READ YOUR WRITES
MONOTONIC READS
MONOTONIC WRITES
WRITES FOLLOW READS
```

These can be useful for user and agent sessions without requiring global strong consistency. Consistency literature distinguishes these guarantees from stronger global models. citeturn0search0turn0search7

## 14. Eventual Consistency

Eventual consistency may be acceptable for derived, non-critical state when temporary divergence does not violate safety or semantic invariants.

It must never be selected merely because it is easier to implement.

## 15. Consistency Classes

Novi should classify state explicitly:

```text
C0 — EPHEMERAL / BEST EFFORT
C1 — EVENTUAL
C2 — SESSION / CAUSAL
C3 — TRANSACTIONALLY CONSISTENT
C4 — LINEARIZABLE
C5 — STRICT SERIALIZABLE
```

Deployments may define additional classes.

## 16. State-to-Consistency Mapping

Example:

```text
CACHE
→ C0/C1

DERIVED SEARCH INDEX
→ C1/C2

SEMANTIC MEMORY
→ C2/C3

IDENTITY / AUTHORIZATION STATE
→ C4 or stronger as required

SAFETY INTERLOCK
→ C4/C5 where the implementation requires it
```

These are starting points, not universal prescriptions.

## 17. Invariants

A state invariant is a condition that must remain true across valid committed states.

Examples:

```text
IDENTITY_ID IS UNIQUE
AUTHORIZATION CANNOT EXCEED GRANTED SCOPE
DELETED DATA CANNOT BE REVIVED BY ORDINARY RETRY
SKILL PROMOTION REQUIRES REQUIRED EVIDENCE
```

## 18. Invariant Protection

A transaction must validate every invariant it can affect before commit.

If an invariant cannot be established:

```text
COMMIT
```

must not silently proceed.

Possible outcomes:

```text
ABORT
RETRY
ESCALATE
QUARANTINE
```

## 19. Read Set / Write Set

Transactions should track, explicitly or equivalently:

```text
READ SET
WRITE SET
```

This enables conflict detection and more precise retry behavior.

## 20. Conflict Types

At minimum distinguish:

```text
READ-WRITE
WRITE-READ
WRITE-WRITE
DELETE-WRITE
AUTHORIZATION-WRITE
SCHEMA-WRITE
POLICY-WRITE
```

## 21. Lost Update

A classic failure is:

```text
T1 reads X=1
T2 reads X=1
T1 writes X=2
T2 writes X=3
```

If T2 silently overwrites T1, the system loses a committed update.

Novi must prevent or explicitly resolve this according to the state contract.

## 22. Write Skew

Snapshot-based approaches can allow transactions to make individually valid writes that jointly violate an invariant.

For example:

```text
T1: doctor A remains on call
T2: doctor B remains on call
```

If the invariant requires at least one of them to remain on call, independent writes can produce an invalid combined state.

The implementation must detect such cross-object conflicts when the invariant requires it.

## 23. Fractured Reads

A reader must not observe a combination of state versions that the declared consistency model prohibits.

```text
ENTITY = V2
POLICY = V1
MODEL = V3
```

may be invalid for a decision requiring a coherent snapshot.

## 24. Stale Reads

Stale reads are acceptable only when explicitly permitted by the state contract.

They are unacceptable when the reader is making a consequential decision requiring current authorization or safety state.

## 25. Check-and-Set

For simple concurrent state transitions, Novi should support compare-and-swap semantics:

```text
IF VERSION = V7
THEN WRITE V8
ELSE CONFLICT
```

This is preferable to blind overwrites for many versioned memory updates.

## 26. Optimistic Concurrency

Optimistic concurrency is appropriate when conflicts are relatively uncommon:

```text
READ V7
 ↓
COMPUTE
 ↓
COMPARE V7
 ↓
WRITE V8
```

If the version changed:

```text
REJECT / REBASE / RETRY
```

## 27. Pessimistic Concurrency

Locks or leases may be appropriate when conflicts are expensive or dangerous, but they introduce deadlock, availability and operational complexity.

Locks must therefore have:

- owner;
- scope;
- expiry or recovery semantics;
- acquisition policy;
- release policy;
- failure behavior.

## 28. Locking Is Not a Universal Solution

A distributed lock does not automatically make a system correct.

The underlying state transition still requires validation and durable commit semantics.

## 29. Leases

For distributed ownership, time-bounded leases may be preferable to indefinite locks.

Lease expiration must account for clock uncertainty and delayed communication.

## 30. Deadlocks

Where locks exist, Novi must detect or prevent deadlocks.

Possible strategies include:

```text
TIMEOUT
WAIT-FOR GRAPH
LOCK ORDERING
ABORT VICTIM
```

## 31. Idempotency

Operations that may be retried must have explicit idempotency semantics.

```text
REQUEST ID X
 ↓
RETRY X
 ↓
ONE LOGICAL EFFECT
```

Idempotency is especially important after timeouts because the client may not know whether the original operation committed.

## 32. Exactly-Once Semantics

Novi should not casually promise exactly-once execution across arbitrary distributed side effects.

Prefer explicit combinations of:

```text
AT-LEAST-ONCE DELIVERY
+
IDEMPOTENT HANDLER
+
DEDUPLICATION
```

or transactional/atomic mechanisms where genuinely supported.

## 33. Retry Safety

Every retriable operation must declare:

```text
SAFE TO RETRY
CONDITIONALLY RETRIABLE
NOT RETRIABLE
```

## 34. Compensation

For external effects that cannot be rolled back:

```text
FAILED TRANSACTION
 ↓
COMPENSATING ACTION
```

Compensation is not equivalent to rollback and must be represented as its own event.

## 35. Transaction Dependencies

Transactions may depend on prior transactions through:

```text
WRITE → READ
READ → WRITE
WRITE → WRITE
```

Dependency graphs can expose cycles and consistency violations. citeturn0search7

## 36. Causal Ordering

When an operation depends on another operation's result, Novi must preserve the relevant causal relationship even if the operations execute on different nodes in the future.

## 37. Real-Time Ordering

Where a state contract requires real-time semantics:

```text
A COMPLETES
 ↓
B STARTS
```

B must not be ordered as if it preceded A.

Real-time dependencies distinguish strong/strict serializable models from weaker serializability variants. citeturn0search14

## 38. Conflict Resolution Policy

Every conflict class must have a defined policy:

```text
REJECT
RETRY
LAST-WRITER-WINS
FIRST-WRITER-WINS
MERGE
MANUAL REVIEW
QUARANTINE
```

No generic conflict resolver should silently apply the same rule to every state.

## 39. Last-Writer-Wins Is Dangerous for Semantic Memory

For example:

```text
MEMORY A: "Alice lives in London"
MEMORY B: "Alice lives in Paris"
```

Timestamp ordering alone does not necessarily establish which statement is semantically correct.

The system should use temporal validity, provenance, identity, evidence and authority from documents 97–106 before resolving the conflict.

## 40. Semantic Merge

Some state can be merged:

```text
TAG SET A ∪ TAG SET B
```

Other state cannot safely be merged:

```text
CURRENT AUTHORIZED PRINCIPAL A
vs
CURRENT AUTHORIZED PRINCIPAL B
```

Mergeability must therefore be part of the schema/state contract.

## 41. CRDT-Compatible State

Where operations are naturally commutative, associative and idempotent, Novi may use CRDT-like structures.

This is particularly attractive for suitable replicated collections, counters and sets.

It must not be used to force semantic merges where conflicts require authority or evidence.

## 42. Human Conflict Resolution

High-impact semantic conflicts may require:

```text
CONFLICT
 ↓
EVIDENCE PACKET
 ↓
HUMAN REVIEW
 ↓
RESOLVE / DEFER
```

This integrates 106.

## 43. Identity Conflict

If two concurrent operations produce competing identity mappings:

```text
OBS A → ENTITY 123
OBS B → ENTITY 456
```

Novi must not merge them merely because one update arrived later.

Identity resolution follows document 97's evidence and confidence semantics.

## 44. Temporal Conflict

Conflicting temporal claims should preserve their validity intervals and observation times rather than collapsing them into a single timestamp.

This integrates 98.

## 45. Spatial Conflict

Conflicting location claims should retain precision, acquisition conditions and spatial uncertainty.

This integrates 99.

## 46. Causal Conflict

Competing causal hypotheses should coexist when evidence is insufficient to discriminate.

```text
H1: A → B
H2: C → B
```

Conflict resolution must not turn uncertainty into a false single answer.

This integrates 100.

## 47. Cross-Modal Conflict

Multiple modalities may disagree:

```text
VISION → CLOSED
SENSOR → OPEN
TEXT → OPEN
```

The resolver must consider provenance, independence, temporal alignment and reliability rather than majority vote alone.

This integrates 101.

## 48. Skill Conflict

Concurrent evidence may increase or decrease competence.

A new failure must not be lost because a previous success was written later.

Competence state should be updated through evidence-aware aggregation defined by 102.

## 49. Schema Conflict

A transaction operating under schema V2 must not blindly overwrite data produced under incompatible schema V3.

Schema compatibility checks from 103 are transaction preconditions where relevant.

## 50. Model/Memory Conflict

If model M2 writes a derived claim while M3 concurrently updates the interpretation layer, the system must preserve lineage to both model versions.

104's model/memory co-evolution rules remain authoritative.

## 51. Policy Conflict

Policy changes require explicit precedence and activation semantics.

An old policy must not be silently applied to a new authorization request after the new policy becomes effective.

## 52. Human Decision Conflict

Two authorized humans may disagree.

The system should preserve:

```text
DECISION A
DECISION B
AUTHORITY
TIME
RATIONALE
```

and invoke the deployment's escalation policy rather than silently choosing the most recent reviewer.

## 53. Transactional Authorization

Authorization should be checked against the relevant state snapshot and policy version.

```text
AUTHORIZE
 ↓
STATE CHANGES
 ↓
COMMIT
```

If authorization assumptions changed before commit, revalidation may be required.

## 54. Stale Approval Protection

A transaction must not use a stale human approval if its scope, target, policy or material state assumptions changed.

## 55. Safety-Critical State

Safety-critical state should use stronger consistency and commit semantics than ordinary derived memory where required.

The exact guarantee is deployment-specific and must be justified.

## 56. Memory Promotion Transactions

Promotion from candidate memory to durable knowledge should be transactional:

```text
CANDIDATE
 ↓
EVIDENCE VALIDATION
 ↓
POLICY CHECK
 ↓
PROMOTION COMMIT
```

Partial promotion must not create an apparently authoritative record without its required provenance.

## 57. Memory Deletion Transactions

Deletion should atomically update all required indexes and dependency records, or expose an explicit transitional state.

```text
DELETE REQUEST
 ↓
DEPENDENCY CHECK
 ↓
COMMIT
 ↓
INDEX / CACHE INVALIDATION
```

This prepares for 111.

## 58. Model Promotion Transactions

Model promotion should similarly bind:

```text
MODEL VERSION
EVALUATION RESULT
POLICY APPROVAL
DEPLOYMENT STATE
```

A deployment record must not claim M3 is active while enforcement still routes traffic to M2.

## 59. Skill Promotion Transactions

Skill promotion should bind evidence, environment, hardware, model version and competence status atomically enough to prevent partial authoritative promotion.

## 60. Snapshot Semantics

A transaction may require a coherent snapshot of multiple state classes:

```text
IDENTITY V
MEMORY V
MODEL V
POLICY V
SKILL V
```

The snapshot must declare whether these versions are guaranteed to be mutually consistent.

## 61. Snapshot Isolation

Snapshot isolation can provide stable transaction views but does not automatically prevent every anomaly, including write skew.

Therefore the architecture must not equate snapshot isolation with serializability.

## 62. Read-Only Transactions

Read-only operations may still require a coherent snapshot if they produce consequential recommendations.

A query is not harmless merely because it performs no writes.

## 63. Long-Running Transactions

Long-running reasoning processes should avoid holding database locks for the duration of inference.

Prefer:

```text
READ SNAPSHOT
 ↓
COMPUTE
 ↓
VALIDATE FRESHNESS
 ↓
COMMIT
```

## 64. Stale Computation

If state changes materially while a long computation runs:

```text
SNAPSHOT V10
 ↓
COMPUTE
 ↓
CURRENT V14
```

The result may require recomputation or explicit conflict handling.

## 65. Compare-and-Commit

The default pattern for many expensive reasoning operations should be:

```text
READ V
 ↓
REASON
 ↓
RECHECK V
 ↓
COMMIT
```

This prevents stale reasoning from blindly overwriting newer state.

## 66. Determinism

Conflict resolution should be deterministic where the same inputs and policy are expected to produce the same result.

If resolution depends on nondeterministic model output, the output and model version must become part of the provenance.

## 67. Ordering Keys

Event IDs, logical clocks, sequence numbers or equivalent ordering metadata may be used to establish deterministic ordering.

A timestamp alone should not be assumed to provide a globally correct total order.

## 68. Logical Clocks

For distributed future implementations, logical or hybrid logical clocks may help represent causality and ordering without assuming perfectly synchronized physical clocks.

## 69. Clock Uncertainty

Physical timestamps should include uncertainty where required.

A timestamp with millisecond precision does not prove that two distributed events were ordered to millisecond precision.

## 70. Concurrency Detection

Novi should be able to distinguish:

```text
ORDERED
CAUSALLY ORDERED
CONCURRENT
UNKNOWN
```

rather than forcing every pair of events into a total order.

## 71. Unknown Ordering

When ordering cannot be established safely:

```text
UNKNOWN
```

is preferable to fabricated ordering.

## 72. Transaction Retry

Retries must preserve the original logical transaction identity while creating distinct execution attempts:

```text
TRANSACTION T7
 ├── ATTEMPT 1
 ├── ATTEMPT 2
 └── ATTEMPT 3
```

This prevents retries from being mistaken for independent operations.

## 73. Abort Semantics

An aborted transaction must be distinguishable from an operation that never executed.

Relevant evidence should remain available for audit without accidentally exposing aborted effects as committed state.

## 74. Partial Failure

A transaction may fail after some external effects occurred.

The architecture must record:

```text
INTENDED
COMMITTED INTERNAL
EXTERNAL EFFECTS
COMPENSATION
FINAL STATUS
```

## 75. Uncertain Commit

After a timeout, Novi may not know whether a transaction committed.

The correct response is:

```text
UNKNOWN COMMIT
 ↓
QUERY STATUS / DEDUPLICATE
```

not automatic blind retry.

## 76. Transaction Status Model

At minimum:

```text
CREATED
RUNNING
PREPARED
COMMITTED
ABORTED
FAILED
UNKNOWN
COMPENSATING
COMPENSATED
```

## 77. Conflict Status

Conflicts should be explicit:

```text
DETECTED
CLASSIFIED
WAITING
AUTO-RESOLVED
HUMAN-RESOLVED
UNRESOLVED
QUARANTINED
```

## 78. Quarantine

If a conflict affects safety, identity, authorization, privacy or high-impact knowledge, the affected state may be quarantined rather than merged automatically.

## 79. Conflict Provenance

Every automatic conflict resolution should record:

```text
INPUT VERSIONS
CONFLICT TYPE
RESOLUTION POLICY
RESOLUTION RESULT
MODEL VERSION IF USED
EVIDENCE
TIME
```

## 80. No Silent Conflict Loss

A system must not report success while silently discarding a concurrent valid update unless the declared policy explicitly permits that loss and the loss is auditable.

## 81. Consistency vs Availability

Strong consistency often requires coordination and can reduce availability under partitions. This is a fundamental tradeoff, not merely an implementation inconvenience. citeturn0search0turn0search24

Novi must therefore select guarantees per workload rather than globally maximizing consistency.

## 82. CAP/PACELC Awareness

The architecture should document relevant partition and latency tradeoffs for distributed deployments.

It must not use CAP as a simplistic slogan to justify arbitrary consistency choices.

## 83. Multi-Object Invariants

If a rule spans multiple objects:

```text
OBJECT A
+
OBJECT B
+
OBJECT C
```

then per-object consistency may be insufficient.

The transaction scope must cover the invariant or use an alternative coordination mechanism that preserves it.

## 84. Cross-Subsystem Transactions

Avoid broad distributed transactions where possible.

Prefer explicit event choreography, sagas or compensating workflows when external services cannot share one transaction boundary.

## 85. Saga Semantics

A saga is a sequence of local transactions with compensating actions for failures.

```text
T1 → T2 → T3
          ✗
       C2 → C1
```

Compensations must be idempotent and separately audited.

## 86. Event Publication

If a committed state change must publish an event, Novi should avoid the failure mode:

```text
STATE COMMITTED
EVENT LOST
```

or:

```text
EVENT PUBLISHED
STATE NOT COMMITTED
```

An outbox or equivalent atomic publication mechanism may be used.

## 87. Transaction/Event Boundary

Where 107 uses events as durable state transitions, 108 must specify whether the event is:

```text
THE COMMITTED FACT
```

or:

```text
A DERIVED NOTIFICATION OF A COMMITTED FACT
```

These are not interchangeable.

## 88. Duplicate Events

Consumers must tolerate duplicate delivery where delivery is at-least-once.

Deduplication should use stable event IDs or transaction IDs.

## 89. Out-of-Order Events

Consumers must declare whether they support:

```text
ORDERED
OUT-OF-ORDER
LATE
```

processing and how late events affect derived state.

## 90. Reordering

Reordering should not alter durable factual history unless the event model explicitly defines a correction/revision event.

## 91. Conflict Resolution and 103

Schema migration may change the shape of conflict records.

Migration must preserve enough information to interpret historical conflicts and their resolution provenance.

## 92. Conflict Resolution and 104

Model updates must not retroactively change the recorded result of an earlier conflict resolution.

A new model may produce a new recommendation about the conflict, but historical resolution remains historical.

## 93. Conflict Resolution and 105

Policy determines which conflicts may be auto-resolved and which require escalation.

For example:

```text
CACHE CONFLICT
→ AUTO-MERGE

AUTHORIZATION CONFLICT
→ DENY / ESCALATE
```

## 94. Conflict Resolution and 106

Human review is an explicit resolution mode, not an invisible fallback.

## 95. Testing Requirements

108 requires concurrency testing with:

- simultaneous writes;
- stale reads;
- lost-update scenarios;
- write skew;
- duplicate retries;
- uncertain commits;
- process crashes;
- delayed messages;
- out-of-order events;
- conflicting human corrections;
- concurrent model promotion;
- policy changes during authorization;
- schema changes during transactions.

## 96. Fault Injection

Future distributed implementations should use failure-injection tooling to validate claimed consistency guarantees under delays, partitions, crashes and message reordering.

Jepsen is an established example of a framework that executes histories under faults and checks whether observed behavior satisfies declared consistency properties. citeturn0search10

## 97. History-Based Verification

The implementation should produce test histories that can be checked against the declared consistency model.

A passing unit test is not sufficient evidence for distributed consistency.

## 98. Invariant-Based Verification

Tests should verify both:

```text
CONSISTENCY MODEL
+
APPLICATION INVARIANTS
```

A system can satisfy a generic consistency model while still violating a domain-specific invariant.

## 99. Performance Measurement

Measure:

- commit latency;
- abort rate;
- retry rate;
- conflict rate;
- lock wait time;
- snapshot age;
- stale-read rate;
- coordination overhead;
- throughput under contention.

## 100. No Global Strong-Consistency Default

Novi must not impose strict serializability on all state by default.

The architecture should make stronger guarantees available where justified and weaker guarantees available where safe.

## 101. Consistency Contract Schema

Every important state class should declare at least:

```text
STATE_CLASS
CONSISTENCY_LEVEL
ISOLATION_LEVEL
INVARIANTS
CONFLICT_POLICY
RETRY_POLICY
STALE_READ_POLICY
AUTHORIZATION_REQUIREMENT
AUDIT_REQUIREMENT
FAILURE_MODE
```

## 102. Example Contract

```text
STATE: CURRENT_AUTHORIZATION
CONSISTENCY: LINEARIZABLE / DEPLOYMENT-SPECIFIC STRONG MODEL
STALE READ: FORBIDDEN
CONFLICT: DENY + ESCALATE
RETRY: IDEMPOTENT ONLY
AUDIT: REQUIRED
```

Versus:

```text
STATE: SEARCH_INDEX
CONSISTENCY: EVENTUAL
STALE READ: ACCEPTABLE
CONFLICT: REBUILD / LAST VALID DERIVATION
AUDIT: DERIVATION TRACE
```

## 103. Architecture Invariants

1. Every important state class declares its consistency contract.
2. Stronger consistency is not automatically better for every workload.
3. Transaction boundaries are explicit.
4. Atomicity is scoped to effects that can actually participate in the transaction.
5. External side effects are not assumed rollback-capable.
6. Authorization is revalidated when material state changes before commit.
7. Stale approvals cannot silently authorize new state.
8. Lost updates are prevented or explicitly resolved.
9. Write skew is considered for multi-object invariants.
10. Snapshot isolation is not equated with serializability.
11. Linearizability is reserved for state that needs real-time semantics.
12. Strict serializability is used only where justified.
13. Eventual consistency is not permitted for state whose invariants require stronger guarantees.
14. Retryable operations have idempotency semantics.
15. Unknown commit status is resolved through status lookup or deduplication, not blind repetition.
16. Transaction retries retain logical transaction identity.
17. External compensation is distinct from rollback.
18. Conflicts are explicit and auditable.
19. Semantic memory conflicts are not resolved by timestamps alone.
20. Identity conflicts follow identity-resolution evidence.
21. Temporal conflicts preserve validity and observation times.
22. Spatial conflicts preserve precision and uncertainty.
23. Causal conflicts may remain unresolved.
24. Multimodal evidence conflicts consider source independence and provenance.
25. Model versions remain attached to derived conflict decisions.
26. Policy determines auto-resolution versus escalation.
27. Human resolution is explicit and attributable.
28. No committed update is silently discarded without an applicable, auditable policy.
29. Event publication cannot silently diverge from committed state.
30. Duplicate event delivery is handled explicitly.
31. Out-of-order event handling is declared per consumer.
32. Distributed clocks are not assumed to provide perfect global ordering.
33. Unknown ordering remains unknown.
34. Cross-object invariants require appropriate transaction or coordination scope.
35. Long-running inference should not hold locks unnecessarily.
36. Expensive computation should validate freshness before commit.
37. Conflict-resolution logic is versioned and governed.
38. Consistency guarantees are tested through concurrent histories and fault injection.
39. Application invariants are tested in addition to generic consistency properties.
40. A consistency guarantee is not valid merely because documentation claims it; implementations must be tested.

## 104. Integration With 107

```text
107 DURABLE EVENT / STATE MODEL
             ↓
108 TRANSACTION / CONCURRENCY MODEL
             ↓
        VALID COMMIT
```

107 defines the durable substrate; 108 defines the rules under which concurrent operations may modify it.

## 105. Integration With 109

109 may safely define replication only after 108 has established:

```text
WHAT MUST CONVERGE?
WHAT MAY DIVERGE?
WHAT ORDER MATTERS?
WHAT CONFLICTS ARE VALID?
WHAT REQUIRES COORDINATION?
```

## 106. Integration With 110

110 recovery must preserve transaction status, commit records, idempotency information, conflict history and invariant validation.

## 107. Integration With 111

Privacy deletion must be transactional where required so deleted state cannot be recreated by a stale writer, retry, replay or migration.

## 108. Integration With 112

Observability must expose transaction latency, conflicts, retries, consistency violations and stale-state behavior as first-class operational signals.

## 109. Integration With 113

Resource scheduling must account for transaction contention, lock/lease occupancy, retry amplification and coordination cost.

## 110. Integration With 114

Multi-agent coordination depends on explicit concurrency and consistency contracts for shared memory and delegated state transitions.

## 111. Final Principle

> **Novi should not treat concurrency as an implementation detail. Every shared state transition must have explicit transaction, visibility, consistency, conflict and recovery semantics appropriate to its meaning and consequence. Strong guarantees should be used where correctness or safety requires them; weaker guarantees should be used deliberately where they preserve invariants while improving availability and performance.**

## 112. Research Cross-Validation

The architecture was cross-validated against established consistency and transaction research and operational verification practice:

- Jepsen's consistency reference defines consistency models as legal sets of concurrent histories and documents the hierarchy and tradeoffs among serializability, linearizability, causal and weaker guarantees. citeturn0search0turn0search2
- Herlihy and Wing's linearizability work established the real-time-aware correctness condition for concurrent objects; current reference material summarizes the formal requirements. citeturn0search1
- Classical database work establishes serializability as a core correctness criterion for concurrent transaction systems. citeturn0search4
- Distributed transaction research connects correctness to both serializability and termination through conflict resolution and failure recovery. citeturn0search3
- Replicated-database research demonstrates that weaker isolation such as snapshot isolation still requires formal replica-control conditions and integrity-constraint reasoning. citeturn0search13
- Jepsen provides a practical fault-injection and history-verification approach for testing whether real implementations satisfy claimed consistency properties. citeturn0search10

These sources support the architectural distinctions; they do not imply that Novi should adopt any single database engine, transaction protocol, consensus algorithm or consistency model globally.
