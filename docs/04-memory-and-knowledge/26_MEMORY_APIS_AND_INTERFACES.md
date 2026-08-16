# 26 — Memory APIs and Interfaces

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define the architectural interfaces through which Novi's perception, cognition, autonomy, learning, agents, synchronization, diagnostics and external applications interact with memory and knowledge.

The goal is to prevent direct, uncontrolled access to canonical memory while allowing the robot to operate with low latency, offline capability, concurrency and clear provenance.

> **Components interact with memory through explicit contracts; they do not directly manipulate the canonical memory store.**

---

## 1. Interface Architecture

```text
                         NOVI
                           │
             ┌─────────────┼─────────────┐
             │             │             │
         Perception     Cognition      Autonomy
             │             │             │
         Learning       Agents       Diagnostics
             │             │             │
             └─────────────┼─────────────┘
                           │
                    MEMORY API LAYER
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
     Query API         Mutation API       Event API
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    POLICY / AUTH
                           │
                    MEMORY MANAGER
                           │
               ┌───────────┼───────────┐
               ▼           ▼           ▼
            SQLite      Files       Indexes
```

The Memory Manager remains the semantic authority.

---

## 2. Interface Principles

1. APIs must be explicit and versioned.
2. Reads should be cheap and safe to perform concurrently.
3. Writes must pass through admission and authorization.
4. Long-running model inference must not hold database transactions open.
5. Interfaces must preserve provenance.
6. Interfaces must support offline operation.
7. Interfaces must be idempotent where retries are expected.
8. API results must expose uncertainty where relevant.
9. Derived indexes must not become canonical authorities.
10. Security policy applies before mutation.
11. Privacy policy applies before retrieval as well as before storage.
12. Critical interfaces must have deterministic failure semantics.
13. Interface schemas must support backward/forward compatibility.
14. Safety-critical control remains outside ordinary memory APIs.

---

## 3. Interface Categories

Novi should separate at least:

```text
QUERY
  retrieve existing information

OBSERVE
  submit physical-world observations

MEMORIZE
  submit memory candidates

UPDATE
  propose changes to mutable semantic state

KNOWLEDGE
  propose/promote knowledge claims

CONTEXT
  request working context

EVENT
  append canonical events

SYNC
  exchange authorized changes

ADMIN
  inspect/maintain the memory subsystem
```

These categories should not automatically share permissions.

---

## 4. Query API

The Query API is the primary read interface.

Typical operations:

```text
get_memory(id)
search_memory(query)
search_semantic(query)
search_spatial(area)
search_temporal(range)
get_related_entities(id)
get_current_state(key)
get_history(entity)
get_knowledge(topic)
get_working_context(task)
```

The actual names are implementation details; the semantic contract is what matters.

---

## 5. Query Contract

A query should define:

- requester identity;
- purpose/context;
- query type;
- scope;
- filters;
- time range;
- spatial range where applicable;
- result limit;
- ranking policy;
- required freshness;
- required confidence;
- privacy/access level;
- cancellation/deadline.

The Memory Manager should not return more information than the requester is authorized to receive.

---

## 6. Query Results

Results should carry enough metadata for downstream reasoning.

Conceptually:

```json
{
  "memory_id": "mem_123",
  "content": "...",
  "score": 0.87,
  "confidence": 0.91,
  "created_at": "...",
  "updated_at": "...",
  "source_type": "sensor",
  "provenance_ref": "...",
  "version": 12
}
```

A retrieval score must not be presented as truth confidence.

---

## 7. Retrieval Score vs Belief Confidence

These are separate:

```text
retrieval_score
= how relevant the item appears to the query

confidence
= how strongly Novi should believe the underlying claim
```

A memory can be highly relevant but poorly supported.

---

## 8. Observation API

Perception and sensor pipelines should submit observations through an observation interface.

The observation contract should carry:

- event ID;
- sensor/source ID;
- acquisition timestamp;
- receive timestamp;
- coordinate frame;
- calibration reference;
- sensor health;
- measurement quality;
- uncertainty;
- model provenance if inferred;
- privacy classification;
- payload/reference.

This directly connects to documents 17 and 18.

---

## 9. Raw Data vs Observation

The memory API must distinguish:

```text
raw sensor stream
       ↓
observation
       ↓
memory candidate
```

