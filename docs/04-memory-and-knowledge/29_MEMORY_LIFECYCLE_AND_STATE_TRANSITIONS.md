# 29 — Memory Lifecycle and State Transitions

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define the complete lifecycle of information that enters Novi's memory system, from initial observation through validation, admission, enrichment, consolidation, retrieval, promotion, supersession, archival and deletion.

The lifecycle is intentionally explicit. A piece of information must not silently become trusted long-term knowledge merely because a model generated it or because it was observed repeatedly.

## Core Principle

> **Memory is a governed lifecycle, not a storage operation.**

Every significant state transition must have a reason, provenance, policy decision and auditable outcome.

---

## 1. Lifecycle Overview

```text
RAW INPUT
   ↓
INGESTED
   ↓
NORMALIZED
   ↓
GROUNDED OBSERVATION
   ↓
CANDIDATE
   ↓
ADMITTED
   ↓
ENRICHED
   ↓
CONSOLIDATED
   ├──────────────→ RETRIEVED
   ↓                     ↓
PROMOTED ←──────────────┘
   ↓
ACTIVE KNOWLEDGE / MEMORY
   ↓
UPDATED / SUPERSEDED
   ↓
ARCHIVED
   ↓
DELETED / PURGED
```

Not every record must traverse every state. Different memory classes have different legal transitions.

---

## 2. State Categories

V1 distinguishes at least:

| State | Meaning |
|---|---|
| INGESTED | Received by Novi but not yet normalized/validated |
| NORMALIZED | Converted into canonical internal representation |
| GROUNDED | Associated with physical or trusted source provenance |
| CANDIDATE | Proposed for memory admission |
| ADMITTED | Accepted into governed memory |
| ENRICHED | Associated with additional context/relations |
| CONSOLIDATED | Integrated with existing memories |
| ACTIVE | Available for ordinary retrieval |
| PROMOTED | Elevated to a stronger knowledge representation |
| SUPERSEDED | No longer current but historically retained |
| ARCHIVED | Retained but removed from normal hot retrieval |
| DELETED | Logically removed according to policy |
| PURGED | Required data physically removed where applicable |
| QUARANTINED | Isolated because integrity/security/evidence is uncertain |
| REJECTED | Not admitted as memory |
```

A record may carry multiple orthogonal attributes, so these states should not be implemented as one giant enum if that would prevent legitimate combinations.

---

## 3. Orthogonal Dimensions

Lifecycle state should be separated from properties such as:

- confidence;
- provenance quality;
- verification status;
- privacy class;
- retention class;
- sensitivity;
- source trust;
- synchronization state;
- deletion state;
- model version;
- schema version;
- spatial grounding;
- temporal validity.

For example:

```text
ACTIVE
confidence = 0.72
provenance = sensor-grounded
verification = unverified
privacy = private
```

This is preferable to encoding all combinations as separate states.

---

## 4. Ingestion

Ingestion is the boundary where external information enters the memory subsystem.

Sources include:

- cameras;
- LiDAR;
- microphones;
- thermal sensors;
- IMU;
- GNSS;
- robot state;
- user interaction;
- system events;
- other local processes;
- authorized synchronization peers.

Ingestion must preserve source identity and acquisition/receipt timing.

No ingestion event is automatically trusted semantic memory.

---

## 5. Normalization

Normalization converts raw input into canonical structures.

Examples:

```text
sensor packet
    ↓
measurement

speech/audio
    ↓
transcript candidate

camera frame
    ↓
perception observation

GNSS packet
    ↓
