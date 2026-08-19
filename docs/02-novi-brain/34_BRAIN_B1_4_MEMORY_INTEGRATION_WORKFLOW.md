# B1.4 — Memory Integration Workflow

**Status:** P0 workflow — implementation complete, validation pending  
**Domain:** Brain / Memory boundary  
**Stage:** B1 Closed Simulated Loop  
**Date:** 2026-08-19  
**Authority:** `docs/04-memory-and-knowledge/01_MEMORY_TAXONOMY_AND_CORE_MODEL.md`, `02_MEMORY_LIFECYCLE_AND_ADMISSION.md`, `04_MEMORY_CONSOLIDATION_RETRIEVAL_AND_CONTEXT.md`

## Purpose

Connect the deterministic B1 world and Cognition boundary to a governed Memory Manager so experience can persist across cognitive cycles without making retrieval equivalent to truth or allowing Memory to authorize actions.

## Architecture

```text
Observation / Event
        ↓
Memory Write Gate
        ↓
MemoryRecord
        ↓
Memory Manager
   ┌────┴─────┐
   ↓          ↓
 retrieve   forget
   ↓
Evidence package
   ↓
Cognition
```

The canonical Memory architecture defines Memory as an evidence-linked, governed state system and requires admission, provenance, deduplication, lifecycle and retrieval boundaries. fileciteturn89file0 fileciteturn102file0

## Implementation baseline

`brain/b1_memory.py` provides a deterministic in-process semantic baseline.

It intentionally does **not** select a production storage engine. The System Architecture storage ADR currently treats SQLite as a candidate requiring benchmark and fault-injection evidence before adoption. fileciteturn81file0

## Canonical contract

Memory records are validated against `novi.memory-record/1.0.0`, whose canonical schema requires memory ID, type, creation time, content, confidence, verification status, privacy class, revision and provenance. fileciteturn95file0

The implementation therefore does not invent a competing MemoryRecord schema.

## Admission gate

The B1 baseline rejects:

- missing provenance;
- empty content;
- confidence outside `[0,1]`.

Accepted records receive deterministic IDs derived from canonical content, making repeated admission idempotent.

This is intentionally a small executable subset of the canonical lifecycle rather than a claim that the complete production admission policy has been implemented. The canonical lifecycle includes identity, integrity, privacy, poisoning/anomaly checks, retention and policy evaluation. fileciteturn102file0

## Retrieval

The B1 baseline provides deterministic lexical/entity retrieval with stable tie-breaking. It is deliberately not a vector database or LLM retrieval pipeline.

The canonical architecture requires retrieval to preserve provenance, apply hard eligibility filters, distinguish retrieval from truth, and eventually support multiple candidate-generation mechanisms. fileciteturn104file0

## Forgetting

`forget()` removes a record from active retrieval while retaining a tombstone in the manager's lifecycle state. This demonstrates the architectural distinction between active eligibility and destructive deletion. Full privacy-aware deletion and dependency propagation remain later Memory implementation work.

## Non-goals

B1.4 does not claim:

- production durable storage;
- SQLite adoption;
- vector retrieval;
- embeddings or reranking;
- knowledge-graph implementation;
- consolidation engine;
- privacy/erasure completion;
- backup/recovery completion;
- distributed replication;
- learned memory selection.

## Acceptance criteria

1. MemoryRecord uses the canonical contract;
2. provenance is required;
3. invalid confidence is rejected;
4. admission is deterministic;
5. duplicate admission is idempotent;
6. retrieval is deterministic;
7. retrieval can be entity scoped;
8. forgotten records are no longer retrievable;
9. Memory cannot authorize actions;
10. no production storage technology is prematurely adopted;
11. implementation remains compatible with later durable-storage selection.

## Validation

The repository Brain CI workflow executes all tests under `brain/tests`, including B1.4. B1.4 becomes **VALIDATED** only after that CI workflow passes for the resulting `main` revision.

## Architectural boundary

```text
Memory
  = persistence + lifecycle + retrieval context

Cognition
  = interpretation + reasoning

Autonomy
  = action selection

Policy / Safety
  = authorization
```

This separation remains mandatory as the implementation becomes more sophisticated.
