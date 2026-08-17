# 30 — Memory Event Model and Event Sourcing

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define the event model that records meaningful changes and observations entering Novi's memory architecture, and establish how trusted events can be projected into memories, current state, knowledge, synchronization state and audit trails.

This document does not require every sensor sample to become a permanent event. It defines the semantic event layer between high-rate physical/operational streams and durable cognitive state.

## Core Principle

> **An event records something that happened; a memory records something Novi decided is worth retaining; a state is a projection; knowledge is an interpreted, evidence-backed claim.**

These concepts must remain distinguishable.

---

## 1. Event Hierarchy

Novi should distinguish:

```text
RAW SENSOR SAMPLE
       ↓
INGESTION EVENT
       ↓
OBSERVATION EVENT
       ↓
MEMORY EVENT
       ↓
KNOWLEDGE CHANGE
       ↓
STATE PROJECTION
```

Not every layer must persist every underlying byte.

High-frequency raw streams may remain in bounded telemetry buffers while semantically important events receive durable retention.

---

## 2. What Is an Event?

A Novi event is an immutable record describing a significant occurrence, observation, accepted transition or authorized operation.

Examples:

- object detected;
- person identified with permitted confidence;
- temperature measurement accepted;
- user statement received;
- memory admitted;
- memory superseded;
- knowledge promoted;
- location changed;
- map updated;
- synchronization change accepted;
- deletion requested;
- model changed;
- hardware fault detected.

Events should describe what occurred, not embed arbitrary mutable current state.

---

## 3. Event Identity

Every durable event requires a globally unique event ID within Novi's event namespace.

Recommended conceptual structure:

```text
node/installation identity
+
monotonic local sequence
+
random/cryptographic uniqueness component where required
```

The exact identifier format is an implementation decision.

Event IDs must remain stable through synchronization, backup and replay.

---

## 4. Event Envelope

A canonical event envelope should contain, as applicable:

```json
{
  "event_id": "evt_...",
  "event_type": "observation.created",
  "schema_version": 1,
  "source_id": "thermal_camera_01",
  "source_instance_id": "...",
  "occurred_at": "...",
  "recorded_at": "...",
  "time_quality": "synchronized",
  "sequence": 183920,
  "causation_id": "evt_...",
  "correlation_id": "corr_...",
  "entity_ids": ["object_123"],
  "payload": {},
  "provenance": {},
  "integrity": {},
  "privacy_class": "private"
}
```

The exact schema will be implemented separately.

---

## 5. Occurred Time vs Recorded Time

Every event should distinguish:

**occurred_at** — when the event happened in the physical/logical world.

**recorded_at** — when Novi accepted the event into its event system.

These may differ due to buffering, processing latency, network transport or offline operation.

The distinction is mandatory for reliable temporal reasoning.

---

## 6. Event Ordering

Novi must distinguish:

- physical time;
- local processing order;
- causal order;
- synchronization arrival order.

Arrival order must never automatically be treated as event truth.

Example:

```text
Event B arrives first
Event A arrives second

A caused B
```

The event model must be able to represent this causal relationship.

---

## 7. Sequence Numbers

A local event source may maintain a monotonic sequence number.

Sequence numbers help detect:

- missing events;
- duplicates;
- reordering;
- replay;
- synchronization gaps.

A sequence number is not a universal replacement for timestamps or causal metadata.

---

## 8. Causation and Correlation

Novi should distinguish:

### Causation ID

The event that directly caused this event.

### Correlation ID

The larger activity/episode/transaction to which multiple events belong.

Example:

```text
voice input
  ↓
ASR result
  ↓
intent interpretation
  ↓
command
  ↓
action
  ↓
action outcome
```

All can share a correlation ID while each event has its own causation relationship.

---

## 9. Event Immutability

Durable events should be immutable after acceptance.

If an event was incorrect, Novi should record a corrective event rather than silently editing history.

Example:

