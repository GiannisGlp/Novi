# 71 — Memory Knowledge Shared Memory and Distributed Knowledge State

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define the distributed state model for shared memory and knowledge across Novi instances and authorized agents, including ownership, replicas, consistency, causality, partitions, conflicts, convergence, deletion, and offline operation.

## Core Principle

> **Shared state must converge without sacrificing provenance, authorization, privacy, local safety, or the distinction between conflicting evidence.**

Distributed memory is not one magical global database. It is a set of local authoritative state, replicas, events, derived projections, and explicitly governed shared knowledge.

---

## 1. Distributed State Model

Conceptually:

```text
LOCAL AUTHORITATIVE STATE
        ↓
EVENT / CHANGE LOG
        ↓
AUTHORIZED REPLICATION
        ↓
REMOTE REPLICA
        ↓
LOCAL VALIDATION
        ↓
LOCAL PROJECTION
```

A replica is not automatically authoritative.

## 2. State Ownership

Every shared resource should have an explicit ownership/authority model.

Possible models:

```text
SINGLE OWNER
CO-OWNED
GROUP SHARED
DERIVED REPLICA
TEMPORARY LEASE
```

The model must be defined per resource class rather than assumed globally.

## 3. Local Authority

Novi remains authoritative for its local:

- safety state;
- local sensor state;
- private memories;
- security policy;
- deletion decisions;
- authorization decisions;
- physical-world observations.

Remote replicas cannot silently override these.

## 4. Shared Knowledge Authority

Some explicitly shared knowledge can have a shared authority domain.

Example:

```text
household/shared
```

All participants may contribute according to policy, but contributions retain individual provenance.

## 5. State vs Events

The architecture should distinguish:

```text
STATE
current representation

EVENT
immutable description of a change/observation
```

Events provide useful provenance and synchronization history; state is a projection that can be rebuilt where practical.

## 6. Event Identity

Changes should have globally or scope-unique identifiers sufficient for deduplication and replay protection.

An event ID must not depend solely on arrival order.

## 7. Causality

Distributed updates need causal information where conflict semantics require it.

Possible mechanisms include:

- logical clocks;
- vector clocks;
- Lamport-style ordering;
- explicit parent/event references.

The chosen mechanism should match system scale and consistency requirements.

## 8. Physical Time vs Logical Order

```text
event time
receipt time
logical order
```

are separate concepts.

Clock disagreement must not automatically create false chronology.

## 9. Versioning

Mutable resources require explicit versions or equivalent causal state.

```text
memory_v7
memory_v8
```

Version numbers alone are not sufficient to determine which branch is semantically correct when concurrent updates occur.

## 10. Replica State

A replica should be able to express states such as:

```text
CURRENT
STALE
SYNCING
DIVERGED
CONFLICTED
QUARANTINED
REVOKED
```

## 11. Consistency Is Resource-Specific

Not every memory requires the same consistency model.

Suggested categories:

```text
SAFETY / CONTROL
strong local consistency

PRIVATE MEMORY
local authority + eventual replication where authorized

SHARED KNOWLEDGE
eventual convergence with conflict semantics

CACHES
best effort
```

## 12. Strong Consistency

Strong consistency may be appropriate when multiple writers cannot safely diverge and a coordination mechanism is available.

It should not be assumed to be available during network partitions.

## 13. Eventual Consistency

For many shared knowledge workloads:

```text
local update
 ↓
replicate later
 ↓
merge
 ↓
converge
```

Eventual consistency is acceptable only when temporary divergence is semantically safe.

## 14. Offline-First Operation

Novi must remain operational without Wi-Fi, Bluetooth, or cloud connectivity.

```text
DISCONNECTED
 ↓
LOCAL WORK
 ↓
LOCAL EVENTS
 ↓
QUEUE CHANGES
 ↓
RECONNECT
 ↓
SYNC
 ↓
CONFLICT RESOLUTION
 ↓
CONVERGENCE
```

## 15. Network Partitions

A partition must not force Novi to stop core local cognition or safety functions.

During a partition:

- local authoritative state continues;
- permitted local memories continue;
- nonessential synchronization waits;
- shared state may diverge;
- conflict information is retained.

## 16. Partition Semantics

Different resource classes require different partition policies.

For example:

```text
local obstacle detection
 → continue locally

shared household note
 → accept local update and sync later

exclusive ownership transfer
 → may require coordination before completion
```

## 17. Conflict Definition

A conflict exists when concurrent state cannot be safely merged under the resource's defined semantics.

Not every difference is a conflict.

Example:

```text
A adds memory X
B adds memory Y
```

may be naturally mergeable.

But:

```text
A: user preference = X
B: user preference = Y
```

may require explicit resolution.

## 18. Last-Write-Wins

