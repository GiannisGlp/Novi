# 56 — Memory Knowledge Query Semantics and Context Resolution

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi converts natural-language or system-generated information requests into precise memory and knowledge queries, resolves temporal/spatial/entity context, applies epistemic constraints, retrieves evidence, handles conflicts and uncertainty, and produces answers without silently inventing missing context.

This document defines **query semantics**, not a particular database or query language. The implementation may use relational queries, graph queries, vector retrieval, full-text search, structured indexes, or combinations of them.

## Research Basis

The architecture is informed by established semantic-query principles and W3C RDF/SPARQL work. RDF represents information as graph-structured statements, while RDF datasets support multiple named graphs and explicit graph separation; RDF 1.2 semantics defines formal entailment regimes rather than treating every syntactic match as truth. These principles support Novi's separation of source/context graphs, evidence and derived knowledge. citeturn0search0turn0search1

## Core Principle

> **A memory query must resolve what the user means, what time and place they mean, which entity they mean, what epistemic status is acceptable, and what evidence is required before retrieval is considered complete.**

---

## 1. Query Pipeline

```text
USER / SYSTEM REQUEST
        ↓
QUERY UNDERSTANDING
        ↓
ENTITY RESOLUTION
        ↓
TEMPORAL RESOLUTION
        ↓
SPATIAL RESOLUTION
        ↓
SCOPE / AUTHORITY CHECK
        ↓
QUERY PLAN
        ↓
RETRIEVAL
        ↓
EVIDENCE FILTERING
        ↓
RANKING
        ↓
CONFLICT / UNCERTAINTY ANALYSIS
        ↓
ANSWER GENERATION
        ↓
PROVENANCE ATTACHMENT
```

---

## 2. Query Is Not Retrieval

A natural-language request is not itself a database query.

```text
"Where is the chair?"
```

must first be interpreted as something like:

```text
entity = chair candidate
predicate = location
reference_time = now
reference_place = current context
validity = current
```

Only then should retrieval occur.

---

## 3. Query Intent

Supported intent classes should include:

```text
LOOKUP
HISTORY
COMPARISON
EXPLANATION
WHY / CAUSAL
LOCATION
TEMPORAL
IDENTITY
RELATIONSHIP
SUMMARY
COUNT
PATTERN
ANOMALY
PREFERENCE
KNOWLEDGE
PROVENANCE
CONFIDENCE
CONFLICT
```

A query may contain multiple intents.

---

## 4. Query Context

Every resolved query should have a structured context where applicable:

```text
subject
predicate
object
reference_time
time_interval
location
entity_scope
source_scope
epistemic_scope
privacy_scope
confidence_requirement
freshness_requirement
result_limit
```

---

## 5. Explicit vs Implicit Context

Explicit context has priority over inferred context.

```text
"Where was the robot at 14:00 yesterday?"
```

contains explicit temporal context.

```text
"Where was it yesterday?"
```

requires reference resolution.

Inferred context must remain distinguishable from explicit context.

---

## 6. Reference Resolution

Resolve references such as:

- it;
- he/she/they;
- this;
- that;
- here;
- there;
- yesterday;
- earlier;
- the other one;
- my usual route.

Resolution should use conversation context, active task context, workspace context and memory evidence according to authority rules.

---

## 7. Ambiguous References

If multiple entities match:

```text
chair_12
chair_19
```

Novi should not silently choose one when the distinction matters.

It should:

```text
ASK
or
RETURN AMBIGUITY
or
USE EXPLICITLY LABELED BEST MATCH
```

---

## 8. Entity Resolution

Entity resolution should consider:

- canonical ID;
- aliases;
- visual identity;
- spatial continuity;
- temporal continuity;
- object attributes;
- relationships;
- source confidence;
- re-identification evidence.

A name match alone is insufficient for high-impact operations.

---

## 9. Entity Identity Hypotheses

If identity is uncertain:

```text
entity candidate A
confidence = high

entity candidate B
confidence = moderate
```

The query result should preserve the ambiguity where relevant.

---

## 10. Temporal Semantics

Queries must distinguish:

```text
NOW
PAST
FUTURE
INTERVAL
POINT_IN_TIME
BEFORE
AFTER
DURING
SINCE
UNTIL
MOST_RECENT
FIRST
LAST
```

---

## 11. Relative Time

