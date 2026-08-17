# 111 — Privacy, Retention, Dependency-Aware Erasure & Data Lifecycle Architecture

**Status:** Normative architecture foundation — P1

**Depends on:** 95–110, especially identity, provenance, cross-modal memory, schema evolution, model/memory co-evolution, governance, durable state, replication and recovery.

**Enables:** 112 observability and lifespan reliability, 113 resource governance, 114 multi-agent coordination.

---

## 1. Purpose

Define how Novi collects, classifies, uses, derives, stores, replicates, retains, restricts, deletes, anonymises, and verifies information throughout its lifecycle.

The architecture treats privacy as a property of the **entire information dependency graph**, not merely of a database row.

The core principle is:

> **Novi must minimize personal and sensitive information, retain it only for justified purposes and periods, track material derivatives, enforce access restrictions throughout distributed copies, and make erasure and retention outcomes verifiable.**

This is consistent with current ICO guidance that AI systems should process only personal information necessary for their purposes, periodically review what they retain, maintain documented retention schedules, and track information across system-development and production stages. citeturn0search1turn0search6

---

## 2. Privacy Is a Lifecycle Property

Privacy must apply across:

```text
COLLECT
 ↓
INGEST
 ↓
CLASSIFY
 ↓
STORE
 ↓
RETRIEVE
 ↓
DERIVE
 ↓
REPLICATE
 ↓
BACKUP
 ↓
USE
 ↓
RETAIN
 ↓
DELETE / ANONYMISE / RESTRICT
 ↓
VERIFY
```

A system cannot claim that information was deleted merely because the primary record disappeared.

---

## 3. Data Minimisation

Novi must collect and process the minimum information required for the declared purpose.

```text
PURPOSE
 ↓
REQUIRED INFORMATION
 ↓
MINIMUM SUFFICIENT SET
```

The system must not adopt a default policy of collecting everything because future usefulness is uncertain. ICO guidance explicitly warns against retaining information merely because it may become useful later. citeturn0search0turn0search2

---

## 4. Purpose Limitation

Every protected data flow should have an explicit purpose or authorized purpose class.

```text
DATA
 ↓
PURPOSE
 ↓
AUTHORIZED USE
```

A record collected for one purpose must not silently become available for unrelated purposes merely because it exists in memory.

---

## 5. Data Classification

Novi should classify information according to sensitivity and operational consequence.

A deployment may define classes such as:

```text
PUBLIC
INTERNAL
CONFIDENTIAL
PERSONAL
SENSITIVE PERSONAL
SECURITY-CRITICAL
SAFETY-CRITICAL
RESTRICTED DERIVED
```

Classification is metadata and must itself be protected from unauthorized alteration.

---

## 6. Personal Data Is Not Limited to Raw Input

Privacy controls must cover:

- raw observations;
- text;
- images;
- audio;
- video;
- telemetry;
- identifiers;
- embeddings where they remain linked or linkable;
- inferred attributes;
- semantic memories;
- causal claims;
- skill records;
- model inputs;
- generated summaries;
- audit records;
- backups;
- cached copies.

Derived information can remain sensitive even after the original source is removed.

---

## 7. Identity and Privacy

Identity from document 97 must be separated from authorization.

```text
ENTITY ID
 ≠
AUTHENTICATION
 ≠
AUTHORIZATION
```

An entity identifier must not itself grant access to the entity's protected information.

---

## 8. Identity Resolution and Privacy Risk

Identity resolution can create privacy risk by linking previously separate observations.

Therefore:

```text
IDENTITY MATCH
 ↓
LINKAGE RISK
 ↓
POLICY CHECK
```

A low-confidence identity match must not automatically expose information associated with another entity.

---

## 9. Temporal Privacy

Time can itself be sensitive.

A system may need to protect:

- precise timestamps;
- schedules;
- historical movements;
- periods of absence;
- recurring routines.

Document 98's temporal precision should therefore be subject to data-classification and access policy.

---

## 10. Spatial Privacy

Precise location can be more sensitive than coarse location.

```text
EXACT COORDINATE
      ↓
NEIGHBORHOOD
      ↓
CITY
```

Precision reduction can be a privacy control, but it is an information transformation and must preserve provenance.

---

## 11. Cross-Modal Privacy

