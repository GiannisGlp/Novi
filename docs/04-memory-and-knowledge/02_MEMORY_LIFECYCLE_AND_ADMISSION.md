# 02 — Memory Lifecycle and Admission

**Status:** CANONICAL — CONSOLIDATED V1

## Purpose

Define the canonical lifecycle from observation to durable memory, including admission, correction, consolidation handoff, staleness, retention and deletion.

> Perception is continuous; persistence is selective.

The Memory Manager is the authoritative orchestration layer for admission, persistence, retrieval coordination, consolidation, deduplication, correction, expiration, deletion, provenance and policy enforcement. The model may propose typed memory operations but cannot bypass the manager. fileciteturn203file0

## Canonical lifecycle

```text
observation
    ↓
event
    ↓
episode
    ↓
memory candidate
    ↓
identity / provenance / privacy / integrity checks
    ↓
admission decision
 ┌──┼──────────────┐
 ↓  ↓              ↓
discard transient   durable candidate
                     ↓
              validation / deduplication
                     ↓
                 active memory
                     ↓
               consolidation
                     ↓
       durable knowledge / procedure / pattern
                     ↓
          validity / relevance monitoring
             ┌───────┼────────┐
             ↓       ↓        ↓
         refresh  supersede  archive/expire
                                ↓
                              delete
```

This replaces competing lifecycle state machines from older documents. fileciteturn202file0 fileciteturn205file0

## Write targets

Novi distinguishes at least:

1. observation;
2. event;
3. episode;
4. memory candidate;
5. semantic knowledge claim;
6. relationship update;
7. preference candidate;
8. routine candidate;
9. procedural candidate;
10. prediction;
11. schema proposal;
12. artifact.

Each target has its own admission requirements. Predictions and model-generated hypotheses are never silently treated as observations.

## Memory write gate

```text
input
 ↓
identity / source
 ↓
integrity
 ↓
privacy classification
 ↓
instruction-data separation
 ↓
poisoning / anomaly check
 ↓
retention decision
 ↓
admission policy
 ↓
Memory Manager
 ↓
storage adapter
```

No ordinary durable memory may bypass this gate. External text, webpages, documents, emails, tool outputs and agent messages are untrusted inputs until validated. fileciteturn214file0

## Admission decision

Admission evaluates:

```text
relevance
novelty
future usefulness
evidence
confidence
verification
consequence
privacy
recurrence
contradiction
retention cost
user intent
```

Possible outcomes:

```text
DISCARD
KEEP_TRANSIENT
STORE_EPISODE
STORE_CANDIDATE
MERGE
UPDATE
VERIFY_FIRST
DEFER_TO_CONSOLIDATION
CREATE_SCHEMA_PROPOSAL
```

High confidence is not sufficient for admission; a model can be confidently wrong. Source reliability is contextual to the claim type. fileciteturn203file0

## Fast path and background path

### Fast path

Used when memory is needed immediately: explicit remember requests, user corrections, active task state, safety-relevant persistence and conversation continuity.

### Background path

Used for expensive work: routine discovery, summarization, large-scale duplicate detection, embeddings, relationship analysis, schema proposals and consolidation.

Background processing must yield to safety-critical perception, navigation, interaction and control. fileciteturn203file0

## Explicit remember requests

An explicit request to remember something receives priority admission handling, subject to privacy and policy.

```text
request
 ↓
extract claim
 ↓
identify subject
 ↓
check existing memory
 ↓
resolve duplicate/conflict
 ↓
store/update
 ↓
confirm persistence
```

## Deduplication and conflict

Before durable admission, compare candidates using exact matching, normalized text, semantic similarity, entity identity, temporal validity, claim identity, relationship identity and provenance.

A conflict must not silently overwrite the existing claim. Preserve competing claims and resolve them using source relevance, recency, evidence, verification, claim type and temporal validity.

## Correction and supersession

For important claims, prefer:

```text
old claim
   ↓
superseded by
   ↓
new claim
```

rather than destructive replacement. Historical evidence remains traceable even when the current interpretation changes. fileciteturn202file0

## Lifecycle states and failure states

The canonical lifecycle must support explicit states relevant to implementation, including:

```text
CAPTURED
CLASSIFIED
ADMITTED
TRANSIENT
INDEXED
ACTIVE
CONSOLIDATING
STALE
SUPERSEDED
ARCHIVED
DELETED
```

Failure/degradation states remain separate:

```text
UNKNOWN
UNAVAILABLE
STALE
CONFLICTED
QUARANTINED
BLOCKED
DEGRADED
PENDING
FAILED
ERASURE_PENDING
PARTIALLY_ERASED
```

An unavailable or uncertain state must never be silently converted into confidence. fileciteturn215file0

## Staleness

A memory may remain historically useful after its validity expires. Stale information must not be presented as current state when the query requires current truth.

## Retention and deletion

Deletion is a policy-controlled lifecycle operation. It must account for derived indexes and artifacts, not merely the primary row.

```text
source
 ↓
dependency graph
 ↓
summaries / embeddings / indexes / derivatives
 ↓
delete / sanitize / recompute
```

If required erasure cannot be verified, the state remains `ERASURE_PENDING`, not `ERASURE_COMPLETE`. fileciteturn214file0

## Resource controls

Admission and background processing must be resource-aware. Controls may cover records/event, bytes/episode, embeddings/hour, generated artifacts, database growth, compute budget and background processing rate.

A memory subsystem that exhausts compute or storage is a system failure. fileciteturn203file0

## Auditability

Every durable admission should record structured decision metadata:

```text
admission_id
candidate_id
source
memory_type
policy_version
decision
reason_codes
evidence_refs
confidence
verification_state
storage_target
actor
created_at
```

Do not persist hidden model chain-of-thought. Store structured policy and decision metadata instead. fileciteturn203file0

## Source consolidation

Merged into this canonical document:

- `02_MEMORY_LIFECYCLE.md`
- `03_MEMORY_WRITE_AND_ADMISSION_POLICY.md`
- lifecycle/admission requirements from Documents 95–96.

Historical source documents remain preserved until final audit and supersession. fileciteturn202file0 fileciteturn203file0