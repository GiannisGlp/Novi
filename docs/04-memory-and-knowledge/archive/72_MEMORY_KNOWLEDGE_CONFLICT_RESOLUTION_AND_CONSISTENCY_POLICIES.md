# 72 — Memory Knowledge Conflict Resolution and Consistency Policies

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi detects, classifies, resolves, preserves, escalates, and audits conflicts in distributed memory and knowledge, and how consistency requirements are selected for different resource classes.

This document operationalizes the distributed-state model in document 71.

## Core Principle

> **A distributed conflict is not merely a technical collision. It is a semantic disagreement whose correct resolution depends on the meaning, authority, time, provenance, safety impact, privacy scope, and consistency requirements of the resource.**

CRDTs can provide strong eventual convergence for suitable data structures, but convergence alone does not establish that a merged result is semantically correct. Research on CRDTs demonstrates both their usefulness for offline/peer-to-peer replication and the need for domain-specific semantics; Byzantine or malicious replicas require additional protections beyond ordinary CRDT guarantees. citeturn0search0turn0search2

---

## 1. Consistency Is a Policy Decision

Novi must not use one consistency model for every memory class.

```text
RESOURCE
   ↓
RISK / SEMANTICS
   ↓
CONSISTENCY POLICY
   ↓
CONFLICT POLICY
```

The policy should be explicit and versioned.

## 2. Consistency Classes

Initial classes:

```text
C0 — BEST EFFORT
C1 — EVENTUAL
C2 — CAUSALLY ORDERED
C3 — STRONG / COORDINATED
C4 — LOCAL SAFETY AUTHORITATIVE
```

The classes are architectural categories, not implementation promises for every deployment.

## 3. C0 — Best Effort

Appropriate for disposable or reconstructable information such as:

- temporary UI state;
- non-authoritative caches;
- low-value derived hints.

Loss or divergence is acceptable within defined limits.

## 4. C1 — Eventual Consistency

Appropriate when temporary divergence is safe and replicas can converge later.

```text
LOCAL UPDATE
   ↓
REPLICATE
   ↓
MERGE
   ↓
CONVERGE
```

This is useful for many shared knowledge and household-information workloads.

## 5. C2 — Causal Consistency

Use when the order/dependency relationship between updates matters.

Examples:

```text
create memory
   ↓
modify memory
```

The second operation must not be applied as though the first never existed.

Causal metadata may include logical clocks, vector clocks, event ancestry, or equivalent mechanisms.

## 6. C3 — Strong / Coordinated Consistency

Use only where semantic correctness requires coordination and the system can tolerate reduced availability during partitions.

Examples may include certain:

- ownership transfers;
- exclusive resource leases;
- security-policy changes;
- administrative state transitions.

Strong consistency is not synonymous with truth.

## 7. C4 — Local Safety Authority

Physical safety decisions remain governed by the local safety architecture and current validated sensor state.

```text
REMOTE STATE
    ↓
context/evidence only

LOCAL SAFETY SYSTEM
    ↓
authoritative safety decision
```

A distributed memory merge must never override emergency stop, collision avoidance, thermal protection, battery protection, or other safety mechanisms.

## 8. Conflict Definition

A conflict exists when two or more concurrent states cannot be safely combined under the resource's merge semantics.

Not every difference is a conflict.

```text
A adds X
B adds Y
→ mergeable

A says preference=X
B says preference=Y
→ semantic conflict
```

## 9. Conflict Dimensions

Every significant conflict should be evaluated across:

- identity;
- authority;
- provenance;
- causal relationship;
- event time;
- receipt time;
- validity interval;
- source reliability;
- evidence independence;
- uncertainty;
- privacy scope;
- user scope;
- physical locality;
- resource class;
- safety consequence;
- currentness;
- schema/model version.

## 10. Conflict Classes

Suggested classes:

