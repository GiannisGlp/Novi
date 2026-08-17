# 73 — Memory Knowledge Causality, Event Log and Temporal Ordering

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi represents events, causal relationships, temporal ordering, replay, and event history so that distributed memory can reason correctly about what happened, when it happened, what caused it, and what was merely observed later.

## Core Principle

> **Novi must never confuse when an event happened with when Novi learned about it.**

Physical/event time, observation time, ingestion time, processing time, synchronization time, and logical causal order are distinct concepts.

## 1. Why an Event Log Exists

An event log can provide:

- durable history;
- provenance;
- synchronization input;
- replay;
- recovery;
- auditability;
- causal reconstruction;
- rebuildable derived state.

The event log is not automatically the source of truth for every memory class. Its authority is defined per resource.

## 2. Event vs State

```text
EVENT
"Novi observed obstacle X at time T"

STATE
"Obstacle X is currently believed to be present"
```

State is a projection that may change; an event describes something that occurred or was recorded.

## 3. Event Identity

Every durable event should have a unique identifier within the required scope.

Recommended metadata may include:

```text
event_id
stream_id
source_id
sequence
schema_version
payload_type
payload
integrity metadata
```

## 4. Event Time

**Event time** represents when the underlying event occurred, according to the best available clock or source timestamp.

For physical observations, sensor timestamping should be as close to acquisition as practical.

## 5. Observation Time

Observation time identifies when a system actually observed or measured the underlying phenomenon.

It can differ from the time a derived interpretation was produced.

## 6. Ingestion Time

Ingestion time identifies when Novi accepted an event into its ingestion boundary.

```text
event occurred
    ↓
observed
    ↓
ingested
```

These timestamps must not be collapsed without justification.

## 7. Processing Time

Processing time identifies when a component processed an event.

Processing delay can be substantial during:

- offline operation;
- resource pressure;
- queue backlogs;
- synchronization;
- recovery.

## 8. Synchronization Time

Synchronization time records when another agent/device received or exchanged an event.

```text
event time ≠ sync time
```

## 9. Logical Time

Logical ordering represents causal relationships when physical clocks cannot establish reliable order.

Possible mechanisms include:

- Lamport clocks;
- vector clocks;
- version vectors;
- explicit parent-event references.

The selected mechanism must match the consistency requirements.

## 10. Causality

If event B was produced because of event A:

```text
A → B
```

B should retain enough causal metadata to identify that relationship where required.

## 11. Causal Precedence

Causal precedence means:

```text
A happened-before B
```

It does not necessarily provide an exact physical timestamp relationship beyond the causal ordering.

## 12. Concurrent Events

Two events may be concurrent when neither causally precedes the other.

```text
A   ↘
     ?
B   ↗
```

Concurrent events must not be ordered arbitrarily and then treated as causally related.

## 13. Physical Clocks

Clock sources may include:

- system clock;
- monotonic clock;
- synchronized network clock;
- sensor clock;
- GNSS time;
- external device clock.

Clock source and synchronization quality should be retained where important.

## 14. Clock Uncertainty

A timestamp should carry uncertainty or quality information where practical.

```text
T = 12:00:00
uncertainty = ±Δ
```

False timestamp precision must be avoided.

## 15. Monotonic Time

Durations and local ordering should prefer monotonic clocks where appropriate because wall clocks can jump due to synchronization or manual changes.

## 16. Wall-Clock Time

Human-facing dates and calendar semantics require wall-clock time and timezone context.

A wall-clock timestamp must not be used as a substitute for causal ordering.

## 17. Time Zones

Events involving human calendar meaning should retain sufficient timezone/offset information.

UTC-normalized storage may be used alongside original timezone context where needed.

## 18. Sensor Timestamping

Sensor measurements should be timestamped as close to acquisition as practical.

For multi-sensor fusion, timestamps must be sufficiently accurate to establish temporal alignment.

## 19. Sensor Time Synchronization

Novi should account for:

- sensor clock offsets;
- clock drift;
- transport latency;
- buffering;
- frame-rate differences;
- timestamp jitter.

## 20. Event Ordering Pipeline

```text
RAW EVENT
   ↓
VALIDATE TIMESTAMP
   ↓
NORMALIZE TIME REPRESENTATION
   ↓
ATTACH CLOCK QUALITY
   ↓
ATTACH CAUSAL METADATA
   ↓
STORE
   ↓
ORDER / INDEX
```

## 21. Arrival Order

Arrival order is an implementation fact, not necessarily event order.

```text
A happened at 10:00
B happened at 10:05

B arrives first
A arrives later
```

Novi must not infer B happened first solely because it arrived first.

## 22. Out-of-Order Events

Out-of-order events are expected in distributed and offline systems.

The event log should support late arrivals within defined policy limits.

## 23. Late Events

A late event may change historical interpretation without necessarily changing current state.

Example:

```text
current state = obstacle absent
late event = obstacle was present 30 minutes ago
```

The event can update history without incorrectly changing current physical state.

## 24. Event Windows

