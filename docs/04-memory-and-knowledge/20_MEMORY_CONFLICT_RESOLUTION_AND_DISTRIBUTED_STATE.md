# 20 — Memory Conflict Resolution and Distributed State

## Status

**DESIGN — V1**

## Purpose

Define how Novi handles disagreement between observations, memories, knowledge claims, processes, local replicas, devices, backups, and future synchronized peers.

The central principle is:

> **Novi must resolve semantic conflicts using evidence, provenance, authority, time, uncertainty and policy—not simply by choosing the latest write.**

Distributed state exists to support resilience and synchronization. It must never create multiple uncontrolled versions of Novi's cognitive truth.

---

## 1. Canonical State

Novi maintains one authoritative local semantic state through the Memory Manager.

Replicas may contain:

- synchronized memories;
- events;
- knowledge claims;
- derived indexes;
- cached state;
- pending commands.

A replica is not automatically authoritative merely because its timestamp is newer.

```text
                 CANONICAL NOVI STATE
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
        Robot          Phone         Desktop
        replica        replica        replica
```

The canonical state remains subject to Novi's memory, privacy, authorization and safety policies.

---

## 2. Conflict Is Not Always Error

Two observations can disagree while both are valid.

Example:

```text
18:00 → Vano in kitchen
18:05 → Vano in bedroom
```

This is normally temporal evolution, not a conflict.

By contrast:

```text
18:05:01 Camera → kitchen
18:05:02 Phone → bedroom
```

may represent genuine uncertainty, stale data, identity confusion or two different people.

The resolver must classify the disagreement before resolving it.

---

## 3. Conflict Classes

### 3.1 Temporal conflict

Different values are valid at different times.

Resolution:

- preserve history;
- update current state when justified;
- do not delete previous observations.

### 3.2 Concurrent observational conflict

Multiple sources describe the same approximate time differently.

Resolution requires evidence evaluation.

### 3.3 Semantic conflict

Two measurements or interpretations cannot both describe the same state under the same assumptions.

### 3.4 Authority conflict

Two actors attempt to modify a state but have different permissions.

Authorization rules take precedence over recency.

### 3.5 Version conflict

A stale process attempts to update an entity that has changed since it was read.

Resolution:

- reject stale write;
- reload;
- reevaluate;
- retry if still valid.

### 3.6 Schema conflict

Replicas or processes understand an entity using incompatible schema versions.

Resolution requires migration/compatibility rules before semantic merge.

### 3.7 Deletion conflict

A replica attempts to reintroduce data that was deleted elsewhere.

Deletion policy wins unless an explicitly authorized restoration operation exists.

---

## 4. Evidence Hierarchy

Conflict resolution should evaluate evidence in approximately this order:

```text
Safety / policy constraints
        ↓
Authorization
        ↓
Provenance integrity
        ↓
Measurement quality
        ↓
Sensor health
        ↓
Temporal relevance
        ↓
Spatial relevance
        ↓
Independent corroboration
        ↓
Source reliability
        ↓
Model confidence
        ↓
Historical patterns
        ↓
Recency
```

This is a conceptual precedence order, not a universal numerical scoring formula. Different state types may define different policies.

Recency is intentionally not first.

---

## 5. Provenance Is Mandatory

A conflict resolver must know where competing claims came from.

Example:

```text
Claim A
  source = camera_03
  acquired = T1
  health = healthy
  confidence = 0.94

Claim B
  source = user statement
  acquired = T2
  authority = user-confirmed
```

The resolver cannot safely compare these claims without their provenance and authority metadata.

---

## 6. Authority Model

Different memory classes have different authoritative sources.

Examples:

| State | Potential authority |
|---|---|
| Current sensor measurement | calibrated sensor pipeline |
| User preference | explicit user confirmation |
| Robot safety state | safety subsystem |
| Battery state | BMS/power subsystem |
| Current robot pose | state-estimation system |
| Historical event | original event source |
| Knowledge hypothesis | knowledge subsystem |
| Schema | protected engineering authority |

The LLM is not automatically authoritative for any of these classes.

---

## 7. Current State vs Historical Truth

Novi must maintain separate representations for:

```text
HISTORICAL EVENTS
what happened and when

CURRENT STATE
best current projection of reality
```

Example:

```text
18:01 kitchen
18:05 hallway
18:07 bedroom
```

can produce:

```text
current_location = bedroom
```

without rewriting the historical events.

---

