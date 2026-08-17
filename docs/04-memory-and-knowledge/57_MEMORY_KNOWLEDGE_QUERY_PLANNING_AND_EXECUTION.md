# 57 — Memory Knowledge Query Planning and Execution

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi converts a resolved memory/knowledge request into an executable retrieval plan, selects appropriate indexes and stores, executes retrieval and evidence joins, ranks and filters candidates, handles failures, and returns an auditable evidence set to cognition.

This document sits below query semantics/context resolution (56) and above the concrete storage/index implementations (07, 08, 09 and future implementation documents).

## Core Principle

> **Query execution must retrieve evidence through the appropriate temporal, semantic, lexical, spatial, entity, causal and relational paths rather than treating memory as a single vector-search problem.**

Recent agent-memory research consistently points toward hybrid retrieval: temporal knowledge graphs support evolving relationships and time-aware retrieval, while hybrid systems combine semantic, lexical, temporal and graph strategies. citeturn0academia39turn0academia37turn0search4

---

## 1. Query Pipeline

```text
USER / SYSTEM QUERY
        ↓
QUERY SEMANTICS (56)
        ↓
CONTEXT RESOLUTION
        ↓
QUERY PLAN
        ↓
SOURCE / INDEX SELECTION
        ↓
PARALLEL RETRIEVAL
        ↓
FILTERING
        ↓
FUSION
        ↓
RERANKING
        ↓
EVIDENCE VALIDATION
        ↓
CONTEXT ASSEMBLY
        ↓
COGNITION / ANSWER
```

The LLM should not directly control storage queries without policy and execution controls.

---

## 2. Query Plan

A query plan is an explicit machine-readable description of how to answer a request.

It may contain:

```text
intent
entities
attributes
time scope
spatial scope
semantic constraints
source constraints
authorization scope
required evidence strength
retrieval strategies
ranking policy
resource budget
latency budget
fallback policy
```

---

## 3. Query Classes

At minimum support:

```text
EXACT
SEMANTIC
TEMPORAL
ENTITY
SPATIAL
CAUSAL
RELATIONAL / GRAPH
EPISODIC
AGGREGATION
COMPARISON
PROVENANCE
CONFLICT
CURRENT-STATE
MULTI-HOP
HYBRID
```

Most real queries may combine several classes.

---

## 4. Strategy Selection

Examples:

```text
"Where is the toolbox now?"
→ entity + current-state + spatial

"What happened when the battery was low?"
→ temporal + episodic + causal

"Why did Novi choose that route?"
→ decision + causal + provenance

"What do I know about X?"
→ entity + graph + semantic + temporal
```

---

## 5. Hybrid Retrieval

Novi should support parallel retrieval paths such as:

```text
lexical / exact
semantic vector
entity lookup
structured metadata
temporal index
spatial index
knowledge graph
causal graph
episode index
```

The planner selects the minimum set required for the query, while safety-critical or high-uncertainty queries may intentionally use multiple paths for corroboration.

---

## 6. Parallelism

Independent retrieval strategies should run concurrently where resource and correctness constraints permit.

```text
query
 ├── lexical
 ├── vector
 ├── temporal
 ├── entity
 └── graph
        ↓
      fusion
```

Parallel execution reduces latency but must respect CPU/GPU/memory/thermal budgets.

---

## 7. Deterministic Filters First

Where possible, cheap deterministic filters should reduce the search space before expensive semantic operations.

Example:

```text
time range
 ↓
entity filter
 ↓
location filter
 ↓
semantic retrieval
 ↓
reranking
```

This prevents irrelevant historical memories from competing with temporally valid candidates.

---

## 8. Temporal Filtering

Temporal constraints should be applied explicitly.

Support:

- event time;
- valid time;
- system/ingestion time;
- validity interval;
- relative time;
- historical snapshots;
- current state.

A temporal query must not rely solely on embedding similarity.