Systems may define acceptable lateness windows for efficient processing.

Events outside the window must not simply be discarded as false; they should enter an explicit late-event policy.

## 25. Event Corrections

If an event is later determined to be erroneous:

```text
original event
      ↓
correction / invalidation event
```

Prefer append-only correction semantics for auditable event classes rather than silently rewriting historical evidence.

## 26. Event Immutability

Important evidence events should be immutable after commitment.

Corrections should create explicit new events or governed supersession relationships.

## 27. Event Deletion

Event immutability does not override privacy or deletion requirements.

When deletion is required, event-history sanitization follows the governed lifecycle and secure-deletion architecture.

## 28. Event Streams

Events may be partitioned into streams by:

- resource;
- device;
- user/owner scope;
- subsystem;
- agent;
- mission/task;
- security domain.

Stream boundaries should align with authorization and lifecycle policies.

## 29. Sequence Numbers

Sequence numbers can provide local stream ordering and gap detection.

They do not necessarily establish global causal ordering.

## 30. Gaps

If an event stream reports:

```text
101
102
104
```

Novi should detect the missing sequence and avoid assuming event 103 never existed.

## 31. Replay

Replay means reprocessing historical events to reconstruct state or validate behavior.

Replay must use the original event semantics and appropriate software/schema versions.

## 32. Deterministic Replay

Where deterministic replay is required, capture sufficient:

- event order/causality;
- configuration;
- model/version information;
- relevant random seeds or nondeterminism controls;
- environment assumptions.

## 33. Replay Safety

Replay must not accidentally:

- actuate motors;
- send external commands;
- delete live memory;
- duplicate notifications;
- trigger irreversible operations.

Replay should normally operate against isolated state or explicitly marked simulation/reconstruction modes.

## 34. Rebuilding Projections

Derived indexes and knowledge projections should be rebuildable from authoritative events/state where practical.

```text
EVENTS
  ↓
REPLAY
  ↓
PROJECTION
```

## 35. Event Log vs Memory

Not every raw sensor event belongs in long-term semantic memory.

```text
event log
   ≠
semantic memory
```

Retention policies determine what remains durable and at what granularity.

## 36. High-Frequency Sensors

Camera frames, audio samples, IMU measurements and other high-rate data can overwhelm an event log.

Use appropriate policies such as:

- aggregation;
- sampling;
- summaries;
- bounded retention;
- event extraction;
- tiered storage.

Critical evidence must not be discarded solely because it is high frequency when required by safety or investigation policy.

## 37. Event Compression

Compression or aggregation must preserve required provenance and semantic meaning.

A compressed representation must not falsely imply that every underlying measurement was identical.

## 38. Causality Across Agents

For distributed agents:

```text
Agent A event
      ↓
message
      ↓
Agent B event
```

B should retain causal linkage where the message materially caused B's event.

## 39. Message Causality

A received message and a subsequent local action are distinct events.

The relationship should be explicit:

```text
received event M
      ↓
decision D
      ↓
action A
```

This supports later audit and reasoning.

## 40. Observation → Interpretation

The event model should distinguish:

```text
OBSERVATION
"camera detected shape"

INTERPRETATION
"shape is probably a person"

DECISION
"slow down"

ACTION
"motor command issued"
```

Each stage has different evidence and authority requirements.

## 41. Knowledge Promotion Events

When a claim becomes durable knowledge, record the promotion event and its supporting evidence.

```text
claim candidate
 ↓
validation
 ↓
promotion event
 ↓
knowledge state
```

## 42. Conflict Events

Distributed conflicts should be represented explicitly where useful:

```text
CONFLICT_DETECTED
CLAIM_A
CLAIM_B
RESOLUTION
```

This preserves the reasoning history.

## 43. Deletion Events

Deletion/restriction transitions should be represented sufficiently to prevent stale replicas from reintroducing protected information.

## 44. Event Authentication

Events received from other agents should carry integrity/authentication metadata appropriate to the trust boundary.

Authentication establishes source identity/integrity—not factual truth.

## 45. Event Provenance

A durable event should be traceable to its source where policy permits:

```text
source sensor / agent / user
 ↓
acquisition
 ↓
event
 ↓
transformation
 ↓
knowledge
```

## 46. Event Schema

Event schemas must be versioned.

Changing event semantics without versioning can make historical replay incorrect.

## 47. Schema Evolution

When an event schema changes:

- preserve historical interpretation;
- define migration rules;
- version parsers;
- test replay compatibility;
- avoid silently changing old semantics.

## 48. Event Retention

Retention should depend on:

- privacy;
- security;
- provenance requirements;
- debugging/audit requirements;
- storage cost;
- safety requirements;
- legal/policy requirements.

There is no universal retention period.

## 49. Tiered Event Storage

Possible tiers:

```text
HOT
recent, frequently accessed

WARM
less frequently accessed

COLD / ARCHIVE
historical, infrequent access

SANITIZED / DELETED
no longer available
```

Tier changes must preserve lifecycle semantics.

