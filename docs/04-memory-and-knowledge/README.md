# 04 — Memory and Knowledge

## High-Level Description

The Memory and Knowledge subsystem is Novi's durable learning and information layer. It converts selected experiences into memories and knowledge, stores them with provenance and epistemic state, retrieves relevant information for cognition, consolidates repeated experiences, resolves contradictions, supports controlled schema evolution, and manages forgetting and retention.

Memory is **not** a single vector database and is not the LLM's context window. Novi uses multiple memory types and storage/indexing mechanisms, each optimized for a different purpose.

The architecture is informed by current agent-memory patterns and NVIDIA's NeMo Agent Toolkit. NVIDIA's current toolkit exposes pluggable memory backends, separate reader/writer/editor/manager interfaces, automatic memory capture/retrieval, and retriever abstractions. NVIDIA's RAG stack also uses staged retrieval, reranking, planning, retries, synthesis and optional verification for complex knowledge queries. These patterns are useful references, but Novi will keep its own vendor-neutral contracts and local-first deployment policy. citeturn0search1turn0search9turn0search0

## Core Principle

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

## Memory Classes

Novi will support distinct memory classes:

- working memory — transient current cognitive state;
- session/conversation memory — current interaction context;
- episodic memory — experiences and events;
- semantic memory — durable facts, concepts and learned information;
- procedural memory — routines, skills and validated procedures;
- relationship memory — person-specific interaction history and relationship state;
- spatial memory — places, objects, locations and spatial relationships;
- temporal memory — routines, sequences and time-dependent knowledge;
- preference memory — user/household preferences with provenance;
- system/operational memory — validated device and environment state/history.

## Knowledge Model

Knowledge is represented separately from raw experience. A knowledge item can contain:

- entity and relation references;
- claim/content;
- evidence;
- provenance;
- confidence;
- epistemic state;
- validity interval;
- verification state;
- source;
- privacy classification;
- retention policy;
- contradiction/supersession links.

## Storage Strategy

The logical memory layer is independent from physical storage. The initial local implementation may use:

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

A separate graph database is not mandatory initially; relationship structures can begin in SQLite and be promoted if benchmarks demonstrate a need.

## Retrieval Strategy

Retrieval is a capability, not a memory type. Novi should combine retrieval methods when appropriate:

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

NVIDIA's NeMo Agent Toolkit provides a useful reference for keeping retrievers behind a standard read-only interface and supporting different data-store providers. citeturn0search3

## Memory Writing

Memory writes are controlled. The reasoning model may propose a memory, but the Memory Manager decides whether it should be persisted.

Possible outcomes:

- discard;
- keep as transient observation;
- create episode;
- create candidate memory;
- merge with existing memory;
- update existing knowledge;
- create new entity/type proposal;
- require human verification;
- mark contradiction;
- schedule later consolidation.

## Consolidation

Novi should asynchronously consolidate experiences so the real-time cognitive loop is not blocked. Consolidation can summarize repeated events, merge duplicates, promote stable patterns, reduce stale memories, and generate knowledge candidates.

## Dynamic Knowledge Evolution

Novi can create new entities, attributes, relationships and—when justified—new schema structures. It must first attempt to fit new information into existing structures.

```text
new concept
 ↓
existing entity?
 ↓ no
existing type?
 ↓ no
existing attribute/relation?
 ↓ no
schema proposal
 ↓
validation/policy
 ↓
migration
```

The immutable protected system area is never modified by this mechanism.

## Provenance and Epistemic State

Memory must preserve the distinction between:

- observed;
- reported;
- inferred;
- hypothesized;
- predicted;
- verified;
- contradicted;
- stale;
- unknown.

A generated statement is never authoritative merely because an LLM produced it.

## NVIDIA Findings and Constraints

NVIDIA's NeMo Agent Toolkit currently provides pluggable memory providers including Mem0, MemMachine, Redis and Zep, plus an automatic memory wrapper and a `MemoryManager` abstraction for higher-level operations such as summarization/reflection. citeturn0search1turn0search9

NVIDIA's NeMo Retriever provides indexing/querying services for multimodal data and a standard retrieval architecture, while the Agentic RAG blueprint demonstrates planning, retrieval, retry, synthesis and verification for complex knowledge queries. citeturn0search6turn0search0

These are **reference implementations and integration candidates**, not architectural mandates. Some NVIDIA Retriever ingestion deployments have substantial infrastructure requirements, so they should not be assumed suitable for the Jetson itself; resource-heavy indexing can remain a development/server-side workload while the robot uses a lightweight local retrieval runtime. citeturn0search10

## Local-First Requirement

The production robot should remain useful without cloud memory services. Any external backend must have a documented reason, data-flow/privacy assessment, local fallback where practical, and migration path.

## Detailed Documentation

The following documents define the implementation in progressively greater detail:

- `00_HIGH_LEVEL_MEMORY_ARCHITECTURE.md`
- `01_MEMORY_TAXONOMY.md`
- `02_MEMORY_LIFECYCLE.md`
- `03_MEMORY_WRITE_AND_ADMISSION_POLICY.md`
- `04_MEMORY_CONSOLIDATION_AND_FORGETTING.md`
- `05_MEMORY_RETRIEVAL_AND_RANKING.md`
- `06_SEMANTIC_KNOWLEDGE_AND_SCHEMA_EVOLUTION.md`
- `07_EPISODIC_MEMORY.md`
- `08_PROCEDURAL_RELATIONSHIP_SPATIAL_AND_TEMPORAL_MEMORY.md`
- `09_PROVENANCE_CONFIDENCE_AND_CONTRADICTIONS.md`
- `10_STORAGE_SQLITE_FILES_AND_INDEXES.md`
- `11_VECTOR_AND_EMBEDDING_ARCHITECTURE.md`
- `12_MEMORY_SECURITY_PRIVACY_AND_ISOLATION.md`
- `13_MEMORY_API_AND_CAPABILITY_CONTRACTS.md`
- `14_MEMORY_GENERATION_AND_LEARNING.md`
- `15_NVIDIA_NEMO_MEMORY_AND_RETRIEVAL_EVALUATION.md`
- `16_ALTERNATIVE_OPEN_SOURCE_MEMORY_SOLUTIONS.md`
- `17_MEMORY_TESTING_AND_BENCHMARKING.md`
- `18_MEMORY_OBSERVABILITY_AND_AUDIT.md`
- `19_MEMORY_BACKUP_RECOVERY_AND_MIGRATION.md`
- `20_MEMORY_IMPLEMENTATION_ROADMAP.md`

## Status

**DESIGN — INITIALIZED**

This folder begins from architecture research. Implementation choices will be benchmarked rather than assumed.
