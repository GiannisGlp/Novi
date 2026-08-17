# 03 — Provenance, Evidence, Trust and Uncertainty

**Status:** CANONICAL — CONSOLIDATED V1.1

## Purpose

Define how Novi records where information came from, how it was transformed, what evidence supports it, how trustworthy it is for a given claim, and what remains uncertain.

> Novi must know not only what it believes, but why it believes it, where the information came from, when it was valid, what evidence supports it, and what could invalidate it.

Provenance is part of the memory model, not optional metadata.

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
        ↓
decision / action / outcome
```

Each stage may have multiple parents. Transformations such as summaries, embeddings, merges, reflections and schema migrations must retain links to supporting evidence.

## Evidence record contract

Consequential evidence should have a stable identity and support, where applicable:

```text
EvidenceRecord
├── evidence_id
├── source_class
├── source_identity
├── actor_or_producer
├── observed_at / captured_at
├── received_at
├── content_ref
├── integrity_metadata
├── provenance_parent_refs
├── transformation_refs
├── independence_group
├── validity_scope
├── reliability_assessment
├── uncertainty
├── verification_state
├── privacy_class
└── retention_policy_ref
```

The physical representation may vary, but these semantics must remain available for consequential evidence.

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

Source classes are not globally ordered. Authority depends on the claim.

## Evidence, claim and belief

```text
Evidence
  ↓
Claim
  ↓
Evaluation
  ↓
Belief state
```

A generated summary remains a derivative. It does not become independent evidence merely because it is stored, retrieved or repeated.

## Trust is contextual

Novi must not use one global trust score.

```text
trust(source, claim_type, context, time, consequence)
```

must be treated as contextual. A user can be authoritative about their own preference while a sensor can be authoritative about a measurement within its calibrated domain.

## Confidence and verification

Confidence describes epistemic strength; verification describes the validation process/status. They remain separate.

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

A high confidence score must never be treated as proof.

## Multidimensional evidence quality

Evidence quality should not collapse into one scalar. Relevant dimensions include:

```text
reliability
freshness
independence
integrity
completeness
precision
relevance
context_fit
verification
source_authority
measurement_quality
```

The weighting and thresholds are claim- and consequence-specific.

## Uncertainty taxonomy

Where material, Novi should distinguish:

```text
EPISTEMIC_UNCERTAINTY     // insufficient knowledge
MEASUREMENT_UNCERTAINTY  // measurement error / precision
ALEATORIC_UNCERTAINTY    // inherent variability
IDENTITY_UNCERTAINTY     // unresolved referent
TEMPORAL_UNCERTAINTY     // uncertain time interval
SPATIAL_UNCERTAINTY      // uncertain location / frame
MODEL_UNCERTAINTY        // model limitations
MISSINGNESS              // expected evidence unavailable
```

Do not infer that one uncertainty type is equivalent to another.

## Independence and common-source dependence

Multiple observations derived from the same underlying source must not be counted as independent corroboration.

```text
camera frame
 ↓
object detector
 ↓
summary
 ↓
embedding
```

This remains one evidence lineage, not four independent confirmations.

Evidence should support an `independence_group` or equivalent dependency representation when corroboration matters.

## Temporal validity

Evidence and claims should distinguish capture/observation time from validity time.

```text
observed_at
valid_from
valid_until
last_confirmed
```

A historical claim may remain true about the past while being invalid for current state.

## Conflict and evidence arbitration

Conflicting claims are first-class state:

```text
CLAIM A
CLAIM B
   ↓
CONFLICT SET
```

Before arbitration, compare identity, predicate, scope, time, location, measurement domain, source authority, independence and evidence quality.

Possible outcomes:

```text
ACCEPT_A
ACCEPT_B
BOTH_CONDITIONALLY_VALID
REFINE
REQUIRE_NEW_EVIDENCE
UNRESOLVED
ABSTAIN
```

There is no universal newest-wins or highest-confidence-wins rule.

## Provenance and derivatives

Every consequential derivative should preserve dependency information sufficient to answer:

```text
WHY DOES THIS EXIST?
WHAT SUPPORTS IT?
WHAT DEPENDS ON IT?
WHO/WHAT PRODUCED IT?
WHEN WAS IT PRODUCED?
WHAT TRANSFORMATIONS OCCURRED?
```

Traceability does not imply truth.

## Erasure and lineage

Deletion must consider the provenance/derivation graph. When a source is erased, applicable summaries, embeddings, indexes and derived records must be deleted, sanitized or recomputed according to policy.

If required erasure cannot be verified, the system reports `ERASURE_PENDING`.

## Security boundary

Persistent memory is an attack surface. Relevant threats include memory poisoning, sleeper memories, indirect prompt injection, provenance forgery, retrieval poisoning, cross-user leakage, malicious synchronization and data exfiltration. Write-time and read-time controls are both required.

## Audit and evaluation

Material evidence and belief revisions should be auditable without storing hidden chain-of-thought. Record structured metadata such as source, evidence IDs, policy version, model/version where applicable, decision reason codes and timestamps.

Evaluation should include provenance coverage, unsupported-claim rate, source-independence errors, stale-evidence rate, calibration, contradiction handling, dependency trace completeness and erasure propagation correctness.

## Abstention

When evidence is insufficient for the consequence of the requested operation, the system should support:

```text
REQUEST_CLARIFICATION
REVALIDATE
ABSTAIN
ESCALATE_TO_HUMAN
```

Uncertainty must remain visible to downstream cognition and governance.

## Research basis

Current RAG research treats relevance, accuracy and faithfulness as distinct evaluation dimensions, while broader trustworthiness work adds robustness, fairness, transparency, accountability and privacy. NIST likewise emphasizes context-specific measurement and documented TEVV rather than a single generic AI quality score.

## Source consolidation

The historical corpus remains preserved in `archive/`. The active authority is this document and the other canonical 01–18 documents.