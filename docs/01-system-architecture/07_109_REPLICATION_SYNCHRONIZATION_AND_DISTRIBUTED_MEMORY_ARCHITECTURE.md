# 109 — Replication, Synchronization & Distributed Memory Architecture

**Status:** Proposed / Architecture Foundation  
**Priority:** P1 — distributed-state foundation  
**Document class:** Detailed system architecture  
**Depends on:** 95–108, especially provenance, governance, human oversight, durable state, event semantics, transactions, concurrency, and consistency  
**Enables:** 110 recovery and disaster resilience, 111 privacy lifecycle, 112 observability and lifespan evaluation, 113 resource governance, 114 multi-agent coordination

---

## 1. Purpose

This document defines how Novi may maintain state across multiple processes, machines, runtimes, or autonomous agents without losing the semantic guarantees established by documents 95–108.

Replication is not simply copying a database. Synchronization is not simply exchanging files. Distributed memory is not a single shared vector store.

The architecture must preserve:

- identity;
- provenance;
- causality;
- authorization;
- policy state;
- versioning;
- consistency requirements;
- offline operation;
- privacy and deletion semantics;
- conflict visibility;
- auditability;
- recovery capability.

The central principle is:

> **Novi should replicate authoritative history and state according to explicit consistency classes, while allowing derived and mergeable state to converge using weaker mechanisms where correctness permits.**

---

## 2. Why Replication Is a Separate Layer

107 established the durable event and state substrate. 108 established the consistency and concurrency vocabulary.

109 now answers:

```text
WHERE does state exist?
HOW is it copied?
WHEN is a copy current?
HOW are divergent copies reconciled?
WHO is allowed to synchronize?
WHAT happens during partitions?
```

The dependency chain is:

```text
107 Durable State
      ↓
108 Consistency / Concurrency
      ↓
109 Replication / Synchronization
      ↓
110 Recovery / Resilience
```

Replication must not invent its own state semantics.

---

## 3. No Global Consistency Policy

Novi must not force every piece of state into one consistency model.

Different state classes have different correctness requirements.

### Class R1 — Strongly consistent

Examples:

- safety policy;
- authority grants/revocations;
- critical authorization state;
- emergency-stop state;
- security configuration;
- distributed ownership/leadership state.

These require strong coordination appropriate to the operation.

### Class R2 — Causally consistent

Examples:

- important episodic history;
- world-model relationships;
- goal and plan state;
- event-derived cognitive state.

Consumers should not observe effects without their relevant causes.

### Class R3 — Eventually consistent

Examples:

- search indexes;
- analytics;
- non-critical derived summaries;
- replicated embeddings where temporary staleness is acceptable.

### Class R4 — Mergeable / convergent

Examples:

- suitable counters;
- sets;
- independently authored annotations;
- some offline-first preference or metadata structures.

CRDT-like mechanisms may be appropriate where their mathematical merge properties match the domain semantics.

### Class R5 — Local-only

Examples:

- transient sensor buffers;
- device-specific caches;
- local model execution context.

No replication obligation exists unless a later subsystem explicitly promotes the data.

---

## 4. Replication Unit

The primary replication unit should be a typed durable event or an explicitly versioned state object derived from events.

Replication must preserve:

```text
EVENT ID
EVENT TYPE
SCHEMA VERSION
CAUSATION
CORRELATION
SOURCE NODE
SOURCE REVISION
PROVENANCE
AUTHORITY CONTEXT
POLICY CONTEXT
INTEGRITY METADATA
```

A replica must not silently convert an event into an unrelated local mutation with no provenance relationship to the source.

---

## 5. Source of Truth

For each replicated domain, Novi must explicitly define the authority model.

Possible models include:

```text
SINGLE AUTHORITATIVE NODE

PRIMARY + REPLICAS

QUORUM / CONSENSUS GROUP

MULTI-WRITER MERGEABLE STATE

LOCAL AUTHORITATIVE UNTIL HANDOFF
```

There must never be an implicit assumption that all replicas are equally authoritative.

Authority is a semantic property, not merely a network topology property.

---

## 6. Replicated Event History

Where feasible, replicas should receive the authoritative event stream rather than independent opaque snapshots.

```text
AUTHORITATIVE HISTORY
       │
       ├────────→ NODE A
       ├────────→ NODE B
       └────────→ NODE C
```

Each replica maintains its applied position and can report:

```text
last_received
last_validated
last_committed
last_materialized
last_projected
```

These positions must not be conflated.

---

