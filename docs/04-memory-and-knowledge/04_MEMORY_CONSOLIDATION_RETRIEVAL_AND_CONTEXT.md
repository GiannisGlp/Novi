# 04 — Memory Consolidation, Retrieval and Context

**Status:** CANONICAL — CONSOLIDATED V1

## Purpose

Unify consolidation, forgetting, retrieval, ranking and context assembly without allowing retrieval to become a truth or authorization mechanism.

> Retrieval is not memory. Similarity is not truth. Consolidation is not summarization.

## Consolidation boundary

```text
observation
 ↓
event
 ↓
episode
 ↓
admitted candidate
 ↓
validation / deduplication
 ↓
active memory
 ↓
consolidation
 ├── merge
 ├── update
 ├── promote
 ├── demote
 ├── supersede
 ├── archive
 ├── expire
 └── delete
```

Consolidation determines what survives, how it is represented, what evidence supports it, what it supersedes and what should be discarded. fileciteturn205file0

## Online and background processing

Online memory work supports immediate continuity. Background work performs clustering, comparison, merge, validation, promotion, indexing and decay/archive operations. Background work must yield to safety-critical robot functions.

Triggers include session completion, repeated observations, contradictions, user correction, prediction error, resource pressure, checkpoint/shutdown and idle periods. A trigger schedules evaluation; it does not guarantee mutation. fileciteturn205file0

## Consolidation invariants

```text
CONSOLIDATION ≠ COPYING
RETRIEVAL ≠ RECONSOLIDATION
DERIVATIVE ≠ INDEPENDENT EVIDENCE
SIGNIFICANCE ≠ TRUTH
```

Repeated retrieval of a generated derivative must not create artificial evidentiary weight. fileciteturn214file0

## Evidence preservation

Consolidation must preserve the evidence graph for consequential knowledge:

```text
knowledge claim
   ├── evidence
   ├── provenance
   └── derivation lineage
```

Summaries reference source memories rather than irreversibly replacing them.

## Promotion

Promotion from episode to durable semantic knowledge considers recurrence, source reliability, independent evidence, confirmation, consistency, temporal stability, consequence of error, relevance and contradiction rate.

```text
observation
 ↓
episode
 ↓
repeated pattern
 ↓
routine hypothesis
 ↓
independent evidence
 ↓
knowledge candidate
 ↓
verification
 ↓
durable knowledge
```

Successful execution alone does not establish general procedural competence. fileciteturn214file0

## Forgetting versus deletion

Novi distinguishes:

- forget from active retrieval;
- archive;
- expire;
- delete;
- explicit user-directed deletion.

Forgetting may reduce retrieval priority or contextual eligibility without destroying historical evidence. Deletion is a separate privacy/lifecycle operation. fileciteturn205file0

## Retrieval architecture

```text
cognitive request
      ↓
query/context analysis
      ↓
retrieval policy
      ↓
parallel candidate generation
 ┌────┼────────┬──────────┬──────────┐
 ↓    ↓        ↓          ↓          ↓
exact semantic temporal structured relationship
 ↓    ↓        ↓          ↓          ↓
 └────┴────────┴──────────┴──────────┘
                 ↓
          candidate union
                 ↓
       authorization/privacy
                 ↓
          hard validity filters
                 ↓
             deduplication
                 ↓
          score normalization
                 ↓
             ranking
                 ↓
        optional reranking
                 ↓
       diversity / coverage
                 ↓
        context budgeting
                 ↓
          evidence package
                 ↓
              cognition
```

The system must not reduce retrieval to `query → vector top-k → LLM`. fileciteturn206file0

## Query understanding

A retrieval policy should capture, where applicable:

```text
intent
entities
relationships
time range
location
memory types
freshness requirement
minimum confidence
privacy scope
risk class
latency budget
candidate_k
final_k
reranking policy
```

Examples:

- preference query → semantic + preference + entity match;
- historical event query → episodic + temporal + spatial;
- current device/location query → structured operational state with high freshness.

## Candidate generation

Use multiple retrieval mechanisms as appropriate:

- exact/lexical;
- semantic/vector;
- temporal;
- structured/SQL;
- relationship/graph;
- file/document retrieval.

The initial local architecture can use SQLite for authoritative state and relationships, SQLite FTS or equivalent for lexical retrieval, a local vector index for semantic retrieval, and files for large artifacts. A separate graph database is not mandatory initially. fileciteturn216file0

## Hard filters versus ranking

Hard eligibility constraints include unauthorized scope, deleted records, invalid records, expired information when current validity is required, quarantined sources and inaccessible tenant/user scope.

Ranking signals include semantic relevance, lexical relevance, freshness, confidence, importance, source quality, relationship relevance, temporal fit and redundancy.

A forbidden memory must never become eligible because it scores highly for similarity. fileciteturn206file0

## Candidate pool and ranking

Candidate generation should favor recall; final ranking should favor precision.

```text
candidate_k > final_k
```

All candidates retain their originating retriever and original score. Scores from heterogeneous retrievers must be normalized or reconciled in a later ranking stage. fileciteturn206file0

## Retrieval is not truth

```text
SIMILARITY ≠ RELEVANCE ≠ TRUTH
RETRIEVAL RELEVANCE ≠ EVIDENCE QUALITY
EVIDENCE QUALITY ≠ AUTHORIZATION
```

Retrieval produces candidates. Evidence quality, provenance, freshness, conflict state and policy determine whether candidates are suitable for context.

## Context assembly

The context builder should produce the **minimum sufficient trustworthy context**, not maximize retrieved records.

Context packages preserve:

- provenance;
- uncertainty;
- conflicts;
- temporal validity;
- source boundaries;
- instruction/data separation;
- authorization/privacy decisions.

This is the boundary between memory retrieval and reasoning. fileciteturn214file0

## Current-state supremacy

Historical memory is not authoritative for current-state decisions when fresh authoritative observations exist.

```text
historical memory → context
current authoritative observation → current state
```

Examples include current location, obstacles, device state, authorization and safety conditions. fileciteturn214file0

## Read gate

```text
query
 ↓
authorization
 ↓
privacy filter
 ↓
relevance
 ↓
freshness
 ↓
evidence quality
 ↓
conflict / independence
 ↓
context budget
 ↓
working memory
```

Retrieval cannot bypass governance. fileciteturn214file0

## Source consolidation

Merged into this canonical document:

- `04_MEMORY_CONSOLIDATION_AND_FORGETTING.md`
- `05_MEMORY_RETRIEVAL_AND_RANKING.md`
- consolidation/retrieval/context requirements from Documents 78–90 and 95–96.

The historical documents remain preserved pending final supersession. fileciteturn205file0 fileciteturn206file0