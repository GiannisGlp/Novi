# 11 — Memory Privacy, Retention and Deletion

## Status

**DESIGN — V1**

## Purpose

Define how Novi minimizes, classifies, protects, retains, restricts, forgets, deletes, anonymizes, and audits information held by the memory and knowledge subsystem.

This document is a technical architecture specification, not legal advice. Where Novi is deployed in a jurisdiction with applicable privacy/data-protection requirements, the implementation and operating policies must be reviewed against those requirements before production use.

## 1. Core Principles

Novi follows these principles:

1. **Local-first:** personal memory remains on the local device by default.
2. **Data minimization:** collect and retain only information needed for a defined capability or user-approved purpose.
3. **Purpose limitation:** information collected for one purpose must not silently acquire unrelated uses.
4. **Storage limitation:** personal information is not retained indefinitely merely because it might become useful.
5. **Accuracy:** incorrect or stale personal information must be correctable and must not silently remain authoritative.
6. **Privacy by architecture:** privacy controls exist below the LLM and cannot depend on the model voluntarily following instructions.
7. **User control:** authorized users can inspect, correct, restrict, export where supported, and delete memory within the applicable policy boundary.
8. **Protected core:** privacy controls, safety rules, authorization boundaries, and immutable system configuration cannot be deleted or weakened by ordinary learning.
9. **Deletion propagation:** deleting a memory means addressing its derivatives and indexes, not merely hiding the primary row.
10. **Audit without unnecessary content:** auditability should rely on metadata and references rather than retaining raw private content indefinitely.

These principles align with the UK ICO's current guidance on data minimisation, accuracy, storage limitation, integrity/confidentiality and erasure. The ICO states that personal data should be adequate, relevant and limited to what is necessary, and should be erased or anonymised when no longer needed. citeturn0search4turn0search0

## 2. Privacy Is a System Boundary

Privacy is not a prompt instruction such as:

> "Do not reveal private memories."

The actual architecture is:

```text
sensor / user / external source
            ↓
       data classifier
            ↓
      privacy metadata
            ↓
       admission policy
            ↓
      memory subsystem
            ↓
  retrieval authorization/filter
            ↓
        context package
            ↓
          model
```

The model receives only information that has already passed the relevant access and privacy controls.

## 3. Data Classification

Every persistent memory or artifact should carry a privacy classification.

Suggested classes:

- `PUBLIC`
- `HOUSEHOLD`
- `PERSONAL`
- `SENSITIVE_PERSONAL`
- `BIOMETRIC`
- `SECURITY_SENSITIVE`
- `SYSTEM_CONFIDENTIAL`
- `PROTECTED_CORE`

Classification is independent from epistemic confidence.

For example:

```text
confidence = 0.97
privacy = SENSITIVE_PERSONAL
```

means highly trusted information that is still highly restricted.

## 4. Purpose Binding

Each retained memory should have a purpose or capability scope.

Examples:

```text
purpose = conversational_personalization
purpose = household_routine
purpose = navigation
purpose = device_control
purpose = safety
purpose = diagnostics
purpose = user_requested_learning
```

A memory should not automatically become available to every subsystem merely because it exists.

## 5. Data Minimization

Novi should prefer the least identifying representation that satisfies the task.

Examples:

- Store `known household member` instead of raw face imagery when identity is already resolved and the image is no longer required.
- Store an event summary rather than unlimited raw audio.
- Store a derived feature/reference rather than repeatedly duplicating large media.
- Store a coarse location when exact coordinates are unnecessary.

Raw media retention must have an explicit reason, retention policy, and storage owner.

## 6. Memory-Type Retention

Retention is defined by memory type and purpose rather than one global timer.

| Memory | Default strategy |
|---|---|
| Working context | short-lived |
| Session state | session/short horizon |
| Raw sensor observations | aggressively bounded |
| Episodic events | importance + policy based |
| Semantic knowledge | durable while useful/valid |
| Relationships | durable but correctable |
| Preferences | durable while relevant |
| Routines | confidence/recency based |
| Embeddings | lifecycle tied to source memory |
| Derived indexes | rebuildable; delete with source |
| Temporary artifacts | short-lived |
| Audit metadata | policy-defined |
| Protected core | never removed by memory lifecycle |

These are architecture defaults, not universal legal retention periods.

## 7. Retention Policy Object

