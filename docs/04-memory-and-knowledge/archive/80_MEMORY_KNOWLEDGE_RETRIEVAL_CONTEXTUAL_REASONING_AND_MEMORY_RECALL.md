# 80 — Memory Knowledge Retrieval, Contextual Reasoning and Memory Recall

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi retrieves useful memories and knowledge for a current interaction, task, perception cycle, or decision without treating retrieval as simple keyword matching or overwhelming the reasoning context.

## Core Principle

> **Novi should retrieve what is relevant to the current situation, not everything that resembles the query.**

Recall is a governed pipeline combining semantic relevance, context, time, space, provenance, uncertainty, authority, privacy, task requirements, and resource limits.

## 1. Retrieval Pipeline

```text
CURRENT QUERY / TASK / STATE
          ↓
CONTEXT CONSTRUCTION
          ↓
CANDIDATE GENERATION
          ↓
ACCESS / PRIVACY FILTER
          ↓
RELEVANCE FILTER
          ↓
TEMPORAL / SPATIAL FILTER
          ↓
PROVENANCE / QUALITY CHECK
          ↓
RANKING
          ↓
DIVERSITY / CONTRADICTION CHECK
          ↓
CONTEXT BUDGETING
          ↓
MEMORY PACK
          ↓
REASONING
```

## 2. Recall Is Not Truth

Retrieval means an item is relevant enough to consider.

```text
RETRIEVED
 ≠
TRUE
```

Every recalled claim retains its status, provenance and uncertainty.

## 3. Query Types

Novi should distinguish:

- factual lookup;
- episodic recall;
- person recall;
- place recall;
- object recall;
- preference recall;
- spatial navigation;
- temporal recall;
- causal investigation;
- safety context;
- task planning;
- conversational continuity.

Different query types require different retrieval policies.

## 4. Context Construction

Context can include:

```text
user intent
conversation state
current task
current location
current time
recent events
active goals
sensor state
known entities
authorization scope
safety state
```

Only relevant context should enter retrieval.

## 5. Current Physical Context

For embodied Novi, retrieval should incorporate current physical context when relevant:

- pose;
- location;
- room/place;
- nearby objects;
- detected people;
- environmental state;
- active map version.

Current sensing remains authoritative for current physical state.

## 6. Multi-Modal Retrieval

Memory candidates can originate from:

- text;
- structured records;
- images;
- audio;
- spatial data;
- maps;
- sensor observations;
- event history;
- semantic graph;
- vector representations.

A retrieval layer may combine these modalities without collapsing their provenance.

## 7. Candidate Generation

Candidate generation may use multiple mechanisms:

```text
lexical search
semantic/vector search
entity lookup
graph traversal
temporal index
spatial index
recent-event index
explicit identifiers
```

No single retrieval mechanism should be assumed sufficient for all memory types.

## 8. Hybrid Retrieval

A practical architecture is:

```text
LEXICAL
   +
SEMANTIC
   +
GRAPH
   +
TEMPORAL
   +
SPATIAL
   +
RECENCY
```

The combination should be task-dependent.

## 9. Entity Resolution

Queries may refer to the same entity using different forms.

```text
"Mum"
"my mother"
"the person who sews bags"
```

Entity resolution must retain uncertainty when identity is ambiguous.

## 10. Ambiguous Entities

If multiple entities match:

```text
candidate A
candidate B
```

Novi should either retrieve both with qualification or request clarification when the distinction matters.

It must not silently merge identities.

## 11. Semantic Expansion

A query can expand through known relationships.

```text
QUERY: "kitchen"
 ↓
PLACE
 ↓
objects
people
routines
events
preferences
```

Expansion is bounded by relevance, authorization and context.

## 12. Associative Recall

A recalled memory may activate nearby semantic associations.

However, association strength is not evidence strength.

```text
associated
 ≠
confirmed
```

## 13. Spreading Activation

A graph-based implementation may use bounded spreading activation:

```text
seed entity
  ↓
1-hop associations
  ↓
selected 2-hop associations
```

Depth and branching must be constrained to prevent context explosion.

## 14. Temporal Retrieval

Temporal queries require explicit time semantics:

- current;
- recent;
- historical;
- before/after an event;
- during an interval;
- recurring pattern.

"Last time" must not be interpreted as "most recently indexed" when event time is available.

## 15. Spatial Retrieval

Spatial recall can use:

- exact location;
- radius;
- room/place;
- route;
- region;
- proximity;
- historical visited areas.

Spatial uncertainty must be preserved.

## 16. Map-Aware Retrieval

For Novi's outdoor use:

```text
CURRENT GNSS / LOCALIZATION
          ↓
CURRENT MAP
          ↓
VISITED-AREA MEMORY
          ↓
LANDMARKS / ROUTES
          ↓
RELEVANT RECALL
```

"Visited before" and "safe/accessible now" remain distinct properties.

## 17. Recency

