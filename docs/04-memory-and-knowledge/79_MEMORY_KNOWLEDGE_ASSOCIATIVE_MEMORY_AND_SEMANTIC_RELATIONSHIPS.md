# 79 — Memory Knowledge Associative Memory and Semantic Relationships

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi connects people, places, objects, events, concepts, preferences, experiences, observations, and knowledge so that memory retrieval can use meaningful context and relationships rather than relying only on lexical similarity.

## Cross-Validation Basis

This architecture is informed by established graph-based knowledge representation concepts. W3C RDF represents information as subject-predicate-object relationships and provides formal semantics for graph-based representation; current RDF 1.2 work also supports expressing metadata about statements, which is relevant to provenance-aware relationships. citeturn0search0turn0search1 NIST defines knowledge as a retrievable set of concepts within memory and defines provenance as information describing origin and changes, supporting the separation of knowledge from its lineage. citeturn0search9turn0search2

Novi is **not required to implement RDF, OWL, SPARQL, or a traditional graph database**. These standards inform the semantic model; implementation is selected later according to performance, offline operation, privacy, storage, and hardware constraints.

## Core Principle

> **Novi should remember relationships, not merely isolated facts.**

A memory becomes more useful when Novi knows how it relates to other memories while preserving the uncertainty, provenance, scope, and temporal validity of those relationships.

## 1. Associative Memory Model

```text
PERSON
  ↕
PLACE ↔ OBJECT
  ↕      ↕
EVENT ↔ EXPERIENCE
  ↕      ↕
PREFERENCE ↔ CONCEPT
  ↕
KNOWLEDGE
```

These are semantic relationships, not necessarily literal database foreign keys.

## 2. Entity Types

Potential entity classes include:

- person;
- agent;
- place;
- room;
- object;
- device;
- organization;
- event;
- activity;
- experience;
- concept;
- preference;
- task;
- route;
- landmark;
- document;
- knowledge item;
- sensor observation.

The ontology must remain extensible.

## 3. Relationship Types

Examples include:

```text
LOCATED_IN
VISITED
OWNS
USES
PREFERS
LIKES
DISLIKES
RELATED_TO
PART_OF
CONTAINS
NEAR
SEEN_AT
HEARD_AT
OCCURRED_AT
CAUSED_BY
RESULTED_IN
PARTICIPATED_IN
WORKS_WITH
DEPENDS_ON
SIMILAR_TO
CONTRADICTS
SUPPORTS
SUPERSEDES
```

Relationship semantics must be explicit.

## 4. Relationship Is a First-Class Object

A relationship may itself require:

```text
source
predicate
target
time
location
confidence
provenance
scope
privacy
validity
```

Therefore relationships should not always be represented as bare unqualified edges.

## 5. Example

```text
Vano
  └── PREFERS ──> coffee
          │
          └── VALID_DURING ──> current preference interval
```

The relationship may change without deleting historical preference evidence.

## 6. Temporal Relationships

Relationships can be:

```text
CURRENT
HISTORICAL
SCHEDULED
RECURRING
EXPIRED
UNKNOWN_VALIDITY
```

For example:

```text
PERSON ──LIVED_AT──> PLACE
```

can be historically true while no longer being current.

## 7. Spatial Relationships

Physical relationships can include:

- inside;
- near;
- above;
- below;
- left/right;
- connected_to;
- route_to;
- visited;
- explored;
- blocked_by.

Spatial claims require coordinate/map context where appropriate.

## 8. Identity vs Similarity

Two entities that look or sound similar must not automatically become the same entity.

```text
SIMILAR_TO
 ≠
SAME_AS
```

Identity merging requires stronger evidence and authorization.

## 9. Entity Resolution

Entity resolution may combine:

- visual evidence;
- voice evidence;
- names;
- contextual evidence;
- device identifiers;
- user confirmation;
- historical relationships.

Conflicting identity evidence should remain contested rather than silently merged.

## 10. Relationship Confidence

A relationship may have confidence/uncertainty, but the value must retain its source and calibration context.

```text
relationship confidence
+ provenance
+ evidence
+ validity
```

A numeric score alone is insufficient.

## 11. Relationship Provenance

Every important derived relationship should link to supporting evidence.

```text
PERSON ──VISITED──> PLACE
          ↑
       evidence
          ↑
     GPS / vision / event
```