The same individual may appear across:

```text
IMAGE
AUDIO
TEXT
VIDEO
SENSOR DATA
```

Cross-modal linking can increase privacy risk even if each modality individually appears low sensitivity.

Privacy classification should therefore consider the combined inference capability of linked modalities.

---

## 12. Derived Data

Novi must distinguish:

```text
SOURCE DATA
DERIVED DATA
INFERRED DATA
AGGREGATED DATA
MODEL STATE
```

A derived claim must carry enough provenance to determine which source information materially contributed to it.

---

## 13. Dependency Graph

The core privacy data structure is a dependency graph:

```text
SOURCE
 ↓
OBSERVATION
 ↓
MEMORY
 ↓
SUMMARY
 ↓
INFERENCE
 ↓
CAUSAL MODEL
 ↓
SKILL / POLICY INPUT
 ↓
DECISION
```

Each edge should indicate derivation where material.

This extends the provenance and durable-event architecture from documents 92, 107 and 109.

---

## 14. Why Dependency-Aware Erasure Is Required

Consider:

```text
PERSONAL OBSERVATION
       ↓
MEMORY
       ↓
EMBEDDING
       ↓
SUMMARY
       ↓
MODEL UPDATE
```

Deleting only the observation may leave multiple downstream representations.

Novi must determine which derivatives contain, encode, expose, or materially depend on the protected information.

---

## 15. Erasure Is Not One Operation

Possible outcomes include:

```text
PHYSICAL DELETE
LOGICAL DELETE
ACCESS REVOCATION
TOMBSTONE
ANONYMISATION
AGGREGATION
RETRAIN / UNLEARN
DERIVATIVE INVALIDATION
RETENTION-LOCKED EXCEPTION
```

The correct operation depends on the information class, system architecture and applicable policy.

---

## 16. Erasure Request Lifecycle

```text
REQUEST
 ↓
AUTHENTICATE / VERIFY SCOPE
 ↓
LOCATE DATA
 ↓
DISCOVER DERIVATIVES
 ↓
CHECK RETENTION / LEGAL CONSTRAINTS
 ↓
PLAN ERASURE
 ↓
EXECUTE
 ↓
PROPAGATE
 ↓
VERIFY
 ↓
REPORT RESULT
```

An erasure request should become a durable governance event.

---

## 17. Erasure Scope

A deletion request must identify the applicable subject, records, purposes and scope.

Novi must avoid both:

```text
UNDER-DELETION
```

and:

```text
OVER-DELETION OF UNRELATED DATA
```

---

## 18. Search for Copies

Erasure planning should search known storage surfaces:

```text
PRIMARY STORE
REPLICAS
CACHE
INDEX
VECTOR STORE
EVENT LOG
SNAPSHOTS
BACKUPS
EXPORTS
STAGING
ANALYTICS
TRAINING DATA
DERIVED MEMORY
```

The inventory should distinguish active, archived, immutable and expired copies.

ICO guidance specifically recommends mapping personal information across AI-system phases and using automated tracing to identify duplication and unnecessary copies. citeturn0search1

---

## 19. Replicated Erasure

Replication from document 109 must integrate with privacy deletion.

```text
DELETE AUTHORITY
 ↓
REPLICATION TOMBSTONE / COMMAND
 ↓
REPLICAS
 ↓
ACKNOWLEDGE
 ↓
VERIFY
```

An offline replica must not resurrect deleted data after reconnecting.

---

## 20. Tombstones

A tombstone can establish:

```text
OBJECT X
STATUS = DELETED
```

and prevent stale replicas from reintroducing it.

Tombstones themselves may contain sensitive identifiers and therefore require retention and access controls.

---

## 21. Backup Erasure

Backups create a special problem.

Novi should define whether deletion means:

```text
IMMEDIATE PHYSICAL REMOVAL
```

or:

```text
ACCESS-BLOCK + EXPIRING BACKUP RETENTION + PURGE
```

where immediate removal from immutable backup media is technically impractical.

Any exception must be explicit, controlled and auditable.

---

## 22. Recovery Interaction

Documents 110 and 111 must cooperate.

A recovery operation must not restore deleted personal information from an old checkpoint without reapplying current deletion state.

```text
OLD CHECKPOINT
     +
CURRENT DELETION LOG
     ↓
RECOVERED STATE
```

