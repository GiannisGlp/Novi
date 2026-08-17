# 04 — Memory and Knowledge Source Material Status Registry

**Status:** CANONICAL CONSOLIDATION REGISTRY
**Date:** 2026-08-17

This registry defines how historical Memory and Knowledge documents are treated during consolidation. `CANONICAL` means normative authority. `SOURCE` means useful material that is not independently authoritative. `MERGE` identifies content that must be extracted into a canonical destination. `MOVE` identifies implementation material that belongs outside semantic memory architecture. `REFERENCE` identifies research/background material.

## Current normative spine

- `95_MEMORY_KNOWLEDGE_MEMORY_ARCHITECTURE_INTEGRATION_AND_REFERENCE_MODEL.md` — CANONICAL
- `96_MEMORY_KNOWLEDGE_ARCHITECTURE_AUDIT_TRACEABILITY_AND_GAP_REGISTER.md` — CANONICAL
- `97_MEMORY_KNOWLEDGE_IDENTITY_AND_ENTITY_RESOLUTION_ARCHITECTURE.md` — CANONICAL
- `98_MEMORY_KNOWLEDGE_TEMPORAL_REASONING_AND_TEMPORAL_MEMORY_ARCHITECTURE.md` — CANONICAL
- `99_MEMORY_KNOWLEDGE_SPATIAL_MEMORY_AND_SPATIAL_STATE_ARCHITECTURE.md` — CANONICAL
- `100_MEMORY_KNOWLEDGE_CAUSAL_WORLD_MODELING_AND_CAUSAL_MEMORY_ARCHITECTURE.md` — CANONICAL
- `101_MEMORY_KNOWLEDGE_CROSS_MODAL_MEMORY_ARCHITECTURE.md` — CANONICAL
- `102_MEMORY_KNOWLEDGE_SKILL_AND_COMPETENCE_VERIFICATION_ARCHITECTURE.md` — CANONICAL
- `103_MEMORY_KNOWLEDGE_SCHEMA_MIGRATION_COMPATIBILITY_AND_EVOLUTION_ARCHITECTURE.md` — CANONICAL
- `104_MEMORY_KNOWLEDGE_MODEL_MEMORY_CO_EVOLUTION_ARCHITECTURE.md` — CANONICAL
- `105_MACHINE_VERIFIABLE_GOVERNANCE_AND_POLICY_ENGINE_ARCHITECTURE.md` — CANONICAL
- `106_MEMORY_KNOWLEDGE_HUMAN_OVERSIGHT_INTERVENTION_ACCOUNTABILITY_AND_GOVERNANCE_ARCHITECTURE.md` — CANONICAL

## Foundational 00–10

| Source | Status | Destination |
|---|---|---|
| `00_HIGH_LEVEL_MEMORY_ARCHITECTURE.md` | FOUNDATIONAL / MERGE | 17 Integration + README |
| `01_MEMORY_TAXONOMY.md` | FOUNDATIONAL / MERGE | 01 Core Model |
| `02_MEMORY_LIFECYCLE.md` | MERGE | 02 Lifecycle |
| `03_MEMORY_WRITE_AND_ADMISSION_POLICY.md` | MERGE | 02 Lifecycle + 03 Provenance/Governance |
| `04_MEMORY_CONSOLIDATION_AND_FORGETTING.md` | MERGE | 04 Consolidation + 14 Privacy |
| `05_MEMORY_RETRIEVAL_AND_RANKING.md` | MERGE | 04 Retrieval/Context |
| `06_MEMORY_PROVENANCE_AND_TRUST.md` | HIGH-VALUE SOURCE / MERGE | 03 Provenance/Evidence/Trust |
| `07_MEMORY_SCHEMA_AND_STORAGE.md` | MERGE / MOVE | 12 Schema semantics; physical storage → system architecture |
| `08_MEMORY_INDEXING_AND_EMBEDDINGS.md` | MERGE / MOVE | 04 Retrieval semantics; physical indexes → system architecture |
| `09_MEMORY_KNOWLEDGE_GRAPH_AND_RELATIONSHIPS.md` | MERGE | 05 Knowledge Graph/Relationships |
| `10_MEMORY_SCHEMA_EVOLUTION_AND_DYNAMIC_DATA.md` | HIGH-VALUE SOURCE / MERGE | 12 Schema Evolution; protected governance → 15 |

## High-overlap generations

### Lifecycle

`29_MEMORY_LIFECYCLE_AND_STATE_TRANSITIONS.md` → MERGE into 02.

Preserve explicit states, promotion/demotion, retention, deletion, idempotency and audit behavior.

### Provenance / evidence / trust

Merge:

- `18_MEMORY_SENSOR_GROUNDING_AND_MEASUREMENT_PROVENANCE.md`
- `51_MEMORY_KNOWLEDGE_PROVENANCE_AND_LINEAGE.md`
- `52_MEMORY_KNOWLEDGE_CONFIDENCE_AND_UNCERTAINTY_MODEL.md`
- `54_MEMORY_KNOWLEDGE_SOURCE_RELIABILITY_AND_TRUST_MODEL.md`
- `74_MEMORY_KNOWLEDGE_PROVENANCE_LINEAGE_AND_EVIDENCE_GRAPH.md`
- `75_MEMORY_KNOWLEDGE_EVIDENCE_QUALITY_CONFIDENCE_AND_UNCERTAINTY.md`
- `92_MEMORY_KNOWLEDGE_MEMORY_PROVENANCE_LINEAGE_AND_TRACEABILITY_ENGINE.md`

