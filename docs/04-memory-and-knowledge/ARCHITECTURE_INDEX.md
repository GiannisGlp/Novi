# 04 — Memory and Knowledge Architecture Index

**Status:** CLEANUP / CONSOLIDATION IN PROGRESS  
**Authority rule:** Only documents explicitly marked **CANONICAL** define the current architecture. Older documents remain available until their content has been reviewed, merged, or superseded.

## Purpose

This index is the navigation and authority layer for the Memory and Knowledge documentation set. The directory currently contains multiple generations of documents covering overlapping concerns. This file prevents accidental use of an older document while consolidation is underway.

## Current canonical spine

The most recent integration/audit series is the primary architectural source for the consolidated design:

| Authority | Current file | Role |
|---|---|---|
| CANONICAL | `95_MEMORY_KNOWLEDGE_MEMORY_ARCHITECTURE_INTEGRATION_AND_REFERENCE_MODEL.md` | Integrated reference architecture and system-wide relationships |
| CANONICAL | `96_MEMORY_KNOWLEDGE_ARCHITECTURE_AUDIT_TRACEABILITY_AND_GAP_REGISTER.md` | Audit, traceability, coverage and remaining gaps |
| CANONICAL | `97_MEMORY_KNOWLEDGE_IDENTITY_AND_ENTITY_RESOLUTION_ARCHITECTURE.md` | Identity and entity resolution |
| CANONICAL | `98_MEMORY_KNOWLEDGE_TEMPORAL_REASONING_AND_TEMPORAL_MEMORY_ARCHITECTURE.md` | Temporal reasoning and temporal memory |
| CANONICAL | `99_MEMORY_KNOWLEDGE_SPATIAL_MEMORY_AND_SPATIAL_STATE_ARCHITECTURE.md` | Spatial memory and spatial state |
| CANONICAL | `100_MEMORY_KNOWLEDGE_CAUSAL_WORLD_MODELING_AND_CAUSAL_MEMORY_ARCHITECTURE.md` | Causal memory and world modelling |
| CANONICAL | `101_MEMORY_KNOWLEDGE_CROSS_MODAL_MEMORY_ARCHITECTURE.md` | Cross-modal memory |
| CANONICAL | `102_MEMORY_KNOWLEDGE_SKILL_AND_COMPETENCE_VERIFICATION_ARCHITECTURE.md` | Skill and competence memory/verification |
| CANONICAL | `103_MEMORY_KNOWLEDGE_SCHEMA_MIGRATION_COMPATIBILITY_AND_EVOLUTION_ARCHITECTURE.md` | Schema migration, compatibility and evolution |
| CANONICAL | `104_MEMORY_KNOWLEDGE_MODEL_MEMORY_CO_EVOLUTION_ARCHITECTURE.md` | Co-evolution of the knowledge model and memory system |
| CANONICAL | `105_MACHINE_VERIFIABLE_GOVERNANCE_AND_POLICY_ENGINE_ARCHITECTURE.md` | Machine-verifiable governance and policy |
| CANONICAL | `106_MEMORY_KNOWLEDGE_HUMAN_OVERSIGHT_INTERVENTION_ACCOUNTABILITY_AND_GOVERNANCE_ARCHITECTURE.md` | Human oversight, intervention, accountability and governance |

## Foundational documents retained for consolidation

These earlier documents contain detailed subsystem material and should **not** be deleted merely because newer architecture documents exist. They are source material for the consolidation pass.

- `00_HIGH_LEVEL_MEMORY_ARCHITECTURE.md` — foundational overview
- `01_MEMORY_TAXONOMY.md` — memory taxonomy
- `02_MEMORY_LIFECYCLE.md` — lifecycle foundation
- `03_MEMORY_WRITE_AND_ADMISSION_POLICY.md` — admission/write policy
- `04_MEMORY_CONSOLIDATION_AND_FORGETTING.md` — consolidation and forgetting
- `05_MEMORY_RETRIEVAL_AND_RANKING.md` — retrieval/ranking foundation
- `06_MEMORY_PROVENANCE_AND_TRUST.md` — provenance/trust foundation
- `07_MEMORY_SCHEMA_AND_STORAGE.md` — schema/storage foundation
- `08_MEMORY_INDEXING_AND_EMBEDDINGS.md` — indexing/embedding foundation
- `09_MEMORY_KNOWLEDGE_GRAPH_AND_RELATIONSHIPS.md` — graph/relationship foundation

