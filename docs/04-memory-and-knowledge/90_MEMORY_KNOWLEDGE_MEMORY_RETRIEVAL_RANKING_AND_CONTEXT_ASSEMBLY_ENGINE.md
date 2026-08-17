# 90 — Memory Knowledge Memory Retrieval, Ranking and Context Assembly Engine

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi retrieves memories, ranks competing candidates, resolves relevance against the current task, assembles a minimal trustworthy context, and exposes provenance and uncertainty to downstream reasoning.

This document is the operational complement to documents 74–89. Document 89 defines how durable memories are consolidated and reconsolidated; document 86 defines metamemory and confidence; document 87 defines decay and erasure; document 88 defines privacy and access control. Document 90 defines how the system selects what reasoning is allowed to see at retrieval time.

## Core Principle

> **Retrieval is not a database lookup. It is a governed evidence-selection process that must optimize task relevance without sacrificing provenance, freshness, uncertainty, independence, privacy or safety.**

A memory being highly similar to a query is not sufficient reason to use it.

---

## 1. Research Boundary

Novi's retrieval architecture is informed by both cognitive memory-search research and modern information-retrieval/RAG research. These bodies of work motivate engineering principles but do not imply that Novi reproduces biological memory mechanisms.

Human memory research shows that retrieval depends strongly on retrieval cues and context; failure to retrieve does not necessarily mean that information was never encoded. Computational memory-search research also models retrieval as a context-sensitive search process rather than a simple address lookup.

Modern retrieval-augmented generation research identifies relevance, accuracy, faithfulness, robustness, privacy and provenance as distinct evaluation concerns. Retrieval quality therefore cannot be reduced to embedding similarity alone.

Representative cross-validation sources:

- Kahana (2020), *Computational Models of Memory Search*, Annual Review of Psychology. https://www.annualreviews.org/content/journals/10.1146/annurev-psych-010418-103358
- *The neurobiological foundation of memory retrieval* (review), PMC. https://pmc.ncbi.nlm.nih.gov/articles/PMC6903648/
- Yu et al. (2024), *Evaluation of Retrieval-Augmented Generation: A Survey*. https://arxiv.org/abs/2405.07437
- Zhao et al. (2024), *Retrieval Augmented Generation (RAG) and Beyond: A Comprehensive Survey on How to Make your LLMs use External Data More Wisely*. https://arxiv.org/abs/2409.14924
- Zhou et al. (2024), *Trustworthiness in Retrieval-Augmented Generation Systems: A Survey*. https://arxiv.org/abs/2409.10102
- Sharma (2025), *Retrieval-Augmented Generation: A Comprehensive Survey of Architectures, Enhancements, and Robustness Frontiers*. https://arxiv.org/abs/2506.00054

The research consistently supports a modular retrieval architecture with explicit evaluation of relevance and grounding rather than treating retrieval as a single similarity operation.

---

## 2. Cross-Validation Requirements

Every production retrieval strategy should be evaluated against:

- retrieval relevance;
- retrieval recall;
- precision of selected context;
- provenance completeness;
- factual grounding;
- freshness;
- conflict handling;
- privacy enforcement;
- robustness to poisoned or misleading memories;
- latency and resource cost;
- downstream answer quality.

No single benchmark or retrieval metric is sufficient.

Where evidence conflicts, the implementation should prefer explicit uncertainty and modular fallbacks over hidden assumptions.

---

## 3. Retrieval Is a Pipeline

```text
CURRENT TASK
    ↓
TASK / INTENT INTERPRETATION
    ↓
RETRIEVAL POLICY
    ↓
CANDIDATE GENERATION
    ↓
ACCESS / PRIVACY FILTER
    ↓
RELEVANCE RANKING
    ↓
EVIDENCE QUALITY RANKING
    ↓
TEMPORAL / SPATIAL FILTERING
    ↓
CONFLICT & INDEPENDENCE ANALYSIS
    ↓
DIVERSIFICATION
    ↓
CONTEXT BUDGETING
    ↓
CONTEXT ASSEMBLY
    ↓
PROVENANCE / UNCERTAINTY PACKAGING
    ↓
REASONING
```

Each stage has a separate responsibility.

---

## 4. Retrieval Must Be Task-Conditioned