This follows the provenance architecture in document 74.

## 12. Associative Retrieval

When retrieving a memory, Novi can expand through relevant relationships:

```text
QUERY
 ↓
DIRECT MEMORY
 ↓
RELATED PEOPLE / PLACES / OBJECTS / EVENTS
 ↓
CONTEXT FILTER
 ↓
RELEVANCE RANKING
 ↓
RESULT
```

Graph expansion must be bounded to prevent irrelevant traversal.

## 13. Semantic Retrieval vs Keyword Retrieval

Keyword retrieval answers:

> Which records contain these words?

Associative retrieval can answer:

> What memories are related to this person, place, event, preference, or concept?

Both approaches should coexist.

## 14. Hybrid Retrieval

A mature retrieval pipeline may combine:

```text
LEXICAL
+
SEMANTIC EMBEDDING
+
ASSOCIATIVE GRAPH
+
TEMPORAL FILTER
+
SPATIAL FILTER
+
PROVENANCE / TRUST
+
USER / TASK CONTEXT
```

No single retrieval mechanism should be assumed universally best.

## 15. Contextual Activation

A current context can activate related memory regions.

Example:

```text
Novi is in kitchen
       ↓
activate kitchen memories
       ↓
objects + people + routines + previous events
```

Activation must remain bounded and privacy-aware.

## 16. Spreading Activation

Associative retrieval may traverse multiple relationships:

```text
PLACE
 ↓
EVENT
 ↓
PERSON
 ↓
PREFERENCE
 ↓
OBJECT
```

Traversal depth and relevance thresholds must be controlled.

## 17. No Unbounded Graph Traversal

A single query must not recursively activate the entire knowledge graph.

Use:

- depth limits;
- relevance thresholds;
- relationship-type filters;
- time windows;
- privacy boundaries;
- resource budgets.

## 18. Context Weighting

A relationship's relevance depends on context.

```text
same object
+ current location
+ current task
+ recent event
```

may be more relevant than a historically frequent but unrelated relationship.

## 19. Recency Weighting

Recent relationships can receive higher retrieval relevance when the task is current-state oriented.

Recency must not erase historical relevance.

## 20. Frequency Weighting

Frequent relationships can become easier to retrieve but must not automatically become more true.

```text
retrieval frequency
 ≠
truth
```

## 21. Importance vs Frequency

A rare but critical memory may be more important than a frequently encountered routine.

The retrieval model should therefore separate:

```text
frequency
importance
relevance
confidence
```

## 22. Personal Preference Graph

User preferences can connect:

```text
PERSON
 ↓
PREFERS
 ↓
OBJECT / FOOD / PLACE / ACTIVITY
```

Preferences should remain scoped to the relevant person and validity interval.

## 23. Shared Preferences

Household preferences should distinguish:

```text
PERSON A preference
PERSON B preference
HOUSEHOLD preference
```

A household preference cannot silently overwrite an individual preference.

## 24. Event Graph

Events can connect participants, locations, objects, time and outcomes:

```text
EVENT
 ├── PARTICIPANT → PERSON
 ├── LOCATION → PLACE
 ├── INVOLVES → OBJECT
 ├── OCCURRED_AT → TIME
 └── RESULTED_IN → OUTCOME
```

## 25. Experience Graph

Experiences can connect:

```text
EXPERIENCE
 ↓
EVENTS
 ↓
OBSERVATIONS
 ↓
OUTCOMES
 ↓
LESSONS / PATTERNS
```

This integrates with document 78.

## 26. Concept Graph

Concepts can form semantic hierarchies and associations:

```text
ANIMAL
 ├── DOG
 │    ├── LABRADOR
 │    └── POODLE
 └── CAT
```

Taxonomic relationships must be distinguished from arbitrary similarity.

## 27. Relationship Semantics

Different predicates have different logical behavior.

For example:

```text
PARENT_OF
```

may imply a different inverse/constraint structure than:

```text
SIMILAR_TO
```

Novi should not infer logical properties unless explicitly defined.

## 28. Inverse Relationships

Some relationships have meaningful inverses:

```text
LOCATED_IN
↔
CONTAINS
```

Where an inverse is valid, it may be derived rather than independently stored, reducing contradiction risk.

## 29. Symmetric Relationships

Some relationships may be symmetric:

```text
NEAR(A,B)
⇒
NEAR(B,A)
```