High-frequency raw streams should normally use dedicated telemetry/data pipelines rather than inserting every frame into semantic memory.

Large media should generally be stored by reference with metadata in the memory layer.

---

## 10. Memory Admission API

A component should submit a **candidate**, not declare that something is definitely memory.

```text
submit_memory_candidate(...)
        ↓
validation
        ↓
policy
        ↓
provenance
        ↓
deduplication
        ↓
importance
        ↓
commit / reject / defer
```

The Memory Manager owns the final admission decision.

---

## 11. Memory Mutation API

Mutable memory changes should use explicit operations such as conceptually:

```text
create
update
supersede
annotate
link
archive
request_delete
restore
```

Each operation must carry the expected entity version when optimistic concurrency is required.

---

## 12. Optimistic Concurrency

Example:

```text
read memory X
version = 12

reasoning occurs

update X
expected_version = 12
```

If the current version is 13:

```text
UPDATE_REJECTED_STALE
```

The caller must reread and reevaluate.

This follows the concurrency architecture already established in document 15.

---

## 13. No Long Transactions Around AI Calls

This is a hard rule.

Never:

```text
BEGIN
 ↓
call LLM
 ↓
call VLM
 ↓
run embedding
 ↓
wait for external service
 ↓
COMMIT
```

Instead:

```text
read snapshot
 ↓
close transaction
 ↓
AI/model computation
 ↓
proposal
 ↓
revalidate version/policy
 ↓
short transaction
 ↓
commit
```

SQLite transactions are explicit units of database work and write transactions can conflict with other writers; the API layer must therefore keep transaction lifetimes short. citeturn0search1turn0search2

---

## 14. Event API

The Event API is responsible for canonical event ingestion.

Conceptual operations:

```text
append_event
append_batch
acknowledge_event
get_event
replay_events
get_event_cursor
```

Events should be immutable once accepted, except for explicit correction/annotation mechanisms.

---

## 15. Event Idempotency

Every event accepted through the API needs a stable event/change identity.

Repeated delivery:

```text
append(event_123)
append(event_123)
```

must not create two semantic events merely because the caller retried.

---

## 16. Batch Ingestion

High-frequency sensors should support batching.

Batch operations must preserve:

- ordering where required;
- individual event identity;
- timestamps;
- provenance;
- partial failure semantics.

A batch failure must not silently duplicate events when retried.

---

## 17. Backpressure

APIs must support resource-aware admission.

If Novi is under pressure:

```text
GPU busy
memory pressure
thermal pressure
battery low
storage pressure
```

low-priority ingestion may be delayed, compressed, sampled or rejected according to policy.

Safety-critical telemetry must have stronger guarantees.

---

## 18. Working Memory API

Cognition needs a fast context interface separate from long-term memory.

Conceptual operations:

```text
get_working_context(task)
add_context_item(...)
remove_context_item(...)
refresh_context(...)
```

Working memory is task-scoped and temporary.

It should not automatically become long-term memory.

---

## 19. Context Assembly

The Context API may combine:

```text
current task
+ current world state
+ recent events
+ relevant memories
+ spatial context
+ user context
+ safety constraints
+ active goals
```

The context assembler should identify where each item came from.

---

## 20. Knowledge API

Knowledge operations should be more restricted than ordinary memory retrieval.

Conceptual operations:

```text
get_knowledge
submit_knowledge_candidate
request_promotion
request_revision
request_retraction
```

Promotion must follow the learning/knowledge policy.

---

## 21. Knowledge Claims Need Evidence

A knowledge API should not accept:

```text
knowledge = arbitrary_string
```

without evidence metadata.

A claim should identify:

- evidence references;
- confidence;
- provenance;
- scope;
- validity interval if applicable;
- creator/process;
- model provenance;
- verification state;
- policy used for promotion.

---

## 22. Spatial Memory API

Because Novi maintains persistent spatial memory, the API should support:

```text
get_current_pose()
get_place(id)
search_places(area)
get_visit_history(place)
get_spatial_memories(area)
get_map_version()
submit_place_observation(...)
submit_map_update(...)
```

Spatial data must respect location privacy policies.

---

## 23. Map Data Separation

Large metric maps and semantic memory should not necessarily live in the same storage representation.