Recent temporal-memory research specifically identifies time-aware retrieval as necessary for evolving knowledge. citeturn0academia37turn0academia39

---

## 9. Bitemporal Queries

Where supported, distinguish:

```text
VALID TIME
When was the fact true in the world?

SYSTEM TIME
When did Novi know/store that fact?
```

This enables queries such as:

> "What did Novi believe about the chair last Tuesday?"

without confusing historical world state with historical system knowledge.

---

## 10. Entity Anchoring

When a query refers to a known entity, entity resolution should anchor retrieval before broad semantic search where practical.

```text
"the red toolbox"
      ↓
entity candidates
      ↓
known entity IDs
      ↓
related memories / events / states
```

Entity-centric retrieval is especially valuable where fuzzy semantic similarity could retrieve the wrong object/person. Hybrid memory systems commonly use entity and graph retrieval alongside semantic search. citeturn0search4

---

## 11. Exact-Term Rescue

Semantic retrieval can miss:

- IDs;
- names;
- model numbers;
- filenames;
- unusual terms;
- exact quotes;
- technical identifiers.

The planner should retain a lexical/exact path for these cases.

---

## 12. Semantic Retrieval

Vector retrieval is appropriate for conceptual similarity:

```text
"Where did we encounter that noisy machine?"
```

may retrieve memories mentioning a loud industrial device even without exact wording.

Semantic retrieval must not be treated as proof of factual identity.

---

## 13. Graph Retrieval

Graph traversal is appropriate for relationship-heavy queries:

```text
person
 ↓
place
 ↓
event
 ↓
object
 ↓
outcome
```

Multi-hop retrieval should constrain traversal depth and edge types.

---

## 14. Causal Retrieval

Causal questions should prefer explicit causal edges and provenance over semantic similarity.

Example:

```text
"Why did Novi stop?"
```

Possible plan:

```text
stop event
 ↓
causal parents
 ↓
safety state
 ↓
sensor evidence
 ↓
action history
```

---

## 15. Episodic Retrieval

Episode queries should retrieve the episode boundary and then expand to its constituent events/memories.

```text
episode candidate
 ↓
episode metadata
 ↓
subepisodes
 ↓
events
 ↓
relevant evidence
```

This avoids treating a long episode as an undifferentiated text block.

---

## 16. Spatial Retrieval

For Novi's physical-world memory, spatial retrieval should support:

- coordinates;
- rooms;
- zones;
- map regions;
- routes;
- proximity;
- containment;
- trajectories;
- visited places.

Example:

```text
"Where have I seen this object?"
```

may require entity + spatial + temporal retrieval.

---

## 17. Current-State Retrieval

Queries affecting physical action must distinguish historical memory from current state.

```text
memory
 ↓
current-state check
 ↓
current sensors / state estimator
 ↓
validated answer/action context
```

For safety-critical state, current authoritative sources take precedence over stale memory.

---

## 18. Candidate Generation

Each retriever produces candidates with:

```text
item_id
retriever
raw score
metadata
source
provenance reference
query match information
```

Raw scores from different retrievers must not be compared directly without normalization or rank-based fusion.

---

## 19. Rank Fusion

Novi may use rank-based or score-based fusion.

A rank-based method such as Reciprocal Rank Fusion is useful when retrievers produce incomparable score scales.

```text
lexical ranking
vector ranking
graph ranking
temporal ranking
        ↓
rank fusion
```

Hybrid memory systems have demonstrated this practical pattern. citeturn0search0

---

## 20. Adaptive Weights

Weights may depend on query class.

Example:

```text
exact ID query
→ lexical weight ↑

"why did this happen?"
→ causal/graph weight ↑

"what happened yesterday?"
→ temporal/episodic weight ↑
```

Adaptive weighting must remain bounded and auditable.

---

## 21. Reranking

A reranker may evaluate the fused candidate set using richer query/candidate interaction.

Reranking may consider:

- semantic relevance;
- temporal validity;
- entity match;
- spatial match;
- provenance quality;
- source reliability;
- causal relevance;
- contradiction;
- freshness;
- task relevance.