Deletion tombstones therefore need sufficient durability to survive disaster recovery.

---

## 23. Event Log Privacy

Event logs are not automatically exempt from privacy requirements merely because they are append-only.

Where events contain personal information, Novi should consider:

- minimizing event payloads;
- tokenized identifiers;
- protected references;
- cryptographic deletion envelopes;
- tombstones;
- retention limits;
- controlled archival.

---

## 24. Immutable Audit Logs

Auditability and erasure can conflict.

Novi must therefore distinguish:

```text
AUDIT INTEGRITY
```

from:

```text
UNLIMITED RETENTION OF PERSONAL CONTENT
```

Where possible, audit records should minimize personal content while retaining sufficient accountability metadata.

---

## 25. Retention Policy

Every retained data class should have a policy specifying, where applicable:

```text
PURPOSE
RETENTION PERIOD
TRIGGER
LEGAL / OPERATIONAL BASIS
ACCESS CLASS
DISPOSAL ACTION
EXCEPTION PROCESS
OWNER
```

ICO guidance recommends documented retention schedules and evidence that they are actually followed. citeturn0search1

---

## 26. Retention Starts With Purpose

Retention should not be chosen first and justified later.

```text
PURPOSE
 ↓
NECESSARY RETENTION
 ↓
RETENTION PERIOD
```

The period should be proportionate to the purpose and risk.

---

## 27. Retention Triggers

A retention period may begin from:

- collection;
- last use;
- relationship termination;
- event completion;
- account closure;
- legal requirement;
- incident resolution;
- model retirement.

The trigger must be explicit.

---

## 28. Rolling Retention

For continuously updated memories or telemetry:

```text
NOW - WINDOW
```

may define a moving retention boundary.

Rolling deletion must not silently remove records required by an active legal, safety or operational retention requirement.

---

## 29. Retention Exceptions

Exceptions should require:

- explicit reason;
- authorized principal;
- scope;
- expiry/review date;
- policy reference;
- audit event.

"Keep forever just in case" is not a valid generic policy.

---

## 30. Data Accuracy and Rectification

Privacy lifecycle management must support correction as well as deletion.

```text
INCORRECT DATA
 ↓
RECTIFICATION
 ↓
DERIVATIVE IMPACT ANALYSIS
```

A corrected source may require derived memories, summaries or models to be reevaluated.

ICO guidance emphasizes that inaccurate personal data should be corrected or erased without delay where required by the applicable principles. citeturn0search5

---

## 31. Correction vs Historical Record

Correcting current semantic state should not rewrite historical provenance.

```text
ORIGINAL EVENT
 ↓
CORRECTION EVENT
```

This preserves accountability while allowing current state to become accurate.

---

## 32. Privacy and Model Training

Novi must track personal data entering:

- pretraining datasets;
- fine-tuning datasets;
- preference data;
- evaluation datasets;
- retrieval corpora;
- memory-derived training sets;
- reinforcement signals.

Training use is a distinct processing purpose and must be governed accordingly.

ICO guidance notes that training-data erasure requests generally require consideration and that deleting training data does not automatically require deleting every model trained on it; the model itself becomes relevant where it contains or can reveal the protected information. citeturn0search8

---

## 33. Model Memory vs Model Parameters

Novi must distinguish:

```text
EXPLICIT MEMORY
 ≠
RETRIEVAL INDEX
 ≠
MODEL PARAMETERS
```

Deleting explicit memory is not equivalent to proving that a trained model has no influence from that information.

---

## 34. Model Unlearning Boundary

If a policy requires information to be removed from model behavior, Novi may require:

```text
DATA REMOVAL
 ↓
IMPACT ASSESSMENT
 ↓
UNLEARNING / RETRAINING / MODEL REPLACEMENT
 ↓
VALIDATION
```

Unlearning must not be assumed successful merely because the source dataset changed.

---

## 35. Embedding Privacy

Embeddings should be treated according to whether they can identify, link to or reveal protected information in the deployment context.

```text
RAW DATA
 ↓
EMBEDDING
```

is a transformation, not automatically anonymisation.

---

## 36. Cache Privacy

Caches must inherit the privacy classification of the data they contain.

Temporary storage is still storage.

