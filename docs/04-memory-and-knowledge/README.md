# 04 — Memory and Knowledge

## Status

**CONSOLIDATION ACTIVE — CANONICAL TRANSITION IN PROGRESS**

This directory contains the Memory and Knowledge architecture for Novi. It contains multiple historical generations of detailed design. The repository now has an explicit consolidation target and source-material registry so older material cannot accidentally become parallel authority.

## Start here

1. `ARCHITECTURE_INDEX.md` — authority and navigation.
2. `CONSOLIDATION_TARGET_ARCHITECTURE.md` — target canonical architecture and responsibility boundaries.
3. `SOURCE_MATERIAL_STATUS.md` — source-to-destination consolidation registry.
4. `95_MEMORY_KNOWLEDGE_MEMORY_ARCHITECTURE_INTEGRATION_AND_REFERENCE_MODEL.md` — current normative integration model.
5. `96_MEMORY_KNOWLEDGE_ARCHITECTURE_AUDIT_TRACEABILITY_AND_GAP_REGISTER.md` — architecture audit and gap register.
6. `97`–`106` — current canonical specialist architecture.
7. `ARCHITECTURE_CONTENT_AUDIT.md` — detailed audit performed before consolidation.

## Authority rule

Until the final rename/consolidation pass is complete:

```text
95–106 = NORMATIVE CANONICAL SPINE
CONSOLIDATION_TARGET_ARCHITECTURE.md = CANONICAL TRANSITION TARGET
SOURCE_MATERIAL_STATUS.md = CANONICAL STATUS / TRACEABILITY REGISTRY
00–94 = SOURCE / HISTORICAL MATERIAL, NOT AUTOMATICALLY AUTHORITATIVE
```

## Core principle

> Experience is not automatically memory, memory is not automatically knowledge, and knowledge is not automatically truth.

The architecture must preserve:

```text
observation ≠ evidence ≠ memory ≠ knowledge ≠ belief
retrieval ≠ truth
confidence ≠ provenance
verification ≠ confidence
trust ≠ authorization
historical state ≠ current authoritative state
model output ≠ independent evidence
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
minimum sufficient context
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

## Memory classes

Novi distinguishes working, session/conversation, episodic, semantic, procedural, prospective, relationship, spatial, temporal, preference and operational memory. These are complementary and must not be collapsed into one generic record type.

## Logical vs physical architecture

Memory semantics must remain independent of physical implementation. SQLite, files, vector indexes, FTS, graph storage, transactions, replication, recovery, scheduling and observability are implementation concerns owned by the appropriate system architecture. Memory documents define the contracts those systems must satisfy.

## Local-first requirement

The production robot should remain useful without cloud memory services. External memory infrastructure requires explicit rationale, privacy/data-flow assessment, local fallback where practical and a migration path.

## Consolidation policy

Consolidation is deliberately non-destructive:

```text
historical documents
      ↓
classification
      ↓
unique-content extraction
      ↓
canonical merge
      ↓
contradiction resolution
      ↓
traceability
      ↓
supersession / move
      ↓
final audit
```

Git history remains the recovery mechanism for renamed or superseded documents.

## Completion criteria

This directory is clean only when:

1. every document has an explicit status;
2. every substantive topic has one canonical home;
3. contradictory requirements are resolved;
4. source-to-destination traceability exists;
5. cross-references use canonical names;
6. obsolete documents are marked `SUPERSEDED` or moved;
7. the README exposes only canonical authority;
8. the final architecture audit has no unresolved documentation-structure gaps.
