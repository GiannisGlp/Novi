# 89 — Memory Knowledge Memory Consolidation and Reconsolidation Engine

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define the engine that transforms experience into durable, reusable memory while preserving provenance, uncertainty, temporal context and the distinction between original evidence and later interpretation.

This document integrates the episodic, semantic, procedural, prospective and metamemory layers defined in documents 82–88 and establishes the controlled transition from transient experience to durable knowledge.

## Core Principle

> **Consolidation should make memory more useful and durable without making it more certain than its evidence warrants. Reconsolidation should permit evidence-based revision without rewriting the historical record.**

## 1. Research Boundary

Novi's architecture is inspired by cognitive memory research but is **not a claim that Novi reproduces biological memory mechanisms**.

Current research supports distinctions among working, declarative and non-declarative memory and describes multiple consolidation processes, including cellular and systems-level consolidation. Research also supports the role of post-encoding processing and sleep in memory stabilization. These findings motivate architectural analogies, not literal implementation requirements.

Research basis:

- Sridhar, Khamaj & Asthana (2023), *Cognitive neuroscience perspective on memory: overview and summary*, Frontiers in Human Neuroscience. https://consensus.app/papers/cognitive-neuroscience-perspective-on-memory-overview-sridhar-khamaj/a29295cfb0cc573993079bec967a78ef/
- Staresina (2024), *Coupled sleep rhythms for memory consolidation*, Trends in Cognitive Sciences. https://consensus.app/papers/coupled-sleep-rhythms-for-memory-consolidation-staresina/a0d6dcf6034d55699a5cf8b1e7ea3f9d/
- Spens & Burgess (2023/2024), *A generative model of memory construction and consolidation*, Nature Human Behaviour. https://consensus.app/papers/a-generative-model-of-memory-construction-and-spens-burgess/0f8c7aa167aa54da88190dff4ec3f157/
- Jardine et al. (2022), *The evidence for and against reactivation-induced memory updating in humans and nonhuman animals*, Neuroscience and Biobehavioral Reviews. https://consensus.app/papers/the-evidence-for-and-against-reactivationinduced-memory-jardine-huff/273cf8c70b9e58ba83168bc2a431375f/

## 2. Cross-Validation Principle

No single research finding should be treated as sufficient justification for a safety-critical architectural decision.

Novi should cross-check proposed mechanisms against:

- multiple peer-reviewed sources;
- replication evidence;
- known boundary conditions;
- engineering constraints;
- privacy requirements;
- provenance requirements;
- safety requirements.

Where biological evidence is mixed, Novi should choose the conservative engineering interpretation and label the biological analogy as uncertain.

## 3. Consolidation vs Storage

Consolidation is not simply copying data from one database to another.

```text
EXPERIENCE
   ↓
SELECTION
   ↓
VALIDATION
   ↓
STRUCTURING
   ↓
LINKING
   ↓
ABSTRACTION
   ↓
DURABLE MEMORY
```

The authoritative source records remain distinct from derived representations.

## 4. Memory Classes

The engine coordinates:

```text
EPISODIC
SEMANTIC
PROCEDURAL
PROSPECTIVE
METAMEMORY
```

Working memory is an active context layer, not a durable consolidation target by default.

## 5. Consolidation Candidate

An experience becomes a consolidation candidate when one or more policy signals justify durable retention:

- explicit user request;
- repeated relevance;
- significant outcome;
- novel information;
- learned skill;
- important location;
- safety relevance;
- unresolved future intention;
- strong evidence of long-term utility.

No candidate is automatically promoted solely because it is recent.

## 6. Selection Is Policy-Driven

The engine should evaluate:

```text
UTILITY
PRIVACY
EVIDENCE
NOVELTY
REPETITION
SAFETY
RETENTION POLICY
STORAGE COST
```

Governance rules from document 88 and retention rules from document 87 remain authoritative.

## 7. Significance Is Not Truth

A highly significant event can still be uncertain.

```text
HIGH SIGNIFICANCE
      ≠
HIGH FACT CONFIDENCE
```

The engine must preserve these dimensions separately.