Cache expiration must therefore be policy-driven rather than left entirely to implementation defaults.

---

## 37. Search Index Privacy

Search indexes can expose information even after source records are inaccessible.

Deletion and access-control changes must propagate to indexes and retrieval layers.

---

## 38. Vector Database Privacy

Vector stores require:

- subject-aware access control;
- deletion propagation;
- metadata filtering;
- tenant isolation;
- retention policies;
- embedding lifecycle management.

A vector index must not become a privacy bypass around the canonical memory store.

---

## 39. Derived Summaries

Summaries may reveal sensitive information even when they do not contain the original text verbatim.

Therefore summarization does not automatically reduce sensitivity.

---

## 40. Aggregation and Anonymisation

Aggregation or anonymisation may reduce privacy risk, but must be assessed against realistic re-identification and linkage risks.

Pseudonymisation is not equivalent to anonymisation; pseudonymised data can remain personal data. ICO guidance explicitly distinguishes these concepts. citeturn0search2

---

## 41. Privacy-Preserving Techniques

Depending on the threat model and workload, Novi may use:

```text
PSEUDONYMISATION
ANONYMISATION
REDACTION
DATA CROPPING
AGGREGATION
DIFFERENTIAL PRIVACY
FEDERATED LEARNING
SECURE COMPUTATION
ENCRYPTION
ACCESS-CONTROLLED DERIVATION
```

No technique should be treated as universally sufficient.

ICO guidance identifies privacy-enhancing techniques including differential privacy, homomorphic encryption and federated learning as possible approaches depending on circumstances and resources. citeturn0search1turn0search2

---

## 42. Access Control

Every protected information access should evaluate:

```text
WHO
WHAT
WHY
WHICH PURPOSE
WHICH DATA
WHEN
WHERE
UNDER WHICH POLICY
```

Document 105 remains the authorization enforcement layer.

---

## 43. Purpose-Aware Retrieval

Memory retrieval should be filtered by purpose.

```text
QUERY
 ↓
PURPOSE
 ↓
AUTHORIZED MEMORY SUBSET
 ↓
RETRIEVAL
```

A user's permission to ask Novi a question does not imply access to every memory related to the query.

---

## 44. Least Privilege

Novi components should receive only the information and capabilities required for their task.

This applies to:

- models;
- tools;
- agents;
- operators;
- services;
- replication peers;
- recovery systems.

---

## 45. Multi-Tenant Isolation

Where multiple users or organizations share infrastructure:

```text
TENANT A
 ≠
TENANT B
```

Cross-tenant retrieval, synchronization and derived-data propagation must be blocked unless explicitly authorized.

---

## 46. Agent Isolation

An agent's access to shared memory must be scoped.

Agent identity does not imply unrestricted access to the memory of other agents.

---

## 47. Delegated Access

Delegation must preserve the original authority boundary:

```text
HUMAN
 ↓
AGENT A
 ↓
AGENT B
```

Agent B must not gain broader data access merely because A delegated a task.

---

## 48. Privacy and Human Oversight

Human reviewers should receive the minimum protected information required to make the decision.

```text
FULL RECORD
 ↓
TASK-RELEVANT REDACTION
 ↓
REVIEWER
```

Oversight interfaces must not become uncontrolled privacy portals.

---

## 49. Privacy and Observability

Logs, traces and metrics from document 112 must be designed to avoid unnecessary personal-data replication.

Prefer:

```text
STABLE NON-SENSITIVE IDENTIFIER
```

over copying raw sensitive payloads into every log entry.

---

## 50. Privacy and Recovery

Recovery checkpoints should be classified and encrypted according to their contents.

Restoring a checkpoint must reapply:

- deletion state;
- revocations;
- retention expiry;
- access policy;
- current tenant boundaries.

---

## 51. Privacy and Replication

Replication scope must be explicitly authorized.

```text
DATA CLASS
 ↓
REPLICATION POLICY
 ↓
AUTHORIZED NODES
```

A node being trusted for availability does not automatically make it trusted for every privacy class.

---

## 52. Privacy and Schema Migration

Schema migrations must preserve privacy classification and retention metadata.

A field split or merge must not accidentally remove its protection class.

```text
OLD FIELD
  ↓
MIGRATION
  ↓
NEW FIELD(S)
  ↓
INHERIT / REEVALUATE PRIVACY
```