## Known overlap clusters

The following clusters require consolidation rather than parallel authority:

### Lifecycle / state
- `02_MEMORY_LIFECYCLE.md`
- `29_MEMORY_LIFECYCLE_AND_STATE_TRANSITIONS.md`

### Schema evolution
- `07_MEMORY_SCHEMA_AND_STORAGE.md`
- `10_MEMORY_SCHEMA_EVOLUTION_AND_DYNAMIC_DATA.md`
- `103_MEMORY_KNOWLEDGE_SCHEMA_MIGRATION_COMPATIBILITY_AND_EVOLUTION_ARCHITECTURE.md`

### Provenance / evidence / trust
- `06_MEMORY_PROVENANCE_AND_TRUST.md`
- `18_MEMORY_SENSOR_GROUNDING_AND_MEASUREMENT_PROVENANCE.md`
- `51_MEMORY_KNOWLEDGE_PROVENANCE_AND_LINEAGE.md`
- `52_MEMORY_KNOWLEDGE_CONFIDENCE_AND_UNCERTAINTY_MODEL.md`
- `54_MEMORY_KNOWLEDGE_SOURCE_RELIABILITY_AND_TRUST_MODEL.md`
- `74_MEMORY_KNOWLEDGE_PROVENANCE_LINEAGE_AND_EVIDENCE_GRAPH.md`
- `75_MEMORY_KNOWLEDGE_EVIDENCE_QUALITY_CONFIDENCE_AND_UNCERTAINTY.md`
- `92_MEMORY_KNOWLEDGE_MEMORY_PROVENANCE_LINEAGE_AND_TRACEABILITY_ENGINE.md`

### Consolidation / reconsolidation
- `04_MEMORY_CONSOLIDATION_AND_FORGETTING.md`
- `77_MEMORY_KNOWLEDGE_MEMORY_RECONSOLIDATION_AND_BELIEF_REVISION.md`
- `78_MEMORY_KNOWLEDGE_MEMORY_CONSOLIDATION_AND_ABSTRACTION.md`
- `89_MEMORY_KNOWLEDGE_MEMORY_CONSOLIDATION_AND_RECONSOLIDATION_ENGINE.md`

### Retrieval / context
- `05_MEMORY_RETRIEVAL_AND_RANKING.md`
- `35_MEMORY_ATTENTION_AND_RELEVANCE_MODEL.md`
- `36_MEMORY_CONTEXT_ASSEMBLY_AND_COGNITIVE_WORKSPACE.md`
- `56_MEMORY_KNOWLEDGE_QUERY_SEMANTICS_AND_CONTEXT_RESOLUTION.md`
- `57_MEMORY_KNOWLEDGE_QUERY_PLANNING_AND_EXECUTION.md`
- `80_MEMORY_KNOWLEDGE_RETRIEVAL_CONTEXTUAL_REASONING_AND_MEMORY_RECALL.md`
- `90_MEMORY_KNOWLEDGE_MEMORY_RETRIEVAL_RANKING_AND_CONTEXT_ASSEMBLY_ENGINE.md`

### Conflict / belief revision
- `20_MEMORY_CONFLICT_RESOLUTION_AND_DISTRIBUTED_STATE.md`
- `50_MEMORY_KNOWLEDGE_CONFLICTS_AND_BELIEF_REVISION.md`
- `72_MEMORY_KNOWLEDGE_CONFLICT_RESOLUTION_AND_CONSISTENCY_POLICIES.md`
- `91_MEMORY_KNOWLEDGE_EVIDENCE_FUSION_CONFLICT_RESOLUTION_AND_BELIEF_ARBITRATION.md`

