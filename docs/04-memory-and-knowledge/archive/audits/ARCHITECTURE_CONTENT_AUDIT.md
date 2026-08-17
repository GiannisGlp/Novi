# 04 — Memory and Knowledge Architecture Content Audit

**Status:** AUDITED — CONSOLIDATION REQUIRED  
**Date:** 2026-08-17  
**Authority:** `ARCHITECTURE_INDEX.md` + canonical 95–106 series  
**Scope:** `docs/04-memory-and-knowledge/`

## 1. Executive verdict

The directory contains substantial high-quality material, but it is **not safe to treat the full directory as one coherent normative architecture**. It contains multiple generations of increasingly refined specifications with significant overlap.

The correct action is **consolidation, not wholesale deletion**.

The latest 95–106 series is the current normative spine. Earlier documents contain valuable details, research notes, implementation constraints, examples, schemas and failure cases that should be mined into the canonical set before being marked superseded.

### Final audit result

```text
CONTENT QUALITY        HIGH
ARCHITECTURAL COHERENCE MEDIUM
DUPLICATION            HIGH
CONTRADICTION RISK     MEDIUM-HIGH
TRACEABILITY           MEDIUM
NAMING CONSISTENCY     LOW
DELETION READINESS     NOT YET
CONSOLIDATION REQUIRED YES
```

## 2. Authority rule

Until consolidation is completed:

```text
95–106 = NORMATIVE CANONICAL SPINE
00–94  = SOURCE MATERIAL / HISTORICAL DESIGN
```

An older document may contain a more detailed rule than a canonical document, but that rule is **not authoritative until explicitly incorporated**.

This distinction is essential because several older documents contain strong technical requirements that are still useful even though their overall scope has been superseded.

## 3. Audit method

The audit used:

1. the actual `main` contents of `04-memory-and-knowledge`;
2. the existing `ARCHITECTURE_INDEX.md` overlap map;
3. the `README.md` authority model;
4. the canonical 95 reference model;
5. representative inspection of foundational and late-generation documents, including lifecycle, schema evolution, provenance/trust, consolidation/reconsolidation and the canonical integration series;
6. comparison of scopes, invariants, dependencies, terminology and likely implementation ownership.

The result is intentionally conservative: a document is not classified as disposable merely because its filename overlaps another document.

## 4. Classification model

| Status | Meaning | Action |
|---|---|---|
| CANONICAL | Current normative authority | Keep; refine only through controlled consolidation |
| SOURCE | Useful technical material not currently authoritative | Extract unique content, then supersede/archive |
| FOUNDATIONAL | Earlier material whose concepts remain useful | Extract core definitions and examples |
| MERGE | Primarily duplicate/overlapping content | Merge unique material into canonical destination |
| SUPERSEDED | Replaced by newer architecture with no material unique content | Mark and remove from active navigation |
| MOVE | Valid material belonging elsewhere | Move to appropriate architecture/domain directory |
| REFERENCE | Research/data/background rather than architecture | Keep as reference, outside normative spine |
| GAP | Missing capability revealed by audit | Create canonical work item/document if needed |

## 5. Canonical documents — retain

| Document | Decision | Reason |
|---|---|---|
| 95 — Integration and Reference Model | CANONICAL | Defines the integrated memory/knowledge architecture and boundaries |
| 96 — Architecture Audit / Traceability / Gap Register | CANONICAL | Defines coverage and remaining architectural gaps |
| 97 — Identity / Entity Resolution | CANONICAL | Dedicated authority for identity and entity semantics |
| 98 — Temporal Reasoning / Temporal Memory | CANONICAL | Dedicated authority for time semantics |
| 99 — Spatial Memory / Spatial State | CANONICAL | Dedicated authority for spatial semantics |
| 100 — Causal World Modeling / Causal Memory | CANONICAL | Dedicated authority for causal semantics |
| 101 — Cross-Modal Memory | CANONICAL | Dedicated authority for multimodal memory semantics |
| 102 — Skill / Competence Verification | CANONICAL | Dedicated authority for skill and competence claims |
| 103 — Schema Migration / Compatibility / Evolution | CANONICAL | Dedicated authority for schema evolution |
| 104 — Model / Memory Co-Evolution | CANONICAL | Dedicated authority for model-memory lifecycle coupling |
| 105 — Machine-Verifiable Governance / Policy | CANONICAL | Dedicated machine governance authority |
| 106 — Human Oversight / Accountability | CANONICAL | Dedicated human governance authority |

## 6. Foundational 00–09 series

These documents should **not be deleted immediately**. They contain the original conceptual foundations and useful implementation details.

