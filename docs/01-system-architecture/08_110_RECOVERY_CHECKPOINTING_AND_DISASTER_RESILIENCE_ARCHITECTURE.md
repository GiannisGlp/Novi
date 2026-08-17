# 110 — Recovery, Checkpointing & Disaster Resilience Architecture

**Status:** Normative architecture foundation — P1

**Depends on:** 95–109, especially durable state, transactions, consistency, replication, governance, human oversight, provenance and privacy semantics.

**Enables:** 111 privacy lifecycle, 112 observability and lifespan reliability, 113 resource governance, 114 multi-agent coordination.

---

## 1. Purpose

This document defines how Novi detects, contains, recovers from, verifies and learns from failures across local execution, distributed state, memory, models, tools, human approvals and autonomous workflows.

Recovery is not merely restarting a process. A restart can reproduce a failure, duplicate an external side effect, lose state, violate an authorization boundary or resume from a corrupted assumption.

The central principle is:

> **Novi must recover from failure without silently changing the meaning, authority, provenance or safety properties of the state it resumes from.**

Current agent reliability guidance emphasizes durable state and checkpoint-based resume rather than replaying long-running work from the beginning. AWS's Agentic AI Lens specifically recommends persisted workflow state, idempotent steps and checkpoint lifecycle management. citeturn0search1

Recent research also shows that checkpoint/restore for agent environments must account for both application-visible state and operating-system side effects; chat-history-only recovery can miss filesystem and runtime state. citeturn0academia26

---

## 2. Recovery Is a State Transition

A recovery operation is itself governed state:

```text
FAILURE / DEGRADATION
        ↓
DETECT
        ↓
CLASSIFY
        ↓
CONTAIN
        ↓
SELECT RECOVERY POINT
        ↓
RESTORE / REPLAY / COMPENSATE
        ↓
VERIFY
        ↓
RESUME / RESTRICT / ESCALATE
        ↓
AUDIT
```

Recovery must never bypass documents 105 and 106 merely because the normal execution path failed.

---

## 3. Failure Taxonomy

Novi should distinguish at least:

```text
PROCESS FAILURE
NODE FAILURE
NETWORK FAILURE
STORAGE FAILURE
DATA CORRUPTION
REPLICATION FAILURE
CONSISTENCY FAILURE
MODEL FAILURE
TOOL FAILURE
EXTERNAL SERVICE FAILURE
AUTHORIZATION FAILURE
POLICY FAILURE
MEMORY CORRUPTION
SCHEMA FAILURE
HUMAN-OVERSIGHT FAILURE
SECURITY INCIDENT
ENVIRONMENTAL DRIFT
BEHAVIORAL DRIFT
```

The recovery strategy depends on the failure class.

---

## 4. Crash vs Drift vs Corruption

These are different:

```text
CRASH
→ execution stopped unexpectedly

DRIFT
→ execution continues but state/behavior becomes inconsistent with intended trajectory

CORRUPTION
→ durable state or its interpretation is no longer trustworthy
```

A crash can usually be recovered by replaying a valid prior state. Drift may require abandoning the current trajectory. Corruption may require quarantine and restoration from a known-good source.

Long-running agent work increasingly requires treating behavioral drift separately from ordinary infrastructure crashes. citeturn0search0

---

## 5. Recovery Domains

Recovery should be scoped to the smallest safe unit:

```text
TOOL CALL
STEP
TRANSACTION
TASK
SESSION
AGENT
NODE
REPLICATION GROUP
MEMORY DOMAIN
MODEL DEPLOYMENT
SYSTEM
```

A failure in one task should not automatically roll back unrelated system state.

---

## 6. Recovery Point

A recovery point is a state at which Novi can safely resume.

It must identify:

- durable event position;
- state version;
- schema version;
- model version;
- memory snapshot/version;
- policy version;
- authority state;
- relevant external-side-effect state;
- integrity metadata;
- provenance.