position observation
```

Normalization must preserve the relationship to the original source.

---

## 6. Grounding

Grounding connects information to evidence.

A grounded observation may contain:

- source sensor/device;
- sensor health;
- calibration;
- timestamp;
- coordinate frame;
- uncertainty;
- model version;
- processing pipeline;
- source media reference;
- spatial position;
- temporal interval.

Grounding is required before high-trust memory promotion.

---

## 7. Candidate Creation

A candidate is a proposed memory, not yet an accepted memory.

Candidates may be created by:

- perception;
- language understanding;
- user interaction;
- reasoning;
- experience extraction;
- synchronization;
- knowledge inference.

The candidate must identify:

```text
what
where
when
source
why it matters
confidence
uncertainty
provenance
```

---

## 8. Admission Policy

Admission determines whether a candidate becomes governed memory.

Admission should consider:

- reliability;
- novelty;
- relevance;
- user value;
- future retrieval value;
- safety impact;
- privacy impact;
- provenance;
- duplication;
- confidence;
- expected retention cost.

A low-value transient observation may remain only in short-lived working context rather than become long-term memory.

---

## 9. Rejection

A candidate may be rejected because it is:

- unsupported;
- duplicate;
- malformed;
- unauthorized;
- too uncertain;
- privacy-prohibited;
- outside retention policy;
- unsafe to store;
- irrelevant;
- corrupted.

Rejection does not necessarily mean the input never existed. The ingestion/audit layer may retain minimal evidence according to security and privacy policy.

---

## 10. Quarantine

Information requiring investigation should enter quarantine rather than ordinary memory.

Examples:

- suspicious synchronization claim;
- corrupted provenance;
- possible memory poisoning;
- conflicting high-impact evidence;
- untrusted model output;
- suspected sensor compromise.

Quarantine prevents uncertain data from silently influencing normal cognition.

---

## 11. Admission Does Not Mean Permanent Truth

Admission means:

> "This information is sufficiently useful and acceptable to retain under current policy."

It does not mean:

> "This information is permanently true."

Memory remains revisable through governed evidence and lifecycle transitions.

---

## 12. Enrichment

After admission, memory can be enriched with:

- entities;
- relationships;
- spatial information;
- temporal relationships;
- related memories;
- people;
- objects;
- places;
- semantic labels;
- embeddings;
- knowledge links.

Enrichment must not silently alter the original evidence.

Derived information must retain its own provenance.

---

## 13. Consolidation

Consolidation integrates related memories.

Example:

```text
observation A
observation B
observation C
        ↓
experience episode
        ↓
consolidated memory
```

Consolidation may reduce redundancy while preserving important source evidence.

A consolidation process must not destroy provenance needed to reconstruct why the consolidated memory exists.

---

## 14. Episodic Formation

Multiple events may form an episode.

Example:

```text
entered kitchen
→ saw cup
→ picked up cup
→ filled cup
→ returned to desk
```

The episode can become a reusable experience while retaining links to constituent events.

This supports explanation and replay.

---

## 15. Semantic Promotion

Repeated or sufficiently verified experience can produce a semantic knowledge claim.

Example:

```text
multiple observations
       ↓
consistent pattern
       ↓
validated abstraction
       ↓
knowledge candidate
       ↓
promotion policy
       ↓
semantic knowledge
```

Promotion requires stronger evidence than ordinary episodic retention when the claim can materially influence future behavior.

---

## 16. Promotion Is Reversible

Knowledge promotion is not irreversible.

New contradictory evidence can:

- lower confidence;
- mark a claim disputed;
- supersede the claim;
- demote it;
- quarantine it;
- invalidate it according to policy.

Historical evidence remains preserved where required.

---

## 17. Retrieval

Retrieval is a read operation over governed state.

Retrieved memory does not change state merely because it was accessed.

However, retrieval may generate telemetry such as:

- retrieval count;
- relevance feedback;
- user correction;
- successful use;
- failure to retrieve.

These signals may influence later consolidation subject to policy.

---

## 18. Retrieval Feedback

If Novi repeatedly retrieves a memory successfully for a particular task, that may be evidence of usefulness.

If retrieval repeatedly fails, the system may consider:

- re-indexing;
- enrichment;
- alternative representations;
- consolidation;
- correction.

Retrieval frequency alone must not make an incorrect memory more authoritative.

---

## 19. Modification

A memory modification must preserve history where the original content is semantically significant.

Prefer:

```text
old claim
   ↓
new evidence
   ↓
new claim
```

rather than destructive replacement.

Current-state projections can change while historical evidence remains intact.

---

## 20. Supersession

A memory becomes superseded when a newer valid state replaces its current semantic role.

Example:

```text
preferred_route = route_A
        ↓
new verified route
        ↓
preferred_route = route_B
```

Route A remains historically meaningful unless retention policy removes it.

---

## 21. Temporal Validity

Memories should distinguish:

- event time;
- observation time;
- ingestion time;
- validity start;
- validity end;
- supersession time.

This prevents stale memories from being interpreted as current facts.

---

## 22. Spatial Validity

Where relevant, memories should carry spatial scope.

Example:

```text
object = heater
location = living_room
valid during = observation interval
```

Spatial memories may become invalid if the physical environment changes.

Map and place-change detection should therefore be able to trigger memory review.

---

## 23. Confidence Evolution

Confidence is dynamic.

```text
candidate: 0.55
   ↓ corroboration
0.73
   ↓ verification
0.94
   ↓ contradiction
0.61
   ↓ unresolved conflict
