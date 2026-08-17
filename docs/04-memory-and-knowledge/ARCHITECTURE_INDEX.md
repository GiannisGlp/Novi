# 04 — Memory and Knowledge Architecture Index

**Status:** CONSOLIDATION ACTIVE

## Authority hierarchy

| Authority | Document | Role |
|---|---|---|
| CANONICAL | `CONSOLIDATION_TARGET_ARCHITECTURE.md` | Target canonical structure and responsibility boundaries |
| CANONICAL | `SOURCE_MATERIAL_STATUS.md` | Source classification and traceability registry |
| CANONICAL | `95_MEMORY_KNOWLEDGE_MEMORY_ARCHITECTURE_INTEGRATION_AND_REFERENCE_MODEL.md` | Current normative integrated reference model |
| CANONICAL | `96_MEMORY_KNOWLEDGE_ARCHITECTURE_AUDIT_TRACEABILITY_AND_GAP_REGISTER.md` | Audit and implementation-readiness gate |
| CANONICAL | `97`–`106` | Specialist architecture produced by the latest integration pass |
| AUDIT | `ARCHITECTURE_CONTENT_AUDIT.md` | Detailed consolidation audit |
| SOURCE / HISTORICAL | `00`–`94` | Earlier material; not independently authoritative |

## Target canonical set

The final active semantic architecture is intended to converge on:

```text
01 Memory Taxonomy and Core Model
02 Memory Lifecycle and Admission
03 Provenance, Evidence, Trust and Uncertainty
04 Memory Consolidation, Retrieval and Context
05 Knowledge Graph, Relationships and Belief Revision
06 Identity and Entity Resolution
07 Temporal Memory and Reasoning
08 Spatial Memory and State
09 Causal World Modeling
10 Cross-Modal Memory
11 Skill and Competence Verification
12 Schema and Knowledge Evolution
13 Model / Memory Co-Evolution
14 Privacy and Memory Data Governance
15 Machine Governance Interface
16 Human Oversight and Accountability
17 Integration and Reference Model
18 Architecture Audit and Traceability
```

These are target names. Existing 95–106 files remain the authoritative implementations of those concerns until their content has been merged into the final names.

## Major consolidation mappings

### Lifecycle

`02_MEMORY_LIFECYCLE.md`, `29_MEMORY_LIFECYCLE_AND_STATE_TRANSITIONS.md` → target 02.

### Admission / write gate

`03_MEMORY_WRITE_AND_ADMISSION_POLICY.md` → target 02 + target 03.

### Consolidation / reconsolidation

`04_MEMORY_CONSOLIDATION_AND_FORGETTING.md`, `77`, `78`, `89` → target 04.

### Retrieval / context

`05_MEMORY_RETRIEVAL_AND_RANKING.md`, `35`, `36`, `56`, `57`, `80`, `90` → target 04.

### Provenance / evidence / trust

`06_MEMORY_PROVENANCE_AND_TRUST.md`, `18`, `51`, `52`, `54`, `74`, `75`, `92` → target 03.

### Schema evolution

`07_MEMORY_SCHEMA_AND_STORAGE.md`, `10_MEMORY_SCHEMA_EVOLUTION_AND_DYNAMIC_DATA.md`, `103` → target 12. Physical storage/migration mechanics move to system architecture.

### Knowledge graph / conflict / belief revision

`09_MEMORY_KNOWLEDGE_GRAPH_AND_RELATIONSHIPS.md`, `20`, `50`, `72`, `91` → target 05.

### Temporal / spatial

`23`, `43`, `44` → targets 07/08; `98`/`99` remain canonical until final rename.

### Cross-modal

`18`, `42`, `69` → target 10; `101` remains canonical until final rename.

### Governance / privacy / security

`11`, `25`, `60`, `61`, `62`, `63`, `64`, `88`, `94` → targets 14/15 and appropriate system-security architecture. `105` and `106` remain canonical governance authorities.

## Non-negotiable boundaries

```text
semantic memory → docs/04
physical storage → system architecture
transactions/concurrency → system architecture
replication → system architecture
recovery → system architecture
runtime scheduling → system architecture
observability → system architecture
machine authorization → 105 / target 15
human governance → 106 / target 16
```

No historical document may reintroduce a competing authority for these concerns.

## Consolidation rules

1. Preserve unique technical content.
2. Merge by responsibility, not filename.
3. Record source-to-destination traceability.
4. Resolve contradictory normative rules before supersession.
5. Keep research findings distinct from architecture requirements.
6. Keep semantic contracts distinct from physical implementation.
7. Preserve provenance through every derived representation.
8. Never treat retrieval as truth or authorization.
9. Never treat generated derivatives as independent evidence.
10. Preserve historical evidence while revising interpretations.
11. Make deletion dependency-aware and verifiable.
12. Preserve Git history.

## Cleanup gates

### Phase 1 — Authority
- [x] Audit directory.
- [x] Establish canonical spine.
- [x] Create consolidation target.
- [x] Create source-material registry.
- [x] Update README.

### Phase 2 — Content
- [ ] Extract remaining unique material from every source cluster.
- [ ] Merge into canonical specialist documents.
- [ ] Resolve all contradictory requirements.
- [ ] Record section-level traceability.

### Phase 3 — Naming
- [ ] Create final 01–18 canonical files from the consolidated content.
- [ ] Update all cross-references.
- [ ] Mark fully incorporated sources `SUPERSEDED`.
- [ ] Move infrastructure material to system architecture.

### Phase 4 — Final audit
- [ ] Verify every source has a disposition.
- [ ] Verify one canonical home per substantive topic.
- [ ] Verify no competing state machines.
- [ ] Re-run architecture audit.
- [ ] Only then continue to the next numbered architecture task.