A checkpoint without these dependencies may be insufficient for safe restoration.

---

## 7. Checkpoint Types

Novi should support multiple checkpoint forms:

### Event checkpoint

A durable position in the event history.

### State snapshot

A materialized state image associated with a specific event/reducer version.

### Workflow checkpoint

A resumable execution boundary.

### Environment checkpoint

Relevant filesystem, process, sandbox or runtime state.

### Cognitive checkpoint

A bounded representation of active goals, plans, assumptions and unresolved questions.

### Governance checkpoint

Policy, authority and approval state required for continuation.

No single checkpoint type should be assumed sufficient for every workload.

---

## 8. Checkpoint Completeness

A checkpoint is complete only relative to its declared recovery contract.

```text
CHECKPOINT
   ↓
DECLARED SCOPE
   ↓
REQUIRED DEPENDENCIES
   ↓
INTEGRITY VERIFIED
```

The system must not label an application-only checkpoint as a complete environment checkpoint.

---

## 9. Checkpoint Frequency

Checkpointing should not rely on a universal fixed interval.

Checkpoint triggers may include:

- semantic state boundary;
- expensive completed operation;
- before high-risk external side effect;
- human approval boundary;
- tool transaction boundary;
- model/version transition;
- significant memory mutation;
- detected drift threshold;
- resource preemption risk;
- topology change.

Recent agent checkpoint research argues that semantic awareness can substantially reduce unnecessary checkpoint traffic while preserving recovery correctness. citeturn0academia26

---

## 10. Checkpoint Before Irreversible Effects

Where practical:

```text
CHECKPOINT
   ↓
AUTHORIZE
   ↓
EXTERNAL SIDE EFFECT
```

This does not make the external operation transactional by itself. It provides a durable pre-effect recovery boundary.

---

## 11. External Side Effects

Examples include:

```text
SEND MESSAGE
PLACE ORDER
MAKE PAYMENT
DEPLOY CODE
DELETE RESOURCE
MODIFY DATABASE
MOVE PHYSICAL OBJECT
```

Recovery must distinguish:

```text
STATE COMMITTED
SIDE EFFECT CONFIRMED
SIDE EFFECT UNKNOWN
SIDE EFFECT FAILED
```

An unknown outcome must not be treated as failure merely because the local process crashed.

---

## 12. The Uncertain Commit Problem

The dangerous sequence is:

```text
EXTERNAL SYSTEM: SUCCESS
        ↓
Novi: CRASH
        ↓
LOCAL STATE: NO RECORD
```

A naive retry can duplicate the effect.

Novi therefore requires idempotency keys, reconciliation, external receipts or domain-specific confirmation wherever possible.

This builds directly on 108.

---

## 13. Recovery Must Preserve Idempotency

Every replayable operation should declare whether it is:

```text
SAFE TO REPLAY
IDEMPOTENT
CONDITIONALLY IDEMPOTENT
NOT SAFE TO REPLAY
```

Non-idempotent effects require compensation, reconciliation or explicit human handling.

---

## 14. Replay

Replay reconstructs state from durable history.

```text
CHECKPOINT
   +
EVENT SUFFIX
   ↓
REPLAY
   ↓
STATE
```

Replay must use compatible schema and reducer semantics. A changed reducer must not silently reinterpret historical events.

---

## 15. Snapshot + Replay

The preferred large-state pattern is:

```text
KNOWN-GOOD SNAPSHOT
        +
EVENTS AFTER SNAPSHOT
        ↓
RECONSTRUCT
```

This limits recovery time while preserving deterministic history.

---

## 16. Deterministic Replay

Where deterministic replay is claimed, Novi must control or record sources of nondeterminism such as:

- random seeds;
- model/version identifiers;
- tool responses;
- clock values;
- external state;
- environment variables;
- feature flags;
- policy versions.

A model invocation should not be assumed reproducible merely because the same prompt is replayed.