Terms such as:

```text
today
yesterday
last week
recently
this morning
before dinner
```

must be resolved using the applicable local clock, timezone and calendar context.

If exact resolution is impossible, the query retains a temporal uncertainty interval.

---

## 12. Historical vs Current Query

```text
"Where is the chair?"
→ current-state query

"Where was the chair yesterday?"
→ historical query
```

The current-state query must not be answered solely from stale historical memory when current state matters.

---

## 13. Temporal Validity Gate

Before using a memory as current knowledge:

```text
memory
 ↓
validity interval
 ↓
freshness
 ↓
contradictions
 ↓
current observation requirement
```

This follows the temporal-validity architecture in document 53.

---

## 14. Spatial Semantics

Resolve:

```text
HERE
THERE
HOME
ROOM
BUILDING
OUTDOORS
CITY
GPS REGION
MAP CELL
ROUTE SEGMENT
LANDMARK
```

Spatial references should be represented using canonical locations where available.

---

## 15. Spatial Frames

A query may use:

```text
robot-local frame
map frame
building frame
geographic frame
GNSS coordinates
```

Transformations must preserve coordinate-frame provenance.

---

## 16. "Here" Resolution

"Here" may refer to:

- Novi's current estimated pose;
- user's location if authorized and available;
- active conversation location;
- referenced place in the current task.

The chosen interpretation must be explicit internally.

---

## 17. "Now" Resolution

"Now" means the current query reference time, not the timestamp of the most recently retrieved memory.

Current sensor state may be required.

---

## 18. Context Window

Queries can inherit context from:

```text
current conversation
active goal
current episode
current location
current entities
recent events
```

Context inheritance must be bounded and auditable.

---

## 19. Context Precedence

A conceptual precedence order is:

```text
explicit current query
        ↓
explicit active task context
        ↓
explicit conversation context
        ↓
validated current state
        ↓
recent relevant memory
        ↓
older inferred context
        ↓
weak hypothesis
```

Higher-priority context must not be silently overridden by weaker retrieval.

---

## 20. Query Rewriting

A natural-language query may be transformed into a canonical query plan.

Example:

```text
"Where did we put the red toolbox?"
```

becomes approximately:

```text
entity_type = object
attributes = {color:red, type:toolbox}
relationship = location
subject_scope = known household entities
reference_time = latest valid placement
```

---

## 21. Query Plan

A query plan should describe:

- target entity/claims;
- filters;
- time constraints;
- spatial constraints;
- source constraints;
- confidence requirements;
- freshness requirements;
- privacy requirements;
- ranking strategy;
- evidence requirements.

---

## 22. Retrieval Sources

Retrieval may combine:

```text
structured memory
knowledge graph
full-text index
vector index
spatial index
temporal index
event store
working memory
current sensor state
```

No one retrieval mechanism is authoritative for every query.

---

## 23. Hybrid Retrieval

A complex query may require:

```text
semantic retrieval
+
structured filtering
+
vector similarity
+
spatial filtering
+
temporal filtering
```

The result should be merged using explicit semantics rather than arbitrary score addition.

---

## 24. Current-State Queries

Queries affecting physical action should prioritize current state.

Example:

```text
"Is the path clear?"
```

should normally use current perception/localization rather than historical memory alone.

---

## 25. Historical Queries

Historical queries should prioritize memories valid during the requested interval.

Example:

```text
"Where was the robot at 18:00 yesterday?"
```

should not be answered using today's location.

---

## 26. Temporal Aggregation

Support queries such as:

```text
first time
last time
most recent
most frequent
average duration
longest visit
number of visits
changes over time
```

Aggregations must declare their interval and inclusion rules.

---

## 27. Spatial Aggregation

Support:

```text
places visited
areas never visited
most frequent locations
route frequency
time spent by zone
```

These results should retain map/version context.

---

## 28. Episode Queries

Examples:

```text
What happened during the park visit?
What caused the navigation failure?
What did Novi learn from that episode?
```

Episode retrieval should return constituent events and causal links where needed.

---

## 29. Causal Queries

Queries beginning with:

```text
why
what caused
what led to
what resulted from
what would have happened
```

must use causal/evidence structures from documents 47–49.

A plausible LLM explanation is not sufficient evidence.

---

## 30. Provenance Queries

Examples:

