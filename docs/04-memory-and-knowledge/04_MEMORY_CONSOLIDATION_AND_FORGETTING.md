# 04 — Memory Consolidation and Forgetting

## Status

**DESIGN — RESEARCHED V1**

## 1. Purpose

This document defines how Novi transforms accumulated memory candidates and experiences into durable, useful, current knowledge while controlling redundancy, staleness, contradiction, storage growth, retrieval pollution, and privacy exposure.

Consolidation and forgetting are part of Novi's learning architecture, not housekeeping.

> **Novi should remember what remains useful, preserve evidence for what matters, revise what changed, and forget what no longer deserves cognitive resources.**

## 2. Research Basis

The design was cross-checked against current NVIDIA NeMo Agent Toolkit memory architecture and contemporary agent-memory research. NVIDIA provides pluggable memory backends, `MemoryEditor`/`MemoryItem` abstractions, automatic capture/retrieval, and higher-level memory-management patterns. Its automatic wrapper can capture messages and retrieve memories without relying on the LLM to remember memory-tool calls. citeturn0search1turn0search4turn0search9

Recent research frames agent memory as a continuous **write → manage → read** loop and identifies continual consolidation, trustworthy reflection, learned forgetting, multimodal memory, and privacy as open problems. citeturn0academia14turn0academia13

Recent long-term-memory benchmarking also shows that agents can continue using obsolete memories when facts change. Novi therefore treats invalidation, supersession, temporal validity, and forgetting-aware evaluation as first-class requirements. citeturn0academia16

## 3. Consolidation Is Not Summarization

Summarization compresses information. Consolidation decides what survives, how it is represented, what evidence supports it, what it supersedes, and what should be discarded or archived. A summary may be an output of consolidation, but it is not the policy itself.

## 4. Canonical Lifecycle

```text
observation
  ↓
event
  ↓
episode
  ↓
admitted memory candidate
  ↓
validation / deduplication
  ↓
active memory
  ↓
consolidation
 ┌────┼───────────┬────────────┐
 ↓    ↓           ↓            ↓
merge update   promote      archive
 ↓    ↓           ↓            ↓
active durable knowledge   cold storage
      ↓
validity / relevance monitoring
      ↓
refresh / supersede / expire
      ↓
forget or retain
```

## 5. Online and Background Paths

Real-time perception and interaction cannot wait for large-scale memory processing.

### Online

```text
observe → admit → make available when appropriate
```

### Background

```text
batch → cluster → compare → merge → validate → promote → index → decay/archive
```

Background consolidation must yield to safety-critical perception, navigation, interaction, and control. NVIDIA's modular memory approach supports keeping memory management behind interfaces rather than coupling it directly to the model call. citeturn0search1turn0search8

## 6. Consolidation Triggers

Possible triggers include scheduled jobs, session completion, queue size, repeated observations, duplicate detection, prediction error, contradictions, knowledge change, user correction, resource pressure, checkpoint/shutdown, high-value event completion, and idle periods.

A trigger schedules evaluation; it does not guarantee mutation.

## 7. Memory-Type-Specific Consolidation

### Episodic

Preserve meaningful experiences and temporal/contextual evidence. Repeated low-value episodes may be compressed into patterns while important episodes remain addressable.

### Semantic

Merge compatible claims, preserve provenance, and supersede obsolete claims rather than silently overwriting history.

### Procedural

Promote repeated successful behavior into a procedure only after sufficient evidence and safety validation.

### Relationship

Update relationship evidence over time; one interaction is not definitive.

### Spatial

Update locations and object relationships when new sensor evidence indicates change.

### Temporal

Learn recurring patterns while keeping them probabilistic and time-bounded.

### Preference

A newer explicit preference generally supersedes an older preference within the same scope.

### Operational

Current device/environment state should prioritize fresh telemetry over old observations.

## 8. Consolidation Operations

```text
KEEP
MERGE
UPDATE
PROMOTE
DEMOTE
SUPERSEDE
SPLIT
ARCHIVE
EXPIRE
DELETE
RETAIN
REQUEST_VERIFICATION
```

