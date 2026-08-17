# 98 — Memory Knowledge Temporal Reasoning and Temporal Memory Architecture

## Status

**NORMATIVE ARCHITECTURE — CRITICAL / V1**

## Purpose

Define how Novi represents, retrieves, reasons over, updates and evaluates information whose meaning depends on time.

This document resolves the second P0 gap identified by document 96 and builds directly on the identity semantics established in 97 and the integrated reference model in 95.

## Core Principle

> **Time is part of the meaning of a memory, not merely metadata attached to it.**

A statement can be correct at one time, incorrect later, valid during an interval, or uncertain about when it was true.

## 1. Why Temporal Reasoning Is Foundational

Static memory representations can become misleading when facts evolve. Research on temporal knowledge graphs explicitly identifies changing real-world facts as a limitation of static knowledge graphs and models temporal validity as a core representation dimension. citeturn0search0turn0search1

Without temporal semantics, Novi risks:

- treating historical facts as current;
- confusing event time with observation time;
- creating impossible timelines;
- retrieving stale knowledge;
- reversing causal order;
- attributing later information to earlier events;
- corrupting longitudinal memory.

## 2. Time Is Multi-Dimensional

Novi must distinguish at least:

```text
EVENT TIME
OBSERVATION / CAPTURE TIME
PUBLICATION TIME
INGESTION TIME
VALIDITY TIME
EXPIRATION TIME
REVISION TIME
DECISION TIME
ACTION TIME
OUTCOME TIME
```

These timestamps are not interchangeable.

## 3. Event Time vs Capture Time

Example:

```text
EVENT OCCURRED: T1
CAMERA CAPTURED IT: T2
SYSTEM INGESTED IT: T3
MODEL ANALYZED IT: T4
```

The memory must preserve all relevant times rather than replacing T1 with T4.

## 4. Valid Time

A claim can have a validity interval:

```text
CLAIM C
VALID FROM T1
VALID UNTIL T2
```

Unknown boundaries should remain unknown rather than fabricated.

## 5. Transaction / System Time

The system should distinguish when a record entered or changed Novi from when the underlying fact was true.

```text
VALID TIME
≠
SYSTEM TIME
```

This is essential for historical reconstruction and correction.

## 6. Temporal Intervals

Novi should represent:

- instants;
- closed intervals;
- open intervals;
- half-open intervals;
- recurring intervals;
- uncertain intervals;
- relative temporal expressions.

The selected representation must preserve boundary uncertainty.

## 7. Temporal Granularity

Support multiple granularities:

```text
NANOSECOND
MICROSECOND
MILLISECOND
SECOND
MINUTE
HOUR
DAY
WEEK
MONTH
YEAR
ERA / DOMAIN-SPECIFIC PERIOD
```

Granularity should not be silently upgraded.

## 8. Temporal Precision

```text
"on 17 August 2026"
```

does not imply:

```text
"at 00:00:00"
```

Unknown precision must remain unknown.

## 9. Temporal Uncertainty

A time can be uncertain:

```text
EVENT OCCURRED
between T1 and T2
```

or:

```text
approximately T
```

The uncertainty interval must be retained when materially relevant.

## 10. Relative Time

Expressions such as:

- yesterday;
- two weeks ago;
- shortly after;
- before the meeting;
- next month;

must be resolved relative to an explicit temporal anchor.

```text
RELATIVE EXPRESSION
 ↓
ANCHOR
 ↓
RESOLVED INTERVAL
```

## 11. Temporal Anchors

Possible anchors include:

- message time;
- event time;
- user-provided reference time;
- current system time;
- calendar event;
- known external event.

The chosen anchor must be recorded when ambiguity matters.

## 12. Temporal Ordering

Novi should support relations such as:

```text
BEFORE
AFTER
DURING
OVERLAPS
MEETS
STARTS
FINISHES
EQUALS
```

These relations should be represented explicitly when required for reasoning.

## 13. Temporal Contradiction

Examples:

```text
A occurred before B
A occurred after B
```

or:

```text
ENTITY X was in London at T1
ENTITY X was simultaneously in Tokyo at T1
```

Such contradictions should enter the conflict model rather than being silently resolved.

## 14. Temporal Identity Integration

Document 97 establishes that entity identity is time-aware.

```text
ENTITY X
 ├─ attribute A [T1–T2]
 └─ attribute B [T2–T3]
```

