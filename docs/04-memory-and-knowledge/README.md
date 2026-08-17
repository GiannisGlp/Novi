# 04 — Memory and Knowledge

## Status

**CANONICAL ARCHITECTURE ACTIVE — V1.1 ENRICHMENT COMPLETE**

This directory contains Novi's current semantic Memory and Knowledge architecture. The active normative architecture is the canonical `01`–`18` set. Historical and transitional material is preserved under `archive/` for provenance and traceability.

## Start here

1. `ARCHITECTURE_INDEX.md` — authority and navigation.
2. `01`–`18` — current canonical semantic architecture.
3. `SOURCE_MATERIAL_STATUS.md` — source disposition registry.
4. `SOURCE_TRACEABILITY_MATRIX.md` — source-to-canonical mapping.
5. `FINAL_CONSOLIDATION_AUDIT.md` — consolidation and V1.1 enrichment status.

## Authority rule

```text
01–18 = CURRENT NORMATIVE CANONICAL AUTHORITY
SOURCE_MATERIAL_STATUS.md = CANONICAL SOURCE DISPOSITION REGISTRY
SOURCE_TRACEABILITY_MATRIX.md = CANONICAL TRACEABILITY ARTIFACT
archive/ = HISTORICAL / TRANSITIONAL / AUDIT MATERIAL, NON-NORMATIVE
```

Historical documents must not be treated as competing implementation authority.

## Core principle

> Experience is not automatically memory, memory is not automatically knowledge, and knowledge is not automatically truth.

The architecture preserves:

```text
observation ≠ evidence ≠ memory ≠ knowledge ≠ belief
retrieval ≠ truth
confidence ≠ provenance
verification ≠ confidence
trust ≠ authorization
historical state ≠ current authoritative state
model output ≠ independent evidence
derived data ≠ source evidence
uncertainty ≠ failure
abstention ≠ system failure
```

## Canonical processing flow

```text
observation
  ↓
evidence registration
  ↓
episode / memory candidate
  ↓
validation + deduplication
  ↓
consolidation / abstraction
  ↓
knowledge / skill / intention
  ↓
provenance + relationship graph
  ↓
retrieval + arbitration
  ↓
minimum sufficient trustworthy context
  ↓
reasoning
  ↓
current authorization + safety
  ↓
action
  ↓
observed outcome
  ↓
evaluation / revision
```

## Responsibility boundaries

```text
semantic memory              → docs/04-memory-and-knowledge
physical storage             → 01-system-architecture
transactions / concurrency   → 01-system-architecture
replication                  → 01-system-architecture
recovery                     → 01-system-architecture
runtime scheduling           → 01-system-architecture
observability implementation → 01-system-architecture
machine authorization        → 15
human governance             → 16
```

## Completion rule

The active directory is clean when one canonical authority exists per substantive semantic topic, historical material is clearly non-normative, cross-references use canonical ownership, infrastructure implementation authority is not duplicated here, and the V1.1 audit gate in document 18 is satisfied.