```text
Where did you learn that?
What evidence supports this?
Who told you?
Which sensor detected it?
When did you learn it?
```

These should query provenance directly rather than reconstructing provenance from natural-language summaries.

---

## 31. Confidence Queries

Examples:

```text
How certain are you?
How reliable is this information?
Why are you uncertain?
```

Results should expose relevant uncertainty dimensions from document 52 and source reliability from document 54.

---

## 32. Conflict Queries

Example:

```text
"What do you know about the chair's location?"
```

If sources disagree:

```text
claim A
claim B
```

Novi should report the conflict rather than silently selecting a winner when the conflict matters.

---

## 33. Evidence Thresholds

Different query types require different evidence thresholds.

```text
casual conversation
 → moderate evidence may suffice

navigation
 → current high-quality state required

safety decision
 → highest applicable evidence/authority
```

---

## 34. Query-Specific Freshness

Freshness requirements depend on query semantics.

```text
"Where is Novi now?"
→ very fresh

"Where was Novi last Tuesday?"
→ historical accuracy

"What is my favorite coffee?"
→ preference freshness may be longer
```

---

## 35. Query-Specific Confidence

A result can be relevant but insufficiently certain.

```text
retrieval relevance = high
claim confidence = low
```

The system must not equate relevance with truth.

---

## 36. Query Result Types

Results should have explicit types:

```text
FACT
OBSERVATION
MEMORY
BELIEF
HYPOTHESIS
PREFERENCE
EVENT
EPISODE
RELATIONSHIP
CONFLICT
UNKNOWN
```

---

## 37. Unknown Result

If no sufficient evidence exists:

```text
UNKNOWN
```

must be a valid result.

Example:

> "I don't have enough evidence to determine where the toolbox is now."

---

## 38. Negative Result

Absence of retrieved evidence must not automatically mean the proposition is false.

```text
not found
 ≠
false
```

Unless the relevant closed-world policy explicitly establishes that interpretation.

---

## 39. Closed-World Queries

Some bounded domains may explicitly use closed-world semantics.

Example:

```text
registered_hardware_inventory
```

may allow:

```text
not registered → not in inventory
```

The query plan must identify when closed-world semantics apply.

---

## 40. Open-World Queries

General world knowledge should default toward open-world reasoning:

```text
absence of evidence
      ↓
UNKNOWN
```

This prevents memory sparsity from becoming false certainty.

---

## 41. Relevance Ranking

Ranking should consider:

- semantic relevance;
- temporal validity;
- spatial relevance;
- entity identity confidence;
- source reliability;
- provenance completeness;
- freshness;
- user intent;
- current task relevance.

No single embedding similarity score is authoritative.

---

## 42. Evidence Diversity

Ranking should prefer useful independent corroboration where appropriate.

Five near-duplicate observations from one source may be less informative than two independent sources.

---

## 43. Retrieval Deduplication

Repeated references to the same underlying event should not be counted as independent evidence.

Canonical IDs should support deduplication.

---

## 44. Result Contradiction Detection

Before answer generation:

```text
retrieved claims
 ↓
compatibility check
 ↓
conflict set
```

Conflicting claims remain separately represented.

---

## 45. Answer Synthesis

The answer generator should receive structured evidence, not only raw retrieved text.

```text
query plan
+
ranked evidence
+
conflicts
+
uncertainty
+
provenance
 ↓
answer
```

---

## 46. No Evidence Fabrication

The answer generator MUST NOT:

- invent missing events;
- invent sources;
- invent timestamps;
- invent certainty;
- merge unrelated entities;
- turn hypotheses into facts.

---

## 47. Answer Qualification

Answers should be qualified when required:

```text
KNOWN
LIKELY
POSSIBLE
CONFLICTED
STALE
UNKNOWN
```

The exact user-facing wording can be natural language.

---

## 48. Clarification Strategy

Novi should ask a clarification question when ambiguity materially changes the result.

Example:

> "Do you mean the red toolbox in the garage or the one in the workshop?"

If ambiguity does not materially affect the answer, Novi may proceed with an explicitly selected interpretation.

---

## 49. Safe Defaults

When clarification is impossible and the query affects physical action:

```text
uncertainty
 ↓
conservative interpretation
or
verify current state
or
abstain
```

---

## 50. Query Authorization

Queries must obey privacy and authorization boundaries.