---

## 53. Privacy and Model/Memory Co-Evolution

When a model or representation changes, dependency mappings must be reevaluated.

A new embedding or summary representation may create new privacy characteristics.

Privacy review therefore participates in model promotion under document 104.

---

## 54. Privacy and Causal Knowledge

Causal models can reveal sensitive relationships even after source observations are removed.

Causal knowledge must therefore inherit privacy classification from material sources where appropriate.

---

## 55. Privacy and Skill Memory

A skill record may contain sensitive contextual information about:

- a person;
- environment;
- workplace;
- equipment;
- behavioral history.

Skill abstractions must be evaluated for residual personal information rather than assumed harmless because they are procedural.

---

## 56. Data Subject / Principal Rights Interface

Where applicable to a deployment, Novi should support controlled workflows for rights requests such as:

```text
ACCESS
RECTIFICATION
ERASURE
RESTRICTION
OBJECTION
PORTABILITY
```

The exact legal applicability and exceptions are deployment-specific and must be determined by appropriate legal/privacy governance.

ICO guidance explicitly discusses individual rights in AI systems, including erasure requests involving training data. citeturn0search8

---

## 57. Request Authentication

A privacy request must not expose or delete another person's information merely because the requester supplied a matching name.

Verification must be appropriate to the sensitivity and request.

---

## 58. Request Authorization

Some requests require additional authority or legal analysis.

The system should distinguish:

```text
REQUEST RECEIVED
REQUEST VERIFIED
REQUEST AUTHORIZED
REQUEST EXECUTED
```

---

## 59. Erasure Verification

Verification should test relevant storage surfaces and derivatives.

Possible evidence:

```text
PRIMARY = DELETED
REPLICA = DELETED
INDEX = REMOVED
CACHE = EXPIRED
BACKUP = PURGE SCHEDULED
DERIVATIVE = INVALIDATED
```

The result should state what was verified and what remains subject to controlled retention.

---

## 60. No False Erasure Claims

Novi must never report:

```text
"Everything has been deleted."
```

unless the system has evidence sufficient to support that claim.

Instead it should report the verified scope and any remaining controlled exceptions.

---

## 61. Deletion Dependency States

Each derivative may be classified:

```text
DIRECTLY DELETABLE
REQUIRES CASCADE
REQUIRES INVALIDATION
REQUIRES REBUILD
REQUIRES RETRAINING / UNLEARNING
LEGALLY RETAINED
UNKNOWN DEPENDENCY
```

`UNKNOWN DEPENDENCY` must not silently become `DELETED`.

---

## 62. Privacy Incident Response

Potential privacy incidents integrate with document 110:

```text
DETECT
 ↓
CONTAIN
 ↓
IDENTIFY SCOPE
 ↓
REVOKE ACCESS
 ↓
PRESERVE NECESSARY EVIDENCE
 ↓
REMEDIATE
 ↓
VERIFY
 ↓
GOVERNANCE REVIEW
```

---

## 63. Privacy Poisoning

Malicious actors may insert sensitive information into memory or training pipelines intentionally.

Novi should therefore distinguish:

```text
DATA PRESENT
```

from:

```text
DATA AUTHORIZED FOR RETENTION / USE
```

Untrusted sensitive content should not automatically become persistent memory.

---

## 64. Privacy Threats

Threat modeling should cover:

- unauthorized retrieval;
- cross-tenant leakage;
- membership inference;
- model inversion;
- re-identification;
- linkage attacks;
- prompt-based extraction;
- malicious memory insertion;
- stale replica resurrection;
- backup leakage;
- log leakage;
- embedding leakage;
- inference of sensitive attributes.

---

## 65. Privacy-Preserving Defaults

Where the system cannot establish that a data flow is authorized:

```text
DO NOT DISCLOSE
```

For high-risk ambiguity, default to restricted access or escalation rather than broad retrieval.

---

## 66. Privacy Classification Propagation

Derived records should inherit or recompute privacy classification based on their dependencies.

```text
SOURCE: SENSITIVE
        ↓
SUMMARY: ?
        ↓
CLASSIFICATION ENGINE
        ↓
SENSITIVE / RESTRICTED / DE-IDENTIFIED
```