The same memory can be relevant to one task and irrelevant to another.

```text
MEMORY X
 ↓
TASK A → relevant
TASK B → irrelevant
TASK C → dangerous if stale
```

Retrieval therefore begins with the current task, not with a generic semantic search.

---

## 5. Query Understanding

The retrieval controller should derive, where applicable:

- entities;
- requested facts;
- time range;
- location;
- user/person scope;
- task type;
- desired memory class;
- freshness requirement;
- safety level;
- confidence threshold;
- authorization context.

If query interpretation is ambiguous, retrieval should preserve multiple plausible interpretations rather than prematurely selecting one.

---

## 6. Retrieval Policy

A retrieval policy should specify:

```text
WHAT MAY BE RETRIEVED?
FROM WHICH MEMORY CLASSES?
FOR WHICH PURPOSE?
WITH WHAT FRESHNESS?
AT WHAT CONFIDENCE?
UNDER WHICH AUTHORIZATION?
WITH WHAT SAFETY CONSTRAINTS?
```

Document 88 remains authoritative for access control.

---

## 7. Candidate Generation

Candidate generation may use multiple retrieval channels:

- lexical search;
- dense/vector search;
- structured metadata filters;
- graph traversal;
- temporal search;
- spatial search;
- entity search;
- episodic search;
- semantic-memory lookup;
- procedural-memory lookup;
- prospective-memory lookup;
- cross-agent memory lookup.

No individual channel should be assumed universally superior.

---

## 8. Hybrid Retrieval

A robust architecture should support combining lexical and semantic retrieval.

```text
LEXICAL
   +
SEMANTIC
   +
STRUCTURED
   +
GRAPH
   ↓
CANDIDATE SET
```

Hybrid retrieval is especially useful when exact names, identifiers, dates or terminology matter alongside conceptual similarity.

---

## 9. Candidate Pool vs Final Context

The candidate pool can be large.

The reasoning context should be small enough to remain interpretable and efficient.

```text
1000 CANDIDATES
      ↓
FILTER / RANK / DIVERSIFY
      ↓
10–50 HIGH-VALUE ITEMS
      ↓
FINAL CONTEXT
```

Exact limits should be task and model dependent.

---

## 10. Hard Filters Before Soft Ranking

Some conditions must be enforced before relevance scoring:

- authorization;
- deletion state;
- privacy policy;
- safety restrictions;
- retention state;
- incompatible scope;
- invalid/corrupt records.

A highly relevant but unauthorized memory must never win a ranking competition.

---

## 11. Relevance Is Multi-Dimensional

Retrieval relevance should consider at least:

- semantic relevance;
- lexical relevance;
- task relevance;
- entity relevance;
- temporal relevance;
- spatial relevance;
- causal relevance;
- procedural relevance;
- conversational relevance.

---

## 12. Recency Is Not Universally Good

Recent information should not automatically outrank older information.

For historical questions:

```text
OLD + CORRECT
    >
NEW + IRRELEVANT
```

For current-state questions, freshness may become dominant.

Freshness must therefore be task-conditioned.

---

## 13. Freshness Model

A memory can be evaluated as:

```text
FRESH
CURRENTLY VALIDATED
AGING
STALE
REQUIRES REVALIDATION
HISTORICAL-ONLY
```

Document 86 defines the metamemory state; document 90 uses it during retrieval.

---

## 14. Temporal Reasoning

The engine should distinguish:

```text
EVENT TIME
OBSERVATION TIME
RECORD TIME
CONSOLIDATION TIME
LAST VALIDATION TIME
RETRIEVAL TIME
```

These timestamps answer different questions.

---

## 15. Temporal Query Semantics

Examples:

```text
"What happened yesterday?"
→ event time

"When did Novi learn this?"
→ acquisition/consolidation time

"Is this still true?"
→ current validity / last validation
```

The retrieval controller must not substitute one temporal dimension for another.

---

## 16. Spatial Retrieval

Spatial queries should use:

- coordinates;
- spatial hierarchy;
- geofences;
- route relationships;
- place/entity identifiers;
- localization uncertainty.

A point estimate should not erase localization uncertainty.

---

## 17. Identity Filtering

Identity should be represented separately from semantic similarity.

```text
SIMILAR FACE
 ≠
CONFIRMED PERSON
```

