# Source Traceability Matrix

**Status:** Active working artifact  
**Authority:** `ARCHITECTURE_INDEX.md`  
**Scope:** Historical and transitional Memory & Knowledge source corpus mapped to canonical 01–18 architecture.

## Purpose

This matrix records where requirements from earlier Memory & Knowledge documents live in the current canonical architecture. It is a migration-control artifact, not an additional architecture specification.

A source may only be marked `SUPERSEDED` after its unique requirements have been extracted, mapped to a canonical destination, checked for contradictions, and its cross-references reviewed.

## Disposition vocabulary

- **MERGED** — substantive requirements incorporated into a canonical document.
- **SUPERSEDED** — replaced by canonical material with no remaining unique normative content.
- **REFERENCE** — retained because it contains useful background or research, but is not normative.
- **MOVED** — material belongs to another architecture directory.
- **HISTORICAL** — preserved for architectural provenance; no current implementation authority.
- **GAP** — a requirement has no satisfactory canonical destination yet.
- **PENDING** — not yet reviewed at sufficient depth.

## Canonical authority map

| Canonical | Authority | Primary responsibility |
|---|---|---|
| 01 | `01_MEMORY_TAXONOMY_AND_CORE_MODEL.md` | Memory ontology, classes, identity of memory objects, core invariants |
| 02 | `02_MEMORY_LIFECYCLE_AND_ADMISSION.md` | Admission, lifecycle, write/update/retirement semantics |
| 03 | `03_PROVENANCE_EVIDENCE_TRUST_AND_UNCERTAINTY.md` | Provenance, evidence, trust, uncertainty, verification |
| 04 | `04_MEMORY_CONSOLIDATION_RETRIEVAL_AND_CONTEXT.md` | Consolidation, retrieval, ranking, context assembly |
| 05 | `05_KNOWLEDGE_GRAPH_RELATIONSHIPS_AND_BELIEF_REVISION.md` | Relationships, claims, beliefs, semantic contradiction and revision |
| 06 | `06_IDENTITY_AND_ENTITY_RESOLUTION.md` | Entity resolution and identity semantics |
| 07 | `07_TEMPORAL_MEMORY_AND_REASONING.md` | Temporal representation and temporal reasoning |
| 08 | `08_SPATIAL_MEMORY_AND_STATE.md` | Spatial representation and spatial state |
| 09 | `09_CAUSAL_WORLD_MODELING.md` | Causal models and causal memory |
| 10 | `10_CROSS_MODAL_MEMORY.md` | Cross-modal representations and alignment |
| 11 | `11_SKILL_AND_COMPETENCE_VERIFICATION.md` | Skill memory and competence evidence |
| 12 | `12_MEMORY_SCHEMA_AND_KNOWLEDGE_EVOLUTION.md` | Schema, migration, compatibility, evolution |
| 13 | `13_MODEL_AND_MEMORY_CO_EVOLUTION.md` | Model/memory co-evolution and compatibility |
| 14 | `14_PRIVACY_AND_MEMORY_DATA_GOVERNANCE.md` | Memory privacy, retention and data governance |
| 15 | `15_MACHINE_GOVERNANCE_INTERFACE.md` | Machine-verifiable governance interface |
| 16 | `16_HUMAN_OVERSIGHT_AND_ACCOUNTABILITY.md` | Human intervention, review and accountability |
| 17 | `17_INTEGRATION_AND_REFERENCE_MODEL.md` | Cross-document integration and end-to-end reference model |
| 18 | `18_FINAL_ARCHITECTURE_AUDIT_AND_TRACEABILITY.md` | Final architecture completeness and traceability |

## Source dispositions

The table below contains the initial 00–40 mapping plus the completed 41–50 content-level review. Final supersession still requires section-level cross-reference repair.

