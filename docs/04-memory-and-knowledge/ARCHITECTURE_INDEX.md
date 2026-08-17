# 04 — Memory and Knowledge Architecture Index

**Status:** CANONICAL ARCHITECTURE ACTIVE — V1.1 ENRICHED

## Authority hierarchy

| Authority | Document | Role |
|---|---|---|
| CANONICAL | `01`–`18` | Current canonical semantic architecture |
| CANONICAL REGISTRY | `SOURCE_MATERIAL_STATUS.md` | Source classification and disposition |
| CANONICAL TRACEABILITY | `SOURCE_TRACEABILITY_MATRIX.md` | Source-to-destination traceability |
| FINAL AUDIT | `FINAL_CONSOLIDATION_AUDIT.md` | Consolidation result and audit history |
| HISTORICAL | `archive/` | Historical, transitional and audit material; non-normative |

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
machine authorization        → 15
human governance             → 16
```

Semantic conflicts belong to `05`; distributed state conflicts belong to system architecture.

## V1.1 completion state

- [x] Canonical 01–18 spine exists.
- [x] All 18 canonical documents enriched with required semantic contracts or confirmed as already complete.
- [x] Retrieval, provenance, uncertainty and abstention requirements are explicit.
- [x] Identity, temporal, spatial, causal and multimodal contracts are explicit.
- [x] Skill, schema, model/memory, privacy and governance contracts are explicit.
- [x] Human oversight state machine and integration scenarios are explicit.
- [x] Final audit in document 18 records the V1.1 completion gate.
- [x] Transitional 95–106 authorities remain archived and non-normative.
- [x] Consolidation/audit artifacts remain archived.
- [x] Historical corpus remains preserved.
- [x] Missing source numbers 24 and 65 are explicitly recorded as inventory gaps.
- [x] No new 19+ semantic architecture series created.

## Canonical rule

If an implementation decision concerns the semantic meaning of memory or knowledge, resolve ownership against `01–18` first. Historical archive material may explain origin or provide evidence, but it cannot override the canonical set.