Identity-sensitive memories require the identity confidence and authorization policy from documents 86 and 88.

---

## 18. Memory-Class Routing

Different tasks should prefer different memory classes.

```text
"What happened?"
→ episodic

"What is true about X?"
→ semantic + supporting episodes

"How do I do X?"
→ procedural

"What did I intend to do?"
→ prospective

"How reliable is this memory?"
→ metamemory
```

Multiple classes may be retrieved when the task requires them.

---

## 19. Episodic Retrieval

Episodic retrieval should prioritize:

- event identity;
- temporal context;
- location;
- participants;
- observed actions;
- source provenance.

Where appropriate, retrieve both the episode and relevant supporting evidence.

---

## 20. Semantic Retrieval

Semantic retrieval should prioritize stable abstractions while retaining links to supporting evidence.

```text
SEMANTIC FACT
   ↓
SUPPORTING EPISODES
```

A semantic assertion should not become self-authenticating merely because it is stored in the semantic layer.

---

## 21. Procedural Retrieval

Procedural retrieval should consider:

- task match;
- current capability;
- preconditions;
- validation history;
- exceptions;
- safety classification;
- version.

An old procedure should not automatically be executed because it matches the task semantically.

---

## 22. Prospective Retrieval

Prospective memories should be retrieved with:

- owner;
- due time;
- trigger condition;
- status;
- authorization;
- cancellation state;
- confidence.

A recalled intention is not automatically an active command.

---

## 23. Metamemory Retrieval

For any important memory candidate, metamemory can supply:

- source quality;
- retrieval completeness;
- freshness;
- confidence;
- conflict state;
- provenance;
- authorization state;
- reconstruction state.

This metadata should influence ranking and be exposed to reasoning when material.

---

## 24. Evidence Quality vs Relevance

A memory can be highly relevant but weak evidence.

```text
HIGH RELEVANCE
+
LOW EVIDENCE QUALITY
```

must not become a high-confidence answer merely because it ranks first.

Conversely, extremely reliable information may be irrelevant to the task.

---

## 25. Ranking Model

A conceptual ranking score may combine:

```text
S = f(
  task relevance,
  semantic similarity,
  lexical match,
  temporal fit,
  spatial fit,
  evidence quality,
  freshness,
  source reliability,
  provenance completeness,
  memory class fit,
  conflict state,
  independence,
  access policy,
  risk,
  redundancy,
  cost
)
```

This is a design abstraction, not a mandated single mathematical formula.

---

## 26. Hard Constraints vs Ranking Features

Hard constraints answer:

```text
CAN THIS MEMORY BE USED?
```

Ranking answers:

```text
WHICH ALLOWED MEMORY SHOULD BE USED FIRST?
```

These must never be conflated.

---

## 27. Confidence-Aware Ranking

Confidence can affect ranking, but it must not erase uncertainty.

A highly confident but irrelevant memory should not outrank a directly relevant memory.

Likewise, a low-confidence memory may remain useful as a hypothesis when the task explicitly permits uncertain evidence.

---

## 28. Risk-Aware Ranking

High-risk tasks should require stronger evidence.

```text
LOW-RISK QUESTION
→ broader retrieval tolerance

HIGH-RISK ACTION
→ narrow, fresh, authoritative evidence
```

The retrieval threshold should therefore be coupled to task risk.

---

## 29. Retrieval Abstention

If no candidate satisfies the required evidence threshold:

```text
NO SAFE MEMORY MATCH
        ↓
ABSTAIN / REQUEST MORE EVIDENCE
```

Retrieval should not always return an answer.

---

## 30. Retrieval Failure Semantics

The engine must distinguish:

```text
NO MATCH
RETRIEVAL FAILURE
ACCESS DENIED
MEMORY DELETED
SOURCE UNAVAILABLE
INDEX STALE
INSUFFICIENT EVIDENCE
```

These states have different downstream implications.

---

## 31. Conflict Retrieval

When competing memories exist, retrieval should expose the conflict rather than silently selecting the most similar one.

```text
CLAIM A
CLAIM B
 ↓
CONFLICT SET
 ↓
REASONING SEES BOTH
```

The ranking system may prioritize one claim, but it must preserve material contradictory evidence.

