# 88 — Memory Knowledge Privacy Access Control and Data Governance

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define the privacy, ownership, authorization, access-control and governance layer for Novi's memory and knowledge systems.

This document establishes who may create, read, modify, derive, share, export, retain, suppress and erase memory, under which conditions, and with what auditability.

## Core Principle

> **Memory belongs to a governed security domain, not to the model merely because the model can technically access it.**

Technical reachability is never equivalent to authorization.

## 1. Position in Architecture

```text
MEMORY / KNOWLEDGE
        ↓
CLASSIFICATION
        ↓
OWNERSHIP + PURPOSE
        ↓
AUTHORIZATION POLICY
        ↓
ACCESS DECISION
        ↓
MINIMIZED DATA
        ↓
USE / DERIVATION / SHARING
        ↓
AUDIT + GOVERNANCE
```

## 2. Data Governance Object

Every governed memory domain should have, where applicable:

```text
OWNER
DATA SUBJECT
CLASSIFICATION
PURPOSE
RETENTION POLICY
ACCESS POLICY
CONSENT / LEGAL BASIS
PROVENANCE
SENSITIVITY
SHARING SCOPE
DELETION POLICY
AUDIT POLICY
```

## 3. Ownership

Ownership and access are distinct.

```text
OWNS MEMORY
 ≠
CAN READ MEMORY
 ≠
CAN MODIFY MEMORY
 ≠
CAN DELETE MEMORY
```

Policies determine each capability independently.

## 4. Data Subject

A memory can concern one or more people even when another party owns or controls the system.

Example:

```text
HOUSEHOLD DEVICE
 ↓
MEMORY ABOUT PERSON B
```

The device owner does not automatically gain unrestricted access to all information about Person B.

## 5. Identity

Access decisions should use authenticated identities where possible.

Identity should be distinct from:

- device presence;
- voice recognition alone;
- physical proximity;
- inferred household membership.

Weak identity signals should not unlock sensitive memories without an appropriate policy.

## 6. Roles

Possible roles include:

```text
SYSTEM OWNER
USER
HOUSEHOLD MEMBER
AUTHORIZED CAREGIVER
OPERATOR
DEVELOPER
SERVICE
OTHER AGENT
UNTRUSTED ACTOR
```

Roles are policy inputs, not universal permissions.

## 7. Least Privilege

Each component should receive only the memory access required for its task.

```text
TASK
 ↓
MINIMUM REQUIRED DATA
 ↓
ACCESS
```

Broad unrestricted memory access should be exceptional.

## 8. Purpose Limitation

Memory should be accessed for a defined purpose.

```text
stored for purpose A
        ≠
automatically usable for purpose B
```

Repurposing requires appropriate policy authorization.

## 9. Data Minimization

Novi should retrieve the smallest useful representation:

```text
FULL MEMORY
    ↓
RELEVANT FACTS / CONTEXT
    ↓
TASK
```

Sensitive information that is irrelevant to the task should remain inaccessible.

## 10. Need-to-Know Retrieval

Retrieval should evaluate:

- who is asking;
- why;
- what is requested;
- sensitivity;
- scope;
- current authorization;
- retention state.

## 11. Memory Classification

Suggested classifications:

```text
PUBLIC
GENERAL
PERSONAL
SENSITIVE
HIGHLY_SENSITIVE
SAFETY_CRITICAL
SECURITY_CRITICAL
RESTRICTED
```

Exact classifications can evolve with governance policy.

## 12. Sensitivity Is Contextual

The same fact may have different sensitivity depending on context.

For example:

```text
favorite_color → usually low sensitivity
home_location → potentially sensitive
access_code → highly sensitive
```

Classification must consider potential harm, not merely data type.

## 13. Metadata Sensitivity

Metadata can itself reveal sensitive information:

```text
memory_exists
memory_timestamp
memory_location
memory_subject
```

Therefore access controls apply to memory metadata as well as content.

## 14. Consent

Where consent is the governing basis for a memory use, Novi should track:

- who provided consent;
- scope;
- purpose;
- timestamp;
- expiry/review condition;
- withdrawal state.

Consent should not be assumed from silence where explicit consent is required.

## 15. Consent Withdrawal

When consent is withdrawn:

```text
WITHDRAWAL
 ↓
ACCESS POLICY UPDATE
 ↓
FUTURE USE BLOCKED
 ↓
RETENTION / ERASURE EVALUATED
```

Withdrawal does not automatically mean every record must be immediately destroyed if another valid retention requirement applies.

## 16. Authorization

Authorization should be evaluated at access time.

```text
AUTHORIZED YESTERDAY
        ≠
AUTHORIZED NOW
```

Revocation must take effect without relying on stale cached permissions.

## 17. Authentication vs Authorization

```text
AUTHENTICATION
"Who are you?"

AUTHORIZATION
"What may you access?"
```