A changed attribute does not automatically create a new entity.

## 15. Temporal Entity States

Entities can have state histories:

```text
DEVICE
OFF [T1–T2]
ON  [T2–T3]
OFF [T3–T4]
```

State must be tied to validity intervals and evidence.

## 16. Temporal Relationships

Relationships can change over time:

```text
A works-for B [T1–T2]
A works-for C [T2–T3]
```

Retrieval must not flatten this into a timeless statement.

## 17. Temporal Events

Events should contain:

```text
EVENT_ID
EVENT_TYPE
PARTICIPANTS
LOCATION
START_TIME
END_TIME
TIME_UNCERTAINTY
SOURCE
PROVENANCE
```

Fields may remain unknown.

## 18. Event Time vs Narrative Order

The order in which information is described is not necessarily the order in which events happened.

```text
NARRATIVE ORDER
≠
EVENT ORDER
```

Novi must not infer chronology solely from textual sequence.

## 19. Temporal Causality

Temporal precedence is necessary for many causal claims but is not sufficient by itself.

```text
A before B
≠
A caused B
```

Full causal modeling is deferred to document 100.

## 20. Temporal Knowledge Graph

Novi's knowledge graph should support temporal facts conceptually as:

```text
SUBJECT
RELATION
OBJECT
VALID_TIME
PROVENANCE
```

Temporal knowledge graph research commonly extends static graph representations with time to model evolving facts and temporal validity. citeturn0search0turn0search1

## 21. Snapshot vs Event-Sourced Representation

The architecture supports both:

```text
SNAPSHOT
```

and:

```text
EVENT HISTORY
```

A snapshot is convenient for current state; event history preserves how state evolved.

They should not be treated as equivalent.

## 22. Current-State Reconstruction

Current state can be derived from valid events and authoritative updates:

```text
EVENT HISTORY
 ↓
TEMPORAL FILTER
 ↓
CONFLICT CHECK
 ↓
CURRENT STATE
```

Where an authoritative current source exists, it supersedes inferred historical state.

## 23. Historical Reconstruction

A query such as:

```text
"What did Novi believe on T?"
```

must be answered using memory state valid at T, not the latest state projected backward.

## 24. Bitemporal Memory

For high-integrity memory, support two temporal axes:

```text
VALID TIME
SYSTEM / TRANSACTION TIME
```

This allows Novi to distinguish:

```text
WHEN THE FACT WAS TRUE
```

from:

```text
WHEN NOVI KNEW / STORED IT
```

## 25. Late-Arriving Evidence

Evidence can arrive after the event it describes.

```text
EVENT T1
 ↓
EVIDENCE ARRIVES T3
```

The late evidence must not be assigned T3 as the event's time merely because it arrived then.

## 26. Retroactive Correction

New evidence may change the assessed validity of an older claim.

```text
OLD CLAIM
 ↓
NEW EVIDENCE
 ↓
REVISED TEMPORAL INTERPRETATION
```

The revision must preserve the old claim and its provenance where policy permits.

## 27. Temporal Reconsolidation

Temporal corrections integrate with document 77:

```text
RETRIEVE OLD MEMORY
 ↓
NEW TEMPORAL EVIDENCE
 ↓
RECONSOLIDATION CANDIDATE
 ↓
VALIDATION
 ↓
REVISED MEMORY
```

Retrieval itself does not authorize temporal rewriting.

## 28. Temporal Decay

Time can affect relevance and confidence, but age alone does not prove falsity.

```text
OLD
≠
FALSE
```

Historical facts can remain authoritative indefinitely.

## 29. Freshness

Freshness is task-dependent.

A claim from yesterday may be:

- extremely fresh for history;
- stale for current weather;
- irrelevant for a permanent historical fact.

Freshness must therefore be evaluated against query semantics.

## 30. Temporal Retrieval

Retrieval queries should support:

```text
AS-OF T
DURING T1–T2
BEFORE T
AFTER T
BETWEEN T1 AND T2
MOST RECENT VALID
FIRST OCCURRENCE
LATEST KNOWN
```

## 31. Temporal Retrieval Must Preserve Validity

A retrieval result should expose temporal validity when it materially affects interpretation.

```text
CLAIM
VALID [T1–T2]
```

not simply:

```text
CLAIM
```

## 32. Temporal Ranking

Temporal ranking should consider:

- query time;
- validity overlap;
- freshness requirement;
- source authority;
- provenance;
- uncertainty;
- conflict;
- task consequence.

