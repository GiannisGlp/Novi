# 00 — High-Level Memory Architecture

## Status

**DESIGN**

## Objective

Provide Novi with durable, queryable, provenance-aware memory and knowledge that can grow through experience while remaining local, auditable, secure and bounded.

## Architectural Separation

```text
Perception
   ↓
Autonomy / Cognition
   ↓
Memory Manager
   ├── working/session state
   ├── episodic memory
   ├── semantic knowledge
   ├── procedural memory
   ├── relationship memory
   ├── spatial/temporal memory
   └── preferences
        ↓
Storage + Indexes
        ↓
Retrieval
        ↓
Context Engine
```

Memory owns persistence. Cognition owns interpretation. Autonomy decides whether memory work is relevant to current behavior.

## Active vs Durable Memory

The system maintains a small active context and larger durable stores.

```text
ACTIVE
working state
current conversation
current situation
recent relevant memories
        │
        ▼
RETRIEVAL
        │
        ▼
DURABLE
episodes / knowledge / procedures / relationships / spatial state
```

The LLM context window is not the durable memory store.

## Memory Manager

The Memory Manager is the authoritative orchestration layer for:

- admission
- persistence
- retrieval coordination
- consolidation
- deduplication
- correction
- expiration
- deletion
- schema evolution requests
- provenance
- policy enforcement

The LLM may propose memory operations through typed interfaces; it cannot bypass the manager.

## Memory Admission

Not every observation becomes memory. Admission considers:

- importance
- novelty
- repetition
- future usefulness
- user relevance
- emotional/social relevance
- confidence
- verification
- privacy
- retention cost

## Retrieval

Simple questions should use the cheapest reliable retrieval path. Complex queries may use multi-stage retrieval, reranking, query decomposition and verification. NVIDIA's Agentic RAG design demonstrates this adaptive pattern. citeturn0search0

## Storage

Initial target:

- SQLite for authoritative structured state and relationships;
- filesystem for documents and large artifacts;
- local vector index for semantic retrieval;
- SQLite FTS or equivalent for lexical retrieval;
- optional graph layer only when relationship workloads justify it.

## Truth Model

Memory records are not automatically truth. Every durable claim has epistemic state and provenance.

## Safety Boundary

Memory cannot alter:

- protected safety rules;
- trust roots;
- authorization policies;
- protected runtime files;
- audit integrity configuration.

## Design Target

The architecture should run locally on the Mac during development and on Jetson AGX Orin 64GB for the robot, with heavier offline indexing/build pipelines allowed on a development workstation if necessary.