0.42
```

The exact mathematical update mechanism is domain-specific and must avoid double-counting correlated evidence.

---

## 24. Verification Levels

V1 should distinguish at least:

```text
UNVERIFIED
OBSERVATION_SUPPORTED
MULTI_SOURCE_SUPPORTED
USER_CONFIRMED
SYSTEM_VERIFIED
```

Verification is not equivalent to confidence.

A highly confident model prediction may still be unverified.

---

## 25. Forgetting

Forgetting is a governed lifecycle transition, not arbitrary deletion.

A memory may be forgotten because of:

- explicit user deletion;
- retention expiry;
- privacy policy;
- low utility;
- redundancy;
- storage pressure;
- legal/compliance requirements where applicable.

Protected memories require stronger deletion rules.

---

## 26. Archival

Archival moves low-frequency but potentially valuable memories out of hot retrieval paths.

```text
ACTIVE
  ↓
ARCHIVED
```

Archived memories remain recoverable if policy allows.

Archival must not change semantic meaning.

---

## 27. Purging

Purging is stronger than archival.

```text
logical deletion
      ↓
retention period / policy
      ↓
purge
```

Purging must account for:

- canonical records;
- event history;
- replicas;
- backups;
- embeddings;
- FTS indexes;
- graph projections;
- caches;
- media references.

The deletion architecture in Document 11 remains authoritative.

---

## 28. Lifecycle and Synchronization

Lifecycle transitions are themselves synchronizable events where required.

Example:

```text
memory X
  ↓
DELETE
  ↓
tombstone
  ↓
replicas reconcile
```

A stale replica cannot re-admit a deleted memory merely because its copy predates the deletion.

---

## 29. Lifecycle and Backup

Backups must preserve enough lifecycle information to reconstruct:

- current state;
- historical state;
- deletions;
- supersessions;
- quarantine state;
- provenance.

Restoration must not accidentally reactivate expired or deleted data.

---

## 30. Lifecycle and Security

Security state can block transitions.

For example:

```text
suspected compromise
       ↓
block promotion
block external sync
protect audit state
       ↓
security investigation
```

Ordinary learning must not bypass these controls.

---

## 31. Lifecycle and Privacy

Privacy classification follows memory through its lifecycle.

A memory does not become public merely because it was enriched, consolidated or promoted.

Derived representations inherit appropriate privacy constraints from their sources.

---

## 32. Lifecycle and Spatial Memory

A spatially anchored memory should remain associated with the appropriate place/map version.

If the map changes significantly, Novi may need to:

- re-localize the memory;
- reduce confidence;
- mark it stale;
- associate it with the historical map;
- request new observation.

---

## 33. Lifecycle and Learning

Learning can propose transitions but cannot bypass lifecycle policy.

```text
experience
   ↓
learning proposal
   ↓
policy
   ↓
validation
   ↓
state transition
```

The learning system is therefore a participant in the lifecycle, not its authority.

---

## 34. Lifecycle and Personality

Personality-related memories and preferences can evolve, but personality should not be allowed to silently modify security, safety or authorization policies.

Example:

```text
user preference
   ↓
long-term preference memory
   ↓