```text
observation.created
      ↓
observation.corrected
```

The original remains available according to retention policy.

---

## 10. Corrections

Corrections should identify:

- original event;
- reason;
- correcting authority/source;
- new interpretation/value;
- timestamp;
- policy used.

A correction does not erase provenance of the original observation.

---

## 11. Event Types

The event taxonomy should remain extensible but controlled.

Initial categories:

```text
sensor.*
observation.*
perception.*
spatial.*
memory.*
knowledge.*
learning.*
action.*
autonomy.*
synchronization.*
security.*
privacy.*
hardware.*
system.*
```

Event types require documented schemas and ownership.

---

## 12. Sensor Events

Sensor events may represent meaningful accepted measurements rather than every raw sample.

Examples:

```text
sensor.temperature.measured
sensor.motion.detected
sensor.audio.detected
sensor.gnss.position_received
sensor.camera.frame_available
sensor.lidar.scan_available
```

High-frequency samples should normally remain in specialized buffers/telemetry paths unless promoted to semantic events.

---

## 13. Observation Events

Observation events represent interpreted evidence.

Example:

```text
observation.object_detected
```

The observation must retain source measurement IDs and perception provenance.

An observation is not automatically a fact.

---

## 14. Memory Events

Memory events represent lifecycle transitions.

Examples:

```text
memory.candidate_created
memory.admitted
memory.enriched
memory.consolidated
memory.superseded
memory.archived
memory.deleted
```

These events allow memory history to be reconstructed without mutating old events.

---

## 15. Knowledge Events

Knowledge events represent changes to knowledge claims.

Examples:

```text
knowledge.candidate_created
knowledge.promoted
knowledge.verified
knowledge.contradicted
knowledge.downgraded
knowledge.superseded
```

Knowledge events should link to supporting evidence.

---

## 16. Spatial Events

Spatial events may represent:

- GNSS position;
- local pose;
- place recognition;
- map update;
- route discovery;
- visit start/end;
- landmark observation;
- spatial relationship changes.

Spatial events should preserve coordinate-frame and uncertainty provenance.

---

## 17. User Events

User-originated events should retain authenticated identity and authority context where applicable.

Examples:

```text
user.statement_received
user.preference_confirmed
user.memory_deleted
user.permission_changed
```

A perceived human voice is not automatically an authenticated user event.

---

## 18. Action and Autonomy Events

Autonomy should emit events for significant decisions and outcomes.

Example:

```text
navigation.goal_selected
navigation.path_planned
navigation.path_rejected
motor.command_issued
motor.action_completed
motor.action_failed
```

This creates the chain needed to answer:

> Why did Novi do that?

The event should reference the decision context without duplicating all memory content.

---

## 19. Decision Provenance

Important decisions should retain references to:

- triggering event;
- relevant memory IDs;
- knowledge IDs;
- sensor observations;
- model/version;
- policy version;
- safety state;
- resource state where relevant;
- action result.

This enables post-incident reconstruction.

---

## 20. Event → Memory Projection

Events are evidence; memories are projections/retentions derived from events and policy.

```text
Event
 ↓
admission policy
 ↓
memory candidate
 ↓
validation
 ↓
Memory
```

Multiple events may contribute to one memory.

One event may contribute to multiple derived memories when policy permits.

---

## 21. Event → Knowledge Projection

Knowledge requires stronger evidence.

```text
many observations
      ↓
pattern
      ↓
knowledge candidate
      ↓
validation
      ↓
knowledge claim
```

The resulting knowledge must retain supporting evidence references.

---

## 22. Current State as Projection

Current state should generally be reconstructible from trusted events and accepted state transitions.

Example:

```text
location.changed → kitchen
location.changed → hallway
location.changed → bedroom
```

projects to:

```text
current_location = bedroom
```

The projection can be rebuilt without rewriting historical events.

---

## 23. Event Sourcing Boundary

Novi should use event-sourcing principles selectively rather than forcing every table into a full event-sourced architecture.