---

## 32. Conflict Severity

Conflict handling should depend on consequence:

```text
LOW
MODERATE
HIGH
SAFETY-CRITICAL
```

Safety-critical conflicts require conservative handling and stronger validation.

---

## 33. Source Independence

Evidence independence must be modeled explicitly.

```text
SOURCE A
 ├─ SUMMARY B
 ├─ EMBEDDING C
 └─ DERIVED FACT D
```

These are one lineage, not four independent confirmations.

---

## 34. Correlation Penalty

Ranking should avoid filling the context with many near-duplicate derivatives.

A diversity/correlation penalty can preserve independent evidence.

---

## 35. Evidence Diversity

When multiple candidates are relevant, prefer complementary evidence where useful:

```text
DIRECT OBSERVATION
+
INDEPENDENT SENSOR
+
USER CONFIRMATION
```

rather than:

```text
ONE OBSERVATION
+
10 GENERATED SUMMARIES
```

---

## 36. Context Diversity

Final context should avoid redundancy across:

- source records;
- summaries;
- duplicate episodes;
- correlated agents;
- repeated retrieval results.

Diversity improves the information value of a fixed context budget.

---

## 37. Context Budget

The final context must respect:

- token budget;
- latency budget;
- model context limits;
- memory bandwidth;
- privacy limits;
- task complexity.

More context is not automatically better.

---

## 38. Minimum Sufficient Context

The target should be:

```text
MINIMUM SUFFICIENT TRUSTWORTHY CONTEXT
```

not maximum context.

Extra irrelevant information can distract reasoning and increase privacy exposure.

---

## 39. Context Assembly

A final context package should normally contain:

```text
TASK INTERPRETATION
RELEVANT MEMORIES
EVIDENCE / PROVENANCE
CONFLICTS
UNCERTAINTY
FRESHNESS
AUTHORIZATION RESULT
RETRIEVAL LIMITATIONS
```

Only information necessary for the task should be included.

---

## 40. Provenance Packaging

Each important retrieved claim should be traceable to:

- memory identifier;
- source record;
- source type;
- timestamp;
- transformation lineage;
- confidence/status;
- validation state.

Reasoning should never have to infer provenance from prose alone.

---

## 41. Claim-Level Grounding

Where feasible, context should preserve claim-to-source mappings:

```text
CLAIM 1 → SOURCE A
CLAIM 2 → SOURCE B + SOURCE C
CLAIM 3 → INFERENCE FROM A + B
```

This supports downstream faithfulness checking.

---

## 42. Retrieved Evidence vs Generated Interpretation

The context should distinguish:

```text
RETRIEVED FACT
RETRIEVED REPORT
MODEL INFERENCE
SYSTEM SUMMARY
```

Generated interpretations must never masquerade as retrieved observations.

---

## 43. Query Expansion

Query expansion may use:

- aliases;
- known entities;
- temporal variants;
- synonyms;
- prior conversation context;
- related graph nodes.

Expansion should be controlled because incorrect expansion can introduce retrieval contamination.

---

## 44. Query Expansion Provenance

The system should record how an expanded query was produced.

If expansion introduced an incorrect entity or concept, the retrieval pipeline should be able to identify that source of error.

---

## 45. Multi-Hop Retrieval

Complex tasks may require:

```text
ENTITY A
 ↓
RELATION
 ↓
ENTITY B
 ↓
EPISODE
 ↓
EVIDENCE
```

Each hop should preserve provenance and confidence.

---

## 46. Multi-Hop Risk

Every additional retrieval hop increases opportunities for:

- drift;
- irrelevant branching;
- unsupported inference;
- provenance loss;
- context explosion.

Use bounded search depth and explicit stopping criteria.

---

## 47. Iterative Retrieval

Reasoning may request additional retrieval when:

- evidence conflicts;
- confidence is insufficient;
- a key entity is missing;
- a temporal gap exists;
- a source needs verification.

The second retrieval should be targeted rather than repeating the original broad search.

---

## 48. Retrieval Feedback

Downstream reasoning can provide feedback such as:

```text
MISSING EVIDENCE
WRONG ENTITY
INSUFFICIENT TIME RANGE
CONFLICT UNRESOLVED
SOURCE TOO WEAK
```