```text
C0 — DUPLICATE
C1 — ORDERING DIFFERENCE
C2 — MERGEABLE CONCURRENT UPDATE
C3 — VALUE CONFLICT
C4 — AUTHORITY CONFLICT
C5 — TEMPORAL CONFLICT
C6 — IDENTITY CONFLICT
C7 — SAFETY-RELEVANT CONFLICT
C8 — SECURITY/POLICY CONFLICT
C9 — PRIVACY/ACCESS CONFLICT
C10 — MALICIOUS OR SUSPICIOUS CONFLICT
```

## 11. Duplicate vs Conflict

Retransmitted identical events are duplicates, not conflicts.

Deduplication must preserve genuinely distinct repeated observations.

## 12. Ordering Differences

Different arrival order does not imply different event order.

Novi should retain:

```text
event_time
receipt_time
logical/causal position
```

## 13. Mergeable Updates

If concurrent operations commute safely, they may be merged automatically.

CRDTs are appropriate where the data type's merge semantics preserve the required application invariants. Formal work on CRDTs shows how strong eventual consistency can be established for suitable data types. citeturn0search1turn0search8

## 14. Semantic Conflicts

For non-commutative values, Novi must apply a domain-specific policy rather than a generic merge.

Example:

```text
User preference
A → 21°C
B → 24°C
```

The system should identify the users, scope, time, and authority before selecting a result.

## 15. Last-Write-Wins Is Not Universal

Never use arrival order as a universal truth rule.

Even timestamp-based last-write-wins can discard valid concurrent evidence.

## 16. Local Preference Rule

Local state may take precedence when the resource is explicitly defined as locally authoritative.

This is appropriate for certain:

- current sensor readings;
- local safety state;
- device health;
- local actuator state.

It is not a universal conflict rule.

## 17. Authority Rule

If a resource has an explicitly designated authority, that authority may resolve conflicts within its scope.

Authority must be explicit, authenticated, authorized, and auditable.

## 18. User Resolution

Some conflicts should be presented to the appropriate user rather than guessed.

```text
CONFLICT
   ↓
LOW RISK + USER PREFERENCE
   ↓
ASK USER
```

The system should avoid repeatedly asking about conflicts that can be safely resolved by established policy.

## 19. Automatic Resolution Threshold

Automatic resolution should depend on:

- confidence;
- evidence quality;
- conflict class;
- consequence of error;
- reversibility;
- authority;
- policy.

High-consequence conflicts should require stronger evidence or explicit resolution.

## 20. Safety Conflicts

For conflicting physical observations:

```text
unsafe possibility
      ↓
conservative safe behavior
```

Novi should not choose the more convenient interpretation when uncertainty could create physical harm.

The precise safety response belongs to the safety architecture.

## 21. Sensor Conflict

Example:

```text
camera → no obstacle
LiDAR  → obstacle
```

Evaluate:

- timestamps;
- calibration;
- occlusion;
- sensor health;
- environmental conditions;
- uncertainty;
- sensor geometry.

Do not blindly average categorical observations.

## 22. Thermal Conflict

Environmental thermal sensing and Novi's internal thermal state are separate domains.

A remote agent saying "Novi is cool" cannot override Novi's local thermal sensors.

## 23. Spatial Conflict

Location/map conflicts must consider:

- coordinate frames;
- localization uncertainty;
- map versions;
- timestamps;
- sensor origin;
- environmental change.

## 24. Temporal Conflict

Two statements may both be correct if they describe different times.

```text
10:00 → door closed
10:05 → door open
```

This is not necessarily a contradiction.

## 25. Validity Intervals

Knowledge should support validity intervals where applicable.

```text
VALID_FROM
VALID_UNTIL
```

A later observation can supersede a current state without invalidating the historical record.

## 26. Identity Conflicts

Identity merging must be conservative.

Conflicting identity evidence should enter a contested/quarantine state rather than automatically merging records.

## 27. User Scope Conflicts

Two users may legitimately have different preferences.

The system should support:

```text
user_A/preferences
user_B/preferences
shared/household
```

rather than forcing one global value.

## 28. Privacy Conflicts