## 7. Replication Is Not Delivery

A message being transmitted does not mean the state is replicated.

The lifecycle is:

```text
GENERATED
 ↓
TRANSMITTED
 ↓
RECEIVED
 ↓
VALIDATED
 ↓
ACCEPTED
 ↓
DURABLY COMMITTED
 ↓
MATERIALIZED
 ↓
AVAILABLE
```

A replica should only advertise a state as committed when it has satisfied the configured durability and consistency guarantee.

---

## 8. Synchronization Protocol

Synchronization should support:

- incremental event exchange;
- range requests;
- acknowledgements;
- resumable transfer;
- integrity validation;
- duplicate suppression;
- missing-event detection;
- conflict detection;
- backpressure;
- retry;
- quarantine of invalid data.

A basic exchange may be:

```text
NODE A → NODE B: I have history through H100
NODE B → NODE A: I have history through H93
NODE A → NODE B: send H94–H100
NODE B → NODE A: validated + committed through H100
```

---

## 9. Idempotent Synchronization

Synchronization must tolerate retries.

The same event may arrive more than once.

```text
receive event E
   ↓
check event identity
   ├── already committed → acknowledge / ignore duplicate
   └── unknown → validate and apply
```

Duplicate delivery must not create duplicate logical state transitions.

---

## 10. Ordering

Distributed delivery can reorder events.

Novi must distinguish:

```text
transport order
recorded order
causal order
commit order
materialization order
```

A node must not infer causality from network arrival order.

If an event depends on another event that has not arrived, the replica may:

- buffer it;
- request the missing dependency;
- materialize a declared provisional state;
- reject it;

according to domain semantics.

---

## 11. Causal Dependencies

Each replicated event should expose enough metadata to identify required causal predecessors.

A replica should be able to detect:

```text
EVENT B received
EVENT A missing
B depends on A
```

rather than silently materializing B as an independent fact.

This is especially important for:

```text
AUTHORIZATION → ACTION
OBSERVATION → MEMORY
MEMORY → DECISION
DECISION → ACTION
ACTION → OUTCOME
```

---

## 12. Conflict Detection

Conflicts are not limited to identical database keys.

Novi must detect semantic conflicts such as:

```text
NODE A: person location = London
NODE B: person location = Paris
```

or:

```text
NODE A: policy permits action
NODE B: policy revokes permission
```

or:

```text
NODE A: memory claim verified
NODE B: same claim retracted
```

Conflict detection must use the domain semantics defined in 97–108.

---

## 13. Conflict Classes

Conflicts should be classified before resolution.

### Identity conflict

Two nodes associate incompatible identities with the same entity.

### Temporal conflict

Events assert incompatible temporal state or ordering.

### Spatial conflict

Nodes report incompatible location state with differing timestamps, precision, or provenance.

### Causal conflict

Two causal interpretations cannot simultaneously satisfy the declared model.

### Knowledge conflict

Two knowledge states have incompatible verification or truth status.

### Policy conflict

Replicas disagree about authorization or governance.

### Model conflict

Different model versions produce incompatible state transitions.

### Human-governance conflict

Authorized human decisions conflict or have incompatible scopes.

### Schema conflict

A node cannot safely interpret the incoming representation.

---

## 14. Conflict Resolution Hierarchy

Conflicts must not be resolved by arbitrary last-write-wins for critical semantic state.

A general hierarchy is:

```text
1. Reject invalid state
2. Apply explicit policy
3. Respect authority ordering
4. Respect causal dependencies
5. Compare versions / revisions
6. Apply domain-specific merge
7. Escalate unresolved conflicts
```

Last-write-wins may be acceptable for narrowly defined low-risk metadata, but it must never be a universal conflict policy.

---

## 15. Strongly Consistent Governance State

Critical governance state requires special handling.

Examples:

```text
AUTHORITY REVOKED
EMERGENCY STOP ACTIVE
SAFETY POLICY UPDATED
CAPABILITY DISABLED
```

A stale replica must not use old state to authorize a consequential action merely because synchronization has not completed.

Safety-sensitive replicas therefore require explicit freshness/lease/authority checks.

---

## 16. Revocation Propagation

A capability revocation must propagate within a defined risk-appropriate bound.

```text
REVOCATION
 ↓
AUTHORITY SOURCE
 ↓
ENFORCEMENT NODES
 ↓
AGENTS / SESSIONS
 ↓
LOCAL CACHES
```

Cached authority must have a bounded validity period where required.

---