## 50. Event Integrity

Important event streams should use integrity mechanisms appropriate to the threat model, potentially including:

- authenticated records;
- hash chaining;
- signed events;
- secure storage;
- append-only controls.

No single mechanism is universally required; the design must match risk.

## 51. Tamper Detection

If event integrity cannot be established:

```text
INTEGRITY UNKNOWN
      ↓
QUARANTINE / DEGRADED TRUST
```

Do not silently treat corrupted history as authoritative.

## 52. Event Recovery

Recovery should detect:

- missing events;
- duplicated events;
- corrupted payloads;
- broken causal links;
- schema incompatibility;
- invalid sequence transitions.

## 53. Distributed Event Merge

Merging streams should preserve:

- event identity;
- source;
- causal relationships;
- timestamps;
- conflicts;
- deletion state.

The merge operation must not manufacture causality where none existed.

## 54. Snapshotting

Long event streams may use periodic snapshots to improve recovery performance.

Snapshots are derived state and should retain the event/version boundary from which they were constructed.

## 55. Snapshot Validation

A restored snapshot should be validated against its associated event position/version before being trusted.

## 56. Checkpointing

Synchronization and replay can use checkpoints to record the highest safely processed state.

A checkpoint must not claim successful processing of an event that was only received but not committed.

## 57. Exactly-Once Semantics

The architecture should not assume universal exactly-once delivery.

Prefer designs that remain correct under:

```text
at-least-once delivery
+ deduplication
+ idempotent processing
```

where appropriate.

## 58. Idempotency

Reprocessing the same event must not create unintended duplicate side effects.

This is essential for:

- synchronization;
- recovery;
- replay;
- retry logic.

## 59. Event Priority

Events may have priority classes.

Example:

```text
SAFETY / SECURITY
CRITICAL STATE
USER INTERACTION
MEMORY
BACKGROUND TELEMETRY
```

Priority must not bypass authorization or integrity validation.

## 60. Resource Limits

Event processing must be bounded by:

- storage;
- CPU;
- GPU;
- memory;
- queue length;
- processing time;
- network bandwidth.

Under pressure, low-priority processing can degrade while critical safety and state handling continue.

## 61. Offline Operation

The event architecture must function without network connectivity.

Local events can accumulate and synchronize later under the distributed-state rules.

## 62. Time When Offline

If network time synchronization is unavailable, Novi should continue using its local clock while recording clock quality/uncertainty.

It must not fabricate synchronized timestamps.

## 63. GPS/GNSS Time

When valid GNSS timing is available, it can improve time reference quality for supported hardware, but loss of GNSS must not disable core event processing.

## 64. Event Privacy

Event metadata can itself reveal:

- location;
- routines;
- identities;
- household activity;
- device usage.

Event logs therefore require the same privacy and authorization discipline as other memory infrastructure.

## 65. Auditability

The event architecture should support answering:

```text
What happened?
When did it happen?
When did Novi learn it?
Who/what observed it?
What caused it?
What did Novi infer?
What changed?
Why did state change?
Which policy allowed it?
```

## 66. Testing

Test:

- clock skew;
- clock jumps;
- sensor timestamp drift;
- out-of-order events;
- late events;
- duplicate events;
- missing sequence numbers;
- replay;
- partial replay;
- corrupted events;
- schema migration;
- concurrent events;
- causal chains;
- offline queues;
- reconnection;
- snapshot recovery;
- interrupted commits;
- deletion during replay;
- privacy filtering;
- unauthorized event injection;
- event floods;
- deterministic replay assumptions.

## 67. Architectural Invariants

1. Event time and ingestion time are distinct.
2. Processing time and synchronization time are distinct.
3. Physical time does not replace causal ordering.
4. Arrival order does not establish event order.
5. Concurrent events must not be given artificial causality.
6. Important evidence events retain provenance.
7. Corrections should preserve historical lineage where required.
8. Event schemas are versioned.
9. Replay cannot trigger uncontrolled real-world side effects.
10. Reprocessing must be idempotent where retries are possible.
11. Event logs are not automatically semantic memory.
12. High-frequency sensor data requires explicit retention/aggregation policy.
13. Event deletion follows privacy and secure-deletion requirements.
14. Distributed event merges preserve causal relationships.
15. Snapshots identify their event/version boundary.
16. Checkpoints distinguish received from committed state.
17. Exactly-once delivery is not assumed universally.
18. Event integrity failures cause degraded trust or quarantine for protected state.
19. Offline operation remains fully functional.
20. Time uncertainty is represented rather than fabricated away.
21. Event metadata is itself protected information.
22. Event history must support reconstruction of why important state changed.

## 68. Final Principle

> **Novi's memory should be able to reconstruct not only what it believes, but how that belief came to exist, what evidence caused it, when the evidence occurred, when Novi learned it, and how later events changed the conclusion.**

The event log and causality model therefore become the temporal backbone of distributed memory, while remaining subject to privacy, security, authorization, retention, deletion, resource, and safety boundaries.