## 8. Evidence Gate

Before consolidation, evaluate:

- provenance;
- source quality;
- observation status;
- temporal consistency;
- spatial consistency;
- identity confidence;
- independent corroboration;
- contradictions.

Weak evidence may be retained as an uncertain memory but must not silently become a strong semantic fact.

## 9. Episode Preservation

The original episode remains authoritative for what was recorded.

Consolidation may create derivatives:

```text
EPISODE
 ↓
PATTERN
 ↓
SEMANTIC / PROCEDURAL KNOWLEDGE
```

It must not overwrite the episode to make the abstraction look cleaner.

## 10. Abstraction

Abstraction removes incidental detail while retaining information useful for generalization.

Example:

```text
Episode 1: Novi opened cabinet A.
Episode 2: Novi opened cabinet B.
Episode 3: Novi opened cabinet C.
        ↓
Candidate pattern: compatible cabinets can be opened using a validated procedure.
```

The pattern must retain the supporting episodes.

## 11. Generalization Threshold

Repeated observations do not automatically prove a universal rule.

The engine should distinguish:

```text
OBSERVED PATTERN
LIKELY PATTERN
VALIDATED GENERALIZATION
UNKNOWN SCOPE
```

## 12. Counterexamples

A counterexample should reduce or challenge an abstraction.

```text
PATTERN
 ↓
COUNTEREXAMPLE
 ↓
REASSESS SCOPE
```

The engine must not selectively ignore contradictory episodes.

## 13. Semantic Promotion

A candidate semantic assertion may be promoted when evidence and policy requirements are met.

```text
EPISODES
 ↓
CANDIDATE ASSERTION
 ↓
EVIDENCE REVIEW
 ↓
SEMANTIC MEMORY
```

Document 76 controls lifecycle status and document 77 controls belief revision.

## 14. Procedural Promotion

Repeated successful task episodes can produce a procedural candidate.

```text
TASK EPISODES
 ↓
ACTION PATTERN
 ↓
PROCEDURE CANDIDATE
 ↓
VALIDATION
 ↓
SKILL
```

Procedural promotion must include safety and capability validation from document 84.

## 15. Prospective Promotion

Repeated accepted future commitments may inform routines, but recurring behavior must not silently create new obligations.

```text
REPEATED INTENTIONS
 ↓
ROUTINE CANDIDATE
 ↓
USER/POLICY ACCEPTANCE
 ↓
RECURRING INTENTION
```

## 16. Metamemory Update

Consolidation should also update knowledge about memory quality:

```text
NEW OUTCOME
 ↓
SOURCE ACCURACY
 ↓
RELIABILITY UPDATE
```

This must not rewrite the original source record.

## 17. Duplicate Detection

The engine should detect whether new information is:

- duplicate;
- corroborating;
- contradictory;
- derivative;
- genuinely novel.

Duplicate copies must not inflate confidence.

## 18. Source Independence

Multiple records derived from one source are not independent evidence.

```text
SOURCE A
 ├── summary B
 ├── embedding C
 └── derived fact D
```

This is one evidence lineage, not four independent confirmations.

## 19. Consolidation Graph

A memory graph can represent:

```text
EPISODE
 ├── supports → FACT
 ├── supports → SKILL
 ├── contradicts → FACT
 ├── related_to → EPISODE
 └── derived → SUMMARY
```

Lineage should remain queryable.

## 20. Temporal Consolidation

Memory may evolve over time:

```text
EVENT
 ↓
SHORT-TERM RECORD
 ↓
LONG-TERM MEMORY
 ↓
LATER REVISION
```

The original event timestamp must remain distinct from consolidation time.

## 21. Spatial Consolidation

Repeated spatial observations can produce knowledge such as:

```text
PLACE → contains → OBJECT
```

but only within an appropriate spatial and temporal scope.

For Novi's outdoor memory, repeated GPS traces can produce route/place knowledge while preserving localization uncertainty and map version.

## 22. Location Generalization

A route frequently traversed successfully does not establish that it is always safe or accessible.

```text
historically traversable
      ≠
currently traversable
```