Every destructive or semantically significant operation must be auditable.

## 9. Deduplication

Deduplication must use more than embedding similarity. Candidate signals include entity identity, claim identity, temporal overlap, source, lexical similarity, semantic similarity, provenance, contradiction status, and scope.

Two semantically similar memories may still describe different events and must not be merged solely because embeddings are close.

## 10. Merge Policy

A merge is allowed only when records represent the same underlying information or compatible observations.

```text
A: Vano prefers cold brew.
B: Vano usually orders cold brew.
→ candidate merge
```

But:

```text
A: cold brew in summer
B: hot coffee in winter
```

should preserve seasonal scope rather than create a false contradiction.

## 11. Evidence Preservation

Consolidation must not destroy the evidence graph behind an important claim.

```text
knowledge claim
   ├── evidence 1
   ├── evidence 2
   ├── evidence 3
   └── provenance
```

Summaries should reference source memories rather than irreversibly replacing them.

## 12. Promotion From Episode to Semantic Knowledge

Promotion should consider recurrence, source reliability, independent evidence, user confirmation, consistency, temporal stability, consequence of error, relevance, and contradiction rate.

```text
one observation
    ↓
episode
    ↓
repeated pattern
    ↓
routine hypothesis
    ↓
independent evidence
    ↓
knowledge candidate
    ↓
verification
    ↓
semantic knowledge
```

## 13. Reflection Is Advisory

A model may identify patterns or propose summaries, but model-generated reflections are proposals.

For example, “Vano is always tired after work” must not become durable knowledge merely because a reasoning model generated it. Evidence, confidence, scope, and epistemic state remain explicit.

## 14. Prediction Error

Prediction errors should trigger reconsideration of routines and expectations.

```text
old prediction
     ↓
prediction error
     ↓
collect evidence
     ↓
update routine model
     ↓
supersede / revise expectation
```

This prevents stale routines from dominating future context.

## 15. Temporal Validity

Durable memory supports, where applicable:

```text
valid_from
valid_until
observed_at
last_confirmed
```

Historical records can remain useful even after current knowledge supersedes them.

## 16. Forgetting Is Not Deletion

Novi distinguishes:

- **forget from active retrieval** — normally no longer surfaced;
- **archive** — retained outside active memory;
- **expire** — no longer valid for current reasoning;
- **delete** — physically removed when policy permits/requires;
- **user-directed deletion** — explicit privacy operation.

Forgetting normally changes cognitive accessibility without destroying historical evidence.

## 17. Forgetting Signals

Candidate archival/forgetting signals include relevance, access frequency, importance, age, expiration, supersession, duplicate status, confidence, unresolved contradiction, privacy policy, storage pressure, and user request.

No single signal should blindly delete a memory.

## 18. Importance Is Not Retrieval Frequency

A rarely accessed memory can be critical; a frequently accessed memory can be obsolete.

```text
importance ≠ access_frequency ≠ current_relevance
```

## 19. Type-Specific Decay

Decay must be memory-type-specific.

Examples:

- device state: rapid decay;
- current location: rapid decay;
- household preference: slow decay;
- historical event: no automatic factual decay;
- predicted routine: confidence decay when prediction errors accumulate.

Decay should normally change retrieval priority or confidence, not rewrite historical facts.

## 20. Context-Aware Forgetting

A memory irrelevant to one task can be critical to another. Therefore “forget” should normally mean “not eligible for this retrieval context,” not “delete globally.”

## 21. Contradiction Handling

```text
new claim
   ↓
conflict detection
   ↓
compare provenance + temporal scope + reliability
   ↓
 ┌──────────────┬──────────────┐
 ↓              ↓              ↓
resolve       coexist       verify
 ↓              ↓              ↓
supersede    scoped claims   pending
```

“Last write wins” is not the universal rule.

## 22. User Corrections

An explicit correction from an authorized user should have high weight, but its scope must be recorded.

```text
User: “I no longer drink coffee.”
```

This updates the current preference without rewriting historical episodes.

## 23. Protected Memories