---

## 17. Model-Aware Recovery

If a model has changed since the checkpoint:

```text
CHECKPOINT CREATED UNDER M1
        ↓
CURRENT MODEL M2
```

Novi must determine whether M2 is compatible with the checkpoint's continuation contract.

If not, options include:

```text
RESTORE M1
REVALIDATE UNDER M2
FORK TRAJECTORY
ESCALATE
ABORT
```

This integrates 104.

---

## 18. Memory-Aware Recovery

Recovery must preserve the memory version associated with the original decision unless a governed migration is explicitly performed.

A newer memory interpretation must not silently rewrite historical decision context.

---

## 19. Policy-Aware Recovery

Policies are live governance state.

```text
OLD APPROVAL
      ↓
FAILURE
      ↓
RECOVERY
      ↓
CURRENT POLICY
```

A previously valid approval may be invalid under a newer policy or changed state.

Recovery therefore rechecks authorization where policy requires it.

---

## 20. Human Approval Recovery

Human approval must be durable enough to survive process failure.

The recovery record should identify:

```text
APPROVER
ACTION
SCOPE
POLICY VERSION
TIME WINDOW
STATE ASSUMPTIONS
APPROVAL ID
```

A chat transcript alone is not a sufficient durable authorization record.

---

## 21. Stale Approval

A recovered workflow must not blindly reuse an expired or state-invalidated approval.

```text
RECOVER
 ↓
CHECK APPROVAL VALIDITY
 ↓
REUSE / REAPPROVE / ABORT
```

---

## 22. Fork Instead of Resume

When the current trajectory is suspect but its history is valuable:

```text
ORIGINAL TRAJECTORY
        │
        ├── preserve for audit
        │
        └── fork corrected trajectory
```

The fork must record its parent checkpoint and reason for divergence.

This is especially useful for behavioral drift, failed plans and experimental recovery.

---

## 23. Recovery vs Rollback

They are not identical.

```text
RECOVERY
→ return to a valid continuation point

ROLLBACK
→ intentionally restore earlier state
```

Rollback can itself cause data loss or violate newer governance decisions, so it requires explicit semantics.

---

## 24. Compensation

When rollback cannot undo an external side effect, use a compensating action where one exists.

```text
PAYMENT
 ↓
FAILURE
 ↓
REFUND / COMPENSATION
```

Compensation is not guaranteed to be semantically equivalent to undo.

---

## 25. Saga-Style Recovery

Long-running workflows may be decomposed into steps with compensation handlers:

```text
A → B → C → D

failure at D

compensate C → B → A
```

Only steps with valid compensations should be treated as compensatable.

---

## 26. Partial Failure

Distributed failures often leave the system partially successful.

Novi must represent:

```text
SUCCESS
FAILURE
UNKNOWN
PARTIAL
PENDING RECONCILIATION
```

Avoid collapsing partial or unknown states into binary success/failure.

---

## 27. Quarantine

Untrusted state should be isolated before restoration:

```text
SUSPECT STATE
   ↓
QUARANTINE
   ↓
INTEGRITY / SEMANTIC VALIDATION
   ↓
PROMOTE OR DISCARD
```

Quarantine applies to memory, snapshots, nodes, models, policies and event ranges.

---

## 28. Corruption Detection

Corruption detection may include:

- cryptographic integrity checks;
- schema validation;
- invariant checks;
- impossible-state detection;
- provenance validation;
- cross-replica comparison;
- semantic consistency checks.

A checksum can establish byte integrity; it cannot establish semantic correctness.

---

## 29. Known-Good State

Recovery requires an explicit definition of "known good."

A state may be:

```text
DURABLE
INTEGRITY-VALID
SEMANTICALLY VALID
POLICY-COMPLIANT
OPERATIONALLY HEALTHY
```

These are distinct properties.

---

## 30. Recovery Validation

After restoration:

```text
RESTORE
 ↓
INTEGRITY CHECK
 ↓
SCHEMA CHECK
 ↓
STATE INVARIANTS
 ↓
POLICY CHECK
 ↓
AUTHORITY CHECK
 ↓
DEPENDENCY CHECK
 ↓
SMOKE TEST
 ↓
RESUME / RESTRICT
```

Recovery is not complete when bytes have been restored.

---

## 31. Recovery Readiness

The system should continuously know whether it has:

- recent valid checkpoints;
- usable replicas;
- recoverable event history;
- tested restoration procedures;
- valid credentials;
- compatible schemas;
- available recovery capacity;
- current recovery metadata.

A backup that has never been restored is an unverified assumption.

---

## 32. Restore Testing

Recovery procedures must be exercised.

Tests should include:

```text
PROCESS CRASH
NODE LOSS
NETWORK PARTITION
DATABASE CORRUPTION
BAD SNAPSHOT
MISSING EVENTS
DUPLICATE EVENTS
STALE POLICY
MODEL VERSION CHANGE
HUMAN APPROVAL EXPIRY
TOOL TIMEOUT
EXTERNAL SIDE EFFECT UNKNOWN
```

---

## 33. Disaster Recovery Tiers

Different domains may have different recovery objectives.

```text
TIER 0 — critical governance / safety
TIER 1 — core durable memory
TIER 2 — active cognitive workloads
TIER 3 — derived indexes
TIER 4 — rebuildable caches
```

Each tier declares RPO/RTO targets appropriate to the deployment.

---

## 34. RPO and RTO

**RPO — Recovery Point Objective:** maximum acceptable loss of durable progress.

**RTO — Recovery Time Objective:** maximum acceptable restoration time.

Novi must not promise zero data loss or instant recovery without an architecture that actually provides it.

---

## 35. Recovery Capacity

Recovery consumes resources.

During a large outage, blindly starting every recovery task can cause a second failure.

Recovery therefore requires:

- prioritization;
- concurrency limits;
- backpressure;
- dependency ordering;
- resource reservations.

This prepares the resource-governance work in 113.

---

## 36. Cascading Failure Protection

Recovery should avoid overwhelming dependencies that are themselves degraded.

```text
FAILURE
 ↓
RETRY STORM
 ↓
DEPENDENCY OVERLOAD
 ↓
MORE FAILURE
```

Use bounded retries, exponential backoff, jitter, circuit breakers, bulkheads and recovery budgets where appropriate.

---

## 37. Graceful Degradation

When full functionality is unavailable:

```text
FULL AUTONOMY
 ↓
RESTRICTED AUTONOMY
 ↓
READ-ONLY
 ↓
LOCAL-ONLY
 ↓
SAFE STOP
```

The degradation path is deployment-specific and must be defined before failure occurs.

Layered resilience patterns such as circuit breakers, fallbacks and isolated failure domains are increasingly used for long-running agent systems with many external dependencies. citeturn0search10

---

## 38. Safe Stop

If safe continuation cannot be established, Novi should transition to the deployment's defined safe state.

```text
UNKNOWN CRITICAL STATE
        ↓
SAFE RESTRICTED STATE
```

This follows 105's default-deny governance principle.

---

## 39. Recovery Under Network Partition

During a partition, each node must respect its local authority envelope.

A disconnected node must not infer that:

```text
NO REVOCATION RECEIVED
      ≠
REVOCATION DOES NOT EXIST
```

Critical authority may therefore require leases, bounded validity or central confirmation.

---

## 40. Split-Brain Recovery

After a partition, divergent histories must be reconciled according to 108 and 109.

```text
NODE A HISTORY
        ↘
         RECONCILIATION
        ↗
NODE B HISTORY
```

Do not automatically pick the newest wall-clock timestamp for semantic conflicts.

---

## 41. Fencing

A node that has lost authority must be prevented from continuing writes that could conflict with the recovered authority.