Classification must not automatically decrease merely because a representation is shorter.

---

## 67. Privacy Composition

Combining individually low-sensitivity records may create a high-sensitivity inference.

Therefore classification should consider combinations and linkage, not only individual fields.

---

## 68. Data Lineage

Novi should maintain lineage sufficient to answer:

```text
Where did this information come from?
What did it derive?
Where was it copied?
Who accessed it?
What model consumed it?
Which outputs depend on it?
```

This supports both privacy governance and technical debugging.

---

## 69. Retention Auditing

Retention compliance should be continuously or periodically evaluated.

```text
DATA INVENTORY
 ↓
RETENTION POLICY
 ↓
AGE / USE CHECK
 ↓
DELETE / EXTEND WITH AUTHORIZATION
```

NIST's AI Risk Management Framework treats governance, mapping, measurement and management as continuous lifecycle functions, supporting a lifecycle rather than one-time governance model. citeturn0search9

---

## 70. Privacy Metrics

Useful metrics include:

- unnecessary-data rate;
- stale-data rate;
- retention violations;
- deletion completion rate;
- deletion verification failures;
- derivative-discovery coverage;
- unauthorized access attempts;
- cross-tenant leakage incidents;
- stale-replica resurrection attempts;
- privacy incident rate;
- time to restrict access;
- time to complete authorized deletion.

Metrics must not themselves expose unnecessary personal data.

---

## 71. Privacy Testing

Test at minimum:

```text
DELETE SOURCE
→ DOES DERIVATIVE REMAIN?

DELETE REPLICA
→ CAN STALE NODE RESURRECT IT?

REVOKE ACCESS
→ CAN CACHE STILL SERVE IT?

CHANGE CLASSIFICATION
→ DO ALL COPIES INHERIT IT?

RECOVER OLD CHECKPOINT
→ DOES DELETED DATA RETURN?
```

---

## 72. Privacy Chaos Testing

Fault injection should include:

- replica offline during deletion;
- backup restore after deletion;
- delayed tombstone;
- corrupted dependency graph;
- stale cache;
- concurrent correction and deletion;
- schema migration during erasure;
- model update during erasure;
- network partition during revocation.

---

## 73. Concurrent Erasure and Update

If an update and deletion occur concurrently, 108's transaction and ordering semantics must determine the final state.

A later update must not silently recreate data that a valid deletion operation made inaccessible.

---

## 74. Concurrent Erasure and Replication

109 must propagate deletion semantics with appropriate consistency.

```text
DELETE
 ↓
REPLICATION
```

must be treated as a protected state transition, not ordinary best-effort metadata.

---

## 75. Concurrent Erasure and Recovery

110 must replay privacy state after restoring old snapshots.

```text
CHECKPOINT T1
 +
DELETION T2
 ↓
RECOVER
 ↓
DELETION STILL APPLIES
```

---

## 76. Privacy and Human Approval

A human must not be able to approve disclosure of protected information merely by overriding a normal application warning unless the governance model explicitly grants that authority.

105 and 106 remain the governing authorization layers.

---

## 77. Privacy and Emergency Operations

Emergency operation may justify restricted access in some deployments, but emergency mode must be:

- authenticated;
- scoped;
- time-bounded;
- logged;
- reviewed afterward.

Emergency status is not unlimited privacy exemption.

---

## 78. Privacy Policy Versioning

Retention, classification, access and erasure rules must be versioned.

Historical decisions should reference the policy version under which they occurred.

---

## 79. Policy Change Impact

Changing a retention policy may affect existing data.

```text
POLICY V2
 ↓
IMPACT ANALYSIS
 ↓
EXISTING DATA
 ↓
MIGRATE / DELETE / RETAIN
```

Policy changes must not silently invalidate accountability history.

---

## 80. Privacy Recovery After System Failure

Privacy controls must be restored before normal high-risk processing resumes.

```text
SYSTEM RECOVERY
 ↓
PRIVACY POLICY RECOVERY
 ↓
DELETION STATE RECOVERY
 ↓
ACCESS CONTROL RECOVERY
 ↓
VALIDATION
 ↓
RESUME
```

---

## 81. Privacy and Multi-Agent Futures

114 must treat shared memory as a privacy boundary.