```text
map / point cloud / occupancy data
              │
              └── map subsystem

semantic place / visit / experience
              │
              └── memory subsystem
```

They are linked through stable IDs and provenance.

---

## 24. Synchronization API

The Sync API should expose changes rather than raw database files.

Conceptual operations:

```text
get_changes(cursor)
push_changes(batch)
ack_changes(...)
get_sync_state(peer)
request_missing_changes(...)
```

Incoming changes always pass through validation, authorization and conflict resolution.

---

## 25. No Database-File Synchronization

The API must never expose:

```text
copy novi.db over network
```

as the synchronization mechanism.

SQLite WAL provides local concurrency and checkpointing, but the database/WAL architecture is not a semantic distributed synchronization protocol. citeturn0search2turn0search8

---

## 26. Subscription / Event Notification API

Consumers may need to know when memory changes.

Conceptual subscription types:

```text
memory_created
memory_updated
memory_deleted
knowledge_promoted
place_entered
place_updated
conflict_detected
security_state_changed
```

Subscriptions must not expose data beyond subscriber authorization.

---

## 27. Query vs Subscription

Use queries for:

```text
"What do you know about X?"
```

Use subscriptions for:

```text
"Tell me when X changes."
```

This avoids inefficient polling.

---

## 28. API Versioning

Every externally consumed interface needs a versioning strategy.

Schema changes must support controlled migration.

Potential approaches:

```text
v1
v2
```

or compatibility negotiated through capabilities.

The exact mechanism will be selected during implementation.

---

## 29. Capability Discovery

Components should be able to determine what the Memory Manager supports.

Example:

```text
supports_spatial_search = true
supports_vector_search = true
supports_change_stream = true
supports_offline_sync = true
api_version = 1
```

Unknown capabilities should degrade safely.

---

## 30. Deadlines and Cancellation

Every potentially expensive request should support cancellation/deadline semantics.

Examples:

```text
retrieve context
deadline = 50ms
```

or:

```text
background consolidation
cancel if thermal pressure exceeds threshold
```

A caller should not be able to create unbounded memory work accidentally.

---

## 31. Error Model

Errors must be structured rather than arbitrary strings.

Examples:

```text
UNAUTHORIZED
FORBIDDEN
NOT_FOUND
STALE_VERSION
INVALID_PROVENANCE
INVALID_SCHEMA
POLICY_REJECTED
CONFLICT
RATE_LIMITED
RESOURCE_EXHAUSTED
TEMPORARILY_UNAVAILABLE
OFFLINE_LIMITATION
INTEGRITY_FAILURE
```

Callers need enough information to decide whether to retry, reevaluate or stop.

---

## 32. Retry Semantics

Retryability must be explicit.

```text
STALE_VERSION
→ reread and reevaluate

RESOURCE_EXHAUSTED
→ backoff

POLICY_REJECTED
→ do not retry blindly

INVALID_SCHEMA
→ fix request

DUPLICATE
→ treat as idempotent success where appropriate
```

Retries must not create duplicate memories or events.

---

## 33. Security Context

Every API request should carry or derive a security context containing:

- caller identity;
- process/agent identity;
- capabilities;
- authorization context;
- privacy scope;
- request ID;
- correlation ID;
- authentication state.

The caller must not be allowed to forge a higher-privilege context through ordinary payload fields.

---

## 34. Provenance Context

The API should preserve the difference between:

```text
caller
source evidence
model that produced interpretation
human confirmation
```

For example:

```text
caller = perception-service
source_sensor = camera_03
model = detector_v5
confirmation = none
```

This prevents the service identity from being mistaken for evidence authority.

---

## 35. Privacy-Aware Retrieval

Retrieval should enforce policy before returning content.

A caller may be authorized to know:

```text
"Vano is home"
```

without being authorized to retrieve:

```text
raw location history for the last 30 days
```

The API therefore needs field/scope-level access controls where appropriate.

---

## 36. Sensitive Data References

Large or sensitive payloads should often be returned by controlled references rather than embedding the full content into every response.

Examples:

```text
media_ref
map_ref
raw_audio_ref
raw_image_ref
```

Dereferencing requires its own authorization check.

---

## 37. Streaming and Large Data