Fencing may use:

- epochs;
- leases;
- fencing tokens;
- revoked credentials;
- storage-level ownership checks.

Recovery without fencing can resurrect a stale writer.

---

## 42. Recovery and Replication

109 provides replicated state; 110 determines which replica or snapshot is trusted during recovery.

Replica selection should consider:

```text
integrity
revision
causal completeness
policy compatibility
schema compatibility
provenance
health
```

The nearest replica is not automatically the safest replica.

---

## 43. Recovery and Privacy

Recovery copies can contain deleted or restricted information.

Therefore backup and checkpoint stores are part of the privacy lifecycle.

```text
PRIMARY DATA
 ↓
CHECKPOINT
 ↓
REPLICA
 ↓
BACKUP
```

Each copy must have an explicit retention and deletion policy.

This is a direct dependency for 111.

---

## 44. Deletion and Restore

A critical rule:

> **Recovery must not resurrect data that has been validly deleted or revoked.**

Deletion tombstones and privacy state therefore need to survive snapshots and disaster restoration.

---

## 45. Security Incident Recovery

Security incidents require a separate recovery path:

```text
DETECT
 ↓
CONTAIN
 ↓
REVOKE
 ↓
ISOLATE
 ↓
PRESERVE EVIDENCE
 ↓
RESTORE TRUSTED STATE
 ↓
REVALIDATE
 ↓
RESUME RESTRICTED
```

Do not restore compromised credentials or poisoned state from a convenient but untrusted backup.

---

## 46. Model Rollback

If a model deployment is found unsafe:

```text
M3 ACTIVE
 ↓
INCIDENT
 ↓
QUARANTINE M3
 ↓
SELECT VERIFIED MODEL
 ↓
REVALIDATE MEMORY / SKILLS / POLICIES
 ↓
RESUME
```

Model rollback must account for state created while M3 was active.

---

## 47. Memory Rollback

Memory rollback is more dangerous than ordinary cache rollback because memory may contain durable human or world-state information.

A rollback must identify:

- affected entities;
- affected events;
- derived claims;
- downstream decisions;
- privacy implications;
- human corrections;
- model dependencies.

---

## 48. Causal Model Recovery

If a causal model becomes suspect, Novi must not silently continue using it because the underlying memory remains available.

```text
CAUSAL MODEL SUSPECT
 ↓
QUARANTINE MODEL
 ↓
FALLBACK / REVALIDATE
 ↓
REASSESS DEPENDENT DECISIONS
```

This integrates 100 and 104.

---

## 49. Skill Recovery

If a skill is discovered to be unsafe:

```text
SKILL ACTIVE
 ↓
FAILURE SIGNAL
 ↓
COMPETENCE REVOKED / RESTRICTED
 ↓
RECOVERY
 ↓
REVALIDATION
```

A recovered process must not automatically regain a capability merely because its code restarted.

---

## 50. Recovery of Human Oversight

If the human approval service is unavailable:

```text
APPROVAL SERVICE DOWN
 ↓
CHECK POLICY
 ├── safe continuation allowed
 ├── restricted continuation
 └── pause / stop
```

The model must not invent human approval.

---

## 51. Recovery of Governance State

Governance state has higher recovery priority than ordinary analytics or derived memory.

At minimum, recovery must establish:

```text
WHO MAY ACT
WHAT MAY BE DONE
WHICH POLICY IS ACTIVE
WHICH CAPABILITIES ARE REVOKED
WHETHER EMERGENCY STOP IS ACTIVE
```

before restoring high-impact autonomy.

---

## 52. Recovery of Identity

Identity state must be restored with provenance and confidence.

Ambiguous identity after recovery should remain ambiguous rather than being resolved by convenience.

This integrates 97.

---

## 53. Temporal Recovery

Recovery must preserve historical time.

A restored event's original timestamp must not be replaced by its recovery timestamp.

Both may be recorded:

