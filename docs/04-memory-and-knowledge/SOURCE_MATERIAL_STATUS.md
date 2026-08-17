# 04 — Memory and Knowledge Source Material Status Registry

**Status:** CANONICAL SOURCE DISPOSITION REGISTRY
**Date:** 2026-08-17

This registry defines how Memory and Knowledge documents are treated. `CANONICAL` means current normative authority. `MERGE` identifies material incorporated into a canonical destination. `MOVE` identifies implementation material belonging elsewhere. `REFERENCE` identifies research/background material. `HISTORICAL` identifies preserved non-normative material.

## Current normative spine

The only active semantic architecture authority is:

- `01_MEMORY_TAXONOMY_AND_CORE_MODEL.md`
- `02_MEMORY_LIFECYCLE_AND_ADMISSION.md`
- `03_PROVENANCE_EVIDENCE_TRUST_AND_UNCERTAINTY.md`
- `04_MEMORY_CONSOLIDATION_RETRIEVAL_AND_CONTEXT.md`
- `05_KNOWLEDGE_GRAPH_RELATIONSHIPS_AND_BELIEF_REVISION.md`
- `06_IDENTITY_AND_ENTITY_RESOLUTION.md`
- `07_TEMPORAL_MEMORY_AND_REASONING.md`
- `08_SPATIAL_MEMORY_AND_STATE.md`
- `09_CAUSAL_WORLD_MODELING.md`
- `10_CROSS_MODAL_MEMORY.md`
- `11_SKILL_AND_COMPETENCE_VERIFICATION.md`
- `12_MEMORY_SCHEMA_AND_KNOWLEDGE_EVOLUTION.md`
- `13_MODEL_AND_MEMORY_CO_EVOLUTION.md`
- `14_PRIVACY_AND_MEMORY_DATA_GOVERNANCE.md`
- `15_MACHINE_GOVERNANCE_INTERFACE.md`
- `16_HUMAN_OVERSIGHT_AND_ACCOUNTABILITY.md`
- `17_INTEGRATION_AND_REFERENCE_MODEL.md`
- `18_FINAL_ARCHITECTURE_AUDIT_AND_TRACEABILITY.md`

## Transitional 95–106 disposition

The former 95–106 transitional authorities have been moved to:

`archive/transitional-95-106/`

They are preserved unchanged for provenance and recovery, but are **NON-NORMATIVE**. Their semantic authority has been consolidated into 01–18.

## Historical 00–94

The historical 00–94 corpus is preserved under:

`archive/`

It is **NON-NORMATIVE**.

Previously established mappings remain valid where recorded in `SOURCE_TRACEABILITY_MATRIX.md`. Files that still require deeper section-level review remain historical/pending rather than being falsely labelled fully superseded.

## Source inventory gaps

The following numeric source identifiers are not present in the repository inventory examined during consolidation:

| Identifier | Status | Decision |
|---|---|---|
| `24` | GAP | No source file found; do not invent one |
| `65` | GAP | No source file found; do not invent one |

These are inventory gaps, not missing canonical architecture documents.

## Infrastructure boundary

The following are not semantic Memory & Knowledge implementation authority:

- physical SQLite/schema mechanics;
- transaction implementation;
- replication transport;
- recovery implementation;
- vector/FTS implementation;
- runtime scheduling;
- observability implementation.

Their semantic requirements may be referenced from Memory & Knowledge, while implementation authority belongs to the appropriate system architecture.

## Supersession rule

Historical files must not be deleted merely because a canonical destination exists. A source may be marked fully `SUPERSEDED` only after its unique requirements, contradictions and cross-references have been verified. Until then, preservation under `archive/` is the safe state.
