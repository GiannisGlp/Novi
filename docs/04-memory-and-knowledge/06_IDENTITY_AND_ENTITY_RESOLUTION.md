# 06 — Identity and Entity Resolution

**Status:** CANONICAL — CONSOLIDATED V1.1

## Purpose
Define how Novi represents entities, resolves observations to entities, expresses identity assurance, and separates entity resolution from identity proofing, authentication and authorization.

## Core boundary

```text
ENTITY RESOLUTION ≠ IDENTITY PROOFING ≠ AUTHENTICATION ≠ AUTHORIZATION
```

A probabilistic match may identify a likely entity without proving that the entity is authenticated or authorized to act.

## Entity model

Novi represents stable entities independently from observations about them. Initial entity classes include person, organization, device, place, object, software agent, account, credential, document and conceptual entity.

Every entity has a stable internal identifier, lifecycle state, provenance, temporal validity, aliases and evidence links. External identifiers are references, not automatically canonical identity.

## Resolution pipeline

```text
OBSERVATION
 ↓
CANDIDATE GENERATION
 ↓
EVIDENCE COLLECTION
 ↓
MATCH / NON-MATCH / UNKNOWN
 ↓
ASSURANCE UPDATE
 ↓
ENTITY LINK
```

Resolution must permit **unknown** and **ambiguous** outcomes; forced matching is prohibited for consequential operations.

## Evidence

Identity evidence may include direct statements, authenticated credentials, device signals, visual/audio observations, documents, contextual relationships, historical continuity and independently corroborating sources. Evidence inherits provenance from document 03.

Similarity is not identity. Confidence is not assurance. Multiple observations from one derivative source are not independent corroboration.

## Identity assurance

Identity state should distinguish:

```text
UNRESOLVED
CANDIDATE
PROBABLE
CORROBORATED
PROOFED
AUTHENTICATED
REVOKED
INVALID
DISPUTED
```

The state is contextual and time-bounded. Identity proofing establishes evidence about a real-world identity; authentication establishes control of an authenticator or credential in a protocol context; authorization determines permitted actions. These must not be collapsed.

## Assurance transition contract

Material assurance changes should follow:

```text
candidate evidence
 ↓
evidence validation
 ↓
assurance evaluation
 ↓
policy threshold
 ↓
ASSURANCE UPDATE
 ↓
audit event
```

Each assurance level must define the evidence required to enter it, the operations it permits, its validity period, revalidation conditions and revocation behavior. Higher assurance must not be inferred merely from repeated observations of the same source.

## Credentials

Machine-verifiable credentials may be represented as evidence. W3C Verifiable Credentials Data Model 2.0 became a Recommendation in 2025 and provides a cryptographically secure, privacy-respecting, machine-verifiable model for claims. A valid credential proves only the claims and authority represented by that credential; it does not automatically grant Novi authorization to act.

Credential evidence should retain issuer, subject, issuance/validity, status/revocation information, verification method and provenance as applicable.

## Merge and split

Entity merge is a high-impact operation. It must preserve both source entities, evidence, provenance and the merge decision. A later split must be able to reconstruct which observations belonged to which entity and why.

```text
ENTITY A + ENTITY B
        ↓
MERGE PROPOSAL
        ↓
VALIDATION / POLICY
        ↓
MERGED VIEW
```

No merge may silently destroy identity history.

## Merge/split safety

A merge should be evaluated for:

```text
false-merge risk
false-split risk
affected relationships
affected permissions
affected memories
temporal consistency
privacy impact
rollback feasibility
```

A consequential merge may require human approval. A split must trigger impact analysis for dependent claims and authorization decisions.

## Temporal identity

Identity relationships are time-scoped. A person may change account, name, role, residence, device or affiliation without becoming a different entity; conversely, reused identifiers must not cause unrelated entities to be merged.

## Cross-modal identity

Vision, audio, text, location, device and behavioral signals are evidence streams. Agreement increases evidence only when the streams are sufficiently independent and their timestamps and provenance are known.

## Privacy

Identity resolution must minimize sensitive attributes, support scoped identifiers, enforce access policy and avoid unnecessary persistent biometric representations. Identity evidence is subject to document 14 and deletion dependencies defined by the system erasure architecture.

## Corrections

A human correction is an evidence-bearing event, not automatic truth. Protected identity changes require authenticated authority and are recorded with time, reason, provenance and previous state.

## Security invariants

1. Never equate similarity with authentication.
2. Never force a consequential ambiguous match.
3. Preserve provenance through merges and splits.
4. Current authentication supersedes stale memory.
5. Revocation must invalidate dependent authorization where required.
6. Identity evidence must remain privacy-scoped.
7. Model-generated identity claims remain derived evidence unless independently verified.
8. Credential validity does not imply authorization outside its declared scope.

## Evaluation

Identity resolution must be evaluated with separate measures for false matches, false non-matches, unresolved cases, calibration, assurance correctness, merge contamination and privacy leakage. Test sets should include aliases, reused identifiers, temporal changes, ambiguous observations, correlated evidence, adversarial inputs and revoked credentials.

## Integration

`03` supplies evidence/provenance. `05` supplies semantic entity relationships. `07` supplies temporal validity. `08` supplies spatial context. `10` supplies cross-modal evidence. `14` supplies privacy policy. `15` supplies machine governance and authorization decisions. `16` supplies human intervention and accountability. Distributed identity-state convergence belongs to system architecture.

## Research basis

NIST SP 800-63-4 (2025) separates identity proofing, authentication, federation and related assertions. W3C Verifiable Credentials 2.0 is a current Recommendation for cryptographically secure, privacy-respecting, machine-verifiable credentials.

## Source consolidation

The historical corpus remains preserved in `archive/`. The active authority is this document and the other canonical 01–18 documents.