Successful authentication alone does not grant memory access.

## 18. Capability-Based Access

Where useful, access can be represented as explicit capabilities:

```text
READ:HOME_AUTOMATION
READ:TRAVEL_HISTORY
EXECUTE:DEVICE_CONTROL
DELETE:OWN_MEMORIES
```

Capabilities should be scoped and revocable.

## 19. Attribute-Based Access

Policies may consider:

- identity;
- role;
- memory classification;
- purpose;
- location;
- device state;
- time;
- relationship;
- emergency state.

## 20. Emergency Access

Emergency access may require narrowly defined break-glass policies.

```text
NORMAL ACCESS
      ↓
DENIED
      ↓
VALID EMERGENCY CONDITION
      ↓
BREAK-GLASS POLICY
      ↓
MINIMUM NECESSARY ACCESS
```

Emergency access should be logged and reviewed.

## 21. Safety-Critical Information

Safety-relevant memory can have stronger availability requirements, but safety access must remain scoped to the actual safety purpose.

Safety does not justify unrestricted access to unrelated personal data.

## 22. Privacy vs Safety

When privacy and immediate physical safety conflict, policy must define the applicable emergency hierarchy.

The system should disclose only what is necessary to address the safety condition.

## 23. Shared Household Memory

Household memory should distinguish:

```text
SHARED
PERSON-SPECIFIC
PRIVATE
DEVICE-SPECIFIC
```

A shared environment does not imply shared memory access.

## 24. Private Spaces

Novi should support privacy boundaries around:

- rooms;
- devices;
- accounts;
- conversations;
- personal storage;
- private routines.

Physical presence alone should not defeat logical privacy controls.

## 25. Children and Vulnerable People

Memory policies concerning children or vulnerable people may require stronger safeguards, reduced retention and narrower sharing.

The system should not infer broad consent from household membership.

## 26. Sensitive Attributes

Sensitive personal information should receive explicit classification and restricted handling.

The architecture should avoid unnecessary collection or inference of sensitive attributes.

## 27. Inference Governance

Derived information can be more sensitive than its source.

```text
OBSERVATIONS
 ↓
INFERENCE
 ↓
SENSITIVE PROFILE
```

The derived profile inherits appropriate governance requirements.

## 28. Privacy Propagation

Privacy metadata should propagate through:

```text
SOURCE
 ↓
EPISODE
 ↓
SUMMARY
 ↓
SEMANTIC ASSERTION
 ↓
EMBEDDING / INDEX
 ↓
DERIVED KNOWLEDGE
```

A derivative must not silently become less protected than its source.

## 29. Aggregates

Aggregated statistics can still leak information about individuals.

Aggregation does not automatically remove privacy requirements.

## 30. Anonymization

Anonymization claims should be treated carefully.

If individuals can reasonably be re-identified, the data should not be treated as anonymous merely because names were removed.

## 31. Pseudonymization

Pseudonyms reduce direct identification but do not necessarily eliminate privacy sensitivity.

Access to mapping information requires separate protection.

## 32. Encryption

Memory should use appropriate encryption:

```text
AT REST
IN TRANSIT
IN BACKUPS
```

Key management must be separated from ordinary memory access.

## 33. Key Separation

Highly sensitive memory may require separate encryption domains or keys.

Compromise of one key should not expose unrelated memory classes unnecessarily.

## 34. Secure Processing

Where feasible, sensitive memory should be processed in isolated execution contexts with minimized exposure.

## 35. Access Logging

Important memory access should produce privacy-safe audit records containing, where appropriate:

- actor;
- resource class;
- purpose;
- decision;
- timestamp;
- policy version.

Logs should avoid unnecessary sensitive content.

## 36. Auditability

Novi should be able to answer, subject to privacy policy:

```text
WHO accessed this?
WHY?
WHAT class of information was accessed?
WHEN?
UNDER WHICH POLICY?
WAS ACCESS GRANTED OR DENIED?
```

## 37. Audit Log Protection

Audit logs are themselves sensitive and require:

- access control;
- retention policy;
- integrity protection;
- tamper detection;
- privacy minimization.

## 38. Modification Control

Memory modification should preserve provenance:

```text
OLD VALUE
 ↓
CHANGE
 ↓
ACTOR
 ↓
REASON / SOURCE
 ↓
NEW VALUE
```

Silent rewriting of important memory should be prohibited.

## 39. User Corrections

A user correction should not necessarily erase the original observation.

Instead, the system can represent:

```text
OBSERVATION
 ↓
CORRECTION / REVISION
 ↓
CURRENT INTERPRETATION
```

Privacy policy may still require erasure of the original record.

## 40. Deletion Governance

Deletion follows document 87.

Authorization must determine who can request it and policy must determine what can legally/technically be erased.

## 41. Export