The retrieval controller can use this feedback to refine the search.

Modern RAG research increasingly treats retrieval as an adaptive component rather than a fixed one-shot operation.

---

## 49. Retrieval Contamination

Retrieved content must not automatically modify memory merely because it entered context.

```text
RETRIEVED
 ≠
LEARNED
```

Memory update requires the consolidation/reconsolidation policies of document 89.

---

## 50. Context-to-Memory Boundary

The architecture must preserve:

```text
MEMORY STORE
    ↓
RETRIEVAL
    ↓
TEMPORARY CONTEXT
    ↓
REASONING
```

Context is not automatically a new memory.

---

## 51. Prompt Injection / Poisoned Memory

Memory may contain adversarial or misleading text.

Retrieved content should therefore be treated as **data**, not as unrestricted instructions.

Instruction authority must come from the control hierarchy, not from a stored memory fragment.

---

## 52. Memory Trust Boundaries

Every retrieved item should have a trust classification such as:

```text
SYSTEM-AUTHORED
USER-AUTHORED
OBSERVED
EXTERNAL
MODEL-GENERATED
UNVERIFIED
```

Trust class affects how the content can influence reasoning and action.

---

## 53. Retrieval and Tool Authority

A memory may describe an authorization, credential, command or policy, but retrieval does not activate that authority.

Current authorization must be checked independently.

---

## 54. Privacy Filtering

Privacy and authorization filtering must happen before the final context is constructed.

The reasoning model should not receive information that it is not permitted to use merely so that it can be instructed to ignore it.

---

## 55. Sensitive Query Handling

Sensitive retrieval should minimize:

- query expansion;
- copied content;
- logging;
- context duplication;
- exposure to unrelated components.

The retrieval system itself is part of the privacy boundary.

---

## 56. Deletion Awareness

Deleted memories must not be retrieved from:

- stale indexes;
- caches;
- replicas;
- summaries;
- embeddings;
- archived search snapshots.

Document 87 remains authoritative for erasure propagation.

---

## 57. Stale Index Handling

If an index points to a deleted or inaccessible source:

```text
INDEX HIT
 ↓
SOURCE CHECK
 ↓
INVALID / STALE
 ↓
REMOVE FROM RESULT
```

An index hit is not sufficient evidence of availability.

---

## 58. Cache Validation

Cached retrieval results should carry:

- cache timestamp;
- source version;
- policy version where relevant;
- invalidation state.

High-freshness tasks should bypass or revalidate stale caches.

---

## 59. Distributed Retrieval

Across Novi instances, retrieval should consider:

- local availability;
- replica freshness;
- synchronization state;
- trust domain;
- network latency;
- authorization;
- conflict state.

A remote result should retain its source-agent provenance.

---

## 60. Offline Retrieval

Offline Novi should distinguish:

```text
NO LOCAL MEMORY
```

from:

```text
REMOTE MEMORY CURRENTLY UNREACHABLE
```

It must not convert connectivity failure into a false statement about memory absence.

---

## 61. Spatial and GPS Memories

For outdoor memory retrieval, context may include:

- coordinate/time pair;
- localization uncertainty;
- route segment;
- map version;
- environmental conditions;
- historical traversal status.

Historical GPS evidence should not be treated as proof of current safety or accessibility.

---

## 62. Retrieval of Skills

Before surfacing a procedure for execution, verify:

```text
TASK MATCH
+
CAPABILITY
+
PRECONDITIONS
+
CURRENT VALIDITY
+
SAFETY
```

Retrieval alone must never authorize execution.

---

## 63. Retrieval of Intentions

A retrieved intention should be classified as:

```text
ACTIVE
PENDING
COMPLETED
CANCELLED
EXPIRED
SUPERSEDED
UNKNOWN
```

Historical intentions must not accidentally become current commands.

---

## 64. User Corrections

A user correction retrieved from memory should carry explicit provenance.

A correction may supersede a previous interpretation but should not silently erase the historical record unless deletion policy requires it.

---

## 65. Retrieval Explanation

For important decisions, the engine should be able to answer:

```text
Why was this memory retrieved?
Why was it ranked above alternatives?
What evidence supports it?
What evidence conflicts?
How fresh is it?
Was it independently corroborated?
What was excluded and why?
```