| Source | Status | Canonical destination | Action |
|---|---|---|---|
| `00_HIGH_LEVEL_MEMORY_ARCHITECTURE.md` | MERGED | 01, 17 | Verify high-level invariants |
| `01_MEMORY_TAXONOMY.md` | MERGED | 01 | Verify terminology |
| `02_MEMORY_LIFECYCLE.md` | MERGED | 02 | Verify lifecycle states |
| `03_MEMORY_WRITE_AND_ADMISSION_POLICY.md` | MERGED | 02, 15 | Separate admission from governance |
| `04_MEMORY_CONSOLIDATION_AND_FORGETTING.md` | MERGED | 02, 04, 14 | Verify forgetting/privacy boundary |
| `05_MEMORY_RETRIEVAL_AND_RANKING.md` | MERGED | 04 | Verify retrieval requirements |
| `06_MEMORY_PROVENANCE_AND_TRUST.md` | MERGED | 03 | Verify evidence independence and provenance |
| `07_MEMORY_SCHEMA_AND_STORAGE.md` | SPLIT / MOVED | 12 + system architecture | Keep semantic schema; move physical storage |
| `08_MEMORY_INDEXING_AND_EMBEDDINGS.md` | SPLIT / MOVED | 04 + system architecture | Keep semantic retrieval; move index infrastructure |
| `09_MEMORY_KNOWLEDGE_GRAPH_AND_RELATIONSHIPS.md` | MERGED | 05 | Verify graph semantics |
| `10_MEMORY_SCHEMA_EVOLUTION_AND_DYNAMIC_DATA.md` | MERGED | 12 | Verify evolution requirements |
| `11_MEMORY_KNOWLEDGE_CONFLICT_RESOLUTION.md` | MERGED | 05, 03 | Semantic conflict vs evidence/trust |
| `12_MEMORY_SECURITY_AND_ACCESS_CONTROL.md` | SPLIT / MOVED | 14, 15 + system architecture | Keep governance; move infrastructure security |
| `13_MEMORY_PRIVACY_AND_RETENTION.md` | MERGED | 14 | Verify retention/deletion |
| `14_MEMORY_DISTRIBUTED_SYNCHRONIZATION.md` | MOVED | system architecture/109 | Distributed consistency is infrastructure |
| `15_MEMORY_CONSISTENCY_AND_CONCURRENCY.md` | MOVED | system architecture/108 | Transaction semantics are infrastructure |
| `16_MEMORY_EVENT_SOURCING_AND_REPLAY.md` | MOVED / MERGED | 02, 17 + system architecture/107/110 | Keep semantic lifecycle; move durable replay |
| `17_MEMORY_VERSIONING_AND_TEMPORAL_HISTORY.md` | MERGED | 07, 12 | Verify temporal/schema semantics |
| `18_MEMORY_DECAY_AND_FORGETTING.md` | MERGED | 02, 14 | Separate decay from privacy deletion |
| `19_MEMORY_RECONSOLIDATION.md` | MERGED | 04, 05 | Retrieval reconsolidation vs belief revision |
| `20_MEMORY_CONTEXT_ASSEMBLY.md` | MERGED | 04 | Verify context/provenance |
| `21_MEMORY_EPISODIC_ARCHITECTURE.md` | MERGED | 01, 02, 04 | Verify episodic semantics |
| `22_MEMORY_SEMANTIC_ARCHITECTURE.md` | MERGED | 01, 05 | Verify semantic/graph boundary |
| `23_MEMORY_SPATIAL_ARCHITECTURE.md` | MERGED | 08 | Verify spatial state |
| `24_MEMORY_PROCEDURAL_ARCHITECTURE.md` | MERGED | 11 | Verify skill semantics |
| `25_MEMORY_WORKING_CONTEXT_ARCHITECTURE.md` | MERGED | 04 | Verify ephemeral context boundary |
| `26_MEMORY_AUTOBIOGRAPHICAL_ARCHITECTURE.md` | MERGED | 01, 02, 05, 06 | Verify identity/self-model requirements |
| `27_MEMORY_EMOTIONAL_AFFECTIVE_ARCHITECTURE.md` | MERGED | 01, 05 | Verify affect representation |
| `28_MEMORY_SOCIAL_ARCHITECTURE.md` | MERGED | 05, 06 | Verify relationships/entities |
| `29_MEMORY_GOAL_ARCHITECTURE.md` | MERGED | 01, 11, 17 | Verify goal-memory boundary |
| `30_MEMORY_NARRATIVE_ARCHITECTURE.md` | MERGED | 04, 05 | Keep narratives derived |
| `31_MEMORY_SCHEMA_DESIGN.md` | MERGED | 12 | Verify schema requirements |
| `32_MEMORY_INDEX_DESIGN.md` | SPLIT / MOVED | 04 + system architecture | Semantic retrieval vs physical index |
| `33_MEMORY_QUERY_ARCHITECTURE.md` | MERGED | 04 | Verify query semantics |
| `34_MEMORY_CACHE_ARCHITECTURE.md` | MOVED | system architecture | Cache infrastructure |
| `35_MEMORY_OBSERVABILITY.md` | MOVED | system architecture | Runtime observability |
| `36_MEMORY_EVALUATION.md` | MERGED | 18, 03, 04 | Preserve evaluation invariants |
| `37_MEMORY_TESTING.md` | MOVED / MERGED | 18 + testing architecture | Keep semantic invariants |
| `38_MEMORY_FAILURE_MODES.md` | MOVED / MERGED | 18 + system architecture/110 | Semantic failures vs recovery |
| `39_MEMORY_BACKUP_AND_RESTORE.md` | MOVED | system architecture/110 | Infrastructure recovery |
| `40_MEMORY_AUDITABILITY.md` | MERGED | 03, 15, 16, 18 | Provenance/governance/auditability |
| `41_MEMORY_LANGUAGE_AND_SEMANTIC_UNDERSTANDING.md` | SPLIT / MOVED | 03, 04, 06, 07, 08, 10 + `03-cognition` | Keep language-as-evidence, grounding, ambiguity and admission boundaries; move primary language pipeline to cognition |
| `42_MEMORY_MULTIMODAL_GROUNDING_AND_SENSOR_FUSION.md` | SPLIT / MOVED | 03, 07, 08, 10 + system architecture | Keep multimodal evidence/alignment; move calibration/time-sync/fusion runtime |
| `43_MEMORY_SPATIAL_WORLD_MODEL_AND_PLACE_MEMORY.md` | MERGED | 08, 07, 03, 06 | Preserve layered spatial/place memory, frames, provenance and uncertainty |
| `44_MEMORY_SPATIAL_TEMPORAL_REASONING_AND_TRAJECTORY_MEMORY.md` | MERGED | 07, 08, 04, 03 | Preserve time-aware trajectories, duration and provenance |
| `45_MEMORY_ENVIRONMENTAL_CONTEXT_AND_PHYSICAL_WORLD_STATE.md` | SPLIT / MOVED | 03, 08, 10 + system architecture | Preserve environmental-state memory semantics; move sensor/runtime implementation |
| `46_MEMORY_OBJECT_AND_ENTITY_LIFECYCLE.md` | MERGED | 01, 02, 06, 03 | Preserve observation→detection→track→identity→entity lifecycle |
| `47_MEMORY_EVENT_CAUSALITY_AND_EPISODE_LINKING.md` | MERGED | 09, 04, 07, 03 | Preserve causal/temporal distinction, event links and episodic traceability |
| `48_MEMORY_COUNTERFACTUAL_REASONING_AND_CAUSAL_LEARNING.md` | MERGED | 09, 13, 04, 03 | Preserve actual/counterfactual separation and intervention provenance |
| `49_MEMORY_LEARNING_FROM_ACTION_OUTCOMES_AND_FEEDBACK.md` | MERGED | 13, 11, 02, 03, 17 | Preserve outcome/feedback evidence and controlled learning updates |
| `50_MEMORY_KNOWLEDGE_CONFLICTS_AND_BELIEF_REVISION.md` | MERGED | 05, 03, 07, 17 | Preserve evidence-vs-belief, historical/current truth and semantic revision |
| `51–94 legacy semantic series` | PENDING | 01–18 | Individual content review required |
| `95–106 transitional authorities` | TRANSITIONAL | 06–18 | Keep until their detailed requirements are fully absorbed |

