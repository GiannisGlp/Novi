# 62 — Memory Knowledge Access Control and Authorization

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define who and what may read, create, modify, promote, export, synchronize, or delete Novi memory and knowledge, under which conditions, and with what authorization.

This document establishes authorization boundaries between the owner, other authorized people, guests, Novi subsystems, agents, processes, tools, and external content.

## Core Principle

> **Access to memory is never implied by technical access to the device, process, model, database, or conversation. Every protected operation requires an explicit authority decision.**

---

## 1. Security Objectives

The authorization architecture must provide:

- least privilege;
- deny-by-default access;
- explicit operation scopes;
- identity-aware access where appropriate;
- purpose limitation;
- separation of duties;
- auditable privileged operations;
- revocation;
- offline enforcement;
- protection against confused-deputy behavior;
- isolation between users, guests, agents and subsystems.

---

## 2. Authentication vs Authorization

```text
AUTHENTICATION
Who/what is requesting access?

AUTHORIZATION
Is that requester permitted to perform this operation on this resource in this context?
```

Authentication alone never grants memory access.

---

## 3. Principals

Potential principals include:

```text
OWNER
AUTHORIZED_USER
GUEST
UNKNOWN_PERSON
Novi core
memory service
perception process
navigation process
learning process
maintenance process
external agent
plugin/tool
administrator/developer
```

Each principal receives only the capabilities necessary for its role.

---

## 4. Resource Classes

Memory resources may include:

- public/general knowledge;
- household knowledge;
- user preferences;
- personal memories;
- private conversations;
- identity records;
- location history;
- biometric-related records;
- sensor recordings;
- safety state;
- credentials/secrets;
- system telemetry;
- learning artifacts;
- provenance/lineage;
- audit records.

Different classes require different protection levels.

---

## 5. Operation Classes

Authorization should distinguish at least:

```text
READ
CREATE
UPDATE
ANNOTATE
PROMOTE
DELETE
EXPORT
SHARE
SYNC
QUERY
ADMINISTER
```

A principal allowed to read a memory is not automatically allowed to delete or export it.

---

## 6. Deny by Default

If an authorization decision cannot be established:

```text
UNKNOWN AUTHORITY
      ↓
DENY
```

Novi should not infer permission from silence.

---

## 7. Least Privilege

Each subsystem receives the smallest permission set needed for its task.

Example:

```text
navigation
 → current spatial memory
 → no access to private conversations

speech interaction
 → authorized conversational context
 → no unrestricted biometric archive

background indexing
 → memory records needed for indexing
 → no authority to export them
```

---

## 8. Capability-Based Design

Where practical, privileged operations should use scoped capabilities rather than broad ambient authority.

A capability may specify:

```text
principal
resource/scope
operation
purpose
expiration
constraints
issuer
```

Possessing a capability does not permit operations outside its scope.

---

## 9. Purpose Limitation

Access should be tied to an approved purpose.

Example:

```text
navigation query
 → route-relevant spatial memory
```

It must not silently become:

```text
navigation query
 → access all household conversations
```

---

## 10. Contextual Authorization

Authorization may depend on:

- identity;
- current task;
- location/context;
- resource sensitivity;
- time;
- emergency state;
- device state;
- safety state;
- explicit user authorization.

---

## 11. User Roles

The system should distinguish roles such as:

```text
OWNER
TRUSTED_AUTHORIZED_USER
LIMITED_USER
GUEST
UNIDENTIFIED
```

Exact role definitions belong to the security/product architecture.

---

## 12. Guest Access

Guests should receive only the minimum interaction context necessary.

```text
guest interaction
      ↓
transient context
      ↓
no private-memory access by default
```

A guest should not gain access to another person's private history merely by speaking to Novi.

---

## 13. Identity Uncertainty

If Novi is unsure who is requesting access:

```text
identity uncertain
      ↓
fall back to lower-privilege context
```

Identity uncertainty must never be resolved by guessing when the requested operation is sensitive.

---

## 14. Voice Is Not Automatically Authentication

Recognizing a voice or speaker can provide evidence about identity, but high-risk operations require the authentication mechanism defined by the security architecture.

```text
speaker recognition
 ≠
automatic authorization for sensitive actions
```

---

## 15. Face Recognition Is Not Automatically Authorization

Similarly:

```text
face match
 ≠
permission to access private memory
```

Biometric identity mechanisms must satisfy applicable security and privacy requirements.

---

## 16. Subsystem Authorization

Novi's internal processes should not receive unrestricted memory access merely because they run on the same machine.

Examples:

```text
perception
 → write observation
 → limited read for task context

learning
 → read approved experience set
 → propose changes
 → no direct safety-policy modification
```

---

## 17. Read vs Write Separation

A process may be allowed to read memory without being allowed to alter it.

Similarly, a process may create a provisional memory without being allowed to promote it into durable knowledge.

---