A more permissive replica must not broaden the privacy scope of a restricted resource.

```text
private
  ↓
replicated
  ↓
still private
```

## 29. Authorization Conflicts

If one replica says access is allowed and another says access is revoked, security policy must not be resolved using ordinary memory merge rules.

Security revocation should use the dedicated authorization/security architecture.

## 30. Deletion Conflicts

Deletion must be treated as a protected lifecycle transition.

A stale update must not resurrect a deleted resource.

```text
DELETE/TOMBSTONE
      >
stale ordinary update
```

Subject to explicit retention and recovery policy.

## 31. CRDT Use Policy

CRDTs may be used for:

- sets;
- counters;
- collaborative collections;
- suitable maps;
- suitable documents;
- other structures with formally appropriate merge semantics.

They should not be used as a universal solution for semantic knowledge conflicts.

## 32. Byzantine/Hostile Replicas

Ordinary CRDT convergence assumes compliant participants. Research shows that malicious or Byzantine replicas can violate ordinary CRDT assumptions and require additional mechanisms. citeturn0search2

Therefore Novi must combine replicated-data algorithms with:

- authentication;
- authorization;
- provenance;
- rate limits;
- validation;
- peer revocation;
- anomaly detection;
- quarantine.

## 33. Evidence vs Resolution

Novi must preserve the distinction:

```text
EVIDENCE
  ↓
CONFLICT
  ↓
RESOLUTION
```

A resolved projection does not erase the evidence that produced the conflict.

## 34. Contested State

When resolution is unsafe or unavailable:

```text
CONTESTED
```

is a valid durable state.

Novi may continue using a conservative operational representation while preserving the contested knowledge.

## 35. Quarantine

Use quarantine when:

- integrity is uncertain;
- peer trust is revoked;
- provenance is missing;
- evidence appears poisoned;
- authorization is ambiguous;
- the conflict is security-sensitive.

Quarantined information must not silently enter authoritative cognition.

## 36. Confidence and Conflict

Confidence should represent evidence quality, not merely agreement count.

```text
5 copies of same source
 ≠
5 independent sources
```

Correlated evidence must not create artificial confidence.

## 37. Source Reliability

Source reliability should be contextual and versioned where necessary.

A historically reliable sensor or agent can still produce bad data under changed conditions.

## 38. Consequence-Aware Resolution

The threshold for automatic resolution should increase with consequence:

```text
LOW CONSEQUENCE
 → automatic merge may be acceptable

MEDIUM
 → stronger evidence / policy

HIGH
 → corroboration or explicit resolution

SAFETY / SECURITY CRITICAL
 → authoritative local policy / safety system
```

## 39. Reversibility

Prefer reversible conflict resolution when uncertainty is material.

```text
provisional projection
      ↓
new evidence
      ↓
re-evaluate
```

Avoid irreversible destructive merges unless explicitly justified.

## 40. Explanation

For significant conflicts, Novi should be able to explain:

- what conflicted;
- which sources were involved;
- their timestamps;
- applicable policy;
- resolution method;
- confidence/uncertainty;
- unresolved alternatives.

## 41. Provenance

Conflict-resolution outputs must retain provenance. NIST defines provenance as information concerning origin, development, ownership, location, and changes to data/system components. citeturn0search7

## 42. Resolution Record

A resolution record should contain, where applicable:

```text
conflict_id
resource_id
participants
versions
causal_context
evidence_refs
policy_version
resolution_strategy
resolver
result
confidence
unresolved_alternatives
time
```

## 43. Determinism

Automatic merge functions should be deterministic for the same valid input state and policy version.

This supports reproducibility and convergence verification.

## 44. Idempotence

Applying the same synchronization or merge operation repeatedly should not produce new semantic changes after the first successful application.

## 45. Commutativity

Where a data type claims conflict-free merge semantics, concurrent operations should satisfy the required commutativity/associativity/idempotence properties for the chosen design.

The formal guarantees must be tested rather than assumed.

## 46. Convergence