## 17. Offline-First Replication

Novi must remain operational when disconnected.

A node may continue local operation only within its locally authorized autonomy envelope.

```text
DISCONNECTED
 ↓
LOCAL AUTONOMY
 ↓
LOCAL EVENT HISTORY
 ↓
RECONNECT
 ↓
VALIDATE
 ↓
RECONCILE
```

Offline capability does not grant additional authority.

---

## 18. Offline Write Rules

Before accepting an offline write, Novi should know whether the state is:

```text
LOCAL-WRITABLE
MERGEABLE
LEASE-BOUND
CENTRAL-AUTHORITY-REQUIRED
```

If central authority is required and unavailable, the system must not manufacture authorization.

It may record a proposal or pending operation instead.

---

## 19. Local-First Memory

Memory should be capable of being captured locally and synchronized later.

A local memory record should retain:

- local identity;
- creation time;
- source provenance;
- confidence;
- local revision;
- dependency references;
- synchronization state.

This allows disconnected cognition without losing later reconciliation context.

---

## 20. Memory Replication Does Not Mean Blind Duplication

Different memory classes may require different replication behavior.

```text
PRIVATE EPISODIC MEMORY
→ restricted replication

VERIFIED GENERAL KNOWLEDGE
→ broader replication where authorized

DERIVED EMBEDDING
→ rebuildable replication

TEMPORARY CONTEXT
→ normally not replicated
```

Privacy and authorization determine where memory may travel.

---

## 21. Selective Replication

Novi should support replication filters based on:

- data classification;
- subject authorization;
- node role;
- geographic constraints;
- retention policy;
- sensitivity;
- operational need;
- legal/deployment requirements.

Replication should follow data-minimization principles rather than defaulting to full database copies.

---

## 22. Dependency-Aware Replication

A derived record should not be replicated without considering its dependencies.

```text
SOURCE
 ↓
MEMORY
 ↓
SUMMARY
 ↓
DECISION
```

If only the summary is replicated, the receiving node must know whether its provenance remains resolvable or whether the summary is explicitly treated as a limited derived artifact.

---

## 23. Privacy and Deletion

Replication must integrate with 111's privacy lifecycle.

Deletion is not complete merely because one node deleted a record.

The system must track:

```text
DELETION REQUEST
 ↓
AUTHORIZED
 ↓
SOURCE DELETED
 ↓
REPLICAS RECONCILED
 ↓
DERIVED COPIES HANDLED
 ↓
DELETION VERIFIED
```

Where immediate physical deletion is impossible, the system must apply the approved tombstone, access-blocking, retention, and eventual purge semantics.

---

## 24. Tombstones

Deleted or invalidated records may require durable tombstones so that an old replica cannot resurrect them during later synchronization.

```text
RECORD X
 ↓
DELETE / INVALIDATE
 ↓
TOMBSTONE X
```

Tombstone retention must itself be governed by policy.

---

## 25. Resynchronization

After a node has been offline, synchronization should be incremental where possible.

```text
LOCAL POSITION
      ↓
REMOTE POSITION
      ↓
MISSING RANGE
      ↓
TRANSFER
      ↓
VALIDATE
      ↓
APPLY
      ↓
RECONCILE CONFLICTS
```

If history is compacted, the node may require a snapshot plus an event suffix rather than the entire historical log.

---

## 26. Snapshot-Based Synchronization

Large replicas may bootstrap using a verified snapshot:

```text
SNAPSHOT S500
     +
EVENTS 501–N
```

The snapshot must identify the source revision, schema/reducer versions, integrity metadata, and provenance compatibility.

An untrusted snapshot must not be treated as authoritative merely because it came from another Novi node.

---

## 27. Integrity Verification

Replicated data should support integrity verification using appropriate mechanisms such as:

- cryptographic hashes;
- authenticated transport;
- signed manifests where required;
- sequence/revision validation;
- authenticated node identity;
- tamper-evident metadata.

Integrity validation must occur before a replica promotes incoming state to authoritative local state.

---

## 28. Node Identity

Every replication participant requires a stable cryptographic or otherwise authenticated node identity appropriate to the deployment.

Node identity must be distinct from:

```text
USER IDENTITY
AGENT IDENTITY
DEVICE IDENTITY
MODEL IDENTITY
```

These identities may be related but must not be conflated.

---

## 29. Trust Between Nodes

A node must authenticate its replication peers and establish their authorization to exchange specific data classes.