High-rate sensor data should use streaming/data-plane interfaces rather than ordinary semantic query APIs.

Examples:

```text
camera frames
LiDAR scans
IMU streams
audio
point clouds
```

The memory API consumes derived observations and selected references.

This keeps the cognitive memory plane from becoming the raw sensor transport layer.

---

## 38. ROS / Isaac ROS Integration

Novi's robotics data plane should remain compatible with ROS 2/Isaac ROS where those interfaces provide appropriate capabilities.

NVIDIA documents Isaac ROS as using standard ROS interfaces on input/output topics and providing GPU-accelerated components for Jetson and NVIDIA platforms. citeturn0search0turn0search7

This suggests a useful separation:

```text
ROS 2 / Isaac ROS
       ↓
robotics data plane
       ↓
Novi adapters
       ↓
Memory Event / Observation API
       ↓
Memory Manager
```

Novi should not force every memory consumer to understand ROS internals.

---

## 39. GPU Data Interfaces

Where perception pipelines use GPU-resident data, Novi should avoid unnecessary copies.

NVIDIA documents NITROS type adaptation/type negotiation as a way for compatible ROS nodes to exchange GPU-accelerated memory and reduce CPU copies. citeturn0search18

Therefore:

```text
GPU sensor pipeline
       ↓
GPU processing
       ↓
Novi adapter
       ↓
semantic observation
       ↓
Memory API
```

The semantic memory API should not require copying entire image/point-cloud payloads merely to record an observation reference.

---

## 40. Local IPC

Inside Novi, interfaces may use local IPC such as:

- Unix domain sockets;
- shared memory;
- ROS 2/DDS;
- local RPC;
- language-native interfaces where safely encapsulated.

The architecture should choose based on latency, reliability, security and operational complexity.

---

## 41. Remote API

Remote access should be a separate trust boundary.

```text
local memory API
      ≠
remote administration API
```

Remote APIs require:

- authentication;
- authorization;
- encryption;
- rate limiting;
- auditing;
- privacy enforcement;
- explicit capability scope.

---

## 42. Control App Interface

The control application should never access SQLite directly.

Instead:

```text
Control App
    ↓
authorized control API
    ↓
Novi service
    ↓
Memory / autonomy / diagnostics interfaces
```

The control app is not a privileged database client.

---

## 43. Admin Interface

Administrative operations should be separated from ordinary cognition.

Potential operations:

```text
health
backup
restore
migration
reindex
inspect
security
sync diagnostics
```

Destructive operations require stronger authorization and explicit confirmation.

---

## 44. Maintenance Mode

Novi should have an explicit maintenance mode for operations that cannot safely run during ordinary autonomy.

Examples:

- schema migration;
- storage repair;
- full index rebuild;
- security recovery;
- hardware replacement.

Maintenance mode must not silently disable safety controls.

---

## 45. Interface Observability

Every request should have a traceable request/correlation ID.

Telemetry should record where appropriate:

- request type;
- caller;
- latency;
- result class;
- error;
- memory IDs affected;
- policy decision;
- resource usage.

Sensitive payload contents should not automatically be logged.

---

## 46. API and Memory Transactions

The API may provide semantic transaction concepts, but they must map safely onto the underlying storage architecture.

A semantic transaction should not imply that arbitrary external computation is performed while holding a SQLite transaction.

Instead:

```text
read snapshot
 ↓
proposal
 ↓
validate
 ↓
short storage transaction
```

This preserves concurrency and responsiveness.

---

## 47. Eventual vs Immediate Consistency

Each interface should declare the consistency expected.

Examples:

```text
safety state → immediate/authoritative
current pose → very fresh
working context → fresh snapshot
long-term semantic search → bounded staleness acceptable
analytics → eventual consistency
embeddings → eventual/rebuildable
```

Callers should not assume every query sees every derived index update immediately.

---

## 48. Offline Behavior

Every API should define behavior when disconnected from networks.

Local operations should continue:

- retrieval;
- memory writes;
- knowledge operations;
- event ingestion;
- spatial memory;
- diagnostics;
- local learning.

Network-dependent operations should return explicit states such as:

```text
OFFLINE
QUEUED
LOCAL_ONLY
SYNC_PENDING
```

They must not block core cognition indefinitely.

---

## 49. API Queues

