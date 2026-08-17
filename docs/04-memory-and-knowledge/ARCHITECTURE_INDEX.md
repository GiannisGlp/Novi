# 04 — Memory and Knowledge Architecture Index

**Status:** CONSOLIDATION AUDIT COMPLETE — HISTORICAL CLEANUP GATED

## Authority hierarchy

| Authority | Document | Role |
|---|---|---|
| CANONICAL | `01`–`18` | Current canonical semantic architecture |
| TRANSITIONAL AUTHORITY | `95`–`106` | Earlier integrated specialist authorities retained until source traceability and cross-reference migration are complete |
| CANONICAL REGISTRY | `SOURCE_MATERIAL_STATUS.md` | Source classification and traceability registry |
| AUDIT | `ARCHITECTURE_CONTENT_AUDIT.md` | Consolidation audit |
| FINAL AUDIT | `FINAL_CONSOLIDATION_AUDIT.md` | Exit criteria and cleanup gate |
| SOURCE / HISTORICAL | `00`–`94` | Earlier material; non-normative and retained until disposition gates pass |

## Canonical semantic architecture

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

## Responsibility boundaries

```text
semantic memory              → docs/04-memory-and-knowledge
physical storage             → 01-system-architecture
transactions / concurrency   → 01-system-architecture
replication                  → 01-system-architecture
recovery                     → 01-system-architecture
runtime scheduling           → 01-system-architecture
observability implementation → 01-system-architecture
machine authorization        → 15 / 105
human governance             → 16 / 106
```

Semantic conflicts belong to `05`; distributed state conflicts belong to `108/109`.

## Consolidation status

### Phase 1 — Authority
- [x] Audit directory.
- [x] Establish canonical spine.
- [x] Create consolidation target.
- [x] Create source-material registry.
- [x] Update README.

### Phase 2 — Content
- [x] Create and populate canonical 01–18 documents.
- [x] Merge the major identified source clusters.
- [x] Establish semantic/infrastructure responsibility boundaries.
- [ ] Complete section-level traceability for every historical file.
- [ ] Resolve remaining contradictory requirements found during source-by-source review.

### Phase 3 — Naming and historical cleanup
- [x] Final canonical 01–18 names created.
- [ ] Redirect all remaining cross-references to historical authorities.
- [ ] Move infrastructure-only material to system architecture.
- [ ] Mark fully incorporated sources `SUPERSEDED`.
- [ ] Remove duplicate active navigation entries.

### Phase 4 — Final audit
- [x] Verify the 01–18 canonical spine exists.
- [x] Verify major responsibility boundaries.
- [x] Publish final consolidation audit.
- [ ] Verify every source has an explicit disposition.
- [ ] Verify one canonical home per substantive topic at section level.
- [ ] Verify no competing state machines remain.
- [ ] Re-run audit after historical cleanup.

## Cleanup rule

**Do not delete historical documents yet.** The corpus remains preserved as source material until every file has an explicit disposition and its unique architectural requirements have been traced into the canonical destination. Git history is not a substitute for architectural traceability.

Only after the final audit gates pass may historical sources be marked `SUPERSEDED`, moved, or deleted.