Good candidates:

- memory lifecycle;
- knowledge lifecycle;
- synchronization changes;
- security events;
- important autonomy decisions;
- user-controlled semantic changes.

Poor candidates for unbounded event sourcing:

- every camera frame;
- every microphone sample;
- every IMU sample;
- high-frequency motor telemetry.

Those belong in specialized telemetry/storage systems with controlled retention.

---

## 24. Raw Data References

Large payloads should normally be referenced rather than embedded directly in the canonical event.

Example:

```text
Event
 ├── metadata
 ├── provenance
 └── media_reference → local object store
```

The reference must contain enough integrity metadata to detect substitution or corruption.

---

## 25. Event Retention

Retention should depend on event class and value.

Potential model:

```text
raw high-rate telemetry → short retention
semantic sensor events → medium/long retention
memory lifecycle events → long retention
security events → policy-defined long retention
critical decisions → long retention
```

Privacy rules remain authoritative.

---

## 26. Event Compaction

Events may be compacted only when doing so does not destroy required provenance, auditability or recovery guarantees.

Example:

```text
1000 repetitive telemetry events
        ↓
statistical summary
```

should not be used when exact events are required for safety or legal/forensic requirements.

Compaction itself should be auditable.

---

## 27. Snapshots

Snapshots can accelerate recovery and state reconstruction.

```text
events 1..100000
      ↓
snapshot 100000
      ↓
events 100001..N
```

A snapshot is a derived checkpoint, not a replacement for the event history unless retention policy explicitly permits history pruning.

Snapshots must carry:

- source event position;
- schema version;
- integrity metadata;
- creation time;
- software/version metadata.

---

## 28. Replay

Trusted events should support deterministic or controlled replay where practical.

Replay enables:

- debugging;
- regression testing;
- recovery;
- model comparison;
- memory-policy testing;
- autonomy investigation.

Replay must distinguish:

```text
historical event
vs
new side effect
```

A replay must not accidentally move motors, send messages or mutate canonical state unless explicitly executed in a controlled mode.

---

## 29. Dry-Run Replay

The default diagnostic replay mode should be non-destructive.

```text
historical events
      ↓
replay engine
      ↓
simulated state
      ↓
analysis
```

It should not write canonical memory or invoke physical actions.

---

## 30. Determinism

Where deterministic replay is required, capture relevant inputs such as:

- event sequence;
- model/version;
- policy/version;
- configuration;
- random seed where applicable;
- time semantics;
- feature flags;
- environment assumptions.

Some neural/real-time systems may remain probabilistic; the replay framework should record this explicitly rather than promising impossible bit-level determinism.

---

## 31. Duplicate Events

Event consumers must be idempotent.

If the same event is delivered twice:

```text
first delivery → apply
second delivery → recognize duplicate → no duplicate semantic mutation
```

Event IDs and consumer checkpoints support this.

---

## 32. Out-of-Order Events

Consumers must tolerate bounded reordering.

An event arriving late should be evaluated using its actual occurrence time and causal context.

If correcting current state would be unsafe or too expensive, Novi may retain the late event and trigger a controlled recomputation.

---

## 33. Missing Events

Missing sequence ranges should be detectable when the source provides sequence numbers.

Possible outcomes:

```text
recover missing event
mark gap
reconstruct from independent source
accept reduced confidence
```

Novi must not silently treat an unknown gap as proof that nothing happened.

---

## 34. Distributed Event Synchronization

Events are suitable synchronization units because they are immutable and identifiable.

```text
Replica A
  event 101
  event 102

Replica B
  event 101
  event 103

reconciliation
  ↓
101 common
102 missing from B
103 missing from A
```

Semantic conflict resolution remains responsible for incompatible claims.

---

## 35. Event Authenticity

For security-sensitive or synchronized events, provenance should include authenticity/integrity metadata.

Possible mechanisms include:

- authenticated channels;
- signatures where justified;
- integrity hashes;
- device identity;
- sequence validation.

The mechanism depends on the threat model and performance requirements.

---

## 36. Event Authorization

Not every component can create every event type.

Examples:

```text
sensor driver → sensor events
memory manager → memory lifecycle events
safety controller → safety events
autonomy → decision/action events
user interface → authorized user events
```

Unauthorized event creation must be rejected.

---

## 37. Event Schema Governance

Each event type requires:

- schema version;
- owner;
- semantic definition;
- required fields;
- optional fields;
- compatibility rules;
- privacy classification;
- retention policy;
- producer permissions;
- consumer expectations.

Schema changes must be versioned and tested.

---

## 38. Schema Evolution

Compatible additions may use the same major schema version when safe.

Breaking changes require a new version and migration/translation strategy.

Consumers should reject or quarantine events they cannot safely interpret rather than guessing.

Unknown fields must not be silently discarded when they may carry security, provenance or semantic meaning.

---

## 39. Event Storage

The initial implementation may use SQLite for the durable semantic event store, provided the workload remains within measured limits.

The design should preserve a clean abstraction so higher-throughput telemetry can use specialized storage without changing semantic event contracts.

SQLite WAL, transactions and backup behavior must follow the database architecture already defined elsewhere.

---

## 40. Event Indexing

Useful indexes may include:

- event ID;
- event type;
- occurred_at;
- recorded_at;
- source ID;
- entity ID;
- correlation ID;
- causation ID;
- schema version;
- privacy class;
- sequence.

Indexes are derived state and must be rebuildable from trusted events.

---

## 41. Event-to-Memory Lineage

A memory should be able to answer:

```text
Which events contributed to me?
```

And an event should be able to answer, where permitted:

```text
Which memories were derived from me?
```

This creates a bidirectional lineage graph without making events and memories the same object.

---

## 42. Event-to-Action Lineage

Important actions should be traceable:

```text
sensor event
 ↓
observation
 ↓
memory
 ↓
knowledge
 ↓
decision
 ↓
action
 ↓
outcome
```

This is necessary for debugging autonomous behavior and evaluating whether learning improved or degraded behavior.

---

## 43. Privacy

Events can contain sensitive information even when they do not contain raw media.

Examples:

- exact location;
- person identity;
- voice metadata;
- activity patterns;
- timestamps;
- household routines.

Therefore event retention, indexing, synchronization and access must follow privacy classification.

---

## 44. Deletion

Deleting a memory does not necessarily mean deleting every underlying event immediately.

The correct behavior depends on the retention/legal/privacy policy.

However, deleted semantic data must not remain queryable through derived indexes, embeddings or projections beyond permitted retention.

Where an event itself must be deleted, deletion must be represented and propagated according to the deletion architecture.

---

## 45. Security Events

Security-sensitive events should include:

- authorization failure;
- integrity failure;
- replay attempt;
- suspicious synchronization;
- policy violation;
- security-state change;
- credential rotation;
- model verification failure.

Security events should have stronger retention and access controls where justified.

---

## 46. Failure Handling

Event ingestion must define behavior for:

- invalid schema;
- missing required fields;
- corrupted payload;
- unknown producer;
- unauthorized producer;
- duplicate event;
- sequence gap;
- clock anomaly;
- storage failure;
- queue overflow;
- disk-full condition.

The system should prefer explicit quarantine/degradation over silent data loss.

---

## 47. Backpressure

High-rate producers must not be allowed to exhaust the semantic event store.

Controls include:

- bounded queues;
- rate limits;
- sampling;
- aggregation;
- priority classes;
- event coalescing;
- dropping only explicitly droppable classes.

Safety and critical semantic events must have protected capacity.

---

## 48. Event Priority

Events may be classified:

```text
CRITICAL
IMPORTANT
NORMAL
BULK
TELEMETRY
```

Priority affects resource allocation and retention, not truthfulness.