An agent may synchronize only data that its authority and role permit.

```text
SHARED MEMORY
 ≠
PUBLIC MEMORY
```

---

## 82. Privacy and Resource Governance

113 should account for the cost of privacy controls without allowing cost pressure to disable mandatory protections.

For example:

```text
STORAGE COST
 ≠
JUSTIFICATION TO RETAIN UNNECESSARY PERSONAL DATA
```

---

## 83. Privacy Architecture Invariants

1. Personal information must be minimized.
2. Purpose must be explicit enough to govern use.
3. Retention must be justified and bounded.
4. Temporary storage is still storage.
5. Derived information can remain sensitive.
6. Embeddings are not automatically anonymous.
7. Pseudonymisation is not automatically anonymisation.
8. Identity resolution does not grant authorization.
9. Cross-modal linkage can increase privacy risk.
10. Classification must propagate through material derivations.
11. Replicas inherit applicable privacy requirements.
12. Backups require privacy lifecycle controls.
13. Event logs can contain personal data and require governance.
14. Deletion must account for known material derivatives.
15. A stale replica must not resurrect deleted information.
16. Recovery must reapply deletion and revocation state.
17. An erasure request must be authenticated and scoped.
18. `UNKNOWN DEPENDENCY` must not be reported as deleted.
19. Privacy exceptions require explicit authority and auditability.
20. Access must be purpose-aware and least-privilege.
21. Tenant boundaries must survive replication and recovery.
22. Human oversight must receive only necessary sensitive information.
23. Observability must minimize personal data in logs and traces.
24. Model parameters are distinct from explicit memory and retrieval indexes.
25. Data deletion does not automatically prove model unlearning.
26. Model updates must consider privacy impact.
27. Schema migration must preserve or reevaluate privacy metadata.
28. Privacy policy changes must be versioned.
29. Privacy controls must recover before high-risk processing resumes.
30. Privacy metrics must not create additional unnecessary exposure.
31. The system must never claim complete erasure without sufficient verification.
32. Legal applicability and exceptions must be determined per deployment by appropriate governance.

---

## 84. Integration With 95–110

```text
97  Identity
→ who the protected information concerns

98  Temporal
→ when the information applies and how long it remains relevant

99  Spatial
→ where precision itself may create sensitivity

100 Causal
→ derived relationships can remain sensitive

101 Cross-Modal
→ linkage can increase inference risk

102 Skill
→ procedural memories can contain personal context

103 Schema
→ privacy metadata must survive migrations

104 Model/Memory
→ learned and derived representations require lifecycle analysis

105 Governance
→ authorization and policy enforcement

106 Human Oversight
→ human review must remain privacy-minimized

107 Durable State
→ lifecycle events and deletion state must be durable

108 Consistency
→ concurrent privacy operations need deterministic semantics

109 Replication
→ deletion/revocation must propagate across replicas

110 Recovery
→ old checkpoints must not resurrect deleted or revoked state
```

---

## 85. Research Cross-Validation

The architecture is grounded in current UK AI/data-protection guidance and risk-management principles.

The ICO emphasizes data minimisation, storage limitation, periodic review, documented retention schedules, lifecycle data mapping, deletion of unnecessary duplicates, and privacy-preserving techniques for AI systems. citeturn0search1turn0search2turn0search6

The ICO also distinguishes deletion of training data from automatic deletion of every trained model, while requiring assessment of whether models themselves contain or can reveal the protected information. citeturn0search8

NIST's AI RMF frames AI risk management as continuous lifecycle work across govern, map, measure and manage, supporting the architecture's requirement for ongoing privacy monitoring rather than a one-time compliance gate. citeturn0search9

These sources establish governance principles and technical considerations; they do not determine Novi's exact legal obligations. Deployment-specific legal requirements, controller/processor roles, lawful bases, exemptions, retention periods and rights procedures require appropriate legal/privacy review.

---

## 86. Final Principle

> **Novi must treat privacy as a lifecycle and dependency problem. Information should be collected only when needed, used only for authorized purposes, retained only as long as justified, propagated only to authorized locations, and removed or transformed through a verifiable process that accounts for replicas, caches, backups, indexes, embeddings, derived memories and other material dependencies. Recovery, model evolution and distributed synchronization must never silently undo a valid privacy decision.**