Last-write-wins should **not** be a universal strategy.

It can destroy meaningful concurrent information and is especially dangerous for:

- provenance;
- safety observations;
- user preferences;
- deletion state;
- conflicting knowledge.

## 19. CRDT-Style Structures

Conflict-free replicated data types may be appropriate for selected data structures where their merge semantics match the domain.

They should not be adopted merely because they provide automatic convergence.

The semantic meaning of merge must remain correct.

## 20. Event-Sourced Structures

Event logs can provide:

- replay;
- provenance;
- auditing;
- recovery;
- deterministic projection rebuilding.

Retention and privacy policy still apply to event history.

## 21. Immutable Evidence

Important observations should preserve their original evidence rather than being destructively merged into a single value.

```text
Agent A observed X
Agent B observed Y
```

Both may remain historical evidence even if a current projection chooses one interpretation.

## 22. Knowledge Projection

A current knowledge state may be derived from evidence:

```text
EVENTS / EVIDENCE
      ↓
VALIDATION
      ↓
CONFLICT EVALUATION
      ↓
KNOWLEDGE PROJECTION
```

The projection should remain traceable to its supporting evidence.

## 23. Provenance Preservation

Merging must never erase:

- source agent;
- original event;
- time;
- context;
- transformation history;
- validation history.

## 24. Confidence Merging

Confidence should not be averaged blindly.

The merge process should consider:

- evidence independence;
- source reliability;
- measurement uncertainty;
- recency;
- context;
- model differences.

## 25. Contradiction Preservation

If evidence conflicts:

```text
CLAIM A
CLAIM B
      ↓
CONTESTED STATE
```

Novi may continue operating with a conservative decision while preserving the disagreement for later resolution.

## 26. Resolution Strategies

Depending on resource type, resolution may use:

- authoritative source;
- explicit user choice;
- newer validated observation;
- causal precedence;
- domain rules;
- corroboration;
- majority agreement where appropriate;
- manual review;
- temporary contested state.

No single algorithm should resolve every knowledge class.

## 27. User Preference Conflicts

If two authorized users have different preferences, they should not automatically overwrite one another.

Preferences should support scoped ownership or identity where applicable.

## 28. Identity Conflicts

Identity records require particularly conservative merging.

Similar names, voices, faces or attributes do not justify merging identities without sufficient evidence and authorization.

## 29. Spatial State Conflicts

Maps and locations can conflict because of:

- coordinate frames;
- stale data;
- sensor uncertainty;
- environmental change;
- localization error.

Map merging must validate spatial reference and timestamp context.

## 30. Temporal State

A later received event may describe an earlier physical event.

Therefore:

```text
received later
 ≠
happened later
```

## 31. Deletion as Distributed State

Deletion must be replicated as an explicit state transition where necessary.

```text
ACTIVE
 ↓
DELETE_REQUESTED
 ↓
DELETED / RESTRICTED
 ↓
TOMBSTONE
```

## 32. Tombstones

Tombstones prevent stale replicas from resurrecting deleted records.

They require retention long enough to protect against relevant stale replicas, subject to privacy and storage policy.

## 33. Secure Deletion

Distributed deletion follows document 63.

A successful local deletion does not necessarily mean every remote replica has been sanitized.

The system must represent deletion status accurately.

## 34. Revoked Replicas

A replica may lose authorization to hold a resource.

It should transition to a restricted/revoked state and follow the applicable deletion or sanitization policy.

## 35. Synchronization Protocol

A conceptual sync sequence:

```text
IDENTIFY PEER
 ↓
AUTHENTICATE
 ↓
AUTHORIZE SCOPE
 ↓
NEGOTIATE VERSION
 ↓
EXCHANGE CHANGE SUMMARY
 ↓
EXCHANGE MISSING EVENTS
 ↓
VALIDATE
 ↓
DEDUPE
 ↓
ORDER / CAUSAL ANALYSIS
 ↓
CONFLICT DETECTION
 ↓
MERGE / QUARANTINE
 ↓
REBUILD PROJECTIONS
 ↓
VERIFY CONVERGENCE
```

## 36. Sync Scope

Synchronization should be scoped.

Do not synchronize the entire memory store merely because two Novi devices are paired.

Scope can depend on:

- owner;
- namespace;
- resource class;
- purpose;
- current authorization;
- storage budget.

## 37. Delta Synchronization

Prefer transmitting changes rather than complete databases where practical.

Benefits include:

- reduced bandwidth;
- reduced exposure;
- faster reconnection;
- better auditability.

## 38. Bandwidth Constraints

Synchronization must respect available bandwidth and battery/thermal budgets.

Critical synchronization can be prioritized over background indexing.

## 39. Backpressure

If remote changes arrive faster than they can be validated:

