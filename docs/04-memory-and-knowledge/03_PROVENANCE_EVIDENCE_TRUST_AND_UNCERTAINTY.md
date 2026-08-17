# 03 — Provenance, Evidence, Trust and Uncertainty

**Status:** CANONICAL — CONSOLIDATED V1

## Purpose

Define how Novi records where information came from, how it was transformed, what evidence supports it, how trustworthy it is for a given claim, and what remains uncertain.

> Novi must know not only what it believes, but why it believes it, where the information came from, when it was valid, what evidence supports it, and what could invalidate it.

Provenance is part of the memory model, not optional metadata. fileciteturn210file0

## Fundamental separations

```text
PROVENANCE ≠ CONFIDENCE
CONFIDENCE ≠ VERIFICATION
VERIFICATION ≠ AUTHORIZATION
TRUST ≠ AUTHORIZATION
EVIDENCE ≠ CLAIM
CLAIM ≠ BELIEF
BELIEF ≠ TRUTH
```

These are architecture-wide invariants. fileciteturn215file0

## Provenance chain

```text
physical / digital source
        ↓
observation
        ↓
event
        ↓
evidence artifact
        ↓
claim
        ↓
memory
        ↓
knowledge
        ↓
retrieval
        ↓
cognitive conclusion
```

Each stage may have multiple parents. Transformations such as summaries, embeddings, merges, reflections and schema migrations must retain links to supporting evidence. fileciteturn210file0

## Source classes

Initial source classes include:

```text
DIRECT_SENSOR
USER_STATEMENT
TRUSTED_PERSON_STATEMENT
OTHER_PERSON_STATEMENT
SYSTEM_STATE
TOOL_OUTPUT
LOCAL_FILE
DOCUMENT
DATABASE
WEB_RESOURCE
MODEL_INFERENCE
MODEL_GENERATED
IMPORTED_DATA
SIMULATION
HUMAN_VALIDATION
DERIVED_MEMORY
```

Source classes are not globally ordered. Authority depends on the claim. For example, a user may be authoritative for their own preference; a sensor may be authoritative for a current measurement; a model prediction is not automatically independent evidence. fileciteturn210file0

## Evidence, claim and belief

### Evidence

Observed, measured, received or retrieved information tied to a source.

### Claim

A proposition derived from one or more evidence items.

### Belief

The currently accepted interpretation used by Novi, subject to validity, provenance, confidence and policy.

```text
Evidence:
"User said: I prefer cold brew."
        ↓
Claim:
"Vano prefers cold brew."
        ↓
Belief:
current_preference(coffee) = cold_brew
status = USER_CONFIRMED
```

This prevents a generated summary from becoming indistinguishable from its source evidence. fileciteturn210file0

## Provenance metadata

Consequential evidence should retain enough information to answer:

```text
Where did this come from?
When was it observed?
Who/what produced it?
How was it transformed?
How independent is it?
How reliable is the source for this task?
Is it current enough?
What depends on it?
```

At minimum, an evidence record should be able to represent source class, source identity, actor, capture/observation time, content reference, integrity metadata and derivation links. fileciteturn210file0

## Trust is contextual

Novi must not use one global trust score.

```text
user → strong source for own preference
camera → strong source for visible appearance
camera → not necessarily strong source for identity/function
LLM → reasoning output, not independent evidence
```

Trust is evaluated relative to the claim, environment, time and consequence.

## Confidence and verification

Confidence describes belief strength; verification describes the validation process/status. They remain separate.

Example states may include:

```text
UNVERIFIED
MODEL_SUPPORTED
MULTI_SOURCE_SUPPORTED
USER_CONFIRMED
SYSTEM_VERIFIED
EXTERNALLY_VERIFIED
CONTRADICTED
EXPIRED
```

A high confidence score must never be treated as proof. fileciteturn203file0

## Independence and common-source dependence

Multiple observations derived from the same underlying source must not be counted as independent corroboration.

```text
one camera frame
 ↓
object detector
 ↓
summary
 ↓
embedding
```

This remains one evidence lineage, not four independent confirmations.

## Temporal validity

Evidence and claims should distinguish capture/observation time from validity time. A historical claim may remain true about the past while being invalid for current state.

```text
observed_at
valid_from
valid_until
last_confirmed
```

Current authoritative state takes precedence over historical memory where current truth is required. fileciteturn214file0

## Conflict and belief revision

Conflicting claims are first-class state:

```text
CLAIM A
CLAIM B
   ↓
CONFLICT SET
```

Possible outcomes include accepted A, accepted B, both conditionally valid, unresolved, or requiring new evidence. The architecture must not force a single answer where evidence does not justify one. fileciteturn214file0

## Provenance and retrieval

Retrieved content remains data, not authority. A memory containing an instruction cannot grant itself permission to modify policy or authorize action.

Retrieval ranking must not silently become a truth ranking or authorization mechanism.

## Provenance and derivatives

Every consequential derivative should preserve dependency information sufficient to answer:

```text
WHY DOES THIS EXIST?
WHAT SUPPORTS IT?
WHAT DEPENDS ON IT?
WHO/WHAT PRODUCED IT?
WHEN WAS IT PRODUCED?
```

Traceability does not imply truth. fileciteturn214file0

## Erasure and lineage

Deletion must consider the provenance/derivation graph. When a source is erased, applicable summaries, embeddings, indexes and derived records must be deleted, sanitized or recomputed according to policy.

If required erasure cannot be verified, the system reports `ERASURE_PENDING`. fileciteturn214file0

## Security boundary

Persistent memory is an attack surface. Relevant threats include memory poisoning, sleeper memories, indirect prompt injection, provenance forgery, retrieval poisoning, cross-user leakage, malicious synchronization and data exfiltration. Write-time and read-time controls are both required. fileciteturn215file0

## Source consolidation

Merged into this canonical document:

- `06_MEMORY_PROVENANCE_AND_TRUST.md`
- provenance/evidence requirements from Documents 74, 75, 91 and 92.
- system-wide provenance invariants from Documents 95–96.

The historical documents remain preserved pending final audit and supersession. fileciteturn210file0