## 33. Current vs Historical Queries

The system must distinguish:

```text
"Where is Alice?"
```

from:

```text
"Where was Alice yesterday?"
```

The first requires current-state validation; the second is historical reconstruction.

## 34. Temporal Context Assembly

Working memory should preserve temporal boundaries:

```text
FACT A [T1–T2]
FACT B [T2–T3]
```

rather than presenting both as timeless facts.

## 35. Temporal Reasoning Operators

The reasoning layer should support operators such as:

```text
BEFORE
AFTER
DURING
OVERLAP
CONTAINS
SINCE
UNTIL
UNTIL-EXCLUSIVE
RECENT
OLDEST
LATEST
```

Operator semantics must be explicit.

## 36. Temporal Aggregation

When aggregating events, preserve the aggregation interval.

```text
"10 events this week"
```

must identify which week and timezone are intended.

## 37. Time Zones

Absolute timestamps should be normalized internally while retaining source timezone information when relevant.

```text
INSTANT
+
SOURCE TIMEZONE
+
LOCAL REPRESENTATION
```

Do not discard the originating timezone when local calendar meaning matters.

## 38. Daylight-Saving Changes

Temporal calculations must account for timezone rule changes and daylight-saving transitions.

A "day" is not universally equivalent to 24 elapsed hours in local civil time.

## 39. Calendar Semantics

Support distinctions between:

- elapsed duration;
- calendar duration;
- business day;
- week;
- month;
- recurrence period.

These are not interchangeable.

## 40. Duration

A duration should be represented independently from its start/end anchor when required.

```text
START + DURATION → END
```

But calendar arithmetic can require timezone/calendar semantics.

## 41. Recurrence

Prospective memories may contain recurring temporal conditions:

```text
EVERY MONDAY
FIRST DAY OF MONTH
EVERY 6 HOURS
```

Recurrence must specify timezone and policy where relevant.

## 42. Temporal Intersections

The engine should be able to determine whether intervals:

- overlap;
- touch;
- contain one another;
- are disjoint;
- have uncertain relationship.

## 43. Incomplete Time

A memory may have only partial temporal information:

```text
YEAR KNOWN
MONTH UNKNOWN
```

The system must not invent the missing month.

## 44. Temporal Granularity Preservation

If a source says:

```text
"in 2024"
```

Novi must not silently transform it into:

```text
"2024-01-01T00:00:00"
```

## 45. Temporal Language

Natural-language time expressions require semantic parsing.

Ambiguous expressions should remain ambiguous when no reliable anchor exists.

Example:

```text
"next Friday"
```

requires a reference date/time and timezone.

## 46. Temporal Ambiguity

When ambiguity materially affects an action or conclusion:

```text
AMBIGUOUS TIME
 ↓
ASK / VERIFY
```

not:

```text
AMBIGUOUS TIME
 ↓
GUESS
```

## 47. Temporal Evidence

Each temporal claim should retain evidence for:

- event time;
- validity interval;
- capture time;
- source;
- extraction method;
- confidence.

## 48. Temporal Provenance

Temporal transformations must be traceable:

```text
SOURCE TEXT
 ↓
TEMPORAL EXTRACTION
 ↓
NORMALIZATION
 ↓
TEMPORAL CLAIM
```

## 49. Temporal Extraction Confidence

Distinguish:

```text
SOURCE EXPLICITLY STATES DATE
```

from:

```text
MODEL INFERRED DATE
```

The latter requires lower epistemic authority unless independently verified.

## 50. Temporal Conflict Arbitration

When sources disagree:

```text
SOURCE A: T1
SOURCE B: T2
```

arbitration should consider:

- source authority;
- directness;
- capture time;
- event-time evidence;
- temporal precision;
- independence;
- contradiction;
- domain rules.

## 51. Temporal Evidence Independence

Multiple reports derived from one original event do not constitute independent temporal evidence merely because they have different textual forms.

## 52. Future Reasoning

Predicting a future event is not equivalent to remembering a future fact.

```text
HISTORICAL FACT
≠
PREDICTION
```

Future predictions must carry forecast status and uncertainty.

## 53. Prediction Lifecycle

```text
PREDICTION
 ↓
FORECAST
 ↓
OUTCOME
 ↓
EVALUATION
```

A forecast must not silently become historical truth without outcome evidence.