| Document | Decision | Consolidation destination |
|---|---|---|
| 00 High-Level Memory Architecture | FOUNDATIONAL | 95 + final overview |
| 01 Memory Taxonomy | FOUNDATIONAL | 95 / memory model section |
| 02 Memory Lifecycle | MERGE | 95 + lifecycle canonical sections |
| 03 Memory Write and Admission Policy | MERGE | 95 + governance/write-gate sections |
| 04 Memory Consolidation and Forgetting | MERGE | consolidation canonical material + 103/111 where relevant |
| 05 Memory Retrieval and Ranking | MERGE | retrieval/context canonical material |
| 06 Memory Provenance and Trust | FOUNDATIONAL / HIGH-VALUE | provenance/evidence destination; retain unique source/trust taxonomy |
| 07 Memory Schema and Storage | MERGE | 103 + 107; physical storage details belong in system architecture |
| 08 Memory Indexing and Embeddings | MERGE / MOVE | retrieval architecture; implementation/storage details should move to system architecture |
| 09 Memory Knowledge Graph and Relationships | MERGE | 95 + identity/causal/cross-modal relationships as appropriate |

## 7. High-value overlap clusters

### 7.1 Lifecycle and state transitions

Documents:

- `02_MEMORY_LIFECYCLE.md`
- `29_MEMORY_LIFECYCLE_AND_STATE_TRANSITIONS.md`

Decision: **MERGE**.

Canonical destination: 95, with operational lifecycle semantics eventually connected to 107.

Important content to preserve:

- explicit lifecycle states;
- admission/rejection;
- promotion/demotion;
- deletion/retention transitions;
- failure states;
- idempotent transitions;
- audit requirements.

Do not maintain two independent lifecycle state machines.

### 7.2 Schema evolution

Documents:

- `07_MEMORY_SCHEMA_AND_STORAGE.md`
- `10_MEMORY_SCHEMA_EVOLUTION_AND_DYNAMIC_DATA.md`
- `103_MEMORY_KNOWLEDGE_SCHEMA_MIGRATION_COMPATIBILITY_AND_EVOLUTION_ARCHITECTURE.md`

Decision: **103 CANONICAL; 07/10 SOURCE → MERGE**.

The inspected `10` contains unusually valuable material around autonomous schema proposals, protected-core boundaries, migration validation, quotas, schema churn prevention, dynamic entities/relationships, SQLite migration constraints, rollback and human confirmation. It should be mined rather than discarded.

Canonical split:

```text
103 = semantic schema evolution / compatibility / migration contract
107 = durable execution / physical state / migration execution substrate
105 = authorization of protected governance changes
```

### 7.3 Provenance / evidence / trust

Documents:

- `06_MEMORY_PROVENANCE_AND_TRUST.md`
- `18_MEMORY_SENSOR_GROUNDING_AND_MEASUREMENT_PROVENANCE.md`
- `51_MEMORY_KNOWLEDGE_PROVENANCE_AND_LINEAGE.md`
- `52_MEMORY_KNOWLEDGE_CONFIDENCE_AND_UNCERTAINTY_MODEL.md`
- `54_MEMORY_KNOWLEDGE_SOURCE_RELIABILITY_AND_TRUST_MODEL.md`
- `74_MEMORY_KNOWLEDGE_PROVENANCE_LINEAGE_AND_EVIDENCE_GRAPH.md`
- `75_MEMORY_KNOWLEDGE_EVIDENCE_QUALITY_CONFIDENCE_AND_UNCERTAINTY.md`
- `92_MEMORY_KNOWLEDGE_MEMORY_PROVENANCE_LINEAGE_AND_TRACEABILITY_ENGINE.md`

Decision: **MERGE into one provenance/evidence authority under 95, with implementation contracts later mapped to 107/112.**

This is one of the highest-value consolidation clusters.

The inspected `06` has strong source-class taxonomy, evidence/claim/belief separation, integrity hashing, temporal provenance, domain-scoped trust, verification states, independence detection, model-version provenance and derived-memory lineage. These are architectural requirements worth preserving.

Critical invariant:

```text
PROVENANCE ≠ CONFIDENCE ≠ VERIFICATION ≠ AUTHORIZATION
```

Do not allow multiple documents to define competing trust hierarchies.

### 7.4 Consolidation / reconsolidation

Documents:

- `04_MEMORY_CONSOLIDATION_AND_FORGETTING.md`
- `77_MEMORY_KNOWLEDGE_MEMORY_RECONSOLIDATION_AND_BELIEF_REVISION.md`
- `78_MEMORY_KNOWLEDGE_MEMORY_CONSOLIDATION_AND_ABSTRACTION.md`
- `89_MEMORY_KNOWLEDGE_MEMORY_CONSOLIDATION_AND_RECONSOLIDATION_ENGINE.md`

Decision: **89 is the strongest detailed source; merge unique material into 95 and retain 89 temporarily as SOURCE.**

The inspected 89 correctly distinguishes evidence from derived memory, significance from truth, source independence, counterexamples, versioned interpretation, deletion-aware consolidation, privacy-aware abstraction, rebuildability and idempotency.

