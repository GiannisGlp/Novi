# 04 — Memory and Knowledge Architecture Index

**Status:** CANONICAL ARCHITECTURE ACTIVE — HISTORICAL CLEANUP COMPLETE

## Authority hierarchy

| Authority | Document | Role |
|---|---|---|
| CANONICAL | `01`–`18` | Current canonical semantic architecture |
| CANONICAL REGISTRY | `SOURCE_MATERIAL_STATUS.md` | Source classification and disposition |
| CANONICAL TRACEABILITY | `SOURCE_TRACEABILITY_MATRIX.md` | Source-to-destination traceability |
| FINAL AUDIT | `FINAL_CONSOLIDATION_AUDIT.md` | Final cleanup result and remaining non-destructive source-review work |
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
transactions / concurrency  → 01-system-architecture
replication                  → 01-system-architecture
recovery                     → 01-system-architecture
runtime scheduling           → 01-system-architecture
observability implementation → 01-system-architecture
machine authorization        → 15
human governance             → 16
```

Semantic conflicts belong to `05`; distributed state conflicts belong to system architecture.

## Final cleanup state

- [x] Canonical 01–18 spine exists.
- [x] Active README identifies only 01–18 as normative.
- [x] Source disposition and traceability registries exist.
- [x] Transitional 95–106 authorities moved out of the active namespace.
- [x] Consolidation/audit artifacts moved to archive.
- [x] Historical corpus remains preserved.
- [x] Missing source numbers 24 and 65 are explicitly recorded as inventory gaps.
- [x] No new 19+ semantic architecture series created.

## Remaining source-review note

The historical archive remains preserved because individual historical files may still contain useful research, implementation details, or requirements that need section-level traceability. This does not affect the canonical authority of 01–18.
