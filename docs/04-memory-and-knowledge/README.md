# 04 — Memory and Knowledge

## Status

**CLEANUP / CONSOLIDATION IN PROGRESS**

This directory contains the Memory and Knowledge architecture for Novi. It currently includes several generations of detailed design documents. Until consolidation is complete, **the authority hierarchy in `ARCHITECTURE_INDEX.md` is normative**.

citeturn0search1turn0search9turn0search0

## Authority

Start with:

- `ARCHITECTURE_INDEX.md` — document authority, overlap clusters, cleanup rules and consolidation plan.
- `95_MEMORY_KNOWLEDGE_MEMORY_ARCHITECTURE_INTEGRATION_AND_REFERENCE_MODEL.md` — integrated reference architecture.
- `96_MEMORY_KNOWLEDGE_ARCHITECTURE_AUDIT_TRACEABILITY_AND_GAP_REGISTER.md` — audit, traceability and gap register.
- `97`–`106` — focused architecture documents produced by the latest integration/audit pass.

The older `00`–`94` documents are **source material**, not automatically authoritative. They will be reviewed and either retained, merged, superseded, or moved as part of the cleanup.

## Core principle

> Experience is not automatically memory, memory is not automatically knowledge, and knowledge is not automatically truth.

The canonical progression is:

```text
observation
    ↓
event
    ↓
episode
    ↓
memory candidate
    ↓
validation / deduplication
    ↓
consolidation
    ↓
durable memory or knowledge
    ↓
indexing
    ↓
retrieval
    ↓
context
    ↓
cognition
```

## Memory classes

Novi supports distinct memory classes, including:

- working memory;
- session/conversation memory;
- episodic memory;
- semantic memory;
- procedural memory;
- relationship memory;
- spatial memory;
- temporal memory;
- preference memory;
- system/operational memory.

## Knowledge model

Knowledge is represented separately from raw experience and should carry evidence, provenance, confidence, epistemic state, validity, verification state, source, privacy classification, retention policy, and contradiction/supersession relationships where applicable.

## Storage direction

The logical memory layer remains independent of physical storage. The initial local direction is:

```text
SQLite
  → authoritative structured state

Files
  → documents, raw/derived artifacts, large payloads

Vector index
  → semantic retrieval

Full-text index
  → exact/lexical retrieval

Graph/relationship layer
  → entity and relationship traversal
```

A separate graph database is not mandatory initially; relationship structures can begin in SQLite and be promoted only when benchmarks justify it.

## Retrieval direction

Retrieval is a capability rather than a memory type. Novi may combine:

```text
query
 ↓
intent / task classification
 ↓
candidate retrieval
 ├── exact / SQL
 ├── full-text
 ├── semantic/vector
 ├── temporal
 ├── graph/relationship
 └── recent episodic
 ↓
filter
 ↓
rank / rerank
 ↓
confidence + provenance checks
 ↓
context package
```

## Local-first requirement

The production robot should remain useful without cloud memory services. External memory/retrieval infrastructure requires an explicit rationale, data-flow/privacy assessment, local fallback where practical, and migration path.

## Documentation lifecycle

The documentation is being consolidated deliberately rather than deleted destructively:

```text
existing documents
       ↓
classification
       ↓
content comparison
       ↓
merge / retain / supersede / move
       ↓
canonical architecture
       ↓
final naming pass
       ↓
architecture audit
```

Git history remains the recovery mechanism for superseded or renamed documents.

## Cleanup policy

Do not use filename numbering alone to determine which design is correct. When documents overlap, the latest integrated architecture and audit documents provide the starting authority, while earlier documents remain evidence until their content has been explicitly reviewed.

For the full status model and consolidation plan, see `ARCHITECTURE_INDEX.md`.

## Completion criterion

This directory is not considered clean until:

1. every document has an explicit status;
2. every substantive topic has one canonical home;
3. contradictory requirements have been resolved;
4. cross-document references point to canonical names;
5. obsolete documents are clearly marked or removed;
6. the final README reflects the canonical architecture;
7. the architecture audit reports no unresolved documentation-structure gaps.