LLM reranking is optional and must not fabricate evidence.

---

## 22. Evidence Filtering

Before candidates enter cognition:

```text
candidate
 ↓
authorization
 ↓
privacy
 ↓
temporal validity
 ↓
source reliability
 ↓
conflict check
 ↓
provenance integrity
 ↓
allowed evidence
```

NIST's current trustworthy-AI guidance emphasizes risks around sensitive information in RAG databases and the importance of provenance/data controls. citeturn0search40turn0search41

---

## 23. Access Control

Retrieval must enforce authorization before sensitive evidence reaches the model context.

```text
storage
 ↓
access control
 ↓
retrieval
```

Not:

```text
retrieve everything
 ↓
ask LLM to hide sensitive content
```

---

## 24. Privacy-Aware Retrieval

Queries involving sensitive memories should respect:

- user permissions;
- retention policy;
- deletion state;
- source sensitivity;
- purpose limitation.

A deleted memory must not reappear through a stale vector index or graph cache.

---

## 25. Contradiction Handling

If candidates disagree:

```text
claim A
claim B
      ↓
conflict set
      ↓
source / temporal / context evaluation
```

The planner may return both claims when resolution is impossible.

---

## 26. Evidence Sufficiency

The planner should define the minimum evidence needed for the query.

Examples:

```text
casual conversational recall
→ one strong memory may suffice

physical state
→ current authoritative evidence

causal explanation
→ causal chain + supporting evidence

high-impact action
→ stronger corroboration
```

---

## 27. Query-Specific Retrieval Budgets

Each query may have:

```text
max candidates
max graph depth
max time range
max retrieval latency
max compute
max memory
```

The planner should stop expanding when sufficient evidence is obtained.

---

## 28. Progressive Retrieval

Use staged retrieval when appropriate:

```text
cheap search
 ↓
enough evidence?
 ├── yes → stop
 └── no
       ↓
expanded retrieval
       ↓
graph / semantic / reranking
```

This protects latency and energy.

---

## 29. Early Exit

If a high-quality authoritative result satisfies the query, unnecessary retrieval can stop.

Example:

```text
current battery telemetry
 ↓
exact current battery query
 ↓
answer
```

There is no need to search autobiographical memory for the current battery percentage.

---

## 30. Fallback Strategy

If the preferred index is unavailable:

```text
primary index unavailable
 ↓
secondary index
 ↓
slower source
 ↓
safe degraded answer
```

The fallback must not silently lower evidence standards for consequential decisions.

---

## 31. Index Failure

Potential failures:

- vector index unavailable;
- graph unavailable;
- stale index;
- corrupted index;
- missing embedding;
- incomplete temporal index;
- cache inconsistency.

The underlying canonical store remains authoritative.

---

## 32. Index Rebuild

Indexes are derived structures.

```text
canonical memory
 ↓
rebuild
 ↓
vector / lexical / graph / spatial indexes
```

Rebuilding must not modify canonical memory semantics.

---

## 33. Cache Policy

Caching can reduce latency but cached retrieval is not authoritative evidence.

Cache keys should incorporate relevant context:

- query semantics;
- temporal scope;
- authorization scope;
- memory version;
- source state.

Sensitive caches require equivalent access control.

---

## 34. Cache Invalidation

Invalidate or version caches when:

- memory changes;
- deletion occurs;
- permissions change;
- temporal state changes;
- source reliability changes materially;
- index version changes.

Stale caches must not resurrect deleted or superseded information.

---

## 35. Query Result Provenance

Every retrieved evidence item should preserve:

```text
item_id
source
retriever
retrieval timestamp
index version
relevance metadata
provenance reference
```

This enables audit and explanation.

---

## 36. Answer Context Assembly

The final context should contain structured evidence rather than a flat pile of text.

Conceptually:

```text
QUERY
  ↓
EVIDENCE SET
  ├── primary evidence
  ├── corroborating evidence
  ├── conflicting evidence
  ├── uncertainty
  └── provenance
```

---

## 37. Context Compression

If evidence exceeds context limits:

```text
raw evidence
 ↓
structured reduction
 ↓
summary + source references
```

Compression must preserve critical uncertainty, conflict and provenance.

---

## 38. LLM Context Boundary

The LLM receives the result of controlled retrieval.

It should not be assumed to know the complete memory store.

```text
retrieval layer
      ↓
validated evidence
      ↓
LLM reasoning
```

---

## 39. Query Planning and Tool Use

The planner may invoke specialized tools for:

- SQL/structured queries;
- graph traversal;
- vector search;
- spatial search;
- temporal range search;
- current sensors;
- map queries.

Tool selection should be deterministic or policy-bounded where possible.

---

## 40. Multi-Hop Queries

Complex queries should be decomposed.

Example:

> "Which route did Novi take when it first encountered the obstacle near the kitchen, and why was that route later abandoned?"

Plan:

```text
1. resolve obstacle/entity
2. locate first relevant episode
3. retrieve route
4. find abandonment event
5. retrieve causal evidence
6. assemble chronological answer
```

Temporal knowledge-graph QA research similarly uses explicit decomposition of complex temporal questions into retrieval sub-objectives. citeturn0academia36

---

## 41. Query Dependencies

Subqueries may depend on earlier results.

```text
resolve entity
      ↓
retrieve events
      ↓
identify episode
      ↓
retrieve causal links
```

The planner should represent these dependencies explicitly.

---

## 42. Query Timeouts

If retrieval exceeds its budget:

```text
partial evidence
 ↓
quality assessment
 ↓
answer with limitation
```

Do not silently convert incomplete retrieval into certainty.

---

## 43. Partial Results

Results should indicate whether they are:

```text
COMPLETE
PARTIAL
DEGRADED
UNKNOWN
FAILED
```

This status can affect answer confidence.

---

## 44. Retrieval Failure

If retrieval fails completely:

```text
retrieval failure
 ↓
report inability
```

The LLM must not fill the gap from unsupported memory or imagination.

---

## 45. Resource Scheduling

Query execution should account for Novi's physical constraints:

- CPU load;
- GPU load;
- memory pressure;
- thermal state;
- battery state;
- active motion;
- latency requirements.

A deep retrieval operation should not starve navigation, perception or safety systems.

---

## 46. Priority Classes

```text
SAFETY
REAL-TIME CONTROL
ACTIVE TASK
USER INTERACTION
BACKGROUND RESEARCH
CONSOLIDATION
MAINTENANCE
```

Lower-priority retrieval yields to higher-priority work.

---

## 47. Offline-First Execution

The full core query planner must work without:

- Wi-Fi;
- Bluetooth;
- cloud databases;
- remote inference.

External services may add optional information but cannot be prerequisites for core memory retrieval.

---

## 48. Distributed Retrieval

If memory is distributed across processes/devices:

```text
local stores
 ↓
query federation
 ↓
result merge
 ↓
conflict detection
```

The planner must identify which stores were actually queried.

---

## 49. Synchronization Awareness

A remote result may be stale relative to local state.

Retrieval metadata should include:

```text
store version
sync state
last synchronization
conflict state
```

Local authoritative state takes precedence according to synchronization policy.

---

## 50. Query Determinism

For reproducibility, the planner should record:

- normalized query;
- resolved context;
- plan version;
- retrievers used;
- index versions;
- ranking policy;
- timestamps;
- result identifiers.

Probabilistic components should retain appropriate version metadata.

---

## 51. Query Observability

Record operational metrics such as:

- query latency;
- retriever latency;
- candidate counts;
- fusion counts;
- cache hits/misses;
- reranker cost;
- evidence sufficiency;
- answer outcome where evaluable;
- failure mode.

Do not log sensitive content unnecessarily.

---