```text
EVENT TIME
RECOVERY TIME
```

This integrates 98.

---

## 54. Spatial Recovery

Recovered spatial state must preserve source precision, coordinate reference and observation time where applicable.

A recovery location is not automatically the event location.

This integrates 99.

---

## 55. Cross-Modal Recovery

If one modality's data is corrupted:

```text
VIDEO CORRUPTED
AUDIO VALID
TEXT VALID
SENSOR VALID
```

Novi should degrade evidence confidence according to the evidence model rather than treating the entire event as either true or false.

This integrates 101.

---

## 56. Recovery Provenance

Every recovery action should itself be an auditable event:

```text
FAILURE
 ↓
RECOVERY ACTION
 ↓
SOURCE CHECKPOINT
 ↓
RESTORED STATE
 ↓
VALIDATION RESULT
```

This makes recovery part of the historical record rather than an invisible infrastructure operation.

---

## 57. Recovery Audit Record

At minimum record:

- incident ID;
- failure classification;
- detection time;
- recovery operator/automation;
- source state/checkpoint;
- model/policy/schema versions;
- actions performed;
- validation results;
- residual uncertainty;
- resumed state;
- follow-up actions.

---

## 58. Recovery Observability

Recovery metrics should include:

```text
TIME TO DETECT
TIME TO CONTAIN
TIME TO RECOVER
RECOVERY POINT AGE
DATA LOSS
REPLAY VOLUME
RECOVERY FAILURE RATE
ROLLBACK RATE
UNKNOWN-SIDE-EFFECT RATE
POST-RECOVERY INCIDENT RATE
```

112 should extend these into longitudinal reliability metrics.

---

## 59. Recovery Verification Is Independent

Where practical, the component performing recovery should not be the only component declaring recovery successful.

Use independent health checks, invariants or external verification for critical systems.

---

## 60. Recovery Readiness Levels

```text
R0 — no verified recovery
R1 — checkpoint exists
R2 — checkpoint + replay verified
R3 — restore tested
R4 — disaster scenario tested
R5 — continuous recovery validation
```

A production-critical deployment should define its required level explicitly.

---

## 61. Disaster Domains

A disaster may affect:

```text
PROCESS
HOST
RACK / ZONE
REGION
CLOUD / PROVIDER
NETWORK
STORAGE
IDENTITY PROVIDER
MODEL PROVIDER
EXTERNAL TOOLS
```

Recovery architecture must consider correlated failures, not only independent machine crashes.

---

## 62. Geographic Recovery

For deployments requiring regional resilience, recovery copies should be sufficiently independent from the primary failure domain.

Simply placing a backup in the same failure domain does not constitute disaster recovery.

---

## 63. Backup Independence

Backups should be protected against:

- accidental deletion;
- ransomware or compromise;
- credential compromise;
- corruption propagation;
- operator error.

Where appropriate use immutability, access separation and independent credentials.

---

## 64. Recovery Key Material

A recovery plan that requires credentials unavailable during the disaster is incomplete.

Key recovery procedures must be tested and governed without creating an uncontrolled bypass around 105.

---

## 65. Recovery Ordering

Dependencies determine restoration order.

A generic sequence is:

```text
IDENTITY / TRUST
 ↓
STORAGE / EVENT LOG
 ↓
POLICY / AUTHORITY
 ↓
CORE STATE
 ↓
MEMORY
 ↓
TOOLS / EXTERNAL INTEGRATIONS
 ↓
MODELS
 ↓
ACTIVE WORKFLOWS
 ↓
DERIVED INDEXES
```

Actual order is deployment-specific.

---

## 66. Do Not Restore Everything at Once

Restoration should be staged:

```text
RECOVER
 ↓
VERIFY
 ↓
ENABLE LOW-RISK READS
 ↓
ENABLE RESTRICTED WRITES
 ↓
ENABLE AUTONOMY
```

This reduces blast radius from a bad restoration.