```text
NODE IDENTITY
 ↓
TRUST / AUTHORIZATION
 ↓
REPLICATION SCOPE
 ↓
DATA EXCHANGE
```

Peer authentication alone does not grant unrestricted data access.

---

## 30. Backpressure

A slow replica must not be allowed to destabilize the authoritative node.

Replication requires:

- bounded queues;
- flow control;
- prioritization;
- retry limits;
- lag measurement;
- snapshot/bootstrap fallback.

Critical governance updates may receive higher propagation priority than analytics projections.

---

## 31. Replica Lag

Replica lag must be measurable in more than wall-clock time.

Useful indicators include:

```text
EVENT POSITION LAG
CAUSAL LAG
STATE REVISION LAG
POLICY VERSION LAG
MEMORY VERSION LAG
```

A node must not claim freshness it cannot establish.

---

## 32. Read Semantics

Every distributed read API should make its freshness/consistency contract explicit.

Possible contracts include:

```text
LOCAL
BOUNDED-STALE
CAUSALLY-CONSISTENT
LINEARIZABLE
READ-YOUR-WRITES
MONOTONIC-READ
```

The application must not silently assume stronger guarantees than the API provides.

---

## 33. Write Semantics

Writes should declare whether they require:

- local durability only;
- authoritative acknowledgement;
- quorum acknowledgement;
- causal predecessor availability;
- conflict-free merge;
- human authorization.

The default must not be "replicate everywhere immediately" because that can be both expensive and semantically wrong.

---

## 34. Replication Topologies

Novi may support different topologies:

```text
PRIMARY → REPLICAS

PEER ↔ PEER

HIERARCHICAL

EDGE → HUB → EDGE

CONSENSUS GROUP
```

Topology is selected per deployment and state class.

No topology is universally correct.

---

## 35. Consensus Where Required

Strongly consistent replicated state may require a consensus protocol or an equivalent coordination mechanism.

The architecture does not mandate a particular implementation, but it requires explicit treatment of:

- leader election;
- quorum;
- term/epoch changes;
- committed index;
- membership changes;
- split-brain prevention;
- recovery after partition.

Consensus should be reserved for state that actually needs it.

---

## 36. Split Brain

Two nodes must not simultaneously believe they have exclusive authority over the same strongly consistent resource.

Protection mechanisms may include:

- quorum;
- leases;
- fencing tokens;
- epochs;
- authoritative coordination service.

A node that loses authority must stop issuing authority-dependent writes.

---

## 37. Fencing

Where stale leaders could cause harmful effects, the physical or logical side-effect boundary should verify an authority epoch/fencing token where feasible.

```text
OLD LEADER
   ↓
STALE TOKEN
   ↓
REJECTED
```

This is particularly important for physical robot control and safety-critical distributed execution.

---

## 38. Multi-Writer State

Multi-writer operation is permitted only where the state semantics support it.

Suitable candidates may include:

- additive counters;
- sets with defined semantics;
- independent annotations;
- certain user preferences;
- explicitly mergeable metadata.

A multi-writer design must define the merge algebra rather than relying on accidental arrival order.

---

## 39. CRDT Use

CRDT-style structures may be used when their convergence properties match the domain.

They are not a universal solution.

A CRDT must not be used for state whose correct meaning requires authority ordering, exclusivity, or business-level validation that the CRDT cannot represent.

Examples of potentially suitable structures include grow-only sets, observed-remove sets, counters, and registers with carefully defined semantics.

---

## 40. Semantic Merge

Some Novi state requires a domain-specific merge rather than a generic data structure.

Example:

```text
NODE A:
"Person X was observed in London at 10:00."

NODE B:
"Person X was observed in Paris at 11:00."
```

These are not necessarily conflicting facts. They may represent a valid temporal sequence.

Therefore merge must consider:

```text
identity
observation time
source
location precision
confidence
causal context
```

---

## 41. Knowledge Conflict Resolution

If two nodes disagree about a knowledge claim, the system should preserve both evidence paths until resolution rather than silently deleting one.

```text
CLAIM A
  ↘
   EVIDENCE GRAPH
  ↗
CLAIM B
      ↓
REVIEW / VERIFICATION
```

The result may be:

- A accepted;
- B accepted;
- both accepted under different contexts;
- one retracted;
- unresolved.

---

## 42. Model Version Conflicts

A node running model M2 may produce a different inference than a node running M1.

Model identity and version must therefore be part of the derived event provenance.

Model disagreement must not be collapsed into a database conflict without preserving the inference provenance.

---

