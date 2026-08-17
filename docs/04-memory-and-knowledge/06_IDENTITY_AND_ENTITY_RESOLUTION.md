# 06 — Identity and Entity Resolution

**Status:** CANONICAL — CONSOLIDATED V1

## Purpose
Define how Novi represents entities, resolves observations to entities, expresses identity assurance, and separates entity resolution from authentication and authorization.

## Core boundary

```text
ENTITY RESOLUTION ≠ IDENTITY PROOFING ≠ AUTHENTICATION ≠ AUTHORIZATION
```

A probabilistic match may identify a likely entity without proving that the entity is authenticated or authorized to act.

## Entity model

Novi represents stable entities independently from observations about them. Initial entity classes include person, organization, device, place, object, software agent, account, credential, document, and conceptual entity.

Every entity has a stable internal identifier, lifecycle state, provenance, temporal validity, aliases, and evidence links. External identifiers are references, not automatically canonical identity.

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

Identity evidence may include direct statements, authenticated credentials, device signals, visual/audio observations, documents, contextual relationships, historical continuity, and independently corroborating sources. Evidence inherits provenance from document 03.

Similarity is not identity. Confidence is not assurance. Multiple observations from one derivative source are not independent corroboration.

## Identity assurance

Identity state should distinguish:

- unresolved;
- candidate;
- probable;
- corroborated;
- proofed;
- authenticated;
- revoked/invalid;
- disputed.

The state is contextual and time-bounded. NIST SP 800-63-4 separates identity proofing, authentication, federation and related assertions; Novi adopts that separation rather than treating a memory match as authentication. citeturn0search0turn0search7

Machine-verifiable credentials may be represented as evidence. W3C Verifiable Credentials 2.0 is a Recommendation and provides cryptographically verifiable, privacy-respecting credential semantics; a valid credential still proves only the claims and authority represented by that credential. citeturn0search17turn0search2

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

## Temporal identity

Identity relationships are time-scoped. A person may change account, name, role, residence, device or affiliation without becoming a different entity; conversely, reused identifiers must not cause unrelated entities to be merged.

## Cross-modal identity

Vision, audio, text, location, device and behavioral signals are evidence streams. Agreement increases evidence only when the streams are sufficiently independent and their timestamps and provenance are known.

## Privacy

Identity resolution must minimize sensitive attributes, support scoped identifiers, enforce access policy, and avoid unnecessary persistent biometric representations. Identity evidence is subject to document 14 and deletion dependencies defined by document 111.

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

## Integration

`03` supplies evidence/provenance. `05` supplies semantic entity relationships. `07` supplies temporal validity. `08` supplies spatial context. `10` supplies cross-modal evidence. `105/106` govern authorization and human intervention. `109` governs distributed identity-state convergence.

## Research basis

NIST SP 800-63-4 (2025) and W3C Verifiable Credentials Data Model 2.0 (2025) were used as current standards anchors. citeturn0search0turn0search16