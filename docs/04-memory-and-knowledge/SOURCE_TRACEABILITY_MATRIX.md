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

## Initial source mapping

The first pass establishes the source families and their likely canonical destinations. Section-level verification remains required before final supersession.

| Source family | Current status | Canonical destination | Action |
|---|---|---|---|
| `00_HIGH_LEVEL_MEMORY_ARCHITECTURE.md` | MERGED | 01, 17 | Verify high-level invariants and integration boundaries |
| `01_MEMORY_TAXONOMY.md` | MERGED | 01 | Verify taxonomy terminology against canonical ontology |
| `02_MEMORY_LIFECYCLE.md` | MERGED | 02 | Verify lifecycle states and transitions |
| `03_MEMORY_WRITE_AND_ADMISSION_POLICY.md` | MERGED | 02, 15 | Separate semantic admission from governance enforcement |
| `04_MEMORY_CONSOLIDATION_AND_FORGETTING.md` | MERGED | 02, 04, 14 | Verify forgetting/privacy boundaries |
| `05_MEMORY_RETRIEVAL_AND_RANKING.md` | MERGED | 04 | Verify retrieval/ranking requirements |
| `06_MEMORY_PROVENANCE_AND_TRUST.md` | MERGED | 03 | Verify evidence independence, provenance and trust requirements |
| `07_MEMORY_SCHEMA_AND_STORAGE.md` | SPLIT / MOVED | 12 + `01-system-architecture` | Keep semantic schema in 12; move physical storage concerns out of 04 |
| `08_MEMORY_INDEXING_AND_EMBEDDINGS.md` | SPLIT / MOVED | 04 + `01-system-architecture` | Keep retrieval semantics in 04; infrastructure/index implementation elsewhere |
| `09_MEMORY_KNOWLEDGE_GRAPH_AND_RELATIONSHIPS.md` | MERGED | 05 | Verify graph and relationship semantics |
| `10_MEMORY_SCHEMA_EVOLUTION_AND_DYNAMIC_DATA.md` | MERGED | 12 | Verify evolution and compatibility requirements |
| `11_MEMORY_KNOWLEDGE_CONFLICT_RESOLUTION.md` | MERGED | 05, 03 | Semantic conflict in 05; evidence/trust implications in 03 |
| `12_MEMORY_SECURITY_AND_ACCESS_CONTROL.md` | SPLIT / MOVED | 14, 15 + `01-system-architecture` | Retain memory governance; move infrastructure security |
| `13_MEMORY_PRIVACY_AND_RETENTION.md` | MERGED | 14 | Verify retention and deletion requirements |
| `14_MEMORY_DISTRIBUTED_SYNCHRONIZATION.md` | MOVED | `01-system-architecture/109` | Distributed consistency is not memory semantics |
| `15_MEMORY_CONSISTENCY_AND_CONCURRENCY.md` | MOVED | `01-system-architecture/108` | Transaction/consistency semantics belong to system architecture |
| `16_MEMORY_EVENT_SOURCING_AND_REPLAY.md` | MOVED / MERGED | 02, 17 + `01-system-architecture/107/110` | Semantic lifecycle retained; durable replay infrastructure moved |
| `17_MEMORY_VERSIONING_AND_TEMPORAL_HISTORY.md` | MERGED | 07, 12 | Verify temporal validity and schema/version semantics |
| `18_MEMORY_DECAY_AND_FORGETTING.md` | MERGED | 02, 14 | Separate lifecycle decay from privacy deletion |
| `19_MEMORY_RECONSOLIDATION.md` | MERGED | 04, 05 | Verify retrieval-driven reconsolidation and belief revision boundaries |
| `20_MEMORY_CONTEXT_ASSEMBLY.md` | MERGED | 04 | Verify context construction and provenance requirements |
| `21_MEMORY_EPISODIC_ARCHITECTURE.md` | MERGED | 01, 02, 04 | Verify episodic semantics against taxonomy/lifecycle |
| `22_MEMORY_SEMANTIC_ARCHITECTURE.md` | MERGED | 01, 05 | Verify semantic memory and knowledge graph boundary |
| `23_MEMORY_SPATIAL_ARCHITECTURE.md` | MERGED | 08 | Verify spatial state and temporal coupling |
| `24_MEMORY_PROCEDURAL_ARCHITECTURE.md` | MERGED | 11 | Verify skill/competence semantics |
| `25_MEMORY_WORKING_CONTEXT_ARCHITECTURE.md` | MERGED | 04 | Verify working-context semantics and ephemeral-state boundary |
| `26_MEMORY_AUTOBIOGRAPHICAL_ARCHITECTURE.md` | MERGED | 01, 02, 05, 06 | Verify identity and self-model requirements |
| `27_MEMORY_EMOTIONAL_AFFECTIVE_ARCHITECTURE.md` | MERGED | 01, 05 | Verify affective representation without conflating it with truth/identity |
| `28_MEMORY_SOCIAL_ARCHITECTURE.md` | MERGED | 05, 06 | Verify relationship and entity semantics |
| `29_MEMORY_GOAL_ARCHITECTURE.md` | MERGED | 01, 11, 17 | Verify goal-memory boundary and integration |
| `30_MEMORY_NARRATIVE_ARCHITECTURE.md` | MERGED | 04, 05 | Verify narrative views remain derived rather than authoritative |
| `31_MEMORY_SCHEMA_DESIGN.md` | MERGED | 12 | Verify schema requirements |
| `32_MEMORY_INDEX_DESIGN.md` | SPLIT / MOVED | 04 + `01-system-architecture` | Semantic retrieval contract vs physical index implementation |
| `33_MEMORY_QUERY_ARCHITECTURE.md` | MERGED | 04 | Verify retrieval/query semantics |
| `34_MEMORY_CACHE_ARCHITECTURE.md` | MOVED | `01-system-architecture` | Cache infrastructure is not semantic memory authority |
| `35_MEMORY_OBSERVABILITY.md` | MOVED | `01-system-architecture/112` | Runtime observability belongs to system architecture |
| `36_MEMORY_EVALUATION.md` | MERGED | 18, 03, 04 | Preserve evaluation invariants and evidence requirements |
| `37_MEMORY_TESTING.md` | MOVED / MERGED | 18 + testing architecture | Keep semantic invariants; implementation testing elsewhere |
| `38_MEMORY_FAILURE_MODES.md` | MOVED / MERGED | 18 + `01-system-architecture/110` | Semantic failure classes vs disaster recovery |
| `39_MEMORY_BACKUP_AND_RESTORE.md` | MOVED | `01-system-architecture/110` | Infrastructure recovery |
| `40_MEMORY_AUDITABILITY.md` | MERGED | 03, 15, 16, 18 | Provenance, governance and auditability |
| `41–94 legacy semantic series` | PENDING | 01–18 | Review individually; do not supersede by filename similarity alone |
| `95_MEMORY_KNOWLEDGE_MEMORY_ARCHITECTURE_INTEGRATION_AND_REFERENCE_MODEL.md` | TRANSITIONAL | 17 | Keep as validation authority until absorbed completely |
| `96_MEMORY_KNOWLEDGE_ARCHITECTURE_AUDIT_TRACEABILITY_AND_GAP_REGISTER.md` | TRANSITIONAL | 18 | Keep until all identified gaps are dispositioned |
| `97_MEMORY_KNOWLEDGE_IDENTITY_AND_ENTITY_RESOLUTION_ARCHITECTURE.md` | TRANSITIONAL | 06 | Validate canonical 06 against its detailed requirements |
| `98_MEMORY_KNOWLEDGE_TEMPORAL_REASONING_AND_TEMPORAL_MEMORY_ARCHITECTURE.md` | TRANSITIONAL | 07 | Validate canonical 07 against its detailed requirements |
| `99_MEMORY_KNOWLEDGE_SPATIAL_MEMORY_AND_SPATIAL_STATE_ARCHITECTURE.md` | TRANSITIONAL | 08 | Validate canonical 08 against its detailed requirements |
| `100_MEMORY_KNOWLEDGE_CAUSAL_WORLD_MODELING_AND_CAUSAL_MEMORY_ARCHITECTURE.md` | TRANSITIONAL | 09 | Validate canonical 09 against its detailed requirements |
| `101_MEMORY_KNOWLEDGE_CROSS_MODAL_MEMORY_ARCHITECTURE.md` | TRANSITIONAL | 10 | Validate canonical 10 against its detailed requirements |
| `102_MEMORY_KNOWLEDGE_SKILL_AND_COMPETENCE_VERIFICATION_ARCHITECTURE.md` | TRANSITIONAL | 11 | Validate canonical 11 against its detailed requirements |
| `103_MEMORY_KNOWLEDGE_SCHEMA_MIGRATION_COMPATIBILITY_AND_EVOLUTION_ARCHITECTURE.md` | TRANSITIONAL | 12 | Validate canonical 12 against its detailed requirements |
| `104_MEMORY_KNOWLEDGE_MODEL_MEMORY_CO_EVOLUTION_ARCHITECTURE.md` | TRANSITIONAL | 13 | Validate canonical 13 against its detailed requirements |
| `105_MACHINE_VERIFIABLE_GOVERNANCE_AND_POLICY_ENGINE_ARCHITECTURE.md` | TRANSITIONAL | 15 | Validate canonical 15 against its detailed requirements |
| `106_MEMORY_KNOWLEDGE_HUMAN_OVERSIGHT_INTERVENTION_ACCOUNTABILITY_AND_GOVERNANCE_ARCHITECTURE.md` | TRANSITIONAL | 16 | Validate canonical 16 against its detailed requirements |

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

The matrix is **started, not closed**. The 00–40 family has an initial disposition; 41–94 require individual verification; 95–106 remain transitional authorities. No source should be treated as fully superseded solely from this first-pass table.