Memory export should be:

- authenticated;
- authorized;
- scoped;
- auditable;
- privacy-aware;
- protected in transit and at rest.

Exports should not silently include unrelated people's information.

## 42. Portability

Export formats should preserve useful metadata such as:

- provenance;
- timestamps;
- classification;
- relationships;
- deletion state where appropriate.

## 43. Sharing

Sharing should define:

```text
WHAT
WHO
WHY
HOW LONG
WHICH DERIVATIVES
WHICH PERMISSIONS
```

Sharing one memory does not automatically grant access to the entire memory graph.

## 44. External Agents

Data shared with another agent or service should use explicit trust and authorization boundaries.

```text
LOCAL MEMORY
      ↓
SHARING POLICY
      ↓
MINIMIZED PAYLOAD
      ↓
EXTERNAL AGENT
```

## 45. Untrusted Input

External text, documents, calendar events or agent messages must not be treated as trusted policy instructions merely because they are stored in memory.

Memory content is data.

## 46. Prompt Injection Boundary

A memory entry can contain adversarial instructions.

Retrieval must not convert stored content into privileged system instructions.

## 47. Tool Authorization

Memory retrieval cannot grant tool permissions.

```text
MEMORY SAYS "YOU MAY"
        ≠
SYSTEM AUTHORIZATION
```

Current authorization policy remains authoritative.

## 48. Multi-Agent Access

For shared Novi instances, each agent should have explicit access scope.

Agent identity must be represented in access and provenance metadata.

## 49. Cross-Device Access

A user's authorization should not automatically imply that every device can access every memory.

Device trust and local security state may be additional policy inputs.

## 50. Offline Authorization

Offline devices may have cached authorization, but high-risk access should require current authorization when feasible.

Cached credentials must have expiry and revocation semantics.

## 51. Data Residency

Memory may be subject to geographic or organizational residency constraints.

The architecture should represent allowed storage/processing regions where applicable.

## 52. Third-Party Services

External services should receive only the data required for their specific function.

Third-party retention and deletion behavior should be part of the integration contract.

## 53. Model Providers

Sending memory to an external model provider is a data-sharing operation.

The system must evaluate:

- data classification;
- purpose;
- provider trust;
- retention;
- training/use policy;
- jurisdiction;
- user authorization.

## 54. Telemetry

Telemetry should minimize memory content and use purpose-limited identifiers.

Debugging should not become an uncontrolled secondary memory store.

## 55. Developer Access

Developers should not receive unrestricted production memory access for convenience.

Development/debugging workflows should use:

- synthetic data;
- redaction;
- scoped access;
- approval;
- time-limited credentials;
- audited break-glass access.

## 56. Testing Data

Production memories should not be copied into test environments unless explicitly authorized and appropriately protected.

Synthetic or de-identified data should be preferred.

## 57. Retention Governance

Retention policy should define:

- default retention;
- category-specific retention;
- user-pinned exceptions;
- legal/audit retention;
- safety retention;
- deletion triggers;
- review points.

## 58. Policy Versioning

Every important access decision should be attributable to the policy version that produced it.

```text
REQUEST
 ↓
POLICY vN
 ↓
DECISION
```

## 59. Policy Changes

When policy changes, existing memories should be reevaluated where required.

Policy updates must not silently broaden access to historical sensitive data without authorization.

## 60. Governance Hierarchy

A generic ordering is:

```text
HARD SAFETY / SECURITY CONTROLS
        ↓
LEGAL / GOVERNANCE REQUIREMENTS
        ↓
EXPLICIT AUTHORIZATION
        ↓
PURPOSE LIMITATION
        ↓
USER PREFERENCES
        ↓
CONVENIENCE
```

The exact hierarchy must be configurable by deployment policy.

## 61. Access Decision

A conceptual decision function:

```text
ACCESS =
  AUTHENTICATED
  ∧ AUTHORIZED
  ∧ PURPOSE_ALLOWED
  ∧ CLASSIFICATION_ALLOWED
  ∧ RETENTION_ACTIVE
  ∧ DEVICE_TRUSTED
  ∧ POLICY_CURRENT
```

Additional conditions may apply.

## 62. Deny by Default

When authorization cannot be established for sensitive memory:

```text
UNKNOWN AUTHORIZATION
        ↓
DENY / REQUEST CONFIRMATION
```

Silence or missing policy should not become permission.

## 63. Explainable Denials

User-facing denials should explain enough to be useful without revealing protected information.

Example:

```text
"I can't provide that information because it is outside your current access permissions."
```

## 64. Privacy-Preserving Responses

Even a refusal should avoid confirming sensitive facts that the requester was not authorized to know.

## 65. Consent and Memory Learning

Learning from an interaction should respect the governing privacy policy.

Not every observed interaction should automatically become durable memory.