Current perception and safety systems remain authoritative.

## 23. Sleep-Inspired Consolidation

If Novi has a scheduled low-load maintenance period, memory processing may occur then.

This is an **engineering scheduling strategy inspired by research**, not a claim that Novi needs biological sleep.

Research indicates that sleep and coordinated oscillatory processes support memory consolidation in biological systems, while post-encoding awake processing can also contribute. Therefore Novi should not hard-code consolidation to sleep alone.

## 24. Awake Consolidation

Useful consolidation can occur during idle or low-priority compute periods:

```text
TASK COMPLETE
 ↓
IDLE WINDOW
 ↓
CONSOLIDATION
```

Safety-critical and user-facing work takes precedence.

## 25. Priority Scheduling

Consolidation priority may consider:

- explicit remember request;
- unresolved contradiction;
- imminent intention;
- new skill candidate;
- safety relevance;
- high-value episode;
- storage pressure.

## 26. Resource Budgets

The engine should enforce budgets for:

- CPU;
- GPU/NPU;
- memory;
- storage I/O;
- energy;
- latency.

Consolidation must never starve real-time control or safety loops.

## 27. Incremental Consolidation

Large histories should be processed incrementally rather than requiring a complete rebuild.

```text
NEW EPISODES
 ↓
INCREMENTAL UPDATE
 ↓
AFFECTED KNOWLEDGE
```

## 28. Batch Consolidation

Periodic batch processing can detect longer-term patterns that are difficult to identify from one episode.

Batch processing must preserve the same evidence and governance rules as online processing.

## 29. Revalidation

A consolidated assertion may require revalidation when:

- world state changes;
- source reliability degrades;
- new contradictory evidence appears;
- hardware changes;
- model changes;
- map changes;
- user correction occurs.

## 30. Reconsolidation

Retrieval can create an opportunity to update an existing memory representation.

However, research indicates reconsolidation is not a universally automatic process and has important boundary conditions and replication challenges. Novi should therefore treat reconsolidation as an explicit controlled operation rather than assuming every retrieval destabilizes memory.

## 31. Reconsolidation Pipeline

```text
RETRIEVE
   ↓
REACTIVATION DETECTED
   ↓
UPDATE ELIGIBILITY CHECK
   ↓
NEW EVIDENCE / CORRECTION
   ↓
REVISED INTERPRETATION
   ↓
VALIDATION
   ↓
RECONSOLIDATE
```

If update eligibility is not established, preserve the existing memory and store the new evidence separately.

## 32. Reactivation Is Not Automatic Permission to Rewrite

```text
RETRIEVAL
 ≠
DESTABILIZATION
 ≠
RECONSOLIDATION
```

This is an explicit architectural safeguard informed by the mixed reconsolidation literature.

## 33. Prediction Error / Conflict

New evidence that conflicts with an existing expectation can be useful for determining whether an update should be considered.

But prediction error alone does not authorize destructive rewriting.

## 34. Safe Memory Updating

Prefer:

```text
OLD RECORD
   +
NEW EVIDENCE
   ↓
CURRENT INTERPRETATION
```

rather than:

```text
OLD RECORD
   ↓
OVERWRITE
```

## 35. Versioned Interpretation

Store:

```text
ORIGINAL OBSERVATION
INTERPRETATION v1
INTERPRETATION v2
CURRENT INTERPRETATION
```

This makes revision auditable.

## 36. Belief vs Evidence

A changed belief must not modify historical evidence.

```text
EVIDENCE: immutable/controlled
BELIEF: revisable
```

The exact mutability policy is governed by provenance and retention requirements.

## 37. False Memory Prevention

Generated summaries, embeddings and abstractions must never become evidence merely because they have been repeatedly retrieved.

```text
DERIVATIVE
  ↓
RETRIEVED 100 TIMES
  ≠
100 independent confirmations
```

## 38. Schema / Ontology Evolution

When the semantic schema changes:

```text
OLD REPRESENTATION
 ↓
MIGRATION
 ↓
NEW REPRESENTATION
```

The migration must preserve lineage and historical meaning.

## 39. Skill Evolution