A successful retrieval match does not imply permission to disclose or act on the information.

---

## 51. Privacy-Aware Retrieval

Sensitive memories should be filtered before answer generation where policy requires.

The LLM should not receive unauthorized candidate memories merely because they are semantically relevant.

---

## 52. Current Sensor Fusion

Memory retrieval may be combined with live sensing:

```text
historical memory
      +
current perception
      ↓
current belief
```

The result must preserve which part came from memory and which from current observation.

---

## 53. Retrieval as Evidence Gathering

Retrieval is an epistemic operation, not merely a relevance operation.

The system should ask:

```text
Is this relevant?
Is it valid?
Is it current enough?
Is the source reliable?
Is the entity correct?
Is there contradictory evidence?
```

---

## 54. Query Caching

Query results may be cached only when their temporal and validity requirements permit it.

A cached current-state answer must have explicit expiration/invalidating conditions.

---

## 55. Cache Invalidation

Invalidate relevant query results when:

- current state changes;
- source evidence is corrected;
- memory is deleted;
- knowledge is superseded;
- entity identity changes;
- spatial map changes;
- policy changes.

---

## 56. Query Planning Under Resource Constraints

For expensive queries:

```text
fast local index
 ↓
coarse filtering
 ↓
precise retrieval
 ↓
expensive reasoning only if necessary
```

Thermal, battery, CPU/GPU and latency budgets must be respected.

---

## 57. Offline Requirement

Core memory querying must work without Wi-Fi, Bluetooth or cloud access.

External information retrieval may be unavailable offline without making local memory inaccessible.

---

## 58. Distributed Querying

When multiple stores exist:

```text
local memory
remote/synchronized memory
sensor state
```

query results must retain source/store identity and synchronization state.

Stale synchronized state must not masquerade as current local state.

---

## 59. Query Versioning

Query semantics and ranking policies should be versioned.

Historical audit records should retain the query/policy version used for consequential decisions.

---

## 60. Query Replay

Important queries should be replayable for debugging and evaluation.

Replay should preserve:

- query;
- resolved context;
- retrieval candidates;
- ranking version;
- evidence state;
- answer version.

---

## 61. Testing Requirements

Test:

- entity ambiguity;
- pronoun resolution;
- relative dates;
- timezone boundaries;
- historical/current distinction;
- spatial frame conversion;
- stale memories;
- conflicting evidence;
- source reliability;
- unknown results;
- open-world behavior;
- closed-world behavior;
- privacy filtering;
- current sensor fusion;
- cache invalidation;
- distributed stale state;
- offline operation;
- thermal/resource pressure;
- provenance preservation;
- adversarial retrieval content;
- prompt injection in retrieved documents;
- answer hallucination prevention.

---

## 62. Architectural Invariants

1. Query interpretation precedes retrieval.
2. Explicit context outranks weak inferred context.
3. Entity ambiguity must remain visible when material.
4. Current queries require current-state validation where appropriate.
5. Historical queries respect historical validity intervals.
6. Relative time is resolved using correct clock/timezone context.
7. Spatial references retain coordinate-frame semantics.
8. Relevance is not truth.
9. Retrieval absence is not automatically falsity.
10. Open-world reasoning is the default for general memory.
11. Closed-world semantics must be explicit and bounded.
12. Conflicting evidence is preserved rather than silently averaged.
13. Source reliability and provenance participate in query evaluation.
14. Current sensor evidence can supersede stale memory for current physical state.
15. Privacy filtering occurs before unauthorized evidence reaches answer generation.
16. LLM output cannot manufacture evidence.
17. Unknown and abstention are valid results.
18. Consequential queries use stricter freshness, confidence and authorization gates.
19. Query results remain traceable to evidence.
20. Core query functionality works offline.
21. Cached results cannot silently become current truth after invalidation.
22. Query semantics and ranking policies are versioned.
23. Distributed stores retain source and freshness state.
24. No retrieval mechanism is universally authoritative.

---

## 63. Final Principle

> **Novi should answer the question the user actually asked, in the context they actually meant, using evidence that is valid for that question—not merely return the most semantically similar memory.**

Query semantics therefore form the bridge between Novi's human-facing cognition and the underlying memory/knowledge architecture. They determine not only what Novi retrieves, but whether the retrieved information is actually appropriate to use.