## 66. Memory Creation Gate

Before durable storage:

```text
OBSERVATION
 ↓
NEED TO RETAIN?
 ↓
CLASSIFY
 ↓
ASSIGN PURPOSE
 ↓
APPLY RETENTION
 ↓
STORE
```

This supports data minimization at creation time rather than relying only on later deletion.

## 67. Sensitive Memory Creation

For highly sensitive information, durable storage may require stronger authorization or explicit user action.

## 68. Inference Limits

Novi should avoid creating sensitive profiles merely because a model can infer them.

Inference capability is not permission to infer or retain.

## 69. Memory Graph Governance

Governance metadata should travel with graph edges as well as nodes.

A relationship such as:

```text
PERSON → location → PLACE
```

can itself be sensitive.

## 70. Cross-Context Leakage

Novi must prevent memory from one context leaking into another unrelated context.

Examples:

```text
USER A conversation
        ≠
USER B conversation

PRIVATE ROOM
        ≠
SHARED ROOM
```

## 71. Context Isolation

Working memory should inherit access constraints from the underlying memory source.

A private fact retrieved into working memory does not become public merely because it is now in context.

## 72. Memory-to-Action Boundary

Memory access cannot itself authorize an action.

```text
MEMORY
 ↓
REASONING
 ↓
CURRENT AUTHORIZATION
 ↓
CURRENT SAFETY
 ↓
ACTION
```

## 73. High-Impact Actions

Actions involving money, access control, privacy, physical safety or irreversible state changes should use stronger authorization and confirmation policies.

## 74. Emergency and Break-Glass Audit

Every break-glass access should produce an auditable event and, where appropriate, require later review.

## 75. Security Incidents

If unauthorized memory access is detected:

```text
DETECT
 ↓
CONTAIN
 ↓
REVOKE
 ↓
ASSESS SCOPE
 ↓
PRESERVE REQUIRED AUDIT DATA
 ↓
RECOVER
```

Incident response must not expose additional memory unnecessarily.

## 76. Integrity

Important memory and governance records should support integrity verification and tamper detection.

## 77. Availability

Critical memory services should have appropriate availability goals, but availability must not override confidentiality or authorization.

## 78. Recovery

Backups and disaster recovery must preserve governance metadata and deletion state.

Restored systems should reapply current policy before serving memory.

## 79. Observability

Track privacy-safe metrics such as:

- access grants/denials;
- policy evaluation failures;
- sensitive-memory access;
- consent changes;
- deletion requests;
- export/share events;
- break-glass usage;
- cross-device access;
- third-party transfers;
- policy-version changes.

## 80. Testing

Test:

- authentication/authorization separation;
- least privilege;
- purpose limitation;
- sensitive classifications;
- household isolation;
- multi-user boundaries;
- child/vulnerable-person safeguards;
- consent withdrawal;
- cached authorization expiry;
- offline authorization;
- emergency access;
- break-glass audit;
- privacy propagation;
- derived inference governance;
- export isolation;
- third-party sharing;
- model-provider boundaries;
- developer access;
- telemetry leakage;
- prompt injection in memory;
- policy version changes;
- restored backups;
- deletion-state preservation;
- unauthorized deletion;
- cross-context leakage;
- memory-to-action authorization.

## 81. Architectural Invariants

1. Technical access is not authorization.
2. Ownership is distinct from read, write, share and delete permissions.
3. Authentication is distinct from authorization.
4. Sensitive metadata is protected as well as sensitive content.
5. Least privilege is the default.
6. Memory access is purpose-limited.
7. Durable memory creation is itself governed.
8. Derived information inherits appropriate privacy controls.
9. Aggregation does not automatically eliminate privacy risk.
10. Household membership does not imply unrestricted access.
11. Stored memory cannot grant tool or action authorization.
12. Current authorization overrides stale permissions.
13. Emergency access is narrow, auditable and purpose-limited.
14. External agents and model providers are separate trust domains.
15. Stored text is data, not privileged instruction authority.
16. Audit logs are themselves governed data.
17. Production memory should not be exposed to developers by default.
18. Policy changes are versioned and attributable.
19. Denials must not leak the protected information they are designed to protect.
20. Memory governance survives backup, synchronization and recovery.
21. Deletion and privacy policies propagate through derivatives.
22. Memory access does not authorize physical action.
23. High-impact operations require stronger controls.
24. Unknown authorization is not permission.
25. Privacy, security and governance are architectural properties, not optional application features.

## 82. Final Principle

> **Novi should remember only what it has a legitimate reason to retain, reveal only what the current requester and purpose authorize, derive only what governance permits, and erase what policy requires—while maintaining enough provenance and auditability to prove that these boundaries are actually enforced.**

This governance layer turns Novi's increasingly capable memory architecture into a controlled information system rather than an unrestricted repository of everything it encounters.