## 43. Policy Version Conflicts

Policy state is special.

If node A uses policy P7 and node B uses P6, B must not silently authorize actions that P7 prohibits.

Policy synchronization must therefore have explicit version and validity semantics.

```text
POLICY P7
 ↓
ACTIVE AUTHORITY

NODE WITH P6
 ↓
STALE
 ↓
RESTRICTED
```

---

## 44. Human Decisions in Distributed State

Human approvals must include:

- principal identity;
- authority scope;
- target;
- action;
- policy version;
- relevant state revision;
- validity period.

A replicated approval cannot be detached from the state and policy under which it was granted.

---

## 45. Stale Approval Protection

If a materially relevant state change occurs after an approval:

```text
APPROVAL T1
 ↓
STATE CHANGE T2
 ↓
VALIDITY CHECK
 ↓
REAPPROVE / REJECT / CONTINUE
```

Replication must preserve enough revision information to perform this check.

---

## 46. Security Boundaries

Replication must not become an authority escalation path.

A node cannot claim:

```text
"another node accepted this"
```

as sufficient authorization unless the architecture explicitly defines that node as an authoritative authority source for that operation.

---

## 47. Network Partitions

During a partition, each state class follows its declared consistency policy.

```text
STRONG STATE
→ restrict writes / require quorum / safe fallback

MERGEABLE STATE
→ allow bounded local progress

EVENTUAL STATE
→ allow local progress and reconcile later

CRITICAL AUTHORITY
→ fail closed where required
```

The system must never treat partition tolerance as permission to ignore safety semantics.

---

## 48. Reconciliation After Partition

Reconciliation should be explicit:

```text
PARTITION ENDS
 ↓
COMPARE HISTORIES
 ↓
VERIFY AUTHORITY
 ↓
DETECT CONFLICTS
 ↓
APPLY MERGE / POLICY
 ↓
VALIDATE RESULT
 ↓
COMMIT RECONCILED STATE
```

Unresolved high-impact conflicts must escalate rather than being silently merged.

---

## 49. Eventual Convergence

For eventual-consistency domains, convergence means that replicas with the same accepted event set and deterministic merge semantics eventually reach equivalent state.

Convergence must not be claimed merely because synchronization eventually stops transmitting.

It should be tested as an explicit invariant.

---

## 50. Observability

109 must expose:

- replication lag;
- synchronization throughput;
- rejected events;
- conflict count;
- conflict classes;
- unresolved conflicts;
- tombstone lag;
- policy-version lag;
- node health;
- peer availability;
- bootstrap duration;
- replay duration;
- reconciliation duration.

These metrics become inputs to 112.

---

## 51. Failure Modes

Test at minimum:

```text
DUPLICATE EVENT
OUT-OF-ORDER EVENT
MISSING EVENT
PARTITION
NODE CRASH
STALE LEADER
CLOCK SKEW
CORRUPTED SNAPSHOT
INVALID EVENT
SCHEMA MISMATCH
POLICY REVOCATION DURING PARTITION
CONCURRENT HUMAN CORRECTIONS
CONCURRENT MODEL UPDATES
DELETE + LATE REPLICATION
```

---

## 52. Security Failure Modes

Also test:

- unauthorized peer;
- stolen/expired credentials;
- replayed event;
- forged event identity;
- malicious snapshot;
- unauthorized replication scope;
- node impersonation;
- privilege escalation through synchronization;
- compromised replica attempting to write authoritative state.

A replica must be treated as potentially faulty or compromised according to deployment threat assumptions.

---

## 53. Data Classification

Every replicated data class should declare:

```text
CLASSIFICATION
REPLICATION SCOPE
CONSISTENCY
RETENTION
DELETION
AUTHORITY
ENCRYPTION
AUDIT REQUIREMENT
```

This creates a machine-checkable bridge between 105 governance and 109 transport/storage behavior.

---

## 54. Replication Policy Example

A policy may express:

```text
State: safety_policy
Consistency: strong
Writers: governance-authority
Readers: safety-gateway
Offline writes: forbidden
Replication: quorum

State: episodic_memory
Consistency: causal
Writers: authorized-local
Offline writes: allowed
Replication: selective

State: embeddings
Consistency: eventual
Writers: projection-service
Offline writes: allowed
Replication: rebuildable
```

Exact policy syntax belongs to the implementation layer.

---

## 55. Resource Constraints

Replication consumes:

- CPU;
- memory;
- storage;
- network bandwidth;
- power;
- synchronization time.