## 54. Temporal Knowledge Completion

Temporal knowledge graph research studies completion of missing links conditioned on temporal validity. citeturn0search1

For Novi, inferred temporal facts must remain explicitly inferred rather than becoming indistinguishable from observed facts.

## 55. Interpolation vs Extrapolation

Temporal reasoning should distinguish:

```text
INTERPOLATION
→ infer within an observed temporal range

EXTRAPOLATION
→ infer beyond the observed range
```

These have different uncertainty profiles. Research explicitly distinguishes these settings in temporal KG reasoning. citeturn0search10

## 56. Abstention in Temporal Reasoning

Temporal reasoning should support abstention.

Recent work on temporal KG reasoning explicitly addresses selective prediction and abstention because indiscriminate uncertain predictions can create real-world risk. citeturn0search2

## 57. Temporal Model Interpretability

Where temporal inference affects consequential decisions, the system should expose:

- relevant historical evidence;
- temporal constraints;
- inferred intervals;
- contradictions;
- confidence/calibration;
- whether the result is interpolation or extrapolation.

## 58. Temporal Memory Types

Temporal semantics apply across all memory classes:

```text
EPISODIC
SEMANTIC
PROCEDURAL
PROSPECTIVE
WORKING
METAMEMORY
```

## 59. Procedural Memory Over Time

A skill can change with:

- practice;
- degradation;
- environment;
- hardware;
- software version.

Skill validity therefore requires temporal and environmental context.

## 60. Prospective Memory Over Time

An intention should include:

```text
CREATION TIME
TRIGGER / DUE TIME
EXPIRATION
COMPLETION TIME
STATUS
```

## 61. Temporal Ownership

The owner of an intention or memory can change only through authorized state transition.

Historical ownership must remain reconstructible when required.

## 62. Temporal Access Control

Authorization can be time-bounded:

```text
ACCESS GRANTED [T1–T2]
```

Past authorization does not imply current authorization.

## 63. Temporal Privacy

Some data becomes more or less sensitive over time, but deletion and access policies must remain explicit.

Temporal changes must not be used as an excuse to bypass retention rules.

## 64. Temporal Erasure

Erasure requests may need to cover all time-indexed derivatives:

```text
EVENT
 ↓
TEMPORAL INDEX
 ↓
SNAPSHOT
 ↓
EMBEDDING
 ↓
DERIVED CLAIM
```

The deletion graph must preserve temporal dependencies.

## 65. Historical Deletion Semantics

When a historical memory is erased, the system must distinguish:

```text
FACT NO LONGER RETAINED
```

from:

```text
FACT WAS NEVER TRUE
```

Deletion changes availability, not historical reality.

## 66. Temporal Distributed State

Distributed agents may observe the same event at different times.

Synchronization must preserve:

- event time;
- observation time;
- causal order;
- version;
- conflict state.

## 67. Clock Skew

Distributed timestamps may disagree because clocks differ.

```text
LOCAL CLOCK
≠
GLOBAL TRUTH
```

The system must record clock source/quality where temporal precision matters.

## 68. Event Ordering

Timestamp order should not automatically be treated as causal order.

Where available, causal metadata should supplement timestamps.

## 69. Late Distributed Events

An event arriving after a later event can require historical insertion:

```text
T1 event arrives at T3
```

Event stores and derived state must support such late arrivals without corrupting chronology.

## 70. Temporal Memory Compaction

Compaction may summarize event history, but must preserve enough information to reconstruct required historical states.

Lossy summarization must be explicitly identified.

## 71. Temporal Summaries

A summary such as:

```text
"Alice lived in London for several years"
```

must not replace precise source intervals when precision is needed.

## 72. Temporal Aggregation Provenance

Aggregates must retain:

- source interval;
- included records;
- aggregation method;
- version;
- uncertainty.

## 73. Temporal Retrieval Evaluation

Test:

- as-of retrieval;
- interval retrieval;
- latest-valid retrieval;
- historical reconstruction;
- stale-memory rejection;
- temporal conflict detection;
- timezone correctness;
- DST transitions;
- incomplete dates;
- late-arriving evidence.

## 74. Temporal Reasoning Evaluation

Include:

```text
BEFORE/AFTER
OVERLAP
DURING
SINCE/UNTIL
TEMPORAL ORDER
INTERPOLATION
EXTRAPOLATION
RECURRING EVENTS
CONFLICTS
UNCERTAIN INTERVALS
```