## 8. Resolution Outcomes

Every conflict should resolve to an explicit outcome where practical:

```text
ACCEPT_A
ACCEPT_B
MERGE
SUPERSEDE
PRESERVE_BOTH
LOWER_CONFIDENCE
REQUEST_VERIFICATION
REQUEST_USER
REJECT
DEFER
```

`DEFER` is a legitimate result when evidence is insufficient.

Novi must not manufacture certainty merely to produce a single value.

---

## 9. Last-Write-Wins Is Not a General Policy

Last-write-wins may be appropriate for explicitly defined ephemeral state.

It is not acceptable as the universal memory conflict strategy.

For example:

```text
user_preference = X
```

must not be replaced merely because a stale synchronized replica reports:

```text
user_preference = Y
```

The system must evaluate authority, version, provenance and policy.

---

## 10. Versioning

Mutable semantic entities should use monotonically increasing versions or equivalent causal metadata.

Example:

```text
entity V
version 17
```

A write based on version 17 must fail if the current version is already 18.

The stale writer must re-read and reevaluate.

---

## 11. Causal Ordering

Where useful, Novi should preserve causal relationships between changes.

Example:

```text
event A
  ↓
user confirmation
  ↓
memory B
  ↓
knowledge C
```

C should not be interpreted independently of the evidence that caused it.

For distributed synchronization, causal metadata such as vector clocks or another compact causal mechanism may be introduced where required by measured complexity.

V1 should not introduce distributed-clock machinery unless the actual synchronization topology requires it.

---

## 12. Physical Observation Conflict

Example:

```text
Camera → object present
LiDAR → object absent
```

The resolver should consider:

- timestamp alignment;
- sensor health;
- calibration;
- field of view;
- occlusion;
- detection confidence;
- spatial overlap;
- sensor modality;
- historical reliability.

It may request active perception rather than immediately choosing one.

---

## 13. Active Verification

Conflict resolution can trigger a new observation.

```text
conflict
   ↓
insufficient evidence
   ↓
request additional observation
   ↓
move camera / change viewpoint / rescan
   ↓
new evidence
   ↓
resolve
```

This creates a direct bridge between memory and autonomy.

The request itself must respect safety and action authorization.

---

## 14. User Verification

Some conflicts are best resolved by asking the user.

Example:

```text
Memory:
Vano prefers coffee type A.

New evidence:
Vano prefers coffee type B.

confidence insufficient
        ↓
ask user
```

A direct user-confirmed answer can receive stronger authority than an inferred preference, subject to privacy and identity verification.

---

## 15. Confidence Reduction

Contradictory evidence may reduce confidence rather than produce a winner.

```text
belief = 0.94
     ↓
credible contradiction
     ↓
belief = 0.61
```

Confidence must be recalculated according to the state-specific policy.

The system must avoid repeatedly reducing confidence without bound merely because multiple correlated observations repeat the same information.

---

## 16. Correlated Evidence

Repeated observations from the same sensor are not automatically independent evidence.

Example:

```text
Camera A reports object 100 times
```

does not necessarily equal:

```text
100 independent confirmations
```

The resolver should account for source correlation when calculating confidence or evidence strength.

---

## 17. Merge Rules

A merge is allowed only when the values are semantically compatible.

Example:

```text
Claim A:
Vano was in kitchen at 10:00.

Claim B:
Vano was cooking at 10:00.
```

These may be merged into a richer episode.

But:

```text
Vano in kitchen at 10:00
Vano in bedroom at 10:00
```

should not be merged into an impossible single location without additional evidence.

---

## 18. Supersession

A claim may supersede another when the domain policy defines the state as temporally replaceable.

Example:

```text
current_location:
kitchen
      ↓
new verified observation
      ↓
current_location:
bedroom
```

The old value remains available as historical evidence.

---

## 19. Preserve Both

Sometimes two claims should coexist.

Example:

```text
Person A believes event happened at 10:00.
Person B reports event happened at 10:05.
```

Novi may preserve both reports with their sources rather than falsely resolving the discrepancy.

This is particularly important for subjective or disputed information.

---

## 20. Distributed Replica Reconciliation

Synchronization operates on changes, not database files.

```text
Replica A
  ↓
changes
  ↓
Replica B
  ↓
conflict detection
  ↓
semantic resolver
  ↓
canonical commit
```

A replica must never overwrite the canonical database wholesale.

---

## 21. Replica Identity