but only when the predicate semantics explicitly define this property.

## 30. Transitive Relationships

Transitivity must never be assumed merely because a relationship looks hierarchical.

For example:

```text
A NEAR B
B NEAR C
```

does not imply:

```text
A NEAR C
```

## 31. Relationship Cardinality

Some relationships may have constraints:

```text
OBJECT HAS_SERIAL_NUMBER → usually one active identifier
```

while others are naturally many-to-many.

The ontology should define applicable cardinality rather than enforcing one global rule.

## 32. Contradictory Relationships

The graph must permit:

```text
A ──LIKES──> X
A ──DISLIKES──> X
```

when the evidence is time-scoped or context-dependent.

Contradictions require temporal/contextual analysis rather than immediate deletion.

## 33. Relationship Versioning

Important relationship changes should preserve version/lineage information.

```text
R1
 ↓ SUPERSEDED_BY
R2
```

## 34. Relationship Expiration

Some relationships should expire naturally:

```text
TEMPORARY_LOCATION
CURRENT_TASK
ACTIVE_ROUTE
```

Expiration should produce an explicit state rather than silently deleting history.

## 35. Memory Neighborhoods

Novi can define bounded neighborhoods around a memory:

```text
memory
 ↓ 1 hop
entities/events
 ↓ 2 hops
related context
```

Neighborhoods can improve contextual retrieval while limiting resource consumption.

## 36. Episode Retrieval

For a query about a past experience, retrieval should prioritize the episode and its supporting context rather than only extracting isolated facts.

## 37. Place-Centric Retrieval

If Novi is at a known location:

```text
CURRENT PLACE
 ↓
previous visits
 ↓
people observed
 ↓
objects encountered
 ↓
important events
 ↓
known hazards / access state
```

Current physical sensing must validate current hazards rather than relying only on remembered relationships.

## 38. Person-Centric Retrieval

A person context can retrieve:

- prior interactions;
- preferences;
- relevant events;
- authorized relationships;
- communication history;
- tasks.

Privacy and identity confidence must constrain retrieval.

## 39. Object-Centric Retrieval

An object can connect to:

- owner;
- location;
- previous sightings;
- maintenance events;
- associated documents;
- usage patterns.

An old location relationship does not establish the object's current location.

## 40. Route and Map Relationships

Maps may contain:

```text
PLACE A
 ↓ ROUTE_TO
PLACE B
```

Routes should retain map version, observation time, confidence and accessibility state where relevant.

## 41. Visited-Place Memory

Novi can retain:

- first visit;
- latest visit;
- visit count;
- approximate dwell time;
- observed landmarks;
- route history;
- uncertainty.

This supports the requirement that Novi remembers where it has been.

## 42. Current vs Historical Location

```text
visited place before
 ≠
currently there
```

Historical spatial relationships must never silently become current localization state.

## 43. GPS/GNSS Integration

GPS/GNSS observations can establish spatial evidence, but localization should also integrate appropriate local sensors and uncertainty.

A remembered GPS coordinate is historical evidence, not necessarily current position.

## 44. Thermal Relationships

Thermal observations may create relationships such as:

```text
OBJECT ──HAS_THERMAL_STATE──> HOT
PLACE ──HAS_REGION──> COOL_AREA
```

These should remain time- and sensor-scoped.

## 45. Audio Relationships

Voice localization can create:

```text
SOUND EVENT
 ↓
DIRECTION / LOCATION
 ↓
POSSIBLE SOURCE
```

The inferred source must remain distinct from raw microphone evidence and identity claims.

## 46. Vision Relationships

Vision can produce:

```text
OBSERVED_AT
POSSIBLE_IDENTITY
OBJECT_RELATIONSHIP
SCENE_CONTEXT
```

Recognition confidence and provenance remain attached.

## 47. Sensor Fusion Relationships

A semantic relationship derived from multiple sensors should link to all materially contributing evidence where practical.

## 48. Knowledge Graph vs Memory Store

The associative graph is not necessarily the raw memory store.

```text
RAW / EPISODIC MEMORY
        ↕
SEMANTIC RELATIONSHIP LAYER
        ↕
KNOWLEDGE PROJECTIONS
```

The graph can be rebuilt or partially rebuilt from authoritative sources where designed accordingly.

## 49. Graph as Derived State

