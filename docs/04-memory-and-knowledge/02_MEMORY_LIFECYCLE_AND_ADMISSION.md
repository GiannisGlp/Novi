# 02 — Memory Lifecycle and Admission

**Status:** CANONICAL — CONSOLIDATED V1.1

## Purpose

Define the canonical lifecycle from observation to durable memory, including admission, correction, consolidation handoff, staleness, retention and deletion.

> Perception is continuous; persistence is selective.

The Memory Manager is the authoritative orchestration layer for admission, persistence, retrieval coordination, consolidation, deduplication, correction, expiration, deletion, provenance and policy enforcement. The model may propose typed memory operations but cannot bypass the manager.

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

## Write targets

Novi distinguishes at least observation, event, episode, memory candidate, semantic knowledge claim, relationship update, preference candidate, routine candidate, procedural candidate, prediction, schema proposal and artifact. Predictions and model-generated hypotheses are never silently treated as observations.

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

No ordinary durable memory may bypass this gate. External text, webpages, documents, emails, tool outputs and agent messages are untrusted inputs until validated.

## Admission decision

Admission evaluates relevance, novelty, future usefulness, evidence, confidence, verification, consequence, privacy, recurrence, contradiction, retention cost and user intent.

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

High confidence is not sufficient for admission; a model can be confidently wrong. Source reliability is contextual to the claim type.

## Fast path and background path

### Fast path

Used when memory is needed immediately: explicit remember requests, user corrections, active task state, safety-relevant persistence and conversation continuity.

### Background path

Used for expensive work: routine discovery, summarization, large-scale duplicate detection, embeddings, relationship analysis, schema proposals and consolidation.

Background processing must yield to safety-critical perception, navigation, interaction and control.

## Explicit remember requests

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

The confirmation must distinguish **accepted for persistence** from **verified as true**.

## Formal lifecycle transition contract

Every material lifecycle transition should be modeled as:

```text
CURRENT_STATE
   ↓
transition request
   ↓
precondition checks
   ↓
policy / authorization
   ↓
evidence / validation checks
   ↓
STATE TRANSITION
   ↓
side effects
   ↓
audit event
```

A transition must define its actor, preconditions, postconditions, side effects, failure state and audit event. A transition that cannot establish its postconditions must not be reported as successful.

## Lifecycle states and failure states

Canonical states:

```text
CAPTURED
CLASSIFIED
ADMISSION_PENDING
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
CONFLICTED
QUARANTINED
BLOCKED
DEGRADED
PENDING
FAILED
ERASURE_PENDING
PARTIALLY_ERASED
```

An unavailable or uncertain state must never be silently converted into confidence.

## Idempotency

Material admission, consolidation and deletion operations should be idempotent where feasible.

```text
same operation + same authoritative input
            ↓
      same semantic result
```

Retries must not create duplicate memories, duplicate evidence, repeated promotions or contradictory deletion outcomes. Non-idempotent operations require explicit operation identifiers and deduplication semantics.

## Deduplication and conflict

Before durable admission, compare candidates using exact matching, normalized text, semantic similarity, entity identity, temporal validity, claim identity, relationship identity and provenance.

A conflict must not silently overwrite the existing claim. Preserve competing claims and resolve them using source relevance, evidence, verification, claim type and temporal validity.

## Correction and supersession

For important claims, prefer:

```text
old claim
   ↓
superseded by
   ↓
new claim
```

rather than destructive replacement. Historical evidence remains traceable even when the current interpretation changes.

## Staleness

A memory may remain historically useful after its validity expires. Stale information must not be presented as current state when the query requires current truth. Freshness requirements should be claim- and consequence-specific.

## Retention and deletion

Deletion is a policy-controlled lifecycle operation. It must account for derived indexes and artifacts, not merely the primary record.

```text
source
 ↓
dependency graph
 ↓
summaries / embeddings / indexes / derivatives
 ↓
delete / sanitize / recompute
 ↓
erasure verification
```

If required erasure cannot be verified, the state remains `ERASURE_PENDING`, not `ERASURE_COMPLETE`.

## Resource controls

Admission and background processing must be resource-aware. Controls may cover records/event, bytes/episode, embeddings/hour, generated artifacts, database growth, compute budget and background processing rate.

A memory subsystem that exhausts compute or storage is a system failure.

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

Do not persist hidden model chain-of-thought. Store structured policy and decision metadata instead.

## Evaluation requirements

Lifecycle testing must include:

- duplicate admission;
- retry after timeout;
- conflicting evidence;
- stale-memory admission;
- failed validation;
- quarantine and release;
- partial deletion;
- dependency-aware erasure;
- crash/restart during transition;
- concurrent update proposals;
- rollback/recovery;
- policy-version changes.

Key metrics include duplicate-admission rate, false-admission rate, stale-current-state rate, failed-transition rate, idempotency failures and verified-erasure success rate.

## Source consolidation

The historical corpus remains preserved in `archive/`. The active authority is this document and the other canonical 01–18 documents.