```text
incoming rate > processing rate
 ↓
queue
 ↓
prioritize
 ↓
backpressure / rate limit
```

Do not allow synchronization to exhaust resources required for local cognition or safety.

## 40. Resource Exhaustion

Distributed state must be protected against:

- event floods;
- enormous objects;
- pathological histories;
- duplicate events;
- malicious peers;
- unbounded queues.

## 41. Security Boundary

A distributed state mechanism must inherit the controls from documents 60 and 62.

Transport authentication does not establish authorization for memory access.

## 42. Privacy Boundary

Shared state must preserve privacy classifications.

A local private record must not become shared merely because it entered a synchronization queue.

## 43. Learning Boundary

Distributed learning artifacts require their own governance.

```text
remote experience
 ↓
local evaluation
 ↓
learning candidate
 ↓
local promotion
```

Remote learning cannot directly modify local behavior without policy and validation.

## 44. Model Version Compatibility

Distributed knowledge derived by different model versions should retain model metadata.

Changes in model behavior may explain apparent disagreement.

## 45. Schema Migration

When schema versions diverge:

```text
peer A: schema v3
peer B: schema v4
```

Use explicit migration/compatibility rules.

Do not silently reinterpret fields whose semantics changed.

## 46. Recovery

After corruption or partial synchronization:

```text
validate local state
 ↓
validate event history
 ↓
identify missing changes
 ↓
replay / rebuild
 ↓
revalidate projections
```

Derived projections should be rebuildable where practical.

## 47. Crash Safety

Synchronization must use atomic or transactional state transitions appropriate to the storage layer.

A crash must not create a state that falsely appears synchronized.

## 48. Acknowledgements

An acknowledgement should distinguish:

```text
RECEIVED
VALIDATED
APPLIED
COMMITTED
PROJECTION_UPDATED
```

Receiving a message does not mean it has become authoritative local state.

## 49. Convergence

Convergence should mean more than identical bytes.

It should mean that authorized replicas reach semantically equivalent state under the defined consistency model while retaining required provenance and history.

## 50. Convergence Verification

After synchronization, verify:

- event completeness;
- integrity;
- authorization scope;
- deletion state;
- projection consistency;
- conflict state;
- provenance links;
- schema compatibility.

## 51. No Silent Data Loss

If a merge discards information, the system should know why and record the policy/result where appropriate.

Silent destructive merges are prohibited for protected memory.

## 52. Conflict Audit

Record significant conflicts and their resolution:

```text
conflict ID
resources
participants
versions
resolution strategy
result
review status
```

## 53. Shared Memory Health

Monitor:

- replica lag;
- queue depth;
- conflict rate;
- failed validation;
- rejected updates;
- stale replicas;
- tombstone lag;
- synchronization failures;
- storage growth.

## 54. Testing

Test:

- simultaneous writes;
- offline divergence;
- network partitions;
- reconnection;
- duplicate events;
- reordered events;
- clock skew;
- stale replicas;
- deletion during partition;
- revoked peer;
- schema mismatch;
- model mismatch;
- malformed events;
- event floods;
- corrupted logs;
- crash during synchronization;
- interrupted commit;
- conflicting user preferences;
- identity conflicts;
- spatial map conflicts;
- malicious peer;
- convergence verification.

## 55. Architectural Invariants

1. Distributed replicas are not automatically authoritative.
2. Local safety and security state remain locally governed.
3. State and events are distinct representations.
4. Important distributed changes retain causal/provenance context.
5. Physical time and logical order are distinct.
6. Consistency requirements are resource-specific.
7. Offline operation is mandatory for core Novi functionality.
8. Network partitions must not compromise local safety.
9. Last-write-wins is not universal.
10. Conflicting evidence is preserved rather than silently destroyed.
11. Knowledge projections remain traceable to evidence.
12. Privacy restrictions survive replication.
13. Deletion propagates as governed distributed state.
14. Tombstones prevent stale resurrection where required.
15. Synchronization is scoped and authorized.
16. Synchronization cannot exhaust resources needed for local operation.
17. Remote learning cannot directly override local behavior.
18. Schema and model versions remain explicit.
19. Acknowledgement does not equal commitment.
20. Convergence must be verified semantically, not assumed.
21. Destructive merges require explicit policy.
22. Compromised or revoked replicas can be isolated.
23. Distributed state failures cannot disable core safety controls.

## 56. Final Principle

> **Novi can share memory without surrendering ownership, can diverge without becoming inconsistent forever, and can converge without erasing the evidence that explains how its knowledge was formed.**

Distributed memory is therefore treated as governed replicated state—not as an unrestricted shared database. Every replica, event, merge, conflict, deletion, and synchronization action remains subject to provenance, authorization, privacy, integrity, resource limits, and local safety.