On Jetson/edge deployments, replication must not starve perception, control, or safety workloads.

Resource governance is expanded in 113.

---

## 56. Bandwidth Prioritization

Replication traffic should be prioritized by semantic importance.

Possible priority order:

```text
SAFETY / AUTHORITY
 ↓
CRITICAL OPERATIONS
 ↓
DURABLE COGNITIVE HISTORY
 ↓
MEMORY
 ↓
DERIVED PROJECTIONS
 ↓
ANALYTICS
```

Deployment-specific policies may differ.

---

## 57. Encryption and Transport

Replication channels must use authenticated and appropriately encrypted transport.

Encryption at rest remains required for protected data.

Transport security does not replace authorization of individual data classes.

---

## 58. Auditability

Every significant synchronization operation should be attributable to:

```text
SOURCE NODE
TARGET NODE
PROTOCOL VERSION
DATA SCOPE
START / END
RESULT
CONFLICTS
AUTHORIZATION CONTEXT
```

Replication audit records themselves are governed data.

---

## 59. Deterministic Replay Across Replicas

Where the same authoritative event history is applied under compatible reducers, replicas should converge to equivalent materialized state.

If they do not, the system must expose:

```text
EVENT DIFFERENCE
SCHEMA DIFFERENCE
REDUCER DIFFERENCE
MODEL-DERIVED DIFFERENCE
CONFIGURATION DIFFERENCE
```

Silent divergence is unacceptable for critical state.

---

## 60. Reproducibility

A distributed state should be reproducible from:

```text
EVENT HISTORY
SNAPSHOT
SCHEMA VERSION
REDUCER VERSION
POLICY VERSION
RELEVANT MODEL VERSION
```

This connects 109 directly to 107's replay contract.

---

## 61. Replication and Recovery

Replication is not a substitute for backup.

A corrupted authoritative state can otherwise corrupt every replica.

109 therefore requires independent recovery mechanisms defined by 110:

```text
REPLICATION
 ≠
BACKUP
 ≠
DISASTER RECOVERY
```

---

## 62. Replica Corruption

If a replica is corrupted:

```text
DETECT
 ↓
ISOLATE
 ↓
STOP PROMOTION
 ↓
VERIFY SOURCE
 ↓
REBUILD / RESYNC
 ↓
VALIDATE
 ↓
RETURN TO SERVICE
```

A corrupted replica must not be allowed to contaminate authoritative history.

---

## 63. Node Membership

Distributed groups require explicit membership semantics.

Membership changes should define:

- node identity;
- role;
- authorization;
- state bootstrap requirement;
- revocation behavior;
- version compatibility;
- removal/fencing semantics.

A removed node must not automatically regain authority merely by reconnecting.

---

## 64. Version Compatibility

Nodes may run different software versions during rolling upgrades.

Replication therefore requires compatibility rules for:

- event schemas;
- state schemas;
- protocol versions;
- reducer versions;
- policy versions;
- model versions.

Unknown critical data must not be silently downgraded into an older semantic representation.

---

## 65. Rolling Upgrades

A safe distributed upgrade should support:

```text
COMPATIBILITY CHECK
 ↓
ADD NEW VERSION
 ↓
MIGRATE / DUAL-READ IF REQUIRED
 ↓
VALIDATE
 ↓
RETIRE OLD VERSION
```

Exact rollout strategy belongs to implementation architecture.

---

## 66. Human Oversight of Distributed Conflicts

High-impact unresolved conflicts should be presented to authorized reviewers with:

- competing states;
- provenance;
- timestamps;
- policy versions;
- node identities;
- model versions;
- consequences of each resolution;
- recommended resolution with uncertainty.

The reviewer must not be forced to trust a black-box automatic merge.

---

## 67. Conflict Escalation

Escalate when:

- critical policy differs;
- identity is ambiguous;
- deletion conflicts with resurrection;
- authority is disputed;
- physical-world state is uncertain;
- causal histories are incompatible;
- schema interpretation is unsafe;
- automatic merge would be irreversible.

---

## 68. Distributed Memory Query Semantics

Memory retrieval should expose whether results are:

```text
LOCAL
REPLICATED
STALE
PARTIALLY SYNCHRONIZED
PROVISIONAL
AUTHORITATIVE
```

The reasoning layer must not be presented with stale replicated memory as if it were current authoritative state without an explicit freshness contract.

---

## 69. Retrieval Under Partition

If remote memory is unavailable, the local runtime should:

- use authorized local memory;
- expose missing context where material;
- avoid fabricating remote state;
- continue within autonomy limits.

Connectivity failure must not become hallucinated knowledge.

---

## 70. Replication and Learning

Learning or memory promotion from one node must preserve provenance and confidence.

A replicated candidate must not automatically become verified knowledge merely because another node stored it.

Verification authority remains governed by the knowledge lifecycle.

---

## 71. Replication and Self-Improvement

A node may replicate a proposal for self-improvement, but replication must not turn a proposal into an approved system change.

```text
PROPOSAL
 ↓
REPLICATED
 ↓
REVIEW / POLICY
 ↓
APPROVED
 ↓
ACTIVATED
```

---

## 72. Distributed Authority

Authority should be represented explicitly rather than inferred from network position.

A node may have:

```text
READ AUTHORITY
WRITE AUTHORITY
APPROVAL AUTHORITY
REPLICATION AUTHORITY
EXECUTION AUTHORITY
```

These permissions can differ.

---

## 73. Least-Authority Replication

A node should receive only the replication privileges and data necessary for its role.

A perception node does not automatically require access to:

- governance history;
- private memories;
- authorization credentials;
- unrelated users' data.

---

## 74. Replication as a Policy-Enforced Capability

Replication itself should be treated as a governed capability:

```text
REQUEST REPLICATION
 ↓
IDENTITY
 ↓
AUTHORITY
 ↓
DATA CLASSIFICATION
 ↓
POLICY
 ↓
TRANSFER
 ↓
AUDIT
```

This integrates 105 and 106.

---

## 75. Testing Strategy

109 requires deterministic simulation of distributed behavior.

Tests should cover:

### Safety

- stale authority;
- revoked capability;
- split brain;
- partition during action authorization.

### Correctness

- concurrent writes;
- duplicate events;
- reordered events;
- missing dependencies;
- merge correctness.

### Resilience

- node crash;
- network loss;
- partial transfer;
- restart during reconciliation;
- replica corruption.

### Privacy

- delete during partition;
- late-arriving deleted record;
- restricted-data replication;
- unauthorized peer.

### Lifespan

- long offline periods;
- large event histories;
- repeated synchronization;
- schema evolution;
- rolling upgrades.

---

## 76. Verification Invariants

At minimum:

1. Replication never bypasses authorization.
2. A replica never becomes authoritative merely by receiving data.
3. Duplicate events do not create duplicate logical transitions.
4. Causality is not inferred from network arrival order.
5. Critical policy state has an explicit consistency guarantee.
6. Revocations cannot be silently hidden by stale replicas.
7. Deleted state cannot be resurrected by ordinary replay.
8. Derived data remains distinguishable from authoritative state.
9. Conflict resolution is domain-specific where required.
10. Unresolved high-impact conflicts escalate.
11. Offline operation never creates authority that was unavailable.
12. Replica lag is observable.
13. Replica corruption cannot silently contaminate authoritative history.
14. Snapshots are validated before promotion.
15. Node identity is distinct from user, agent, model, and device identity.
16. Replication scope is policy-controlled.
17. Model/version differences remain provenance-visible.
18. Human approvals remain bound to their state and policy context.
19. Replication is not treated as backup.
20. Eventual convergence is tested rather than assumed.

---

## 77. Relationship to 108

108 defines which consistency and concurrency guarantees are required.

109 implements distributed mechanisms capable of satisfying those guarantees.

```text
108: WHAT consistency means
          ↓
109: HOW replicas achieve it
```

109 must not weaken a guarantee merely because a replication mechanism makes it inconvenient.

---

## 78. Relationship to 110

109 establishes replicated-state behavior.

110 will define:

- backup;
- checkpoint recovery;
- disaster recovery;
- corruption recovery;
- failover;
- restore verification;
- recovery-point objectives;
- recovery-time objectives.

A replicated system without independent recovery is not resilient by default.

---

## 79. Relationship to 111

111 will define the complete privacy and retention lifecycle.

109 must already provide the mechanisms required for:

- selective replication;
- deletion propagation;
- tombstones;
- retention enforcement;
- provenance-aware dependency handling.

---

## 80. Relationship to 112

112 will consume replication telemetry and evaluate distributed behavior over time.

109 must expose enough state to diagnose:

```text
lag
conflicts
partitions
convergence
stale policy
replica divergence
```

---

## 81. Relationship to 113

Replication is a resource consumer.

113 will govern:

- bandwidth budgets;
- CPU/GPU budgets;
- storage budgets;
- scheduling;
- priority;
- energy constraints.