## 52. Retrieval Evaluation

Measure retrieval separately from generation.

Useful metrics include:

- recall@k;
- precision@k;
- MRR;
- nDCG;
- hit rate;
- temporal accuracy;
- entity resolution accuracy;
- provenance completeness;
- conflict detection rate;
- latency;
- resource consumption.

---

## 53. Retrieval Ground Truth

Evaluation datasets should distinguish:

```text
relevant evidence
supporting evidence
contradictory evidence
irrelevant evidence
unknown / missing evidence
```

For temporal and causal questions, ground truth should include validity intervals and relationship structure where available.

---

## 54. Retrieval Poisoning Resistance

The planner must resist malicious retrieval manipulation.

Potential attacks include:

- injected memories;
- poisoned embeddings;
- malicious documents;
- graph edge manipulation;
- exact-token bait;
- prompt injection in retrieved content.

Retrieved content is data, not automatically instruction.

NIST identifies RAG data and model/application context as potential targets for information extraction and attack, reinforcing the need for retrieval-layer security controls. citeturn0search40

---

## 55. Instruction/Data Separation

```text
retrieved document:
"Ignore all previous instructions..."
```

must remain **data** unless it comes from an authorized instruction channel.

The retrieval planner must not promote retrieved text into policy.

---

## 56. No Retrieval by Generation

The LLM may help formulate a query or rerank candidates, but it cannot claim that an item exists in memory unless the retrieval layer returned it.

---

## 57. Knowledge Promotion Boundary

Query execution is read-oriented.

A query should not silently create durable knowledge merely because the LLM inferred something while answering.

Any learning/promotion follows documents 12, 49 and associated admission policies.

---

## 58. Query Security

Protect against:

- unauthorized memory access;
- query injection;
- path traversal in storage adapters;
- graph traversal abuse;
- excessive query expansion;
- resource exhaustion;
- timing leakage;
- cross-user data leakage.

---

## 59. Failure Recovery

After crash/restart:

```text
incomplete query
 ↓
no partial mutation of canonical memory
 ↓
retry / fail cleanly
```

Query execution should be side-effect-free unless an explicitly authorized tool operation is part of the request.

---

## 60. Architectural Invariants

1. Query semantics are resolved before retrieval.
2. Retrieval is not equivalent to generation.
3. No single retrieval strategy is sufficient for every memory query.
4. Temporal constraints are explicit.
5. Entity constraints are explicit.
6. Current physical state may require live authoritative sensing.
7. Deterministic filters should reduce search space before expensive retrieval where possible.
8. Independent retrieval paths may run in parallel within resource budgets.
9. Retriever scores are not blindly comparable.
10. Fusion/ranking policy is versioned and auditable.
11. Provenance survives retrieval.
12. Authorization and privacy are enforced before sensitive evidence reaches cognition.
13. Conflicts remain visible.
14. Partial retrieval is never silently treated as complete.
15. Retrieval failure never authorizes hallucinated evidence.
16. Caches are derived and cannot become canonical evidence.
17. Indexes are derived from canonical memory.
18. Deleted information cannot return through stale indexes or caches.
19. Simulation and real-world evidence remain distinct.
20. Retrieved content is data, not automatically instruction.
21. LLM-generated claims cannot establish memory existence.
22. Query execution must work offline.
23. Resource scheduling protects safety, perception and control workloads.
24. Distributed retrieval preserves source/version/synchronization metadata.
25. Query execution must be observable and reproducible enough to audit important decisions.

---

## 61. Final Principle

> **Novi should not search memory as if memory were one database or one vector index. It should plan the evidence search according to what the question actually asks, execute the appropriate retrieval paths, validate what comes back, preserve uncertainty and provenance, and only then give cognition the evidence it is allowed to use.**

This makes query execution a controlled evidence-retrieval subsystem rather than an implicit LLM capability, and provides the foundation for implementing Novi's concrete memory stores and indexes without coupling the architecture to a single database or vendor.