---

## 67. Recovery Canary

A restored node can enter a canary state where a restricted workload verifies behavior before broader traffic is admitted.

```text
RESTORED
 ↓
CANARY
 ↓
VALIDATED
 ↓
PRODUCTION
```

---

## 68. Recovery and Model Evaluation

A model may behave differently after recovery due to:

- different context;
- changed tool state;
- updated model version;
- changed memory;
- altered policy;
- changed external environment.

Therefore recovery verification should test behavior, not only infrastructure health.

---

## 69. Recovery and Long-Running Trajectories

For long-running agents, the recoverable unit is not merely the last message.

It may include:

```text
GOAL
PLAN
PROGRESS
TOOL HISTORY
EXTERNAL RECEIPTS
OPEN QUESTIONS
MEMORY CHANGES
POLICY STATE
ENVIRONMENT STATE
DRIFT SIGNALS
```

This is consistent with current state-aware agent runtime research emphasizing separation of model generation from canonical state, validation, commit/rollback and audit traces. citeturn0search13

---

## 70. Recovery and Drift

If recovery reveals that the trajectory was already drifting before failure:

```text
CRASH
 ↓
RESTORE CHECKPOINT
 ↓
DRIFT DETECTION
 ↓
DO NOT BLINDLY RESUME
```

The correct action may be fork, replan, human review or rollback.

---

## 71. Recovery and Self-Healing

Automated self-healing may detect, classify and recover from failures, but its authority remains bounded by 105.

Self-healing research for LLM agents combines failure detection, reliability assessment and adaptive recovery, but autonomous repair must remain constrained by system governance. citeturn0academia27

```text
DETECT
 ↓
PROPOSE RECOVERY
 ↓
POLICY CHECK
 ↓
EXECUTE IF AUTHORIZED
 ↓
VERIFY
```

---

## 72. Human Escalation

Escalate recovery when:

- state integrity is uncertain;
- external side effect is unknown and consequential;
- authorization cannot be established;
- privacy deletion may be violated;
- model compatibility is unknown;
- conflicting authoritative histories exist;
- safety state cannot be verified.

---

## 73. Recovery Anti-Patterns

Avoid:

```text
RESTART FROM ZERO
BLIND REPLAY
BLIND RETRY
LATEST-WRITE-WINS FOR EVERYTHING
RESTORE WITHOUT VALIDATION
RESTORE WITHOUT POLICY CHECK
RESTORE WITHOUT DELETION STATE
TRUST THE NEAREST REPLICA
ASSUME CHECKSUM = SEMANTIC VALIDITY
ASSUME MODEL REPRODUCIBILITY
ASSUME HUMAN APPROVAL SURVIVES FOREVER
```

---

## 74. Recovery Invariants

1. Recovery is a governed state transition.
2. Checkpoints have explicit scope and dependencies.
3. A crash, drift and corruption are distinct failure classes.
4. Recovery preserves provenance.
5. Recovery preserves historical time.
6. Recovery does not silently change identity semantics.
7. Recovery does not silently rewrite historical memory.
8. Recovery does not bypass policy.
9. Recovery does not manufacture human approval.
10. Unknown external effects remain unknown until reconciled.
11. Replay requires compatible state semantics.
12. Non-idempotent effects require compensation, reconciliation or escalation.
13. Stale approvals are not automatically reusable.
14. Deleted data must not be resurrected by restore.
15. Security-compromised state must be quarantined.
16. Stale writers must be fenced before recovery completes.
17. Recovery must be independently validated for critical systems.
18. Disaster recovery includes correlated failure domains.
19. Backups are part of the privacy and security boundary.
20. Recovery capacity must be resource-governed.
21. Recovery should be staged rather than enabling all autonomy immediately.
22. Model changes can invalidate a recovery continuation.
23. Memory changes can invalidate historical decision context.
24. Skill competence does not automatically survive recovery.
25. Governance state must be restored before high-impact autonomy resumes.
26. A successful byte-level restore is not proof of semantic correctness.
27. Recovery actions themselves are auditable events.
28. A known-good state must be defined, not assumed.
29. Recovery must preserve the distinction between fact, inference, prediction and recommendation.
30. When safe continuation cannot be established, the system enters the deployment's restricted or safe state.