## 75. Longitudinal Evaluation

Evaluate temporal memory across long histories:

```text
DAY 1
 → DAY 30
 → DAY 365
 → DAY 1000
```

Measure whether temporal errors accumulate or propagate into semantic memory.

## 76. Temporal Calibration

Predictions and inferred temporal claims should be evaluated for calibration, not only accuracy.

## 77. Harm-Weighted Temporal Errors

A wrong historical timestamp may be harmless in one task and dangerous in another.

Evaluation should weight errors by downstream consequence.

## 78. Temporal Security

Threats include:

- timestamp manipulation;
- replay attacks;
- forged event time;
- stale-record injection;
- temporal prompt injection;
- delayed malicious updates;
- history rewriting;
- time-based access bypass.

## 79. Temporal Replay Defense

Replayed historical events must not automatically be interpreted as new events.

Event identity, source, sequence and provenance are required.

## 80. Temporal Poisoning

An attacker may inject a false historical record designed to influence future reasoning.

Temporal provenance and anomaly detection should be applied before consolidation.

## 81. Sleeper Temporal Memories

A malicious memory may be harmless until a future temporal condition triggers retrieval.

Temporal retrieval must therefore be included in security testing.

## 82. Current-State Supremacy

As required by 95:

```text
HISTORICAL MEMORY
        ↓
CONTEXT

CURRENT AUTHORITATIVE STATE
        ↓
CURRENT DECISION
```

Historical information must not override current authoritative state for consequential decisions.

## 83. Temporal Decision Boundary

Before a consequential action:

```text
HISTORICAL CLAIM
 ↓
CURRENT VALIDITY CHECK
 ↓
CURRENT AUTHORIZATION / SAFETY
 ↓
ACTION
```

## 84. Temporal Failure States

Support explicit states:

```text
TIME_UNKNOWN
TIME_UNCERTAIN
STALE
CONFLICTED
INVALIDATED
OUT_OF_RANGE
CLOCK_UNTRUSTED
LATE_ARRIVAL
TEMPORALLY_INCONSISTENT
```

## 85. Implementation Components

Logical components should include:

```text
Temporal Normalizer
Time Expression Resolver
Temporal Index
Temporal Query Engine
Temporal Constraint Engine
Temporal State Reconstructor
Temporal Conflict Resolver
Temporal Evaluation Harness
Temporal Provenance Service
```

## 86. Storage Independence

Temporal semantics should be implementable over:

- relational databases;
- event stores;
- graph databases;
- document stores;
- vector indexes;
- object stores.

Storage technology must not erase temporal semantics.

## 87. Reference Temporal Data Model

Conceptually:

```text
TemporalAssertion {
  assertion_id
  subject_entity_id
  predicate
  object / value
  valid_from
  valid_to
  valid_precision
  valid_uncertainty
  observed_at
  ingested_at
  source_id
  provenance_id
  epistemic_status
  confidence
  version
}
```

Fields may be null/unknown when evidence does not provide them.

## 88. Temporal Event Model

```text
TemporalEvent {
  event_id
  event_type
  participants
  start_time
  end_time
  time_precision
  time_uncertainty
  observed_at
  source_id
  provenance_id
  version
}
```

## 89. Query Contract

A temporal query should carry:

```text
QUERY
REFERENCE_TIME
TIMEZONE
TEMPORAL_OPERATOR
PRECISION
CONSEQUENCE_LEVEL
```

Where missing, defaults must be explicit and safe.

## 90. Research Boundary

Temporal knowledge graph research is useful for representation and reasoning, but Novi's memory architecture is broader.

Novi additionally requires:

- personal memory;
- provenance;
- privacy;
- deletion;
- authorization;
- distributed state;
- action safety;
- longitudinal evaluation.

Therefore temporal KG techniques are implementation candidates, not the architecture itself. Surveys classify temporal and dynamic graph reasoning as a distinct family while also emphasizing practical challenges and evolving knowledge. citeturn0search6turn0search7

## 91. Architectural Invariants