A low-priority event can still be true; it may simply have lower operational urgency.

---

## 49. Relationship to Memory Lifecycle

The lifecycle architecture in document 29 uses events to represent transitions.

```text
observation event
      ↓
memory candidate
      ↓
memory.admitted
      ↓
memory.consolidated
      ↓
memory.superseded
```

The event stream therefore provides the historical explanation for memory state.

---

## 50. Relationship to Conflict Resolution

Conflict resolution consumes competing events/claims and produces a new resolution event.

Example:

```text
claim A
claim B
  ↓
conflict.detected
  ↓
conflict.resolved
  ↓
current state updated
```

The competing evidence remains auditable.

---

## 51. Relationship to Backup and Recovery

Recovery can use snapshots plus event replay.

```text
verified snapshot
      ↓
replay trusted events
      ↓
rebuild state
      ↓
verify projections
```

This can be more robust than trusting a mutable derived database state alone.

---

## 52. Relationship to Evaluation

The event model provides reproducible evaluation inputs.

A benchmark can replay:

```text
sensor events
observation events
memory events
user events
spatial events
```

and compare Novi versions under controlled conditions.

This supports longitudinal evaluation without requiring identical physical-world conditions.

---

## 53. Relationship to Spatial Memory

Spatial events provide the temporal backbone for place history:

```text
GNSS position
local pose
place recognition
visit start
visit end
landmark observation
map update
```

These can be combined into visit episodes and spatial memories.

---

## 54. Event Store vs Memory Store

The event store and memory store should remain conceptually distinct even if SQLite initially stores both.

```text
EVENT STORE
what happened

MEMORY STORE
what Novi retained

KNOWLEDGE STORE
what Novi currently believes/knows

PROJECTIONS
optimized views
```

This separation prevents implementation convenience from collapsing semantic boundaries.

---

## 55. Event Store vs Raw Telemetry

Raw telemetry is optimized for high-volume physical data.

Semantic events are optimized for meaningful reconstruction.

Example:

```text
1000 IMU samples/sec
        ↓
telemetry storage
        ↓
selected motion event
        ↓
event store
```

The system must not force the event store to carry all raw sensor traffic.

---

## 56. Testing Requirements

Test:

- unique event IDs;
- duplicate delivery;
- out-of-order delivery;
- missing sequences;
- clock anomalies;
- causal chains;
- correlation chains;
- schema evolution;
- malformed events;
- unauthorized producers;
- replay;
- deterministic replay where supported;
- snapshot/replay recovery;
- event compaction;
- deletion propagation;
- privacy filtering;
- storage failure;
- disk-full behavior;
- queue overflow;
- synchronization gaps;
- conflict resolution;
- event-to-memory lineage;
- event-to-action lineage.

---

## 57. Architectural Invariants

1. Durable events are immutable after acceptance.
2. Corrections are represented as new events.
3. Event occurrence time and recording time remain distinguishable.
4. Arrival order is not automatically causal order.
5. Event IDs remain stable across synchronization and recovery.
6. Duplicate delivery must be idempotent.
7. Missing event ranges must be detectable where sequencing permits.
8. High-rate raw telemetry is not automatically semantic memory.
9. Memory and knowledge remain projections/claims distinct from events.
10. Important decisions retain event lineage.
11. Derived indexes are rebuildable.
12. Event schemas are versioned.
13. Unauthorized producers cannot create privileged events.
14. Replay must not cause unintended physical side effects.
15. Privacy and deletion policies apply to events and their projections.
16. Event retention must remain bounded and policy-driven.
17. Event sourcing is applied selectively, not dogmatically.

---

## 58. Final Principle

> **Events are Novi's durable account of what happened; memories are what Novi chose to retain from those events; knowledge is what Novi has sufficient evidence to believe.**

Keeping those layers separate gives Novi the ability to learn, recover, audit, replay, synchronize and evolve without losing the distinction between observation, interpretation and truth.