Every durable memory should resolve to a retention policy containing at least:

```text
policy_id
purpose
privacy_class
retention_mode
retention_period / review_period
last_reviewed_at
expiry_at (if applicable)
legal_or_policy_basis (if applicable)
user_override
protected_status
cascade_policy
```

Possible retention modes:

- `EPHEMERAL`
- `UNTIL_SESSION_END`
- `TIME_LIMITED`
- `REVIEW_REQUIRED`
- `UNTIL_CORRECTED_OR_SUPERSEDED`
- `DURABLE_WHILE_PURPOSE_EXISTS`
- `USER_CONTROLLED`
- `PROTECTED`

## 8. Review and Expiry

A memory can become stale without becoming immediately useless.

Therefore:

```text
ACTIVE
  ↓
REVIEW_DUE
  ↓
 ┌──────────────┐
 │              │
valid          stale
 │              │
ACTIVE       EXPIRED
                ↓
             ARCHIVED
                ↓
              PURGED
```

Review should consider current use, accuracy, purpose, sensitivity and downstream dependencies.

The ICO recommends documented retention periods where possible, periodic review, and deletion or anonymisation when information is no longer needed. citeturn0search0

## 9. Deletion Semantics

Novi must distinguish:

### Logical deletion

The item is immediately excluded from ordinary retrieval.

### Physical deletion

The primary data is removed from live storage where technically and operationally appropriate.

### Cryptographic destruction

Where encryption/key architecture supports it, destruction of a dedicated key can make retained ciphertext inaccessible. This is a complementary technique, not a substitute for a complete deletion policy.

### Anonymization

Information is transformed so that the person is no longer identifiable using means reasonably available to the system/controller.

Pseudonymization is not automatically anonymization.

The ICO explicitly notes that taking data offline is not the same as deletion and that pseudonymised information may still permit identification. citeturn0search0

## 10. Deletion Propagation

Deleting a memory must trigger a dependency-aware cascade:

```text
canonical memory
      ↓
claims / relationships
      ↓
embeddings
      ↓
FTS entries
      ↓
graph indexes
      ↓
caches
      ↓
retrieval summaries
      ↓
derived artifacts
      ↓
backup lifecycle
```

The system must know which derived records are dependent on the deleted source.

A derived record that cannot be safely separated from deleted personal data must be deleted, regenerated without that data, or otherwise rendered non-identifying according to policy.

## 11. Backup Deletion

Deletion must account for backups.

For local backups, Novi should use one of:

- backup generation expiry;
- encrypted backup key destruction where appropriate;
- deletion/rewrite of affected backup data where feasible;
- documented delayed purge windows when immediate physical modification is impractical.

During a backup purge window, deleted data must be inaccessible to normal Novi operation.

The ICO notes that if personal data is deleted from a live system, appropriate deletion from backups should also be considered. citeturn0search0

## 12. Vector and Embedding Deletion

Embeddings are derived personal data when they remain linkable to a person or source.

Therefore deleting source memory must invalidate its embedding records.

```text
source_id
  ↓
embedding records
  ↓
vector index
```

The index must support tombstoning or rebuilding so deleted vectors cannot continue influencing retrieval.

## 13. Graph Deletion

Relationships derived from deleted personal information must be reviewed.

Example:

```text
Vano ← lives_with → Person A
```

If the underlying Person A record is deleted, the relationship cannot remain as an orphaned retrievable fact.

Graph edges must therefore retain source/dependency references.

## 14. Files and Media

Managed files must have:

- artifact ID
- owner/purpose
- privacy classification
- source memory references
- retention policy
- checksum
- creation time
- deletion status

Deletion of a memory must identify whether associated images, audio, video, documents or generated artifacts also contain the deleted information.

Novi must not assume that deleting a database row deletes information embedded in an external file.

## 15. Caches

Caches are privacy-sensitive copies.

A deletion event must invalidate relevant:

- application caches
- retrieval caches
- prompt/context caches
- model-result caches
- materialized summaries

NVIDIA NeMo Guardrails documents that model caches can retain prompts and responses, demonstrating why caching must be included in the privacy inventory rather than treated as harmless implementation detail. citeturn0search5

## 16. Telemetry and Audit

Novi should avoid placing raw private memory content into logs by default.

Audit records should prefer:

```text
memory_id
request_id
actor
operation
policy decision
timestamp
result
source references
```

rather than duplicating full content.

NVIDIA's current documentation similarly warns that captured prompts/responses can contain PII and sensitive information and that content capture should only be enabled when needed with an appropriate retention policy. citeturn0search10

## 17. User Deletion Request

A user-authorized deletion request should create a deletion job rather than allowing a model to execute arbitrary destructive commands.

```text
user request
    ↓
authorization
    ↓
resolve target
    ↓
impact/dependency analysis
    ↓
policy validation
    ↓
delete/restrict/anonymize
    ↓
invalidate indexes/caches
    ↓
backup handling
    ↓
integrity verification
    ↓
audit completion
```

For high-impact deletion, Novi may show the scope before execution.

## 18. Restriction of Processing

Some workflows may require restricting processing rather than immediately deleting data.

A restricted item should be retained only as necessary to enforce the restriction and should be excluded from ordinary cognition/retrieval.

The ICO describes restriction as limiting future processing while allowing the data to remain stored under controlled access. citeturn0search13

## 19. Correction

Correction is not the same as deletion.

When a user says:

> “That information is wrong.”

Novi should preserve the relevant provenance and create a correction/supersession record rather than silently rewriting history.

```text
old claim
   ↓
CORRECTED / SUPERSEDED
   ↓
new claim
   ↓
correction provenance
```

Current retrieval should prefer the corrected claim while historical audit can preserve that an earlier claim existed.

## 20. Household Privacy

Novi is expected to operate in a shared physical environment. It must therefore distinguish:

- information about the household as a whole;
- information about an individual;
- information learned in a private interaction;
- information that a person is not authorized to access.

A person being physically present does not automatically authorize access to another person's memories.

Identity, relationship and authorization remain separate concepts.

## 21. Biometric Data

Face embeddings, speaker embeddings and other biometric representations require elevated protection.

Novi should prefer storing derived representations only when necessary and should retain raw biometric media for the shortest practical period.

Biometric deletion must include both raw source media and derived representations where they are linkable.

## 22. Learning and Privacy

Continuous learning must not mean indefinite accumulation.

Before a memory becomes a learning candidate, Novi should evaluate:

- purpose
- sensitivity
- necessity
- provenance
- confidence
- retention
- whether the information is about the user or another person
- whether it should influence future model behavior

Sensitive information must not silently become generalized model-training data.

## 23. Model Training Boundary

Ordinary memory is not automatically training data.

```text
memory
  ↓
learning candidate
  ↓
privacy review
  ↓
consent/policy
  ↓
curation
  ↓
dataset
  ↓
training/evaluation pipeline
```

This protects against accidental personalization data becoming permanent model weights.

## 24. Protected Core

The following are outside ordinary memory deletion:

- safety policies
- authorization rules
- protected system configuration
- cryptographic trust anchors
- immutable audit requirements
- core recovery mechanisms
- protected software/runtime components

However, this does **not** mean personal data should be placed in the protected core.

Protected core means protection of system integrity, not exemption from privacy obligations.

## 25. NVIDIA Integration

NVIDIA NeMo Agent Toolkit provides pluggable memory providers and memory operations, including add/get/delete memory APIs. This makes it a candidate implementation behind Novi's memory interfaces, but not the owner of Novi's privacy policy. citeturn0search3turn0search6

NVIDIA NeMo Guardrails is also relevant because its architecture provides input, retrieval, execution and output rails, including PII detection/masking and validation of retrieved content. citeturn0search7turn0search14

These capabilities should be evaluated locally and benchmarked against other open-source solutions. Novi must retain a vendor-neutral privacy contract.

NVIDIA's own security guidance recommends parameterizing and validating inputs/outputs, using allow-lists and fail-closed behavior, isolating authentication information from the LLM, and avoiding persistent changes where possible. citeturn0search15

## 26. Local-First Requirement

The default architecture is:

```text
camera/microphone/sensors
        ↓
local processing
        ↓
local memory
        ↓
local retrieval
        ↓
local reasoning
```

Cloud transfer of personal memory requires an explicit capability-level policy and should be exceptional.

If cloud is ever used, Novi must know:

- what data leaves the device;
- why it is needed;
- which provider receives it;
- whether it is retained;
- whether it is used for provider training;
- how deletion is handled;
- what happens when the service is unavailable.