Information may be marked user-pinned, safety-critical, system-required, operationally retained, or audit-required. Protected status prevents ordinary forgetting but does not bypass applicable privacy/deletion rights.

The immutable protected system area remains outside the Memory Manager's authority.

## 24. Privacy-Aware Forgetting

Privacy retention can override normal relevance scoring. Temporary visitor identity, raw audio/video, derived metadata, and relationship information may have different retention policies. User-requested deletion must propagate to indexes and derived caches according to the deletion policy.

## 25. Multimodal Consolidation

Novi may consolidate linked:

```text
video + audio + speech + face + speaker + pose
+ location + IoT event + conversation + time
```

Multimodal episodes should preserve links between evidence modalities rather than forcing everything into one text summary.

## 26. Logical Storage Tiers

```text
HOT     active/session/important memories
WARM    durable searchable memories
COLD    archived historical evidence
PURGED  policy-authorized deletion
```

The physical implementation may use SQLite, files, indexes, or another local backend. Logical lifecycle must remain storage-independent.

## 27. Consolidation Scheduling

Scheduling should consider CPU/GPU availability, memory pressure, thermal state, power/battery state, interaction load, queue size, deadline, and importance.

On Jetson, background consolidation yields to real-time safety workloads.

## 28. Jetson and Mac Deployment

The target production environment is Jetson AGX Orin 64GB, but development-time bulk reindexing, migration, evaluation, and large consolidation jobs may run on the Mac/workstation. Validated artifacts can then be deployed locally.

Production must retain a local-capable consolidation path.

## 29. NVIDIA Integration

NVIDIA NeMo Agent Toolkit is an integration candidate because it provides memory abstractions, automatic capture/retrieval, pluggable providers, and structured `MemoryItem` representations. citeturn0search1turn0search4turn0search9

However, a provider's automatic capture must not bypass Novi's admission, privacy, provenance, contradiction, retention, or immutable-core policies.

NVIDIA's broader NeMo stack is modular and framework-agnostic, so it can be evaluated alongside other local open-source implementations rather than becoming a hard dependency. citeturn0search2turn0search7

## 30. Metrics

Track:

- memory growth rate;
- duplicate rate;
- merge precision;
- merge false-positive rate;
- promotion rate;
- stale-memory retrieval rate;
- contradiction rate;
- obsolete-memory usage;
- forgetting precision/recall;
- retrieval relevance;
- consolidation latency;
- CPU/GPU/memory use;
- storage growth;
- user correction rate;
- prediction-error reduction.

A critical metric is **obsolete-memory usage**: how often Novi relies on information that should no longer influence its response. Recent research specifically identifies obsolete-memory reuse as a major weakness and proposes forgetting-aware evaluation. citeturn0academia16

## 31. Safety Invariants

1. Consolidation cannot modify the immutable protected system area.
2. Model reflection cannot directly become authoritative knowledge.
3. Historical evidence cannot be silently rewritten to match current beliefs.
4. Stale memory must not outrank fresh authoritative state merely because it is semantically similar.
5. Forgetting cannot silently delete audit-critical information.
6. User deletion must propagate according to policy.
7. Memory operations cannot bypass authorization.
8. Failed consolidation leaves the previous valid state recoverable.
9. A corrupted index is never authoritative data.
10. Background consolidation cannot compromise real-time safety workloads.

## 32. Transactionality and Recovery

Multi-step consolidation should follow:

```text
prepare → validate → write new state → update indexes → verify → commit
```

On critical failure:

```text
rollback / mark incomplete
```

The authoritative store must never claim that an invalid derived index is current.

## 33. Idempotency

Consolidation jobs may be retried. Operations therefore require idempotency keys or deterministic merge rules where practical. Repeating a job must not create duplicate knowledge or repeatedly reduce confidence.

## 34. Concurrency

The Memory Manager must handle concurrent writes, version conflicts, stale readers, duplicate candidates, simultaneous user correction, and simultaneous consolidation. Optimistic concurrency/version checks are preferred where appropriate.

## 35. LLM Authority Boundary