Background operations should use durable queues where losing the request would be harmful.

Examples:

- synchronization;
- embedding generation;
- noncritical consolidation;
- backup jobs;
- deferred indexing.

Queue entries need identity and retry semantics.

---

## 50. Priority Classes

Memory work should have priority classes.

Example:

```text
P0 — safety / critical state
P1 — cognition / active task
P2 — memory writes
P3 — retrieval/index maintenance
P4 — consolidation / background learning
P5 — analytics
```

Exact priorities will be tuned during implementation.

---

## 51. API Rate Limits

Limits should exist per caller and operation class.

This prevents one component from starving the memory subsystem.

High-rate sensor ingestion should use bounded queues and backpressure rather than unrestricted API calls.

---

## 52. Schema Ownership

Each interface schema must have an explicit owner.

Changes require:

- compatibility review;
- migration plan;
- test updates;
- version change where required;
- documentation update.

No component should silently change the meaning of a shared field.

---

## 53. Interface Testing

Every critical interface requires:

- unit tests;
- contract tests;
- schema compatibility tests;
- authorization tests;
- privacy tests;
- concurrency tests;
- retry/idempotency tests;
- failure injection;
- offline tests;
- resource exhaustion tests;
- corruption tests;
- performance benchmarks.

Cross-process and cross-language clients should use contract tests rather than relying only on implementation-level tests.

---

## 54. Reference Interface Matrix

| Interface | Primary users | Writes canonical state? | Offline | Typical consistency |
|---|---|---:|---:|---|
| Query | cognition, agents | No | Yes | snapshot/eventual by query |
| Observation | perception | Candidate/event | Yes | ordered/eventual |
| Memory admission | cognition/learning | Through policy | Yes | authoritative |
| Knowledge | learning/cognition | Through policy | Yes | authoritative |
| Working context | cognition | Task-local | Yes | fresh |
| Event | sensor/robotics | Append | Yes | ordered |
| Sync | peer devices | Through policy | Queueable | reconciled |
| Subscription | services | No | Local | event-driven |
| Admin | operators | Restricted | Yes | authoritative |
| Remote control | authorized app | Restricted | No remote dependency | authoritative |

---

## 55. Implementation Boundary

The first implementation should expose a small stable core rather than dozens of endpoints.

Recommended V1 primitives:

```text
append_event
submit_observation
submit_memory_candidate
get_memory
search_memory
get_working_context
submit_knowledge_candidate
get_current_state
get_changes
apply_change
subscribe_to_changes
```

Higher-level operations can be composed from these primitives.

---

## 56. Why the API Layer Matters

Without a formal interface boundary, the architecture can degrade into:

```text
agent → SQLite
agent → JSON file
agent → vector DB
agent → graph DB
agent → cache
agent → random memory file
```

That would make provenance, security, concurrency, recovery and evolution extremely difficult to control.

Instead:

```text
all semantic memory access
          ↓
      Memory API
          ↓
     Memory Manager
          ↓
canonical state + derived state
```

---

## 57. Architectural Invariants

1. No ordinary component directly writes canonical memory storage.
2. Every mutation is authorized and policy-checked.
3. Every important mutation has provenance.
4. Retries cannot duplicate semantic events.
5. Stale writes are rejected or explicitly reconciled.
6. Long-running AI operations never hold database transactions open.
7. Query relevance and belief confidence remain distinct.
8. Raw sensor streams are not automatically semantic memory.
9. Derived indexes are not canonical authorities.
10. Remote interfaces cannot bypass local policy.
11. Offline operation remains functional for local memory capabilities.
12. API schemas are versioned and contract-tested.
13. Security and privacy policies apply at the interface boundary.
14. Safety-critical state remains outside ordinary semantic memory authority.
15. Every significant API operation is observable without logging unnecessary sensitive content.
16. Interface failures have deterministic retry/non-retry semantics.

---

## 58. Final Principle

> **The Memory API is the controlled nervous system through which Novi's mind interacts with its accumulated experience.**

It must be simple enough for every subsystem to use, strict enough to preserve security and provenance, fast enough for real-time cognition, resilient enough for offline operation, and stable enough that Novi can evolve internally without breaking every component that depends on memory.

The interface is therefore not merely an implementation detail. It is a long-term architectural contract.