Preserve these invariants:

```text
CONSOLIDATION ≠ COPYING
RETRIEVAL ≠ RECONSOLIDATION
DERIVATIVE ≠ INDEPENDENT EVIDENCE
SIGNIFICANCE ≠ TRUTH
```

### 7.5 Retrieval / context

Documents:

- `05_MEMORY_RETRIEVAL_AND_RANKING.md`
- `35_MEMORY_ATTENTION_AND_RELEVANCE_MODEL.md`
- `36_MEMORY_CONTEXT_ASSEMBLY_AND_COGNITIVE_WORKSPACE.md`
- `56_MEMORY_KNOWLEDGE_QUERY_SEMANTICS_AND_CONTEXT_RESOLUTION.md`
- `57_MEMORY_KNOWLEDGE_QUERY_PLANNING_AND_EXECUTION.md`
- `80_MEMORY_KNOWLEDGE_RETRIEVAL_CONTEXTUAL_REASONING_AND_MEMORY_RECALL.md`
- `90_MEMORY_KNOWLEDGE_MEMORY_RETRIEVAL_RANKING_AND_CONTEXT_ASSEMBLY_ENGINE.md`

Decision: **MERGE**.

Target canonical scope: retrieval and context assembly within 95, with physical execution details later belonging to system/runtime architecture.

Do not let retrieval ranking become an implicit truth/authorization system.

Required separation:

```text
retrieval relevance
≠ evidence quality
≠ truth
≠ authorization
```

### 7.6 Conflict / belief revision

Documents:

- `20_MEMORY_CONFLICT_RESOLUTION_AND_DISTRIBUTED_STATE.md`
- `50_MEMORY_KNOWLEDGE_CONFLICTS_AND_BELIEF_REVISION.md`
- `72_MEMORY_KNOWLEDGE_CONFLICT_RESOLUTION_AND_CONSISTENCY_POLICIES.md`
- `91_MEMORY_KNOWLEDGE_EVIDENCE_FUSION_CONFLICT_RESOLUTION_AND_BELIEF_ARBITRATION.md`

Decision: **MERGE**.

Semantic conflict resolution belongs in the memory/knowledge layer. Distributed consistency and transaction semantics now belong in 108/109 and must not be duplicated here.

Canonical boundary:

```text
semantic conflict → memory/knowledge
state concurrency → system architecture
authorization conflict → 105
human governance dispute → 106
```

### 7.7 Spatial / temporal

Documents:

- `23_MEMORY_SPATIAL_MEMORY_AND_PLACE_HISTORY.md`
- `43_MEMORY_SPATIAL_WORLD_MODEL_AND_PLACE_MEMORY.md`
- `44_MEMORY_SPATIAL_TEMPORAL_REASONING_AND_TRAJECTORY_MEMORY.md`
- `98_TEMPORAL`
- `99_SPATIAL`

Decision: **98/99 CANONICAL; older documents SOURCE → MERGE.**

Preserve useful trajectory, place-history, uncertainty, map-version and temporal-validity details. Do not retain competing definitions of temporal validity or spatial state.

### 7.8 Multimodal / sensor grounding

Documents:

- `18_MEMORY_SENSOR_GROUNDING_AND_MEASUREMENT_PROVENANCE.md`
- `42_MEMORY_MULTIMODAL_GROUNDING_AND_SENSOR_FUSION.md`
- `69_MEMORY_KNOWLEDGE_SENSOR_DATA_INGESTION_AND_FUSION.md`
- `101_CROSS_MODAL`

Decision: **101 CANONICAL; older documents SOURCE → MERGE.**

Preserve modality-specific provenance, calibration, timestamping, uncertainty, common-source dependence and sensor-fusion failure modes.

### 7.9 Privacy / security / governance

Documents:

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
- `106_HUMAN_OVERSIGHT...`

Decision: **105/106 canonical for governance; privacy/security material must be consolidated with 111 where lifecycle/erasure is concerned and with the appropriate system-security architecture where infrastructure controls are concerned.**

Important boundary:

```text
memory privacy semantics → memory/knowledge + 111
machine authorization → 105
human governance → 106
physical/system security → system architecture/security domain
```

Do not keep a second memory-local authorization engine.

## 8. Special architectural boundary discovered

The old memory documents frequently mix three layers:

```text
SEMANTIC MEMORY CONTRACT
        +
PHYSICAL STORAGE IMPLEMENTATION
        +
DISTRIBUTED SYSTEM BEHAVIOR
```

The new architecture should separate them.

Examples:

- SQLite schema mechanics → 107/implementation architecture, not semantic memory authority.
- Replication → 109, not memory semantics.
- Transactions/concurrency → 108.
- Recovery → 110.
- Privacy lifecycle/erasure → 111.
- Observability → 112.
- Resource scheduling → 113.