personality adaptation
```

The protected-policy boundary remains intact.

---

## 35. State Transition Rules

Each transition must define:

- allowed source state;
- destination state;
- triggering event;
- required evidence;
- required authority;
- side effects;
- audit requirements;
- rollback behavior;
- privacy impact.

Example:

```text
CANDIDATE → ADMITTED
```

requires an admission policy decision.

```text
ACTIVE → DELETED
```

requires deletion authorization/policy.

---

## 36. Illegal Transitions

Examples of transitions that must be blocked:

```text
REJECTED → ACTIVE
```

without a new admission process.

```text
DELETED → ACTIVE
```

without explicit authorized restoration/re-admission.

```text
QUARANTINED → PROMOTED
```

without resolution.

```text
UNVERIFIED → SAFETY_AUTHORITY
```

without the required verification path.

---

## 37. Atomicity of Transitions

A lifecycle transition must update all required canonical state atomically.

For example, promotion may need to update:

- memory state;
- provenance link;
- knowledge relation;
- version;
- audit record;
- derived-state invalidation marker.

These changes must not leave a partially promoted memory visible as authoritative.

SQLite transactions are the local mechanism for these atomic state changes. Long-running model computation must remain outside the transaction boundary. SQLite documents that transactions provide atomic commit/rollback and that WAL changes concurrency behavior, while long-running readers can affect checkpoint progress. citeturn0search0turn0search1

---

## 38. Idempotency

Lifecycle commands should be idempotent where practical.

Example:

```text
PROMOTE memory X
PROMOTE memory X
```

must not create duplicate knowledge entities.

Every transition should have a unique operation/event identity.

---

## 39. Concurrency

Two workers may attempt the same transition concurrently.

The Memory Manager must use version checks and transactional commit semantics so only a valid transition becomes canonical.

Stale workers must re-read state and reevaluate rather than overwrite newer state.

---

## 40. Event-Sourced Trace

Significant lifecycle transitions should produce events such as:

```text
MemoryCandidateCreated
MemoryAdmitted
MemoryEnriched
MemoryConsolidated
KnowledgePromoted
MemorySuperseded
MemoryArchived
MemoryDeleted
MemoryPurged
MemoryQuarantined
MemoryRestored
```

Event names are illustrative; final API/event contracts belong in the implementation layer.

---

## 41. Lifecycle State Machine

Conceptually:

```text
                 ┌───────────────┐
                 │   INGESTED    │
                 └───────┬───────┘
                         ↓
                 ┌───────────────┐
                 │   NORMALIZED  │
                 └───────┬───────┘
                         ↓
                 ┌───────────────┐
                 │    GROUNDED   │
                 └───────┬───────┘
                         ↓
                 ┌───────────────┐
                 │   CANDIDATE   │────→ REJECTED
                 └───────┬───────┘
                         ↓
                 ┌───────────────┐
                 │    ADMITTED   │────→ QUARANTINED
                 └───────┬───────┘
                         ↓
                 ┌───────────────┐
                 │    ACTIVE     │
                 └───┬─────┬─────┘
                     │     │
             enrich/consolidate
                     │     │
                     ↓     ↓
                PROMOTED  SUPERSEDED
                     │       │
                     └───┬───┘
                         ↓
                    ARCHIVED
                         ↓
                     DELETED
                         ↓
                      PURGED
```

The actual implementation may represent some of these as orthogonal flags/events rather than a single state machine.

---

## 42. Lifecycle Guarantees

The system should guarantee:

1. No unadmitted candidate is treated as ordinary long-term memory.
2. Provenance survives enrichment and consolidation.
3. Historical evidence is not silently destroyed by supersession.
4. Deletion is propagated according to policy.
5. Derived representations can be invalidated/rebuilt.
6. Security/quarantine states block unauthorized promotion.
7. Lifecycle changes are auditable.
8. Concurrent transitions cannot silently overwrite newer state.
9. Lifecycle behavior remains available offline.
10. Restoration does not silently reactivate deleted data.
11. Promotion requires stronger evidence than simple persistence when appropriate.
12. Forgetting is governed by explicit policy.

---

## 43. Failure Handling

If a lifecycle transition fails:

```text
attempt
  ↓
failure
  ↓
rollback / retry / quarantine
  ↓
consistent previous state
```

Partial transitions must not create contradictory canonical state.

Derived-state failures should generally be recoverable by rebuilding from canonical state.

---

## 44. Testing

Required lifecycle tests include:

- every legal transition;
- every illegal transition;
- concurrent transitions;
- crash during transition;
- power loss during commit;
- duplicate transition;
- stale worker;
- schema migration;
- synchronization race;
- deletion race;
- restore after deletion;
- quarantine/promotion;
- confidence changes;
- spatial map changes;
- privacy-class changes;
- model-version changes;
- corrupted derived indexes;
- recovery from incomplete enrichment;
- long-term archival and purge.

Property-based testing should be considered for transition invariants because the lifecycle has many combinations of state and metadata.

---

## 45. External Reference Architecture

Research supports treating memory as an active cognitive subsystem rather than passive storage. Robot-memory literature describes memory as mediating sensorimotor data, semantic interpretation, planning and prediction, and recent embodied-memory work uses multiple memory scales/modalities for long-horizon robot tasks. citeturn0academia39turn0academia38turn0academia36

The lifecycle design also follows established managed-component principles: ROS 2 lifecycle nodes explicitly model controlled initialization, activation, deactivation and cleanup, which is a useful pattern for the runtime portions of Novi's memory subsystem. citeturn0search3turn0search8

---

## 46. Final Principle

> **Every memory has a history, a current status, a provenance chain and a governed future.**

Novi's memory must therefore behave like a living, auditable information system: it can learn, consolidate, evolve, forget and correct itself, but every meaningful transition remains bounded by evidence, policy, security, privacy and explicit state rules.