---

## 75. Integration With 107

107 provides durable events, state transitions and execution semantics.

110 turns those primitives into recoverable execution:

```text
EVENT HISTORY
 +
CHECKPOINT
 +
COMPATIBLE REDUCER
 ↓
RECOVERED STATE
```

---

## 76. Integration With 108

108 defines transactions, concurrency and consistency.

110 uses those guarantees to determine whether recovery can safely replay, compensate, retry or reconcile an interrupted operation.

---

## 77. Integration With 109

109 defines replication and distributed memory.

110 defines how Novi selects, validates and restores from replicated state after failure or partition.

Replication is availability machinery; recovery is the controlled process of returning the system to a verified operational state.

---

## 78. Integration With 111

111 must treat checkpoints, replicas and backups as data copies subject to retention, access, deletion and dependency-aware erasure.

Recovery must preserve deletion semantics.

---

## 79. Integration With 112

112 should measure whether recovery actually preserves long-term reliability rather than merely reducing downtime.

Post-recovery drift and repeated failure must remain visible.

---

## 80. Integration With 113

Recovery consumes compute, storage, network and model capacity.

113 should provide explicit recovery budgets and priority rules so an incident does not create a resource-exhaustion cascade.

---

## 81. Integration With 114

In multi-agent systems, one agent may fail while others continue.

Recovery must preserve delegation, authority, shared-state consistency and task ownership.

A recovered agent must re-establish its identity and lease/authority before writing shared state.

---

## 82. Research Cross-Validation

The architecture was cross-validated against multiple current sources rather than relying on a single vendor pattern:

- AWS Agentic AI Lens recommends persisted state, checkpoint-based resume, idempotent workflow steps and explicit checkpoint lifecycle management. citeturn0search1
- Recent agent sandbox checkpoint research identifies the semantic gap between application-level agent state and OS/runtime side effects, motivating checkpoint mechanisms that understand both. citeturn0academia26
- Recent LLM inference research demonstrates that long-running inference can retain valuable GPU-resident execution state and explores checkpointing that state for fault tolerance. citeturn0academia25
- Berkeley fault-tolerance research emphasizes exploiting workload semantics to improve recovery efficiency rather than treating all workloads identically. citeturn0search2
- Recent self-healing agent research supports combining failure detection, reliability assessment and recovery rather than relying solely on restart. citeturn0academia27
- Current state-aware agent-runtime work emphasizes canonical state, validation, commit/rollback and audit as separate from model generation. citeturn0search13

These sources support the architectural principles but do not establish a single implementation technology. Novi therefore defines contracts and invariants rather than mandating Temporal, Kubernetes, a particular database, a particular checkpoint format, or a particular model runtime.

---

## 83. Architecture Decision Summary

Novi adopts:

```text
DURABLE EVENTS
      ↓
VERSIONED CHECKPOINTS
      ↓
SEMANTICALLY VALIDATED RESTORE
      ↓
POLICY / AUTHORITY RECHECK
      ↓
STAGED RESUMPTION
```

with optional:

```text
REPLAY
COMPENSATION
RECONCILIATION
FORK
ROLLBACK
HUMAN ESCALATION
```

according to failure class.

---

## 84. Final Principle

> **A resilient Novi is not a system that never fails. It is a system that can determine what state remains trustworthy, preserve what happened, contain what is unsafe, recover from a verified point, reconcile what occurred outside its control, and resume only when its semantic, security and governance invariants are restored.**

This makes recovery a first-class part of Novi's cognition infrastructure rather than an afterthought in its hosting environment.
