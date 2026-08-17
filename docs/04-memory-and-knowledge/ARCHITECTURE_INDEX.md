# 04 — Memory and Knowledge Architecture Index

**Status:** CANONICAL SET CONSOLIDATION IN PROGRESS

## Authority hierarchy

| Authority | Document | Role |
|---|---|---|
| CANONICAL | `01`–`18` below | Current consolidated semantic architecture |
| CANONICAL | `95`–`106` | Normative integration/governance authorities retained during migration |
| CANONICAL | `CONSOLIDATION_TARGET_ARCHITECTURE.md` | Responsibility boundaries |
| CANONICAL | `SOURCE_MATERIAL_STATUS.md` | Source classification and traceability registry |
| AUDIT | `ARCHITECTURE_CONTENT_AUDIT.md` | Detailed consolidation findings |
| HISTORICAL | `00`–`94` not yet superseded | Source material; not independent authority |

## Canonical set

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
13 Model and Memory Co-Evolution
14 Privacy and Memory Data Governance
15 Machine Governance Interface
16 Human Oversight and Accountability
17 Integration and Reference Model
18 Final Architecture Audit and Traceability
```

## Current consolidated documents

- `01`–`05` — consolidated in the first content pass.
- `06`–`11` — consolidated in the current specialist pass.
- `12` — consolidated previously.
- `13`–`18` — consolidated in the current specialist pass.

## Responsibility boundaries

```text
semantic memory → docs/04-memory-and-knowledge
physical storage → 01-system-architecture
transactions/concurrency → 01-system-architecture
replication → 01-system-architecture
recovery → 01-system-architecture
runtime scheduling → 01-system-architecture
observability → 01-system-architecture
machine authorization → 105 / 15
human governance → 106 / 16
```

Semantic conflicts belong to `05`; distributed state conflicts belong to `108/109`.

## Consolidation rules

1. Preserve unique technical content.
2. Merge by responsibility, not filename.
3. Maintain source-to-destination traceability.
4. Resolve contradictory normative rules before supersession.
5. Keep research findings distinct from requirements.
6. Keep semantic contracts distinct from physical implementation.
7. Preserve provenance through derived representations.
8. Never treat retrieval as truth or authorization.
9. Never treat generated derivatives as independent evidence.
10. Preserve historical evidence while revising interpretations.
11. Make deletion dependency-aware and verifiable.
12. Preserve Git history.

## Remaining gates

### Content
- [x] Canonical specialist documents created for 01–18.
- [ ] Complete section-level traceability for every legacy source.
- [ ] Resolve any remaining contradictions found by source-level review.

### Naming / archival
- [ ] Update all cross-references to canonical names.
- [ ] Mark fully incorporated sources `SUPERSEDED`.
- [ ] Move infrastructure-only material to system architecture.

### Final audit
- [ ] Verify every source has a disposition.
- [ ] Verify one canonical home per substantive topic.
- [ ] Verify no competing state machines.
- [ ] Re-run architecture audit.
- [ ] Only then close `04-memory-and-knowledge` and continue to the next architecture task.