This is one of the main reasons the old directory became difficult to navigate.

## 9. Canonical set should be smaller

The eventual active 04 directory should not contain 100+ normative documents.

Recommended active semantic architecture set:

```text
01  Memory Taxonomy and Core Model
02  Memory Lifecycle and Admission
03  Provenance, Evidence, Trust and Uncertainty
04  Memory Consolidation, Retrieval and Context
05  Knowledge Graph / Relationships / Belief Revision
06  Identity and Entity Resolution
07  Temporal Memory and Reasoning
08  Spatial Memory and State
09  Causal World Modeling
10  Cross-Modal Memory
11  Skill and Competence Verification
12  Schema / Knowledge Evolution
13  Model / Memory Co-Evolution
14  Privacy and Memory Data Governance
15  Machine Governance Interface
16  Human Oversight and Accountability
17  Integration and Reference Model
18  Architecture Audit / Traceability
```

This is a **target structure**, not yet a rename/delete instruction.

## 10. Documents that should move out of 04

Physical implementation documents should eventually move when their scope is primarily infrastructure rather than memory semantics.

Candidates include material primarily concerned with:

- storage engines;
- vector index implementation;
- FTS implementation;
- database migration mechanics;
- replication transport;
- transaction engines;
- distributed synchronization;
- runtime scheduling.

The semantic contract should remain in 04, while the implementation contract belongs in `01-system-architecture` or the appropriate subsystem directory.

## 11. Documents that should remain reference material

Research citations, empirical comparisons, biological-memory analogies and implementation experiments should not become normative architecture unless explicitly promoted.

The consolidation process must preserve useful citations and research conclusions while clearly separating:

```text
RESEARCH FINDING
      ≠
ARCHITECTURAL REQUIREMENT
```

This is particularly important for biological memory analogies in consolidation/reconsolidation documents.

## 12. Contradiction risks found

The audit identifies several areas where parallel documents could produce conflicting implementations if treated as authoritative:

1. lifecycle state names;
2. schema-change authority;
3. trust/verification ranking;
4. conflict-resolution ordering;
5. retrieval ranking vs truth;
6. deletion completeness;
7. distributed consistency semantics;
8. memory vs current-state precedence;
9. model-generated information vs evidence;
10. human confirmation vs machine authorization.

These should be resolved in consolidation by one canonical rule per concern.

## 13. Critical invariants to preserve during consolidation

```text
Experience ≠ memory
Memory ≠ knowledge
Knowledge ≠ truth
Evidence ≠ claim
Claim ≠ belief
Confidence ≠ provenance
Verification ≠ confidence
Trust ≠ authorization
Retrieval ≠ truth
Retrieval ≠ reconsolidation
Historical state ≠ current authoritative state
Model output ≠ independent evidence
Derived data ≠ source evidence
Human presence ≠ human authority
Human override ≠ unrestricted bypass
Skill success ≠ general competence
Schema change ≠ ordinary learning
Deletion ≠ merely removing one database row
```

These invariants should survive every rename and merge.

## 14. Consolidation order

Do not rename everything first. The safe order is:

```text
1. Freeze canonical authority
        ↓
2. Extract unique content from old documents
        ↓
3. Merge into canonical destinations
        ↓
4. Resolve contradictions
        ↓
5. Update cross-references
        ↓
6. Mark old documents SUPERSEDED
        ↓
7. Move infrastructure material
        ↓
8. Rename canonical documents
        ↓
9. Rebuild README + index
        ↓
10. Run final audit
```

## 15. Current disposition

**No old document should be deleted yet.**

The audit establishes that many older documents contain unique material worth preserving. The next action is a controlled **content-consolidation pass**, cluster by cluster.

### Priority order

1. Provenance / evidence / trust
2. Consolidation / reconsolidation
3. Retrieval / context
4. Lifecycle / admission
5. Conflict / belief revision
6. Privacy / security / governance boundaries
7. Schema / storage separation
8. Spatial / temporal / multimodal legacy material
9. Remaining low-risk historical documents

## 16. Completion criterion

The directory is ready to leave cleanup mode only when:

- every retained document has a status;
- every substantive topic has exactly one canonical semantic home;
- physical implementation details have an appropriate system-architecture home;
- contradictory requirements are resolved;
- all cross-references point to canonical documents;
- superseded documents are clearly marked or removed from active navigation;
- README and index agree;
- 95–106 no longer depend on obsolete names without explicit compatibility mapping;
- a final traceability audit shows no orphaned unique requirements.

## 17. Audit conclusion

The existing documentation is **valuable but over-fragmented**. The correct strategy is not to throw away the earlier work. It is to convert it from a collection of competing specifications into a traceable source corpus feeding a much smaller canonical architecture.

The next phase is therefore **content consolidation**, not document generation.