109 must expose resource demand and allow throttling without violating safety guarantees.

---

## 82. Relationship to 114

114 will build multi-agent coordination on top of the distributed-state substrate.

Agents must not invent their own synchronization semantics.

```text
107 durable state
 ↓
108 consistency
 ↓
109 replication
 ↓
114 agent coordination
```

---

## 83. Technology Selection Principles

109 does not mandate a single technology.

Candidate mechanisms should be evaluated against:

- offline-first operation;
- embedded deployment;
- Jetson resource limits;
- strong consistency requirements;
- event replication;
- selective replication;
- resumability;
- encryption;
- schema evolution;
- conflict handling;
- observability;
- operational complexity.

Consensus systems, log replication, streaming systems, CRDT libraries, databases, and custom synchronization should be selected only after mapping their guarantees to Novi state classes.

---

## 84. Architecture Decision Rule

The default decision process is:

```text
DEFINE STATE SEMANTICS
 ↓
DEFINE CONSISTENCY REQUIREMENT
 ↓
DEFINE AUTHORITY
 ↓
DEFINE FAILURE BEHAVIOR
 ↓
DEFINE PRIVACY / RETENTION
 ↓
DEFINE REPLICATION TOPOLOGY
 ↓
SELECT TECHNOLOGY
```

Never reverse this order by choosing a database first and adapting semantics afterward.

---

## 85. Final Architecture

Novi's distributed memory architecture is therefore:

```text
                    AUTHORITATIVE HISTORY
                            │
                ┌───────────┼───────────┐
                ↓           ↓           ↓
             NODE A       NODE B       NODE C
                │           │           │
          local state   local state   local state
                │           │           │
                └──── synchronization ──┘
                            │
                 consistency contracts
                            │
                  conflict resolution
                            │
                     convergence
```

But the actual semantics are state-specific:

```text
CRITICAL AUTHORITY
      → strong coordination

CAUSAL COGNITIVE STATE
      → causal synchronization

MERGEABLE STATE
      → deterministic merge

DERIVED STATE
      → eventual / rebuildable

EPHEMERAL STATE
      → local only
```

---

## 86. Final Principles

1. Replication copies governed state; it does not create authority.
2. Every replicated state class must declare its consistency requirement.
3. Strong consistency is reserved for state that needs it.
4. Eventual consistency is acceptable only where temporary divergence is semantically safe.
5. CRDTs are tools for suitable mergeable data, not universal conflict resolution.
6. Replication must preserve provenance and causality.
7. Network order is not causal order.
8. Duplicate delivery must be harmless.
9. Offline operation must remain within local authority.
10. Stale safety or authorization state must not authorize consequential actions.
11. Revocations require bounded propagation appropriate to risk.
12. Deletion must account for replicas and derived state.
13. Tombstones may be required to prevent resurrection.
14. Replica identity is distinct from user, agent, device, and model identity.
15. Replicas must be authenticated and explicitly authorized.
16. A replica cannot silently promote itself to authority.
17. Conflict resolution must respect domain semantics.
18. High-impact unresolved conflicts require escalation.
19. Human approvals must remain bound to the state and policy under which they were granted.
20. Model-version disagreement must remain visible in provenance.
21. Replication is not backup.
22. Corrupted replicas must be isolated and rebuilt.
23. Replica lag and divergence must be observable.
24. Synchronization must support retry, resumability, backpressure, and validation.
25. Distributed state must remain compatible with schema evolution.
26. Replication must not starve safety, perception, or control workloads.
27. Privacy and replication policies must be jointly enforced.
28. Distributed memory must expose freshness and authority semantics to reasoning systems.
29. Convergence must be tested, not assumed.
30. Technology selection follows semantics, consistency, authority, privacy, and failure requirements—not the other way around.

---

## 87. Completion Checkpoint

With 109, Novi now has the complete conceptual path from durable local state to distributed state:

```text
95–106
Semantics + governance
      ↓
107
Durable event/state substrate
      ↓
108
Transactions + consistency
      ↓
109
Replication + synchronization + distributed memory
```

The next architectural dependency is **110 — Recovery, Checkpointing & Disaster Resilience Architecture**.

Replication makes multiple copies possible. It does not guarantee that those copies remain correct, recoverable, or trustworthy after corruption, software failure, operator error, catastrophic hardware loss, or a compromised authoritative node.

That resilience layer must therefore be specified before Novi's distributed architecture is considered operationally complete.