When procedural knowledge changes:

```text
SKILL v1
 ↓ evidence
SKILL v2
```

The engine should record why the change occurred and which episodes validated it.

## 40. Routine Formation

Repeated intentions or behaviors can reveal routines.

A routine candidate should include:

- frequency;
- context;
- exceptions;
- confidence;
- owner;
- authorization;
- evidence.

A routine must not silently become an autonomous commitment.

## 41. Consolidation of Failure

Failures can be consolidated as:

```text
failure context
 ↓
failed assumption
 ↓
recovery knowledge
```

But Novi must avoid turning a local failure into a global belief such as "this task can never be done."

## 42. Negative Evidence

Repeated absence of an observation can be informative only when the sensing process makes absence meaningful.

```text
not observed
 ≠
absent
```

The consolidation engine must preserve this distinction.

## 43. Contradiction Handling

When evidence conflicts:

```text
ASSERTION A
ASSERTION B
   ↓
CONFLICT SET
   ↓
REVIEW / REWEIGHT / SUPERSEDE / KEEP BOTH
```

The engine must support unresolved conflicts.

## 44. Multi-Agent Consolidation

Knowledge received from another Novi instance is external evidence.

It should retain:

- source agent;
- timestamp;
- provenance;
- confidence;
- synchronization state;
- trust context.

## 45. Cross-Agent Corroboration

Two agents independently observing the same event can provide stronger corroboration than two copies of one agent's report.

Independence must be established, not assumed.

## 46. Offline Consolidation

Novi can consolidate locally while offline.

Later synchronization should reconcile derived knowledge using causal/version metadata rather than blindly replacing local state.

## 47. Deletion-Aware Consolidation

Before generating durable derivatives, the engine must associate them with their source dependencies.

This is required so document 87 can propagate future erasure through the memory graph.

## 48. Privacy-Aware Consolidation

The engine must not promote sensitive information into broader, more accessible abstractions merely because abstraction is technically useful.

Privacy classification must propagate to derivatives.

## 49. Minimum Necessary Abstraction

When consolidating sensitive information, retain only the semantic detail required for the legitimate purpose.

```text
RAW DETAIL
 ↓
MINIMUM NECESSARY KNOWLEDGE
```

## 50. Consolidation Rollback

If a derived abstraction is found to be invalid:

```text
DERIVED KNOWLEDGE
 ↓
INVALIDATED
 ↓
REBUILD FROM AUTHORITATIVE SOURCES
```

The engine should not merely patch the derivative indefinitely.

## 51. Rebuildability

Important semantic and procedural representations should be rebuildable from authoritative records when retention permits.

This reduces dependence on opaque derived state.

## 52. Auditability

For every important promotion or reconsolidation, record:

- source memories;
- decision policy/version;
- evidence considered;
- confidence/status before;
- confidence/status after;
- model/software version;
- time;
- actor/system component.

## 53. Explainability

The engine should answer:

```text
Why was this memory promoted?
Which episodes support it?
What contradicts it?
When was it last validated?
Why was it revised?
Which derivatives depend on it?
```

Explanations must use provenance, not post-hoc generated stories.

## 54. Consolidation Idempotency

Running consolidation twice on the same unchanged evidence should not create duplicate independent memories or inflate confidence.

## 55. Deterministic Lineage

Each derived memory should have stable lineage identifiers so repeated processing can recognize existing derivatives.

## 56. Human Correction

A user correction should be treated as new evidence with explicit provenance.

It can trigger:

```text
CURRENT BELIEF
 ↓
REASSESSMENT
 ↓
RECONSOLIDATION
```

The previous interpretation remains historically traceable where policy requires.

## 57. User-Controlled Memory

Explicit user requests to remember or forget have governance significance but remain subject to authorization, privacy and system constraints.

## 58. Safety Boundary

Consolidation and reconsolidation must never modify real-time safety constraints merely because a learned pattern suggests a different behavior.

Safety systems remain authoritative.

## 59. Testing Strategy

Test at minimum:

- duplicate evidence;
- correlated evidence;
- novel evidence;
- contradictory evidence;
- counterexamples;
- semantic promotion;
- procedural promotion;
- prospective routine formation;
- confidence calibration;
- reconstruction labeling;
- reconsolidation eligibility;
- retrieval without rewriting;
- false-memory prevention;
- versioned interpretation;
- schema migration;
- hardware/model changes;
- map changes;
- privacy propagation;
- deletion propagation;
- offline consolidation;
- distributed merge;
- idempotency;
- rollback/rebuild;
- provenance integrity;
- resource exhaustion;
- safety starvation;
- malicious memory injection;
- malicious consolidation triggers.

## 60. Failure Injection

Deliberately test:

```text
CORRUPTED SOURCE
MISSING SOURCE
CONFLICTING SOURCES
STALE SOURCE
FALSE SUMMARY
DUPLICATE EVENTS
WRONG TIMESTAMP
WRONG LOCATION
IDENTITY COLLISION
DELETION DURING CONSOLIDATION
HARDWARE FAILURE
MODEL UPGRADE DURING CONSOLIDATION
OFFLINE PARTITION
```

The engine should fail conservatively and preserve provenance.

## 61. Performance Requirements

The engine should support:

- incremental processing;
- bounded queues;
- prioritization;
- resumable jobs;
- checkpointing;
- backpressure;
- resource budgets;
- cancellation.

No consolidation workload should block real-time control.

## 62. Security Requirements

Protect against:

- memory poisoning;
- fabricated provenance;
- malicious repeated confirmations;
- derivative amplification;
- unauthorized promotion;
- unauthorized reconsolidation;
- deletion bypass;
- prompt injection through stored memories.

Stored memory is data, not executable authority.

## 63. Observability

Track privacy-safe metrics such as:

- candidates created;
- candidates promoted;
- promotion rejection rate;
- reconsolidation attempts;
- reconsolidation success/failure;
- contradictions discovered;
- stale memories revalidated;
- invalidated derivatives;
- consolidation latency;
- compute/resource usage;
- rollback frequency;
- deletion propagation events.

## 64. Architectural Invariants

1. Consolidation increases durability or usability, not epistemic certainty by itself.
2. Original evidence remains distinct from derived memory.
3. Episodic, semantic, procedural and prospective memory remain distinct but interconnected.
4. Duplicate copies do not create independent evidence.
5. Generalization requires evidence and scope.
6. Counterexamples can weaken or invalidate abstractions.
7. Current state remains distinct from historical knowledge.
8. Retrieval does not automatically rewrite memory.
9. Reconsolidation is controlled and eligibility-based.
10. Biological memory research is an architectural inspiration, not a claim of biological equivalence.
11. Sleep-inspired processing is optional scheduling, not a hard dependency.
12. Awake/idle consolidation remains possible.
13. Evidence and belief have separate lifecycles.
14. Revisions preserve historical lineage.
15. Generated summaries and embeddings never become independent evidence.
16. Derived knowledge retains source dependencies.
17. Deletion requirements propagate through dependencies.
18. Privacy classifications propagate through derivatives.
19. Safety controls cannot be modified by ordinary consolidation.
20. Consolidation is incremental, resumable and resource-bounded.
21. Distributed consolidation preserves source and causal metadata.
22. Offline consolidation remains valid but must reconcile later.
23. Important promotion and revision decisions are auditable.
24. Consolidation is idempotent over unchanged evidence.
25. Invalid abstractions can be rolled back and rebuilt.
26. User corrections become explicit evidence rather than silent rewrites.
27. Memory poisoning defenses apply to both source and derived memories.
28. Metamemory is updated alongside memory quality changes.
29. Uncertainty survives consolidation.
30. The system must be able to say that no safe or justified consolidation decision is currently possible.

## 65. Final Principle

> **Novi's consolidation engine should transform experience into durable capability and knowledge through evidence-gated, provenance-preserving, privacy-aware and reversible processes—while treating reconsolidation as controlled belief revision rather than permission to rewrite history.**

This engine is the bridge between Novi's lived episodes and the durable knowledge, skills, routines and expectations it uses to operate over long periods of time.