For data types designed for strong eventual consistency:

```text
same valid event set
      ↓
same merge semantics
      ↓
semantically equivalent state
```

Research on verified CRDTs demonstrates the value of formal verification for convergence properties. citeturn0search1turn0search8

## 47. Non-Convergent Semantic Knowledge

Some knowledge cannot safely be forced into a single convergent scalar.

Examples:

```text
"Alice prefers X"
"Bob prefers Y"
```

or:

```text
Agent A observed X
Agent B observed not-X
```

The correct state may remain multi-valued or contested.

## 48. Multi-Value Registers

For certain conflicting values, a multi-value representation may be preferable to silently selecting one.

```text
value_A
value_B
```

with provenance and validity context.

## 49. Conflict Escalation

```text
AUTO-MERGE
   ↓ if unsafe
RULE-BASED RESOLUTION
   ↓ if unresolved
USER / AUTHORITY REVIEW
   ↓ if unavailable
CONTESTED / QUARANTINED
```

## 50. Policy Versioning

Conflict decisions must identify the policy version that produced them.

Changing policy must not make historical decisions uninterpretable.

## 51. Policy Changes

When a conflict policy changes:

```text
existing state
 ↓
policy migration/evaluation
 ↓
new projection
```

Do not silently reinterpret historical evidence without preserving the prior result where required.

## 52. Offline Conflict Queue

During offline operation, unresolved conflicts can be queued:

```text
LOCAL CONFLICT
 ↓
PERSIST
 ↓
CONTINUE SAFE OPERATION
 ↓
RECONNECT
 ↓
RESOLVE
```

Core safety must not depend on resolving a non-safety memory conflict.

## 53. Conflict Storm Protection

Large synchronization events may create many conflicts.

Novi must enforce:

- queue limits;
- prioritization;
- batching;
- backpressure;
- CPU/GPU budgets;
- thermal/battery budgets.

Synchronization must not starve perception, safety, or core cognition.

## 54. Observability

Track:

- conflict counts;
- conflict classes;
- auto-resolution rate;
- escalation rate;
- contested duration;
- resolution latency;
- source/peer distribution;
- failed merges;
- policy versions;
- convergence failures.

## 55. Testing

Test:

- concurrent writes;
- offline divergence;
- clock skew;
- duplicate events;
- out-of-order events;
- stale replicas;
- deletion races;
- privacy conflicts;
- authorization revocation races;
- sensor disagreement;
- map disagreement;
- user preference conflicts;
- identity collisions;
- malicious peers;
- Byzantine updates;
- malformed data;
- CRDT invariant violations;
- deterministic replay;
- idempotent retries;
- convergence;
- policy-version migration;
- conflict storms;
- recovery after crash.

## 56. Architectural Invariants

1. Consistency is resource-specific.
2. Safety state is locally authoritative.
3. Authentication is not authorization.
4. Arrival order is not truth.
5. Last-write-wins is not universal.
6. CRDTs are selected only where their semantics fit the data.
7. Convergence does not imply factual correctness.
8. Conflicting evidence is preserved.
9. High-consequence conflicts require stronger resolution.
10. Security and deletion conflicts use specialized policy.
11. Privacy restrictions never broaden through conflict resolution.
12. Identity conflicts are conservative.
13. Contested is a valid final state.
14. Quarantine prevents untrusted conflict inputs from becoming authoritative knowledge.
15. Resolution retains provenance.
16. Automatic merge functions are deterministic and idempotent where required.
17. Offline operation can queue non-safety conflicts without disabling Novi.
18. Conflict processing cannot starve local safety or core cognition.
19. Malicious peers require controls beyond ordinary CRDT convergence.
20. Policy versions are explicit and auditable.

## 57. Final Principle

> **Novi must prefer an explicit uncertainty over a confidently wrong merge.**

A distributed memory system is successful not when it eliminates every conflict, but when it knows which differences can be merged safely, which require stronger evidence, which require human or authoritative resolution, and which must remain contested until uncertainty is reduced.