Recency is a relevance feature, not a universal truth signal.

A recent incorrect observation must not automatically outrank a validated stable fact.

## 18. Freshness

Time-sensitive knowledge should carry freshness requirements.

```text
fresh enough for task
        ↓
usable

stale for task
        ↓
qualified / revalidate
```

## 19. Task-Specific Relevance

The same memory can be relevant to one task and irrelevant to another.

Example:

```text
route planning
 → map + obstacles + destination

conversation
 → preferences + previous discussion

maintenance
 → device history + sensor history
```

## 20. Goal-Directed Recall

Active goals can increase relevance for memories directly supporting the goal.

Goals must not cause unrelated private information to enter the reasoning context.

## 21. User Context

User preferences may influence retrieval when relevant and authorized.

Personalization must remain scoped to the correct user.

## 22. Privacy Filtering

Privacy and authorization filters should occur before sensitive memory is exposed to reasoning components whenever practical.

```text
candidate
 ↓
authorization
 ↓
privacy policy
 ↓
retrieval
```

Retrieval must not be used to bypass access controls.

## 23. Security Boundary

A retrieved memory is data, not an instruction.

Stored content must never automatically acquire execution authority.

This protects against memory-based prompt injection and malicious external content.

## 24. Provenance Preservation

Every recalled knowledge item should retain enough provenance metadata to communicate:

- source;
- timestamp/validity;
- confidence/status;
- relevant transformation;
- scope;
- conflict state.

## 25. Evidence Diversity

Ranking should distinguish genuinely independent evidence from multiple records derived from the same source.

Otherwise retrieval may create an illusion of consensus.

## 26. Contradictory Recall

When strong memories conflict:

```text
Claim A
Claim B
   ↓
CONFLICT SET
```

Novi should either present the conflict or apply the documented resolution policy.

It must not hide contradictions merely to produce a cleaner answer.

## 27. Historical vs Current Recall

A query about current state should prioritize current valid state.

A query about history should preserve historical state.

```text
"Where does the user live now?"
 ≠
"Where did the user live in 2025?"
```

## 28. Confidence-Aware Ranking

Ranking can use evidence quality and confidence, but these should not be reduced to one opaque score.

A ranking explanation should identify major factors.

## 29. Authority-Aware Ranking

Source authority depends on domain.

Examples:

```text
current battery temperature
 → safety telemetry

user's stated preference
 → authorized user memory

historical event
 → event/provenance record
```

Semantic similarity alone cannot override authority.

## 30. Safety-Critical Retrieval

Safety systems should not depend on ordinary semantic retrieval for immediate protection.

Memory may provide context, but dedicated real-time safety systems remain authoritative.

## 31. Retrieval Budget

The reasoning system has finite context and compute.

Retrieval therefore requires budgets for:

- number of candidates;
- token/context size;
- graph expansion depth;
- latency;
- memory bandwidth;
- CPU/GPU usage.

## 32. Context Compression

When many relevant items exist, Novi may compress them into a derived memory pack.

Compression must preserve:

- important evidence;
- contradictions;
- uncertainty;
- temporal scope;
- provenance.

## 33. Memory Pack

A memory pack is a bounded representation supplied to the reasoning layer.

Example:

```text
CURRENT CONTEXT
RELEVANT FACTS
RELEVANT EPISODES
RELEVANT RELATIONSHIPS
CONFLICTS
UNCERTAINTIES
PROVENANCE
```

## 34. No Hidden Context Injection

The system should make the boundary between retrieved memory and current user instructions explicit to downstream reasoning components.

Memory should not masquerade as a new user instruction.

## 35. Retrieval Order

A useful conceptual order is:

```text
ACCESS
 →
RELEVANCE
 →
AUTHORITY
 →
FRESHNESS
 →
EVIDENCE QUALITY
 →
DIVERSITY
 →
UTILITY
```

Actual ranking can be learned/optimized but must respect hard policy constraints.

## 36. Hard vs Soft Filters

Hard filters include:

- authorization failure;
- deleted state;
- incompatible privacy scope;
- invalid object;
- prohibited disclosure.

Soft ranking factors include:

- similarity;
- recency;
- frequency;
- contextual relevance.

Soft ranking must never override hard filters.

## 37. Retrieval Failure

If no sufficiently reliable memory is available:

```text
NO_RELIABLE_RECALL
```

is preferable to fabricated certainty.

## 38. Missing Memory

Novi should distinguish:

```text
NOT FOUND
NOT RETAINED
NOT AUTHORIZED
NEVER OBSERVED
UNKNOWN
```

These states have different meanings.

## 39. Retrieval Feedback

Retrieval outcomes can inform indexing improvements, but retrieval frequency must not automatically modify belief confidence.

## 40. Memory Reinforcement

Accessing a memory should not itself strengthen its truth status.

A frequently used incorrect memory remains incorrect.

## 41. Revalidation on Recall

High-consequence or stale memories may trigger revalidation before use.