Where relationships are derived, their graph representation should be treated as a projection with provenance rather than the sole source of truth.

## 50. Graph Storage Strategy

Possible implementation strategies include:

- relational tables with relationship records;
- property graph;
- RDF graph;
- hybrid relational + vector + graph architecture;
- specialized in-memory structures.

The final implementation should be selected after performance, offline, storage and privacy requirements are benchmarked.

## 51. Offline Operation

The associative layer must function locally without Wi-Fi, Bluetooth or cloud services.

External knowledge can enrich the graph but is never required for core associations.

## 52. Distributed Graph Synchronization

When sharing relationships between Novi instances:

```text
relationship
 ↓
provenance
 ↓
authorization
 ↓
scope
 ↓
sync
 ↓
local validation
```

Remote relationships are external evidence until locally admitted.

## 53. Graph Conflicts

Conflicts can occur when agents assert different relationships.

Example:

```text
A ──LOCATED_IN──> Room 1
B ──LOCATED_IN──> Room 2
```

Resolution must consider timestamps, physical evidence, localization uncertainty and object identity.

## 54. Privacy Boundaries

Graph traversal must enforce authorization at every relevant node/edge.

Knowing a person is connected to another person does not automatically authorize revealing the relationship.

## 55. Sensitive Inferences

Associative graphs can reveal sensitive patterns even when individual edges appear harmless.

Examples:

```text
PERSON
 ↓ visits
PLACE
 ↓ at time
ROUTINE
```

Access control must consider derived inferences.

## 56. Prompt Injection Boundary

Text stored in the graph remains data.

A relationship label or document content cannot become a system instruction merely because it is retrieved through associative memory.

## 57. Retrieval Security

Retrieved memories must remain subject to:

- authorization;
- privacy;
- trust;
- provenance;
- relevance;
- safety policy.

## 58. Retrieval Explainability

For important answers, Novi should be able to explain which relationships and memories materially contributed to retrieval.

The explanation must use actual retrieval/provenance data rather than a fabricated narrative.

## 59. Relationship Garbage Collection

When a node is deleted or restricted, dependent edges and derived relationships must be evaluated.

Stale relationships must not silently resurrect deleted information.

## 60. Resource Budgets

Graph traversal must respect:

- CPU;
- memory;
- storage;
- latency;
- battery;
- thermal budget.

A large graph query must not starve safety-critical processing.

## 61. Testing

Test:

- incorrect entity merging;
- ambiguous identity;
- temporal relationship changes;
- contradictory edges;
- invalid transitivity;
- invalid inverse inference;
- stale spatial relationships;
- map-version mismatch;
- privacy leakage through graph traversal;
- sensitive inference;
- prompt injection through stored text;
- distributed graph conflicts;
- offline graph updates;
- duplicate relationships;
- deleted-node resurrection;
- graph traversal explosion;
- corrupted relationship provenance;
- model-version mismatch;
- sensor-fusion lineage;
- user preference conflicts;
- current-vs-historical confusion.

## 62. Architectural Invariants

1. Relationships are first-class semantic information.
2. Important relationships retain provenance and validity context.
3. Similarity is not identity.
4. Historical relationships are distinct from current state.
5. Frequency does not equal truth.
6. Retrieval frequency does not strengthen evidence.
7. Transitivity, symmetry and inverse semantics are explicit rather than assumed.
8. Contradictory relationships can coexist when context or time explains them.
9. Graph traversal is bounded.
10. Graph retrieval is subject to authorization and privacy.
11. Derived relationships can themselves be sensitive information.
12. Associative memory complements rather than replaces lexical and vector retrieval.
13. The graph is not automatically the authoritative raw memory store.
14. Remote relationships are not automatically trusted.
15. Current physical state requires current validated sensing.
16. Historical location does not establish current location.
17. Sensor-derived relationships preserve relevant evidence lineage.
18. Deletion and restriction propagate to dependent relationships.
19. Stored text remains data and cannot become system authority through retrieval.
20. Graph processing cannot starve safety-critical computation.
21. Important retrieval decisions remain explainable through actual provenance.
22. Offline operation remains fully functional.

## 63. Final Principle

> **Novi's memory should behave less like a collection of isolated records and more like a carefully governed web of experiences, people, places, objects, events, concepts and knowledge—while never confusing a relationship with proof of truth.**