## Batch verification: 41–50

**Result: content-level review completed.** The batch does not justify additional top-level Memory & Knowledge documents.

Key findings:

- **41:** Language understanding is primarily cognition. Memory-specific requirements are provenance, grounding, ambiguity preservation, identity/temporal/spatial grounding, multimodal grounding, and controlled memory admission. Language must remain evidence, not automatic world truth.
- **42:** Multimodal fusion is an evidence problem. Raw sensor calibration, synchronization and fusion runtime belong outside semantic memory; provenance, uncertainty, modality alignment and grounded memory belong in 03/10 and spatial/temporal authorities.
- **43–45:** Spatial and environmental documents reinforce the separation of geometry, pose, semantic place, historical memory, environmental observation, estimate and prediction. No new spatial/environmental memory document is warranted.
- **46:** Observation, detection, tracking, identity hypothesis, established entity and durable knowledge are distinct states. This validates the 01/02/03/06 boundary.
- **47–48:** Temporal order, correlation, causal hypothesis, supported causality and counterfactual branches must remain distinct. Counterfactuals are not memories or facts.
- **49:** Action learning requires expected-vs-observed outcome comparison, feedback evaluation and controlled promotion into learning/behavior. One experience must not silently rewrite protected behavior.
- **50:** Semantic conflict handling must preserve evidence, distinguish historical from current truth, evaluate source authority and revise beliefs only when justified. Distributed consistency remains a system-architecture concern.

## Verification protocol

For each source, reviewers must check:

1. Every substantive requirement has a canonical destination.
2. The destination actually contains the requirement, not merely a similar title.
3. Terminology is consistent with the canonical model.
4. Contradictory requirements have an explicit resolution.
5. Infrastructure concerns have not leaked into semantic memory documents.
6. Privacy/deletion requirements remain compatible with recovery and replication architecture.
7. Cross-references point to canonical paths.
8. The source can then be classified as `MERGED`, `SUPERSEDED`, `REFERENCE`, `MOVED`, or `HISTORICAL`.

## Current conclusion

The matrix is **actively progressing**. 00–40 have initial dispositions; **41–50 have now been content-reviewed**; 51–94 remain pending; 95–106 remain transitional authorities. No source is marked fully `SUPERSEDED` until final section-level verification and cross-reference repair are complete.