Explanations should derive from ranking/provenance metadata rather than generated post-hoc rationalizations.

---

## 66. Retrieval Audit

Record privacy-safe metadata for important retrieval events:

- task class;
- retrieval policy/version;
- candidate count;
- selected memory IDs;
- exclusion reasons;
- ranking model/version;
- freshness checks;
- conflict state;
- latency;
- final context size.

Do not log sensitive content unnecessarily.

---

## 67. Retrieval Evaluation

Measure separately:

### Retrieval

- Recall@K;
- Precision@K;
- MRR;
- nDCG;
- candidate coverage;
- latency.

### Grounding

- claim support;
- faithfulness;
- provenance completeness;
- contradiction exposure.

### System

- task success;
- hallucination rate;
- privacy leakage;
- unsafe retrieval rate;
- stale-memory usage;
- unnecessary context volume.

Modern RAG evaluation literature emphasizes that retrieval and generation quality must be evaluated separately as well as together.

---

## 68. Retrieval Regression Testing

Maintain benchmark suites for:

- exact entity retrieval;
- semantic retrieval;
- temporal retrieval;
- spatial retrieval;
- multi-hop retrieval;
- conflicting memories;
- stale memories;
- deleted memories;
- restricted memories;
- duplicate evidence;
- poisoned memories;
- low-confidence memories;
- procedural retrieval;
- prospective retrieval;
- offline retrieval.

---

## 69. Adversarial Testing

Test whether malicious memories can cause:

- instruction injection;
- privilege escalation;
- false authority;
- identity confusion;
- deletion bypass;
- privacy leakage;
- ranking manipulation;
- evidence inflation;
- stale-state execution.

---

## 70. Calibration Testing

Test whether retrieval confidence corresponds to actual retrieval usefulness.

A candidate ranked highly should not systematically have poor evidentiary quality.

Calibration should be measured by task class, because retrieval confidence may have different meanings across domains.

---

## 71. Resource-Aware Retrieval

Retrieval should account for:

- latency;
- energy;
- network cost;
- storage I/O;
- accelerator usage;
- context-token cost.

However, resource optimization must never bypass privacy or safety filters.

---

## 72. Graceful Degradation

If dense retrieval is unavailable:

```text
VECTOR SEARCH
     ↓ unavailable
LEXICAL / STRUCTURED / LOCAL GRAPH
```

If remote memory is unavailable:

```text
REMOTE
  ↓ unavailable
LOCAL MEMORY
  ↓
EXPLICIT LIMITATION
```

The fallback must preserve uncertainty.

---

## 73. Determinism and Reproducibility

For important decisions, preserve enough metadata to reproduce why a memory was selected:

- query representation/version;
- retrieval policy;
- index version;
- ranking version;
- source versions;
- authorization state.

Exact byte-for-byte reproduction may not always be possible, but causal auditability should be.

---

## 74. Versioned Retrieval Policies

Changing ranking logic can change Novi's behavior.

Therefore retrieval policies should be versioned:

```text
RETRIEVAL POLICY v1
        ↓
RETRIEVAL POLICY v2
```

Historical retrieval decisions should retain the policy/version metadata where auditability matters.

---

## 75. Ranking Model Evolution

A new ranking model must be evaluated for:

- relevance regressions;
- confidence calibration;
- privacy leakage;
- bias;
- safety regressions;
- evidence diversity;
- latency.

A higher benchmark score is not sufficient for deployment.

---

## 76. Context Assembly Ordering

A useful default ordering is:

```text
TASK / CONSTRAINTS
↓
DIRECT EVIDENCE
↓
HIGH-CONFIDENCE SEMANTIC KNOWLEDGE
↓
RELEVANT EPISODES
↓
PROCEDURES / INTENTIONS
↓
CONFLICTS / ALTERNATIVES
↓
UNCERTAINTY / LIMITATIONS
```

The exact ordering should be task-specific.

---

## 77. Context Compression

Compression may summarize redundant material, but compressed context must retain:

- provenance;
- uncertainty;
- conflict;
- temporal scope;
- source lineage.

Compression must not transform uncertain evidence into confident prose.

---

## 78. Summary Lineage

Every generated retrieval summary should retain links to the records it summarizes.