Destination: 03.

Required invariant:

`PROVENANCE ≠ CONFIDENCE ≠ VERIFICATION ≠ AUTHORIZATION`.

### Consolidation / reconsolidation

Merge:

- `77_MEMORY_KNOWLEDGE_MEMORY_RECONSOLIDATION_AND_BELIEF_REVISION.md`
- `78_MEMORY_KNOWLEDGE_MEMORY_CONSOLIDATION_AND_ABSTRACTION.md`
- `89_MEMORY_KNOWLEDGE_MEMORY_CONSOLIDATION_AND_RECONSOLIDATION_ENGINE.md`

with `04_MEMORY_CONSOLIDATION_AND_FORGETTING.md`.

Destination: 04.

Preserve source independence, counterexamples, versioned interpretation, deletion-aware consolidation, privacy-aware abstraction, rebuildability and idempotency.

### Retrieval / context

Merge:

- `35_MEMORY_ATTENTION_AND_RELEVANCE_MODEL.md`
- `36_MEMORY_CONTEXT_ASSEMBLY_AND_COGNITIVE_WORKSPACE.md`
- `56_MEMORY_KNOWLEDGE_QUERY_SEMANTICS_AND_CONTEXT_RESOLUTION.md`
- `57_MEMORY_KNOWLEDGE_QUERY_PLANNING_AND_EXECUTION.md`
- `80_MEMORY_KNOWLEDGE_RETRIEVAL_CONTEXTUAL_REASONING_AND_MEMORY_RECALL.md`
- `90_MEMORY_KNOWLEDGE_MEMORY_RETRIEVAL_RANKING_AND_CONTEXT_ASSEMBLY_ENGINE.md`

with `05_MEMORY_RETRIEVAL_AND_RANKING.md`.

Destination: 04.

### Conflict / belief revision

Merge:

- `20_MEMORY_CONFLICT_RESOLUTION_AND_DISTRIBUTED_STATE.md`
- `50_MEMORY_KNOWLEDGE_CONFLICTS_AND_BELIEF_REVISION.md`
- `72_MEMORY_KNOWLEDGE_CONFLICT_RESOLUTION_AND_CONSISTENCY_POLICIES.md`
- `91_MEMORY_KNOWLEDGE_EVIDENCE_FUSION_CONFLICT_RESOLUTION_AND_BELIEF_ARBITRATION.md`

Destination: 05.

Semantic conflict belongs in memory/knowledge. Distributed concurrency belongs in system architecture. Authorization conflicts belong in 15. Human governance disputes belong in 16.

### Temporal / spatial

Merge:

- `23_MEMORY_SPATIAL_MEMORY_AND_PLACE_HISTORY.md`
- `43_MEMORY_SPATIAL_WORLD_MODEL_AND_PLACE_MEMORY.md`
- `44_MEMORY_SPATIAL_TEMPORAL_REASONING_AND_TRAJECTORY_MEMORY.md`

into 07/08 respectively. 98 and 99 remain the current canonical authorities until the final rename pass.

### Cross-modal / sensor grounding

Merge:

- `42_MEMORY_MULTIMODAL_GROUNDING_AND_SENSOR_FUSION.md`
- `69_MEMORY_KNOWLEDGE_SENSOR_DATA_INGESTION_AND_FUSION.md`

into 10. 101 remains canonical until final rename.

### Privacy / security / governance

Merge or move:

- `11_MEMORY_PRIVACY_RETENTION_AND_DELETION.md` → 14
- `25_MEMORY_SECURITY_AND_INTEGRITY.md` → system security where infrastructure-specific
- `60_MEMORY_KNOWLEDGE_SECURITY_AND_MEMORY_INTEGRITY.md` → 14/system security by scope
- `61_MEMORY_KNOWLEDGE_PRIVACY_AND_PERSONAL_DATA_BOUNDARIES.md` → 14
- `62_MEMORY_KNOWLEDGE_ACCESS_CONTROL_AND_AUTHORIZATION.md` → 15
- `63_MEMORY_KNOWLEDGE_SECURE_DELETION_AND_CRYPTOGRAPHIC_ERASURE.md` → 14/system security by scope
- `64_MEMORY_KNOWLEDGE_DATA_LIFECYCLE_AND_INFORMATION_GOVERNANCE.md` → 14
- `88_MEMORY_KNOWLEDGE_MEMORY_PRIVACY_ACCESS_CONTROL_AND_DATA_GOVERNANCE.md` → 14/15
- `94_MEMORY_KNOWLEDGE_MEMORY_SECURITY_THREAT_MODEL_AND_ADVERSARIAL_DEFENSE.md` → system security + 15 where policy semantics apply

105 and 106 remain canonical governance authorities.

## Canonical boundary with system architecture

The following must not remain as competing semantic memory authority:

- SQLite/physical schema mechanics
- transaction implementation
- replication transport
- recovery implementation
- vector database implementation
- FTS implementation
- runtime scheduling
- observability implementation

Their semantic requirements remain referenced from Memory and Knowledge, but their implementation authority belongs in the system architecture.

## Supersession rule

No source document may be deleted or marked `SUPERSEDED` until:

1. its unique requirements are extracted;
2. the destination document is identified;
3. contradictions are resolved;
4. source-to-destination traceability is recorded;
5. cross-references are updated;
6. the final canonical document contains the required material.

Until then, historical documents remain present but are **not normative**.