Every synchronization participant needs a stable identity.

Examples:

```text
robot-main
phone-user
laptop-user
backup-node
```

The identity must not be confused with the human user identity.

A device can act on behalf of a user without becoming the authority for every user-owned memory.

---

## 22. Change Identity

Every synchronized mutation should contain enough information to identify:

- source replica;
- command/event ID;
- entity ID;
- entity version;
- operation type;
- causal parent where available;
- creation time;
- authorization context;
- provenance.

This supports duplicate detection and conflict analysis.

---

## 23. Concurrent Replica Updates

Example:

```text
Robot:
preference = A, version 12

Phone:
preference = B, version 12
```

Both changed the same prior state.

The system must identify this as a concurrent conflict rather than choosing the higher device timestamp.

Possible resolution:

```text
REQUEST_USER
```

or a domain-specific merge if supported.

---

## 24. Deleted Data and Tombstones

Deletion requires durable knowledge that deletion occurred long enough to prevent stale replicas from resurrecting the data.

```text
Robot:
DELETE memory X

Phone:
old copy of X

Phone reconnects
      ↓
sees deletion marker
      ↓
does not re-create X
```

Tombstone retention must be governed by synchronization and privacy requirements.

---

## 25. Offline Divergence

Novi may continue operating offline.

During offline operation:

```text
local state evolves
       ↓
changes queued
       ↓
network returns
       ↓
reconciliation
```

Offline state must never be considered invalid merely because it was created without network access.

---

## 26. Conflict Resolution After Offline Operation

When reconnecting:

1. authenticate peer;
2. exchange supported protocol/schema versions;
3. exchange change summaries;
4. detect missing changes;
5. identify concurrent changes;
6. resolve deletions;
7. evaluate conflicts;
8. apply accepted canonical changes;
9. regenerate derived state;
10. acknowledge synchronization.

The order is important because derived indexes must not be reconciled before canonical semantic state.

---

## 27. Backup State

Backups are not peers.

A backup is normally a recovery artifact, not an equal-authority source of current truth.

Restoring from backup must be an explicit recovery operation with a defined cutoff/version policy.

A stale backup must not silently overwrite newer memories.

---

## 28. Cloud State

Cloud synchronization, if ever used, is an optional external replica.

Cloud data must not become the default authority for local cognition.

Sensitive memory should remain local unless explicitly permitted by policy.

Cloud synchronization must support:

- encryption;
- authentication;
- authorization;
- deletion propagation;
- provenance;
- schema compatibility;
- conflict resolution.

---

## 29. Embeddings and Derived State

Embeddings, FTS indexes and graph projections should generally not participate as independent semantic authorities.

If two replicas have different embeddings for the same canonical memory:

```text
canonical memory wins
       ↓
correct embedding model/version
       ↓
regenerate
```

This prevents derived-state divergence from becoming cognitive truth divergence.

---

## 30. Model Version Conflicts

Two replicas may use different perception or reasoning model versions.

A claim should retain the model provenance that generated it.

When reconciling:

```text
model v1 claim
vs
model v2 claim
```

Novi should not assume v2 is automatically correct.

The evidence chain, validation policy and model evaluation status determine how the claims are treated.

---

## 31. Schema Version Conflicts

Before synchronization:

```text
peer schema version
        ↓
compatibility check
        ↓
compatible → synchronize
incompatible → migrate/translate/defer
```

Unknown fields must not be silently discarded.

A peer running an older schema should not be allowed to downgrade canonical state without an explicit compatibility policy.

---

## 32. Security and Authorization

Synchronization is an untrusted boundary.

Every incoming mutation must be checked for:

- peer identity;
- authentication;
- authorization;
- capability;
- provenance validity;
- schema validity;
- replay protection;
- privacy policy;
- deletion policy.

A valid cryptographic signature does not automatically make the content semantically authoritative.

---

## 33. Replay Protection

A previously accepted synchronization command must not be executable again as a new mutation.

Use:

- change IDs;
- sequence/cursor tracking;
- idempotency records;
- authenticated transport;
- bounded replay windows where appropriate.

---

## 34. Malicious or Corrupted Replica Data

Incoming data may be:

- malformed;
- stale;
- duplicated;
- corrupted;
- malicious;
- generated by compromised software.

The Memory Manager treats synchronized data as input to validation, not as trusted truth.

Malformed or unauthorized data must be rejected without modifying canonical state.

---

## 35. LLM Role in Conflict Resolution