### Spatial / temporal
- `23_MEMORY_SPATIAL_MEMORY_AND_PLACE_HISTORY.md`
- `43_MEMORY_SPATIAL_WORLD_MODEL_AND_PLACE_MEMORY.md`
- `44_MEMORY_SPATIAL_TEMPORAL_REASONING_AND_TRAJECTORY_MEMORY.md`
- `98_MEMORY_KNOWLEDGE_TEMPORAL_REASONING_AND_TEMPORAL_MEMORY_ARCHITECTURE.md`
- `99_MEMORY_KNOWLEDGE_SPATIAL_MEMORY_AND_SPATIAL_STATE_ARCHITECTURE.md`

### Multimodal / sensor grounding
- `18_MEMORY_SENSOR_GROUNDING_AND_MEASUREMENT_PROVENANCE.md`
- `42_MEMORY_MULTIMODAL_GROUNDING_AND_SENSOR_FUSION.md`
- `69_MEMORY_KNOWLEDGE_SENSOR_DATA_INGESTION_AND_FUSION.md`
- `101_MEMORY_KNOWLEDGE_CROSS_MODAL_MEMORY_ARCHITECTURE.md`

### Privacy / security / governance
- `11_MEMORY_PRIVACY_RETENTION_AND_DELETION.md`
- `25_MEMORY_SECURITY_AND_INTEGRITY.md`
- `60_MEMORY_KNOWLEDGE_SECURITY_AND_MEMORY_INTEGRITY.md`
- `61_MEMORY_KNOWLEDGE_PRIVACY_AND_PERSONAL_DATA_BOUNDARIES.md`
- `62_MEMORY_KNOWLEDGE_ACCESS_CONTROL_AND_AUTHORIZATION.md`
- `63_MEMORY_KNOWLEDGE_SECURE_DELETION_AND_CRYPTOGRAPHIC_ERASURE.md`
- `64_MEMORY_KNOWLEDGE_DATA_LIFECYCLE_AND_INFORMATION_GOVERNANCE.md`
- `88_MEMORY_KNOWLEDGE_MEMORY_PRIVACY_ACCESS_CONTROL_AND_DATA_GOVERNANCE.md`
- `94_MEMORY_KNOWLEDGE_MEMORY_SECURITY_THREAT_MODEL_AND_ADVERSARIAL_DEFENSE.md`
- `105_MACHINE_VERIFIABLE_GOVERNANCE_AND_POLICY_ENGINE_ARCHITECTURE.md`
- `106_MEMORY_KNOWLEDGE_HUMAN_OVERSIGHT_INTERVENTION_ACCOUNTABILITY_AND_GOVERNANCE_ARCHITECTURE.md`

## Gaps and anomalies

- Numeric sequence has gaps at `24` and `65`. These are treated as **unassigned numbers**, not missing architecture requirements, until the historical commit context is reviewed.
- The directory has a very large number of documents with overlapping scopes. Filename numbering alone must no longer be treated as authority.
- The README's previous 00–20 detailed-document list is obsolete and must not be used as the architecture index.

## Consolidation rules

1. Preserve all useful technical content until reviewed.
2. Do not delete a document solely because a newer document has a similar name.
3. When content is merged, record the source document in the canonical document's consolidation notes.
4. Once a document is fully superseded, mark it **SUPERSEDED** and remove it from the active architecture navigation.
5. Canonical documents must avoid conflicting normative requirements with other canonical documents.
6. Architecture documents should describe stable contracts and decisions; research notes and implementation experiments should not silently become normative architecture.
7. The final directory should have a small, coherent canonical set rather than one document per incremental thought.

## Cleanup phases

### Phase 1 — Authority and navigation
- [x] Establish this index.
- [ ] Replace the stale README document list.
- [ ] Record canonical vs source-material status for every document.

### Phase 2 — Content consolidation
- [ ] Review every overlap cluster.
- [ ] Merge unique material into canonical documents.
- [ ] Resolve contradictory requirements.
- [ ] Record traceability from old documents to canonical destinations.

### Phase 3 — Naming and structure
- [ ] Adopt short, stable canonical filenames.
- [ ] Remove obsolete numeric-generation naming from active documents.
- [ ] Preserve Git history for renamed/superseded documents.

### Phase 4 — Finalization
- [ ] Reduce the active architecture set to the minimum complete set.
- [ ] Update all cross-document references.
- [ ] Update README.
- [ ] Re-run architecture audit and close remaining gaps.
- [ ] Only then continue to the next numbered architecture task.