```text
SUMMARY S
 ├── SOURCE A
 ├── SOURCE B
 └── SOURCE C
```

If any source is later deleted or invalidated, the summary must be reevaluated under documents 87 and 89.

---

## 79. Context Expiration

A context assembled for one task should not automatically persist into another task.

Context should have:

- creation time;
- task scope;
- authorization scope;
- expiration/validity;
- source versions.

This reduces accidental cross-task contamination.

---

## 80. Cross-Task Contamination

Information retrieved for one purpose should not silently become available for unrelated purposes.

```text
TASK A CONTEXT
     ≠
GLOBAL MEMORY
```

If information should become durable memory, document 89's consolidation process must explicitly promote it.

---

## 81. Reasoning Feedback Boundary

Reasoning may request more evidence, but reasoning should not directly mutate retrieval rankings or memory truth without going through controlled update paths.

```text
REASONING
 ↓ request
RETRIEVAL
 ↓ evidence
REASONING
```

Memory mutation follows document 89.

---

## 82. Retrieval and Belief Revision

When new evidence changes a conclusion:

```text
OLD MEMORY
+
NEW RETRIEVAL
 ↓
CURRENT BELIEF
```

The old evidence remains traceable unless deletion policy requires its removal.

---

## 83. Retrieval and Metamemory Feedback

Retrieval outcomes should update metamemory when justified:

```text
EXPECTED SOURCE
 ↓
RETRIEVAL RESULT
 ↓
ACTUAL QUALITY
 ↓
SOURCE / INDEX RELIABILITY UPDATE
```

This creates a feedback loop without allowing the retrieval system to rewrite source history.

---

## 84. Retrieval and Consolidation Feedback

Repeated retrieval usefulness can be a signal for future consolidation, but retrieval frequency alone must not prove truth.

```text
FREQUENTLY USED
 → candidate for optimization

NOT

FREQUENTLY USED
 → therefore true
```

---

## 85. Retrieval Safety Gate

Before retrieved information influences a physical or high-impact action, verify:

```text
AUTHORIZATION
CURRENT STATE
SOURCE QUALITY
FRESHNESS
CONFLICTS
SAFETY POLICY
CAPABILITY
```

Retrieval is an evidence provider, not an action authority.

---

## 86. Architectural Invariants

1. Retrieval is task-conditioned.
2. Authorization and privacy are hard filters, not ranking features.
3. Deleted information must not be retrieved through stale derivatives.
4. Retrieval failure is distinct from memory absence.
5. Relevance is distinct from evidence quality.
6. Freshness is task-dependent.
7. Event time is distinct from retrieval and consolidation time.
8. Memory class should match task requirements.
9. Semantic similarity alone cannot establish truth.
10. Duplicate derivatives are not independent evidence.
11. Material conflicts must remain visible.
12. High-risk tasks require stronger evidence and freshness.
13. Retrieval may abstain when evidence is insufficient.
14. Retrieved content is data, not unrestricted instructions.
15. Retrieval does not grant authority.
16. Retrieval does not automatically create memory.
17. Context is temporary and task-scoped unless explicitly consolidated.
18. Generated summaries retain source lineage.
19. Context compression must preserve provenance and uncertainty.
20. Multi-hop retrieval must preserve provenance across every hop.
21. Remote unavailability is not equivalent to memory absence.
22. Stale indexes must be validated against authoritative sources.
23. Retrieval policies and ranking models are versioned.
24. Retrieval explanations must derive from actual metadata.
25. Retrieval evaluation must separate retrieval quality from generation quality.
26. Resource optimization cannot bypass safety or privacy.
27. Ranking changes require regression evaluation.
28. Reasoning feedback cannot directly rewrite memory truth.
29. Retrieval outcomes may inform metamemory but must not corrupt source history.
30. Retrieval frequency is not evidence of truth.

---

## 87. Final Principle

> **Novi should retrieve the smallest set of the strongest, freshest, authorized and most task-relevant memories needed for the current decision, preserve their provenance and uncertainty, expose meaningful conflicts, and abstain when the available evidence is not sufficient.**

The retrieval engine is therefore not merely a search layer. It is the boundary between Novi's accumulated memory and its current reasoning state. The quality of that boundary determines whether the system reasons from evidence or merely from whatever memory happens to look similar.