The LLM may assist with interpretation but does not own final conflict authority.

Acceptable:

```text
conflict
 ↓
LLM proposes explanation
 ↓
deterministic evidence/policy evaluation
 ↓
resolution
```

Not acceptable:

```text
conflict
 ↓
LLM chooses whichever feels most likely
 ↓
canonical state changed
```

The final decision must be constrained by the memory and authorization architecture.

---

## 36. Conflict Resolution Algorithm — High Level

```text
incoming claim/change
        ↓
validate identity + integrity
        ↓
validate schema
        ↓
validate authorization
        ↓
check deletion state
        ↓
check entity/version
        ↓
load competing evidence
        ↓
classify conflict
        ↓
evaluate provenance + authority
        ↓
evaluate time + uncertainty
        ↓
evaluate independent corroboration
        ↓
apply domain-specific policy
        ↓
┌──────────────┬───────────────┬──────────────┐
│              │               │
resolve       verify          defer
│              │               │
commit       new evidence    preserve state
```

---

## 37. Domain-Specific Policies

There must not be one universal conflict algorithm.

Examples:

### Location

Favor fresh, spatially reliable, well-calibrated observations.

### User preference

Favor explicit authenticated user confirmation.

### Battery state

Favor the authoritative BMS/power subsystem.

### Safety state

Favor the independent safety subsystem and fail safe when uncertainty matters.

### Historical event

Preserve the original event rather than superseding it.

### Knowledge claim

Require evidence and verification according to claim risk.

---

## 38. Safety-Critical Conflict

If two sensors disagree on a safety-relevant condition and the system cannot establish which is correct, Novi should choose the safer permitted state.

Examples may include:

- obstacle detection;
- motor stall;
- excessive temperature;
- battery fault;
- emergency-stop state.

Safety resolution belongs to the hardware/safety architecture, not ordinary semantic memory.

---

## 39. Conflict Audit Trail

Every significant conflict should be auditable.

Record:

- conflict ID;
- competing claims;
- sources;
- versions;
- timestamps;
- classification;
- policy used;
- resolution;
- confidence impact;
- verification requested;
- final authority;
- resolver/software version.

Sensitive audit information remains subject to privacy policy.

---

## 40. Observability

Monitor:

- conflict frequency;
- conflict type;
- resolution outcome;
- unresolved conflict count;
- user-verification requests;
- active-verification requests;
- stale replica rate;
- rejected synchronization changes;
- deletion conflicts;
- schema conflicts;
- repeated source disagreements;
- sensor disagreement patterns.

A high conflict rate from one sensor may indicate hardware failure rather than a memory problem.

---

## 41. Testing

Required tests include:

- concurrent updates;
- offline divergence;
- duplicate synchronization;
- stale replicas;
- deletion races;
- backup restore against newer state;
- schema mismatch;
- model-version mismatch;
- conflicting sensor measurements;
- conflicting user statements;
- malicious peer data;
- replay attacks;
- clock skew;
- out-of-order changes;
- correlated observations;
- active-verification loops;
- unresolved conflicts;
- safety-critical disagreement.

Tests must verify that conflicts cannot silently produce unsupported certainty.

---

## 42. Architectural Invariants

1. Canonical local semantic state has one authoritative owner.
2. Replicas are not automatically authoritative.
3. Last-write-wins is not the general memory conflict policy.
4. Historical evidence is not silently destroyed by current-state changes.
5. Provenance is required for conflict evaluation.
6. Authorization outranks recency.
7. Deletion cannot be undone by stale replicas.
8. Derived indexes cannot become independent semantic authorities.
9. The LLM cannot unilaterally resolve authoritative conflicts.
10. Uncertainty may remain unresolved.
11. Active verification may be requested when physical evidence is insufficient.
12. User confirmation may be required for user-owned semantic conflicts.
13. Safety-critical conflicts follow the safety architecture.
14. Offline operation can create legitimate state that must later be reconciled.
15. Backup data is recovery material, not automatically current truth.
16. Schema and model versions remain part of provenance.
17. Every significant resolution must be auditable.

---

## 43. Final Principle

> **When Novi does not know which claim is true, the correct behavior is to preserve the evidence, represent uncertainty, seek better evidence when possible, and ask when necessary—not invent certainty.**

This is essential for a robot that continuously learns from sensors, people, local experiences and synchronized devices. Conflict is an expected property of an evolving physical world, not an exceptional database error.