1. Event time is distinct from capture time.
2. Valid time is distinct from system time.
3. Historical truth is distinct from current truth.
4. Old does not mean false.
5. Current does not mean universally true.
6. Temporal precision must not be fabricated.
7. Unknown temporal boundaries remain unknown.
8. Relative time requires an anchor.
9. Timezone is part of temporal interpretation where local time matters.
10. Calendar duration is not universally equal to elapsed duration.
11. Narrative order is not event order.
12. Temporal precedence does not prove causality.
13. Late-arriving evidence must preserve event time.
14. Historical corrections preserve provenance.
15. Retrieval does not automatically rewrite temporal memory.
16. Predictions are not historical facts.
17. Interpolation and extrapolation are distinct.
18. Temporal inference must support abstention.
19. Temporal conflicts remain explicit until resolved.
20. Temporal validity must be preserved through retrieval.
21. Current authoritative state overrides historical memory for current consequential decisions.
22. Time-based access does not imply permanent authorization.
23. Deletion changes retained availability, not historical truth.
24. Distributed clocks are not automatically authoritative.
25. Timestamp order does not automatically establish causality.
26. Temporal summaries must preserve required reconstruction capability.
27. Temporal confidence is distinct from identity confidence.
28. Temporal errors must be evaluated by downstream consequence.
29. Temporal provenance must be traceable.
30. Temporal semantics must survive storage and migration.

## 92. Integration With 95

98 implements the temporal portion of the reference pipeline:

```text
OBSERVATION
 ↓
TEMPORAL INTERPRETATION
 ↓
EVIDENCE
 ↓
TEMPORAL MEMORY
 ↓
TEMPORAL RETRIEVAL
 ↓
ARBITRATION
 ↓
CURRENT-STATE VALIDATION
 ↓
REASONING
 ↓
ACTION
```

## 93. Integration With 97

Identity and time are inseparable for many entity attributes and relationships.

```text
ENTITY X
 ├─ IDENTITY
 ├─ ATTRIBUTES OVER TIME
 ├─ RELATIONSHIPS OVER TIME
 └─ STATE HISTORY
```

98 therefore treats 97's canonical entity IDs as stable references while keeping mutable attributes and relationships temporally versioned.

## 94. Integration With 96

98 resolves P0 gap #2:

**Temporal Reasoning / Temporal Memory.**

It establishes prerequisites for:

- 99 spatial memory;
- 100 causal world modeling;
- 101 cross-modal memory;
- 102 procedural skill verification;
- 103 migration;
- 104 model/memory co-evolution.

## 95. Final Principle

> **Novi must remember not only what it believes happened, but when it happened, when the evidence was observed, when the claim was valid, how precisely that time is known, and how the temporal interpretation was derived. A historical memory must remain historical; a prediction must remain a prediction; and current consequential decisions must be grounded in current authoritative state rather than stale memory.**

## Research References

1. Zhang, Y., Kong, X., Shen, Z., Li, J., Yi, Q., Shen, G., Dong, B. (2024). **A survey on temporal knowledge graph embedding: Models and applications.** *Knowledge-Based Systems*, DOI 10.1016/j.knosys.2024.112454. citeturn0search0
2. Cai, B., Xiang, Y., Gao, L., Zhang, H., Li, Y., Li, J. (2023). **Temporal Knowledge Graph Completion: A Survey.** *Proceedings of IJCAI 2023*, pp. 6545–6553. DOI 10.24963/ijcai.2023/734. citeturn0search1
3. Hou, Z., Jin, X., Li, Z., Bai, L., Guo, J., Cheng, X. (2024). **Selective Temporal Knowledge Graph Reasoning.** *LREC-COLING 2024*, pp. 14555–14566. citeturn0search2
4. Chen, K., Wang, Y., Li, Y., Li, A., Yu, H., Song, X. (2024). **A Unified Temporal Knowledge Graph Reasoning Model Towards Interpolation and Extrapolation.** *ACL 2024*. citeturn0search10
5. Su, M., Li, Z., Chen, Z., Bai, L., Jin, X., Guo, J. (2024). **Temporal Knowledge Graph Question Answering: A Survey.** citeturn0academia21
6. Zhang et al. (2024). **A Survey of Knowledge Graph Reasoning on Graph Types: Static, Dynamic, and Multi-Modal.** *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 46(12), 9456–9478. DOI 10.1109/TPAMI.2024.3417451. citeturn0search7
7. Pan, Q., Yao, L., Shen, G., Han, X., Chen, Y., Kong, X. (2025). **Leveraging temporal validity of rules via LLMs for enhanced temporal knowledge graph reasoning.** *Knowledge-Based Systems*, 327, 114094. DOI 10.1016/j.knosys.2025.114094. citeturn0search8
