# 04 — Memory and Knowledge Consolidation Target Architecture

**Status:** CANONICAL TRANSITIONAL TARGET
**Authority:** This document defines the target structure and boundaries for the consolidation of the existing Memory and Knowledge architecture. The existing 95–106 documents remain normative until their content is explicitly merged into the final named set.

## Purpose

This document turns the 2026-08-17 audit into an executable consolidation target. It prevents the repository from replacing one generation of overlapping documents with another generation of overlapping documents.

## Canonical principles

Novi memory is a governed, evidence-linked state system. Preserve these distinctions:

```text
observation ≠ evidence ≠ memory ≠ knowledge ≠ belief
retrieval ≠ truth
confidence ≠ provenance
verification ≠ confidence
trust ≠ authorization
historical state ≠ current authoritative state
model output ≠ independent evidence
derived data ≠ source evidence
skill success ≠ general competence
schema change ≠ ordinary learning
intention ≠ action ≠ completion
```

## Canonical processing pipeline

```text
world / user / tools / agents
        ↓
observation / input
        ↓
identity + integrity + privacy gate
        ↓
evidence registration
        ↓
episode / candidate memory
        ↓
validation + deduplication
        ↓
consolidation / abstraction
        ↓
semantic / procedural / prospective knowledge
        ↓
relationship + provenance graph
        ↓
retrieval / ranking
        ↓
evidence arbitration
        ↓
minimum sufficient context
        ↓
reasoning
        ↓
current authorization + current safety
        ↓
action
        ↓
observed outcome
        ↓
evaluation / revision
```

## Target canonical documents

The final active semantic architecture should converge on these documents:

1. `01_MEMORY_TAXONOMY_AND_CORE_MODEL.md`
2. `02_MEMORY_LIFECYCLE_AND_ADMISSION.md`
3. `03_PROVENANCE_EVIDENCE_TRUST_AND_UNCERTAINTY.md`
4. `04_MEMORY_CONSOLIDATION_RETRIEVAL_AND_CONTEXT.md`
5. `05_KNOWLEDGE_GRAPH_RELATIONSHIPS_AND_BELIEF_REVISION.md`
6. `06_IDENTITY_AND_ENTITY_RESOLUTION.md`
7. `07_TEMPORAL_MEMORY_AND_REASONING.md`
8. `08_SPATIAL_MEMORY_AND_STATE.md`
9. `09_CAUSAL_WORLD_MODELING.md`
10. `10_CROSS_MODAL_MEMORY.md`
11. `11_SKILL_AND_COMPETENCE_VERIFICATION.md`
12. `12_SCHEMA_AND_KNOWLEDGE_EVOLUTION.md`
13. `13_MODEL_MEMORY_CO_EVOLUTION.md`
14. `14_PRIVACY_AND_MEMORY_DATA_GOVERNANCE.md`
15. `15_MACHINE_GOVERNANCE_INTERFACE.md`
16. `16_HUMAN_OVERSIGHT_AND_ACCOUNTABILITY.md`
17. `17_INTEGRATION_AND_REFERENCE_MODEL.md`
18. `18_ARCHITECTURE_AUDIT_AND_TRACEABILITY.md`

These are the **target names**. Do not delete the old files until their content has been extracted and traceability recorded.

## Responsibility boundaries

### Semantic memory architecture
Owns memory meaning, lifecycle, evidence, provenance, epistemic state, retrieval semantics, consolidation, relationships, temporal/spatial/causal semantics and governance contracts.

### System architecture
Owns physical storage engines, database mechanics, transactions, replication, recovery, runtime scheduling, observability and infrastructure implementation.

### Governance
`105` remains the machine-verifiable policy authority. `106` remains the human oversight authority. Memory must not create a competing authorization root.

### Current state
Current authoritative perception, device state, authorization and safety conditions override historical memory where current truth is required.

## Consolidation rules

1. Preserve unique technical requirements from every source document.
2. Merge by semantic ownership, not filename similarity.
3. Keep provenance from source document to destination section.
4. Resolve conflicting normative requirements before marking a source superseded.
5. Separate research findings from architecture requirements.
6. Separate semantic contracts from implementation mechanics.
7. Do not promote generated derivatives into independent evidence.
8. Do not let retrieval ranking become a truth or authorization mechanism.
9. Preserve historical records while revising interpretations.
10. Make deletion dependency-aware and verifiable.
11. Make every important state machine canonical rather than locally redefined.
12. Preserve Git history for every superseded or renamed document.

## High-value material that must survive

### Provenance / trust
Preserve source classes, evidence/claim/belief separation, integrity hashes, temporal provenance, domain-scoped reliability, verification states, evidence independence, model-version provenance and derived-memory lineage.

### Consolidation / reconsolidation
Preserve source independence, counterexamples, versioned interpretations, deletion-aware consolidation, privacy-aware abstraction, rebuildability, idempotency and the distinction between retrieval and reconsolidation.

### Schema evolution
Preserve protected-core boundaries, existing-schema-first rules, schema proposals, deterministic validation, migration isolation, quotas, churn protection, rollback, data preservation and model-generated proposal separation.

### Retrieval
Preserve exact, lexical, semantic, temporal, graph and episodic retrieval paths; authorization/privacy filtering; evidence-quality checks; conflict handling; provenance; freshness; and minimum-sufficient context assembly.

### Spatial / temporal / multimodal
Preserve uncertainty, temporal validity, trajectory/place history, map versions, modality-specific provenance, calibration, timestamping and common-source dependence.

## Required canonical state concepts

The final architecture must define one shared vocabulary for:

```text
MemoryIdentity
MemoryLifecycleState
EvidenceStatus
EpistemicStatus
VerificationStatus
AccessDecision
RetentionClass
DeletionState
ProvenanceRecord
ConflictState
RetrievalResult
ContextPackage
SkillConfidence
IntentionState
EvaluationResult
SecurityState
```

No subsystem document may silently introduce a competing definition.

## Required implementation gate

A memory component is not implementation-ready until it documents:

1. owned data;
2. consumed data;
3. produced data;
4. authoritative vs derived state;
5. provenance chain;
6. access controls;
7. retention/deletion behavior;
8. failure states;
9. security threats;
10. evaluation metrics;
11. current-state override rules;
12. dependency on the integration model.

## Completion gate

Consolidation is complete only when:

- every source document has an explicit status;
- every substantive topic has one canonical home;
- contradictions are resolved;
- source-to-destination traceability exists;
- cross-references use canonical names;
- obsolete documents are marked `SUPERSEDED` or moved;
- the README exposes only the canonical architecture as active authority;
- the final audit reports no unresolved documentation-structure gaps.