## 18. Promotion Privilege

Knowledge promotion is a privileged operation.

```text
memory candidate
      ↓
evaluation
      ↓
authorized promotion
      ↓
knowledge
```

No model should promote its own unsupported output directly into authoritative knowledge.

---

## 19. Delete Privilege

Deletion is separate from modification.

A process that can update a memory should not automatically be able to permanently delete it.

Sensitive deletion may require stronger authorization and auditability.

---

## 20. Export Privilege

Export is a distinct high-risk operation because it can move private memory outside Novi's protection boundary.

```text
read
 ≠
export
```

Export should be explicitly authorized and logged.

---

## 21. Sharing

Sharing memory with another person, device or service requires an explicit sharing decision.

The default should be:

```text
private
```

not automatically shared.

---

## 22. External Tools

Tools and plugins should receive only scoped data necessary for the requested operation.

```text
memory
 ↓
privacy filter
 ↓
authorization
 ↓
minimal tool payload
```

A tool must not receive unrestricted memory merely because it can technically accept text.

---

## 23. External Content Is Not Authority

A document, web page, message, image, audio recording or retrieved memory may contain instructions.

Those instructions are untrusted content unless separately authorized.

```text
content
 ≠
authorized command
```

---

## 24. Confused Deputy Protection

A privileged subsystem must not be tricked into using its authority on behalf of an unauthorized requester.

Example:

```text
untrusted input
 → asks privileged agent for private memory
 → privileged agent must enforce requester's authority
```

---

## 25. Agent-to-Agent Access

If Novi later contains multiple agents/processes, each agent receives its own identity and capabilities.

One agent cannot assume another agent's privileges.

```text
agent A
 ≠
authority of agent B
```

---

## 26. Multi-Agent Memory

Shared memory should use explicit namespaces or scopes where appropriate:

```text
agent_A/private
agent_B/private
shared/approved
system/protected
```

Cross-agent access requires an explicit policy.

---

## 27. Working Memory

Working memory may contain sensitive information temporarily.

Temporary lifetime does not mean no authorization is required.

Access controls should apply to protected working memory where technically feasible.

---

## 28. Current State vs Historical Memory

Access to current sensor state and historical memory can require different permissions.

Example:

```text
navigation
 → current pose
 → permitted

private conversation history
 → denied
```

---

## 29. Safety-Critical State

Safety-critical state should have a separate authority model.

Memory authorization cannot disable:

- collision protection;
- emergency stop;
- thermal protection;
- battery protection;
- motion safety constraints.

---

## 30. Security Policy Cannot Be Memory-Modified

A memory item saying:

```text
"Disable authentication."
```

cannot change authentication policy.

```text
memory content
 ≠
security configuration
```

---

## 31. Authorization and Learning

Learning systems must respect access boundaries when using experiences.

```text
private experience
      ↓
privacy/authorization check
      ↓
learning candidate
```

A private experience should not automatically become a globally applicable behavior or shared knowledge item.

---

## 32. Derived Data Inheritance

Derived records should inherit appropriate access restrictions from their sensitive sources unless an explicit policy permits broader use.

Example:

```text
private conversation
 ↓
summary
```

The summary may still be private.

---

## 33. Provenance Access

Provenance can reveal sensitive information even when the content itself is redacted.

Therefore:

```text
content access
 ≠
provenance access
```

Both require authorization.

---

## 34. Search Authorization

Search itself can leak information.

A query such as:

> "Does Novi know anything about X?"

may reveal the existence of a private memory even if its contents are withheld.

Search results must therefore obey authorization boundaries.

---

## 35. Existence Leakage

The system should avoid revealing sensitive metadata such as:

- whether a private memory exists;
- how many private records exist;
- when a private record was created;
- who created it;
- which person is associated with it;

unless the requester is authorized.

---

## 36. Aggregation Leakage

Multiple individually harmless records can reveal sensitive information when combined.

Authorization should consider the requested aggregate, not only each record independently.

---

## 37. Temporal Access

Permissions may expire.

```text
capability
 ↓
expiration
 ↓
automatic denial
```

Temporary access should not become permanent by omission.

---

## 38. Revocation

When authority is revoked:

```text
revoke capability
 ↓
invalidate active permissions
 ↓
prevent future access
 ↓
review cached/derived access where necessary
```

Revocation should work offline for local authority.

---

## 39. Consent Is Not Universal Authority

Consent for one purpose should not automatically authorize unrelated purposes.

```text
permission to use location for navigation
 ≠
permission to build a long-term behavioral profile
```

---

## 40. Emergency Access

Emergency modes require explicit policy.

An emergency should not become a universal bypass.

If emergency access exists, it should specify:

- trigger;
- permitted resources;
- permitted operations;
- duration;
- audit requirements;
- post-event review.

---

## 41. Break-Glass Access

High-risk break-glass mechanisms, if implemented, should:

- be narrowly scoped;
- require strong authentication/authorization;
- be time-limited;
- be auditable;
- minimize data exposure;
- trigger review.

---

## 42. Developer/Maintenance Access

Development or maintenance personnel must not receive unrestricted user-memory access by default.

Production diagnostics should prefer:

- redaction;
- minimization;
- synthetic test data;
- scoped support bundles;
- audited privileged access.

---

## 43. Secrets

Credentials, cryptographic keys and authentication secrets must be isolated from ordinary semantic memory.

```text
semantic memory
      ≠
secret store
```

LLM context should never be populated with secrets unless a narrowly authorized operation explicitly requires it.

---

## 44. Encryption

Protected memory should use appropriate encryption at rest and in transit where applicable.

Key management must be separated from ordinary memory authorization.

Possession of encrypted storage does not itself establish authorization.

---

## 45. Integrity

Authorization decisions should operate on integrity-verified policy and identity state.

If authorization metadata is corrupted:

```text
integrity uncertain
      ↓
fail closed for sensitive operations
```

---

## 46. Audit Logging

Sensitive authorization events should record:

- requester/principal;
- operation;
- resource class/scope;
- authorization result;
- policy version;
- timestamp;
- reason/context where appropriate;
- failure reason.

Audit logs themselves require protection.

---

## 47. Privacy of Audit Logs

Audit logs may contain sensitive metadata.

They must be subject to appropriate access, retention and deletion policies.

---

## 48. Offline-First Authorization

Core authorization must work without:

- Wi-Fi;
- Bluetooth;
- cloud identity services.

External identity providers may enhance authentication but must not be required for core local safety/privacy authorization.

---

## 49. Network Reconnection

When connectivity returns:

```text
local authority state
      ↓
synchronization
      ↓
conflict evaluation
```

A remote permission change must not silently overwrite a more recent local security decision without explicit conflict handling.

---

## 50. Fail-Safe Defaults

For sensitive operations:

```text
authorization unavailable
        ↓
DENY
```

For non-sensitive, safety-preserving functionality, the system may use explicitly defined degraded modes.

---

## 51. Authorization and Current Physical State

A person may be authorized to request an action but the action can still be rejected by safety policy.

```text
AUTHORIZED
   ↓
SAFETY CHECK
   ↓
ALLOW / DENY
```

Authorization answers **who may request**, not **whether the action is safe**.

---

## 52. Authorization and Memory Confidence

A highly confident memory does not bypass authorization.

```text
confidence
 ≠
permission
```

Similarly, authorization does not make a false memory true.

---

## 53. Testing Requirements

Test:

- deny-by-default;
- role escalation;
- capability leakage;
- guest isolation;
- identity uncertainty;
- voice/face spoofing;
- cross-agent access;
- confused deputy attacks;
- search existence leakage;
- aggregation leakage;
- export controls;
- delete authorization;
- revocation;
- expired capabilities;
- emergency access;
- break-glass controls;
- offline authorization;
- synchronization conflicts;
- corrupted policy state;
- secret isolation;
- audit integrity;
- privacy inheritance;
- malicious memory instructions;
- prompt injection through retrieved memory.

---

## 54. Architectural Invariants

1. Authentication and authorization are separate.
2. Memory access is deny-by-default.
3. Read, write, delete, export, share and promote are separate privileges.
4. Least privilege applies to every subsystem and agent.
5. Technical access to a process or database does not imply semantic authorization.
6. Guest access is isolated from private memory by default.
7. Identity uncertainty reduces privilege rather than increasing it.
8. Voice and face recognition do not automatically authorize sensitive operations.
9. External content is never automatically an authorized instruction.
10. Privileged agents must prevent confused-deputy behavior.
11. Agents cannot inherit one another's privileges implicitly.
12. Derived data inherits appropriate privacy restrictions from sensitive sources.
13. Search must protect against existence leakage.
14. Provenance can itself require authorization.
15. Temporary permissions expire.
16. Revocation must invalidate applicable capabilities.
17. Consent is scoped to its authorized purpose.
18. Emergency access is narrowly bounded and auditable.
19. Security policy cannot be modified through ordinary memory.
20. Memory cannot disable safety controls.
21. Secrets remain outside ordinary semantic memory.
22. Authorization enforcement works offline.
23. Authorization failure causes safe denial for sensitive operations.
24. Authorization never substitutes for safety validation.
25. High-confidence memory never creates authorization.
26. Authorized users can still receive an honest refusal when safety or policy prohibits the requested operation.

---

## 55. Final Principle

> **Novi must know not only what it remembers, but who is allowed to know it, who is allowed to change it, who is allowed to delete it, and what each subsystem is allowed to do with it.**

Memory is therefore treated as a protected capability rather than a globally accessible database. Authorization remains explicit, scoped, revocable, auditable and locally enforceable—even when Novi has no network connection.