```text
retrieve
 ↓
check freshness
 ↓
revalidate if required
 ↓
use
```

## 42. Retrieval-Time Conflict Resolution

If a conflict is unresolved and the task is high consequence, Novi should prefer:

```text
safe conservative behavior
OR
request clarification
OR
obtain new evidence
```

rather than silently choose an arbitrary claim.

## 43. Episodic Recall

When recalling an event, preserve:

- who/what;
- where;
- when;
- observed facts;
- interpretation;
- outcome;
- uncertainty.

This reduces reconstruction errors.

## 44. Conversational Recall

Conversation memory should distinguish:

```text
what user explicitly said
what Novi inferred
what Novi proposed
what was accepted
what remained unresolved
```

A suggestion must not become a user preference merely because it appeared in conversation.

## 45. Preference Recall

Preferences should retain:

- owner;
- scope;
- timestamp;
- source;
- confidence/status;
- expiration/change conditions.

Preferences can change without invalidating historical preference records.

## 46. Person Recall

Person-related retrieval should preserve identity confidence and source provenance.

A visual match alone may not establish identity with sufficient certainty.

## 47. Object Recall

Object memories should account for:

- object identity;
- appearance changes;
- location history;
- ownership/association;
- last observed state;
- uncertainty.

"Last seen at X" is not equivalent to "currently at X."

## 48. Place Recall

Place memories should distinguish:

- visited;
- observed;
- mapped;
- currently located;
- accessible;
- preferred;
- historically associated.

## 49. Outdoor Recall

For outdoor operation, recall can combine:

```text
GNSS
+
localization
+
map
+
visited history
+
landmarks
+
current sensor observations
```

The system should tolerate GNSS loss and preserve uncertainty.

## 50. Offline Retrieval

All essential local memory retrieval must operate without network access.

Cloud/remote knowledge is optional and separately authorized.

## 51. Distributed Retrieval

Remote memory can contribute candidates through the distributed knowledge system.

Remote data must retain source identity, synchronization status and trust context.

## 52. Stale Replica Handling

A remote replica may be behind local state.

Retrieval should consider synchronization/version metadata before treating remote knowledge as current.

## 53. Retrieval Caching

Caches may accelerate retrieval but must respect:

- invalidation;
- deletion;
- authorization;
- privacy;
- versioning.

A cache must not resurrect deleted information.

## 54. Index Updates

Semantic/vector/graph indexes are derived structures.

When source memory changes, indexes should be updated or marked stale according to policy.

## 55. Retrieval Observability

Record appropriate telemetry for:

- retrieval latency;
- candidate counts;
- ranking outcomes;
- cache hit/miss;
- stale-memory use;
- conflict frequency;
- retrieval failures;
- context size;
- authorization filtering.

Telemetry itself must respect privacy and retention policy.

## 56. Evaluation

Measure:

- recall quality;
- precision/relevance;
- freshness;
- provenance completeness;
- contradiction handling;
- privacy correctness;
- latency;
- context efficiency;
- hallucination/fabrication rate;
- retrieval stability.

## 57. Adversarial Testing

Test:

- malicious stored instructions;
- poisoned memories;
- misleading summaries;
- stale replicas;
- forged provenance;
- ambiguous identities;
- graph-expansion attacks;
- retrieval flooding;
- private-memory leakage;
- deletion-cache resurrection;
- conflicting evidence;
- prompt injection in documents.

## 58. Architectural Invariants

1. Retrieval relevance does not imply truth.
2. Authorization and privacy are hard boundaries.
3. Stored content is data, not executable instruction.
4. Current physical safety state does not depend on ordinary semantic recall.
5. Current and historical knowledge remain distinct.
6. Event time is preferred over indexing/arrival time for temporal questions.
7. Spatial uncertainty is preserved.
8. Associations are not evidence by themselves.
9. Correlated evidence is not counted as independent corroboration.
10. Contradictions remain visible or follow explicit resolution policy.
11. Deleted or unauthorized information cannot be retrieved through caches or indexes.
12. Retrieval cannot resurrect deleted memory.
13. Retrieval frequency does not strengthen truth confidence.
14. High-consequence stale knowledge can require revalidation.
15. Missing memory states are represented explicitly.
16. Memory packs preserve relevant provenance and uncertainty.
17. Context expansion is bounded by resource budgets.
18. Remote replicas carry synchronization/trust context.
19. Offline local retrieval remains functional.
20. Retrieval telemetry is itself governed data.
21. Retrieval failures must not cause fabricated answers.
22. Retrieval must remain auditable and testable.

## 59. Final Principle

> **Good memory is not the ability to remember everything. It is the ability to recall the right information, at the right time, with the right context, while preserving uncertainty, provenance, authorization and the distinction between memory and truth.**

This retrieval layer turns the semantic memory architecture into an operational recall system while preserving the safety, privacy, distributed-state and epistemic constraints established by documents 70–79.