NVIDIA's privacy documentation similarly notes that third-party inference endpoints have their own privacy terms and that local telemetry opt-outs do not automatically control third-party data collection. citeturn0search1

## 27. Access Control

Memory access must be capability-based.

```text
requester
   ↓
identity
   ↓
authorization
   ↓
purpose
   ↓
privacy scope
   ↓
memory query
```

The model must not receive unrestricted database credentials.

## 28. Deletion Safety

Deletion operations must be:

- authenticated;
- authorized;
- scoped;
- idempotent;
- auditable;
- transactionally safe where possible;
- recoverable from failure without leaving inconsistent indexes.

A partial failure must result in a visible `DELETION_INCOMPLETE` state rather than falsely reporting success.

## 29. Privacy State Machine

```text
COLLECTED
    ↓
CLASSIFIED
    ↓
ADMITTED
    ↓
RETAINED
    ↓
 ┌───────────────┐
 │               │
REVIEW_DUE     RESTRICTED
 │               │
 ├─ VALID        │
 │               │
 ├─ EXTEND       │
 │               │
 └─ EXPIRE       │
       ↓
    DELETION_PENDING
       ↓
    DEPENDENCIES
       ↓
    DELETED / ANONYMIZED
       ↓
    VERIFIED
```

## 30. Metrics

Privacy operations should be observable without exposing private content.

Track:

- memories by privacy class
- memories approaching expiry
- expired-memory backlog
- deletion requests
- deletion completion time
- deletion failures
- orphaned derived records
- cache invalidation failures
- embedding invalidation failures
- backup purge status
- restricted records
- unauthorized access attempts
- cloud-transfer events
- raw-media retention volume

## 31. Testing

Tests must include:

- deletion of simple memory;
- deletion with embeddings;
- deletion with FTS;
- deletion with graph edges;
- deletion with files;
- deletion with cached context;
- deletion during active retrieval;
- deletion during consolidation;
- deletion during backup;
- concurrent deletion/update;
- failed deletion recovery;
- unauthorized deletion;
- cross-person access attempt;
- biometric deletion;
- stale-memory expiry;
- correction/supersession;
- restricted processing;
- cloud-disabled mode;
- offline deletion;
- protected-core tampering attempts.

## 32. Design Invariants

The implementation must preserve these invariants:

1. A deleted memory cannot remain normally retrievable.
2. Derived indexes cannot silently resurrect deleted information.
3. A model cannot bypass deletion policy.
4. A model cannot change retention policy through ordinary tool calls.
5. Personal data is not retained solely because it might be useful someday.
6. Protected core cannot be modified by memory operations.
7. Privacy classification survives consolidation and transformation.
8. Provenance survives correction where retention is permitted.
9. Cloud is never required for local deletion.
10. Failure of one deletion component cannot be represented as successful completion.

## 33. Implementation Principle

The final architecture is:

```text
                 PRIVACY POLICY
                       │
          ┌────────────┴────────────┐
          │                         │
       RETENTION                 ACCESS
          │                         │
          └────────────┬────────────┘
                       ▼
                 MEMORY MANAGER
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
    SQLite          Files           Indexes
       │               │                │
       └───────────────┼────────────────┘
                       ▼
               deletion coordinator
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     vectors          FTS          caches
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                 audit/verification
```

The memory subsystem therefore remains capable of continuous learning while retaining explicit boundaries around privacy, retention, deletion, authorization and system integrity.

## 34. References

Primary references used for this design include:

- NVIDIA NeMo Agent Toolkit memory architecture and memory operations. citeturn0search3turn0search6
- NVIDIA NeMo Guardrails rail types and privacy/security guidance. citeturn0search7turn0search14turn0search15
- NVIDIA NeMo privacy/telemetry documentation. citeturn0search1turn0search10
- UK Information Commissioner's Office guidance on data minimisation, storage limitation, accuracy, security and erasure. citeturn0search0turn0search4turn0search11turn0search13

## Conclusion

Novi is intended to continuously learn, but **continuous learning is not continuous retention**.

The memory system must be capable of remembering useful experiences for years while also being capable of forgetting an irrelevant observation minutes later, correcting a false belief, restricting sensitive information, and completely removing personal information when required.

Privacy, retention and deletion are therefore core memory capabilities—not administrative features added after implementation.