The reasoning model may identify important experiences, propose summaries/merges/knowledge candidates, explain contradictions, propose forgetting candidates, and propose schema evolution.

It may not independently delete authoritative memory, mark claims verified without permitted evidence, modify immutable data, bypass retention, alter authorization, or execute arbitrary storage operations.

## 36. Consolidation State Machine

```text
CANDIDATE
   ↓
ELIGIBLE
   ↓
PROCESSING
   ├──→ RETAINED
   ├──→ MERGED
   ├──→ PROMOTED
   ├──→ SUPERSEDED
   ├──→ ARCHIVED
   ├──→ EXPIRED
   ├──→ DELETED
   └──→ NEEDS_VERIFICATION
```

Every transition should be observable and auditable.

## 37. Example — Changing a Preference

```text
2026-01
Vano likes cold brew.
source = direct statement
status = verified

2026-08
Vano: “I don't drink coffee anymore.”
source = direct statement
status = verified

consolidation:
  old preference → superseded
  new preference → active

historical episodes remain unchanged
```

## 38. Example — Learning a Routine

```text
Day 1: arrive home → shower
Day 2: arrive home → shower
Day 3: arrive home → shower
        ↓
   routine candidate

Day 4: arrive home → cooking
        ↓
   prediction error

Final knowledge:
“often showers after arriving home”
not:
“always showers after arriving home”
```

## 39. Example — Unknown Concept

```text
repeated observation
       ↓
unknown object
       ↓
candidate concept
       ↓
trusted-user validation / evidence gathering
       ↓
validated concept
       ↓
semantic knowledge
       ↓
future observations reference same entity
```

If the concept does not fit an existing schema, a schema extension can be proposed and separately validated.

## 40. Testing Requirements

Test duplicate and near-duplicate episodes, contradictory claims, changed preferences, stale device state, changing routines, false model reflections, malicious memory proposals, privacy deletion, corrupted indexes, interrupted transactions, repeated retries, concurrent updates, resource exhaustion, multimodal evidence, and long-duration simulations.

## 41. Research-Driven Evaluation

Novi must evaluate more than simple recall. It should demonstrate that it can:

1. remember useful information;
2. reason over accumulated information;
3. update information when circumstances change;
4. stop using obsolete information;
5. preserve historical context;
6. consolidate repeated experience;
7. forget according to policy;
8. avoid hallucinated memory.

This follows current research showing that static recall is insufficient for long-running agents. citeturn0academia14turn0academia16

## 42. Design Decisions

### Consolidation is a first-class subsystem

Memory growth and knowledge quality cannot be safely managed by retrieval alone.

### Forgetting is policy-driven

Relevance, age, frequency, privacy, importance, and validity have different meanings.

### Historical evidence is preserved where required

Current knowledge must not erase the ability to understand what happened in the past.

### Model reflection is advisory

LLMs can synthesize useful patterns but can also hallucinate or overgeneralize.

### Consolidation is mostly asynchronous

Real-time embodied interaction has strict latency requirements.

### Storage and consolidation are decoupled

Novi remains free to select the best local storage/indexing technology.

### Forgetting must be evaluated explicitly

Obsolete-memory reuse is a known failure mode of long-running agents. citeturn0academia16

## 43. Acceptance Criteria

Novi must eventually demonstrate controlled consolidation, safe merging, explicit supersession, temporal validity, policy-driven forgetting, archive/delete semantics, contradiction-aware consolidation, provenance preservation, asynchronous processing, transactional recovery, idempotent retries, concurrent-update handling, privacy-aware retention, immutable-core protection, local execution, measurable obsolete-memory reduction, and regression evidence that consolidation improves rather than degrades cognition.

## 44. Next Document

The next specification is **`05_MEMORY_RETRIEVAL_AND_RANKING.md`**. Consolidation determines what survives; retrieval determines what Novi is allowed to bring into active cognitive context.

It must cover hybrid retrieval, temporal filtering, semantic search, exact search, relationship/graph traversal, reranking, freshness, confidence, provenance, task-specific relevance, context budgets, and protection against stale or poisoned memories.
