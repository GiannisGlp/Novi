# 27 — Memory Runtime and Execution Model

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi's memory subsystem executes continuously as a real-time, resource-constrained, safety-aware service on the robot.

This document specifies the runtime model between the memory APIs and the underlying storage, indexing, learning, synchronization, perception and autonomy systems.

It answers:

- Which processes exist?
- Which workloads are synchronous vs asynchronous?
- How are queues scheduled?
- How are CPU/GPU resources allocated?
- How does memory behave under overload?
- What happens during startup, shutdown and restart?
- How are failures isolated?
- How does the system remain functional offline?
- How does memory remain responsive while models are running?

The implementation must remain compatible with the project's broader principle:

> **Novi is an autonomous, continuously evolving robot, but its memory system must remain deterministic at its trust boundaries, observable, bounded and recoverable.**

---

## 1. Architectural Position

The runtime sits between the public memory interfaces and the physical storage/derived-state workers.

```text
Perception ───────┐
Cognition ────────┤
Autonomy ─────────┤
Learning ─────────┤
Spatial subsystem ─┤
Synchronization ──┤
Agents ────────────┘
        │
        ▼
   Memory API
        │
        ▼
 Memory Runtime
        │
 ┌──────┼───────────────┐
 ▼      ▼               ▼
Queues  Scheduler   Policy/Gates
 │       │               │
 └───────┼───────────────┘
         ▼
 Canonical Store
         │
 ┌───────┼──────────────┐
 ▼       ▼              ▼
Indexes  Embeddings   Graph/Maps
```

The runtime owns execution coordination. It does not become a second semantic authority.

---

## 2. Core Runtime Principles

1. Canonical memory writes are short and transactional.
2. Long-running model inference never holds a storage transaction open.
3. CPU/GPU-heavy work is asynchronous unless a strict synchronous result is required.
4. Safety-critical workloads have priority over background learning.
5. Memory remains operational when networking is unavailable.
6. Derived-state workers can be stopped and rebuilt without destroying canonical memory.
7. Backpressure is explicit; queues are bounded.
8. A failing worker must not normally crash the entire memory subsystem.
9. Runtime state is observable and auditable.
10. Shutdown and recovery are designed states, not exceptional afterthoughts.
11. The runtime must degrade gracefully under CPU, GPU, RAM, thermal, power and storage pressure.
12. Autonomous learning cannot starve perception, safety, navigation or core memory operations.

---

## 3. Process Model

The implementation should initially favor a small number of clearly separated services/processes rather than a large microservice deployment on the robot.

A conceptual V1 layout is:

```text
Novi Memory Runtime
│
├── memory-api
├── memory-manager
├── event-ingestor
├── scheduler
├── retrieval-worker
├── consolidation-worker
├── learning-worker
├── embedding-worker
├── graph/spatial-worker
├── sync-worker
├── backup-worker
└── health/telemetry
```

These may be implemented as threads, task executors or separate processes depending on measured isolation and performance requirements.

The architecture does not mandate process-per-component.

---

## 4. Process vs Thread Boundary

Use a process boundary when a component:

- has materially different failure characteristics;
- loads a large or unstable native library;
- executes untrusted/less-trusted code;
- requires independent restart;
- has strong resource-isolation requirements;
- interacts with hardware drivers where isolation is valuable.

Use threads/tasks within a process when:

- low-latency communication is important;
- shared state is safe and controlled;
- failure isolation does not justify IPC overhead;
- the workload is small and stable.

The final boundary must be validated on Jetson Orin 64GB rather than chosen for architectural aesthetics.

---

## 5. Recommended Initial Runtime Topology

A practical initial topology is:

```text
                ┌────────────────────┐
                │   Novi Core        │
                │                    │
                │ Memory API         │
                │ Memory Manager     │
                │ Scheduler          │
                │ Policy Engine      │
                └─────────┬──────────┘
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
     Fast workers    Background       External I/O
                    workers
          │               │                │
       retrieval       learning         sync/backup
       admission       embedding
       working         consolidation
       context         graph
```

This is intentionally simpler than deploying every function as a network service.

Local IPC or in-process queues should be preferred for hot paths.

---

## 6. Runtime Classes

Work should be classified by urgency.

### Class A — Safety / Critical

Examples:

- safety-state memory reads;
- emergency state persistence;
- safety-relevant evidence;
- critical fault recording.

These must preempt or bypass ordinary background work as defined by the safety architecture.

### Class B — Interactive / Real-Time

Examples:

- current context retrieval;
- recent memory retrieval;
- active spatial state;
- user interaction context.

### Class C — Normal Cognitive

Examples:

- episodic memory admission;
- knowledge retrieval;
- consolidation triggers.

### Class D — Background

Examples:

- embeddings;
- graph rebuilding;
- index maintenance;
- synchronization;
- backups;
- long-term consolidation.

### Class E — Opportunistic

Examples:

- expensive replay;
- large-scale reindexing;
- retrospective analysis;
- benchmark jobs.

Class E work should run only when resources permit.

---

## 7. Priority Rule

The default priority relationship is:

```text
Safety
  >
Interactive cognition
  >
Core memory persistence
  >
Navigation/spatial continuity
  >
Normal learning
  >
Synchronization
  >
Index/embedding maintenance
  >
Backup/replay/benchmarking
```

The exact priority of navigation and persistence relative to cognition must be validated against the autonomy architecture.

A background task must never cause a critical queue to become unavailable.

---

## 8. Synchronous vs Asynchronous Operations

### Synchronous

Use synchronous execution when the caller needs a deterministic immediate result and the operation is bounded.

Examples:

- read current working context;
- validate a memory identifier;
- commit a small memory mutation;
- retrieve a small result set.

### Asynchronous

Use asynchronous execution for:

- embedding generation;
- large retrieval expansion;
- consolidation;
- knowledge promotion analysis;
- graph updates;
- map processing;
- synchronization;
- backups;
- long-running model inference;
- historical replay.

A synchronous API must not secretly perform unbounded background work while pretending to be instantaneous.

---

## 9. Queue Architecture

Each workload class should have an explicit bounded queue.

```text
                 Scheduler
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
   Critical      Interactive   Background
     queue          queue         queue
       │              │             │
       └──────────────┼─────────────┘
                      ▼
                   workers
```

Queues should expose:

- depth;
- oldest item age;
- throughput;
- failure count;
- retry count;
- dropped/coalesced count;
- processing latency.

---

## 10. Backpressure

When producers are faster than consumers, the system must apply backpressure rather than allowing unbounded memory growth.

Possible actions:

```text
slow producer
batch
coalesce
sample
prioritize
spill to durable queue
reject low-priority work
```

Never silently drop high-value canonical events.

Dropping a low-value derived telemetry sample may be acceptable under policy.

---

## 11. Event Coalescing

High-rate sensor streams may generate enormous numbers of observations.

The runtime may coalesce redundant derived work while preserving canonical evidence required by policy.

Example:

```text
1000 camera frames
      ↓
1000 perception results
      ↓
10 meaningful memory candidates
```

The reduction must not erase evidence required for safety, auditing or later reconstruction.

---

## 12. Transaction Boundary

Storage transactions must be short.

Correct pattern:

```text
read snapshot
    ↓
release transaction
    ↓
model / business logic
    ↓
produce mutation proposal
    ↓
re-read/revalidate if needed
    ↓
short write transaction
    ↓
commit
```

Incorrect pattern:

```text
BEGIN
  ↓
call LLM
  ↓
call embedding model
  ↓
wait for network
  ↓
process image
  ↓
COMMIT
```

SQLite's concurrency model makes long write transactions especially undesirable because write access is serialized at the database level. WAL improves reader/writer concurrency but does not turn SQLite into an unlimited multi-writer system. citeturn0search4turn0search9

---

## 13. SQLite Connection Model

The initial implementation should use controlled connection ownership.

Recommended conceptual pattern:

```text
Memory Manager
   │
   ├── read connections / pool
   └── controlled write path
```

Do not allow arbitrary components to create uncontrolled SQLite connections against the canonical store.

All connections must use a defined configuration for:

- journal mode;
- busy timeout/retry policy;
- synchronous policy;
- foreign-key enforcement;
- transaction mode;
- checkpoint behavior;
- connection lifecycle.

The exact values are implementation decisions and must be benchmarked on target storage.

---

## 14. WAL and Checkpoint Scheduling

WAL should be treated as part of the storage runtime, not an implementation detail hidden from operations.

Checkpoint work can compete with other I/O.

The runtime should observe:

- WAL size;
- checkpoint duration;
- checkpoint frequency;
- blocked writers/readers;
- storage latency.

Background checkpoint work should be scheduled so it does not interfere with interactive cognition or safety-critical persistence.

SQLite documents automatic checkpointing and allows applications to control checkpoint behavior; Novi should therefore explicitly benchmark checkpoint policy rather than accepting defaults blindly. citeturn0search4

---

## 15. CPU Scheduling

CPU-heavy work includes:

- parsing;
- indexing;
- database maintenance;
- graph operations;
- compression;
- some perception preprocessing;
- embedding preparation.

The runtime should avoid unrestricted worker pools.

Each workload should have:

- concurrency limit;
- queue limit;
- priority;
- CPU budget where practical;
- cancellation policy.

---

## 16. GPU Scheduling

GPU-heavy work may include:

- VLM inference;
- embeddings;
- vision processing;
- speech models;
- perception;
- reranking;
- generative models.

The memory runtime should not assume that GPU work is free merely because memory is available.

GPU contention can increase latency for perception and cognition.

GPU-intensive background work must therefore be throttled when interactive or safety-critical inference is active.

---

## 17. Jetson Resource Awareness

Novi targets Jetson Orin 64GB, so runtime scheduling must be resource-aware.

Relevant runtime signals include:

- RAM usage;
- swap usage;
- CPU utilization/frequency;
- GPU utilization/frequency;
- accelerator utilization;
- temperatures;
- power consumption;
- storage pressure;
- thermal throttling;
- process health.

NVIDIA's `tegrastats` exposes processor, memory, temperature and power-related measurements, making it appropriate as one input to the runtime health layer. citeturn0search7

Jetson power and thermal management can actively throttle hardware and can perform shutdown actions, so memory scheduling must treat thermal state as a real execution constraint rather than merely a telemetry metric. citeturn0search0turn0search8

---

## 18. Thermal-Aware Scheduling

If Novi enters thermal degradation:

```text
NORMAL
   ↓
thermal pressure
   ↓
reduce opportunistic work
   ↓
reduce background inference
   ↓
reduce indexing/consolidation
   ↓
preserve safety + core cognition
```

The runtime must not wait until thermal shutdown to react.

Thermal thresholds must be derived from the actual carrier board, cooling design and Jetson configuration rather than copied blindly from development hardware.

---

## 19. Power-Aware Scheduling

When battery or power availability is constrained, background work should be reduced.

Examples:

```text
low battery
   ↓
stop benchmark jobs
stop large reindexing
slow consolidation
reduce synchronization
preserve critical memory
```

Memory persistence must remain available while lower-priority work is suspended.

---

## 20. Storage-Aware Scheduling

Storage pressure should influence runtime behavior.

Example:

```text
storage normal
 → normal operation

storage warning
 → reduce derived artifacts
 → accelerate cleanup

storage critical
 → stop non-essential writes
 → protect canonical memory
 → preserve recovery metadata
```

The system must reserve enough storage for emergency persistence and recovery operations.

---

## 21. Runtime State Machine

The memory runtime should expose an explicit lifecycle:

```text
BOOTING
   ↓
INITIALIZING
   ↓
RECOVERING
   ↓
READY
   ↓
DEGRADED
   ↓
RECOVERING
   ↓
READY
```

Terminal/exceptional state:

```text
FAILED
   ↓
SAFE / READ-ONLY MODE
   ↓
RECOVERY
```

Exact interaction with the robot-wide safety state is defined elsewhere.

---

## 22. Startup Sequence

Recommended startup sequence:

1. verify runtime configuration;
2. verify storage availability;
3. verify database integrity/recovery state;
4. load protected policies;
5. establish canonical store access;
6. validate schema version;
7. recover durable queues;
8. validate indexes/derived state;
9. initialize resource monitors;
10. start critical workers;
11. expose memory API;
12. start background workers;
13. enter READY.

Background indexing must not block essential memory availability unless required for correctness.

---

## 23. Graceful Shutdown

Shutdown should proceed approximately as:

```text
stop new background work
       ↓
finish/abort safe queued work
       ↓
commit critical state
       ↓
flush durable queues
       ↓
checkpoint according to policy
       ↓
write shutdown marker/telemetry
       ↓
close connections
```

The system must also tolerate abrupt power loss and recover without relying on graceful shutdown.

---

## 24. Crash Recovery

After an unexpected restart:

```text
start
 ↓
inspect storage
 ↓
SQLite recovery
 ↓
validate event/queue state
 ↓
recover pending mutations
 ↓
rebuild invalid derived state
 ↓
resume runtime
```

The runtime should distinguish:

- committed work;
- uncommitted work;
- acknowledged external work;
- queued but unprocessed work.

This prevents duplicate side effects.

---

## 25. Worker Failure Isolation

A worker failure must normally be isolated.

Example:

```text
embedding worker crashes
        ↓
embeddings unavailable
        ↓
canonical memory remains available
        ↓
retrieval falls back to supported methods
        ↓
worker restarts
        ↓
embeddings rebuild
```

A derived-state failure should not normally become a cognitive-memory failure.

---

## 26. Worker Supervision

Workers should expose:

- health;
- heartbeat;
- queue depth;
- current task;
- task age;
- restart count;
- last failure;
- resource usage.

A supervisor may restart failed workers according to bounded retry/backoff policy.

Repeated failure should transition the subsystem to DEGRADED rather than causing an infinite restart loop.

---

## 27. Cancellation

Long-running work must support cancellation where technically possible.

Cancellation is especially important for:

- background model inference;
- reindexing;
- synchronization;
- backups;
- replay;
- consolidation.

Cancellation must leave canonical state consistent.

A partially generated derived artifact should be discarded or marked incomplete.

---

## 28. Deadlines

Interactive requests should have deadlines.

Example:

```text
memory context request
deadline = 100 ms
```

If the preferred retrieval path cannot meet the deadline, the runtime should return an acceptable degraded result rather than blocking indefinitely.

Deadline values are engineering targets, not universal constants.

---

## 29. Graceful Degradation

The memory system should have fallback layers.

Example:

```text
semantic retrieval
   ↓ timeout/degraded
lexical retrieval
   ↓ unavailable
recent-memory retrieval
   ↓ unavailable
working-memory snapshot
```

The fallback hierarchy must be explicit and must not silently change the semantic meaning of a result.

---

## 30. Offline Operation

The memory runtime must operate without:

- Internet;
- cloud APIs;
- remote databases;
- remote model services.

Networking-dependent workers should become suspended/deferred rather than blocking the core runtime.

```text
Wi-Fi OFF
   ↓
local memory continues
local retrieval continues
local cognition continues
local learning continues
sync queue grows within limits
```

This follows the architectural requirement that connectivity is optional infrastructure, not a prerequisite for Novi's core functionality.

---

## 31. Synchronization Worker

Synchronization should be isolated from the canonical write path.

```text
canonical changes
      ↓
outbox
      ↓
sync worker
      ↓
network
      ↓
remote peer
```

Incoming changes pass through validation, conflict resolution and authorization before canonical application.

A network outage must not block local writes.

---

## 32. Backup Worker

Backups should run asynchronously.

The backup worker must:

- select a consistent snapshot;
- avoid long blocking transactions;
- monitor I/O impact;
- throttle when necessary;
- verify output;
- record backup metadata;
- report failures.

Backup activity must yield to critical workloads.

---

## 33. Embedding Worker

Embedding generation should be decoupled from memory admission.

```text
memory committed
     ↓
embedding job
     ↓
embedding generated
     ↓
validate source version
     ↓
index
```

If the source memory changes before embedding completion, the worker must detect the version mismatch and regenerate rather than attaching a stale embedding to newer memory.

---

## 34. Consolidation Worker

Consolidation is background work.

It should:

- consume eligible memories;
- apply deterministic admission/consolidation policies;
- generate proposals;
- commit short transactions;
- record provenance;
- remain interruptible.

Consolidation must never starve current-memory retrieval or safety workloads.

---

## 35. Learning Worker

The learning worker is one of the least trusted runtime components from a policy perspective because it can influence future behavior.

It must:

- operate on bounded input;
- produce explicit proposals;
- preserve provenance;
- pass evaluation gates;
- respect protected policies;
- support rollback;
- expose resource usage.

Learning should never directly modify protected runtime/security configuration.

---

## 36. Spatial Worker

Spatial memory can be computationally expensive.

Tasks may include:

- map updates;
- place recognition;
- SLAM integration;
- map indexing;
- route history;
- spatial embeddings;
- place summaries.

Spatial updates should be prioritized according to autonomy needs. A currently active navigation map is more urgent than retrospective processing of a month-old visit.

---

## 37. Retrieval Execution

Retrieval should be treated as a pipeline rather than one monolithic query.

```text
request
 ↓
policy filter
 ↓
working memory
 ↓
structured retrieval
 ↓
lexical retrieval
 ↓
vector retrieval
 ↓
spatial/temporal filters
 ↓
ranking
 ↓
context assembly
 ↓
result
```

Each stage should have resource and latency limits.

---

## 38. Context Assembly

Context assembly must not blindly return the largest possible amount of memory.

It should respect:

- token budget;
- relevance;
- recency;
- authority;
- privacy;
- spatial relevance;
- temporal relevance;
- contradiction state;
- uncertainty.

Large context should not be treated as inherently better cognition.

---

## 39. Runtime Fairness

One workload must not monopolize the runtime.

Example failure:

```text
continuous embedding generation
        ↓
GPU saturated
        ↓
vision latency rises
        ↓
autonomy degrades
```

The scheduler must prevent this class of failure.

---

## 40. Resource Budgets

Each worker class should eventually have measurable budgets:

- CPU concurrency;
- GPU concurrency;
- RAM limit/target;
- queue size;
- latency target;
- power target;
- thermal constraints;
- storage/I/O budget.

Initial values should be experimentally determined on the target Jetson.

---

## 41. Thermal and Power Feedback Loop

The scheduler should consume hardware health signals:

```text
hardware telemetry
      ↓
resource state
      ↓
scheduler policy
      ↓
worker budgets
      ↓
actual load
      ↓
hardware telemetry
```

This creates a controlled feedback loop.

It must be bounded and stable; the scheduler should not oscillate aggressively between modes.

---

## 42. Priority Inversion

Priority inversion is possible when a high-priority operation waits on a resource held by lower-priority work.

The runtime should minimize this through:

- short transactions;
- bounded locks;
- priority-aware queues;
- avoiding long critical sections;
- priority inheritance where supported/needed;
- separate resources for critical workloads.

SQLite write contention is one reason to keep critical transactions small.

---

## 43. Locking Policy

Avoid application-level global locks around the entire memory subsystem.

Prefer:

```text
small resource scope
short critical section
transactional state change
```

over:

```text
GLOBAL MEMORY LOCK
   ↓
model inference
   ↓
network
   ↓
database
```

The latter would make the entire system fragile.

---

## 44. Durable Queues

Queues whose contents represent important semantic work should be durable.

Examples:

- accepted event ingestion awaiting processing;
- memory mutation proposals that have been admitted but not finalized;
- synchronization outbox;
- deletion propagation;
- recovery operations.

Purely derived/recomputable jobs may remain ephemeral.

Each queue must explicitly declare whether loss is acceptable.

---

## 45. Exactly-Once vs At-Least-Once

The runtime should not assume exactly-once execution where it cannot guarantee it.

Prefer:

```text
at-least-once delivery
+
idempotent processing
+
unique operation identity
```

for many asynchronous workflows.

Canonical state transitions must be protected against duplicate application.

---

## 46. Idempotency

Every durable asynchronous operation should have an operation ID where duplicate execution is possible.

Example:

```text
operation_id = embed(memory_123, version_8)
```

If the worker crashes after completing the operation but before acknowledging it, retrying must not corrupt state.

---

## 47. Retry Policy

Retries should be classified.

### Transient

Retry with bounded backoff.

### Permanent

Reject and record.

### Unknown

Retry a limited number of times, then quarantine.

Never retry indefinitely.

---

## 48. Quarantine

Repeatedly failing jobs should enter quarantine.

```text
job
 ↓
retry
 ↓
retry
 ↓
failure
 ↓
quarantine
```

This prevents one corrupt memory or malformed artifact from blocking an entire queue.

---

## 49. Runtime Configuration

Runtime configuration should be separated into:

```text
protected policy
operational configuration
experimental configuration
learned state
```

Only authorized configuration classes may be changed at runtime.

A learned model must not silently overwrite protected runtime limits.

---

## 50. Observability Contract

Every worker should expose at least:

- state;
- health;
- queue depth;
- throughput;
- latency;
- failures;
- retries;
- resource usage;
- last successful operation;
- current version/configuration.

This feeds document 24's observability architecture.

---

## 51. Tracing

A request should carry a correlation identity through the runtime.

```text
request_id
   ↓
memory API
   ↓
retrieval
   ↓
ranking
   ↓
context assembly
   ↓
cognition
```

Similarly:

```text
sensor event ID
   ↓
observation
   ↓
memory candidate
   ↓
knowledge
   ↓
decision
```

This allows end-to-end diagnosis without requiring every component to duplicate the complete data payload.

---

## 52. Runtime Security

The runtime must enforce the security architecture from document 25.

Workers should not be able to:

- bypass authorization;
- directly rewrite provenance;
- disable audit logging;
- alter protected policies;
- arbitrarily access encrypted memory;
- grant themselves capabilities.

Process isolation, OS permissions and application-level authorization should work together.

---

## 53. Failure Modes

The runtime must explicitly handle:

- database unavailable;
- database corruption;
- WAL growth;
- storage full;
- RAM exhaustion;
- GPU OOM;
- CPU saturation;
- thermal throttling;
- power reduction;
- worker crash;
- queue overflow;
- malformed event;
- model unavailable;
- embedding failure;
- synchronization failure;
- backup failure;
- clock problems;
- schema mismatch.

Each should map to a defined degraded mode.

---

## 54. Memory-Store Unavailable

If canonical storage is unavailable, the runtime must not pretend writes succeeded.

Possible response:

```text
storage unavailable
      ↓
protect critical state
      ↓
use bounded emergency buffer if supported
      ↓
read-only/degraded mode
      ↓
recover storage
      ↓
replay validated durable events
```

The emergency buffer must have explicit capacity and durability guarantees.

---

## 55. GPU Out-of-Memory

If a model exhausts GPU memory:

```text
GPU OOM
 ↓
terminate/cancel offending job
 ↓
protect critical inference
 ↓
free resources
 ↓
retry with smaller workload/model if policy permits
 ↓
otherwise degrade
```

A background model must never be allowed to destabilize the entire robot because of GPU memory pressure.

---

## 56. RAM Pressure

At high RAM pressure:

1. stop opportunistic work;
2. reduce concurrency;
3. release caches;
4. pause background model loading;
5. preserve canonical memory;
6. preserve safety-critical services;
7. escalate if pressure remains.

Novi should not rely on swap as a substitute for proper runtime budgeting.

---

## 57. Network Failure

Network failure must isolate only network-dependent functions.

```text
network unavailable
       │
       ├── local memory → RUNNING
       ├── local cognition → RUNNING
       ├── local autonomy → RUNNING
       ├── synchronization → PAUSED
       └── cloud backup → DEFERRED
```

This reinforces the formal offline-capability rule.

---

## 58. Thermal Emergency

If hardware enters a severe thermal condition, the runtime must reduce non-essential work immediately and defer to the hardware/safety thermal controller.

The memory runtime must never attempt to override hardware thermal protection.

NVIDIA documents thermal sensing, throttling and shutdown behavior on Jetson Orin, reinforcing the need for this separation. citeturn0search0

---

## 59. Runtime Testing

Testing must include:

- sustained high-rate ingestion;
- concurrent retrieval and writes;
- long-running embedding load;
- GPU contention;
- RAM pressure;
- storage pressure;
- thermal throttling;
- low battery/power modes;
- worker crashes;
- repeated retries;
- queue overflow;
- cancellation;
- restart during transactions;
- power loss;
- network loss;
- synchronization backlog;
- backup contention;
- stale derived state;
- malformed jobs;
- SQLite lock contention;
- WAL growth;
- checkpoint latency;
- recovery after corruption.

These tests must run on the target Jetson hardware before final budgets are accepted.

---

## 60. Performance Acceptance Metrics

The runtime should eventually measure:

- p50/p95/p99 memory API latency;
- write latency;
- retrieval latency;
- queue wait time;
- worker utilization;
- CPU utilization;
- GPU utilization;
- RAM usage;
- storage I/O;
- thermal state;
- power consumption;
- recovery time;
- synchronization backlog;
- dropped/coalesced work;
- failed jobs.

No fixed universal numbers are established here; target values belong in benchmark and deployment profiles after hardware testing.

---

## 61. Mac Development vs Jetson Runtime

The architecture must allow substantial development and functional testing on macOS/Linux workstations.

However, final validation of:

- GPU contention;
- Jetson thermal behavior;
- power-aware scheduling;
- Jetson-specific accelerators;
- memory bandwidth;
- hardware I/O;
- production sensor timing;

must occur on the target hardware.

The runtime should therefore have a hardware-abstraction boundary and a deterministic test mode.

---

## 62. Deterministic Test Mode

A test runtime should allow:

- simulated clock;
- deterministic queues;
- deterministic sensor events;
- controlled model outputs;
- reproducible failures;
- fake resource telemetry;
- simulated network loss;
- simulated power/thermal states.

This enables reliable CI tests without requiring a physical robot for every test.

---

## 63. Simulation and Replay

Historical events should be replayable into a test runtime where permitted.

```text
recorded events
      ↓
replay engine
      ↓
memory runtime
      ↓
observed state
      ↓
compare with expected result
```

Replay must preserve event ordering, timestamps and provenance semantics.

Sensitive data used for replay must follow privacy controls.

---

## 64. Runtime Evolution

The runtime itself must evolve cautiously.

Changes to:

- scheduler policy;
- queue semantics;
- storage transaction behavior;
- worker priority;
- resource budgets;
- failure handling;

must pass regression and benchmark gates.

Novi's learned state must not be allowed to modify runtime implementation code autonomously.

---

## 65. Relationship to Other Architecture Documents

```text
17 Event Ingestion
        ↓
18 Sensor Grounding
        ↓
19 Synchronization
        ↓
20 Conflict Resolution
        ↓
21 Backup / Recovery
        ↓
22 Evaluation
        ↓
23 Spatial Memory
        ↓
24 Observability
        ↓
25 Security / Integrity
        ↓
26 Memory APIs
        ↓
27 Runtime / Execution
```

Document 27 turns the preceding semantic contracts into a continuously executing subsystem.

---

## 66. Architectural Invariants

1. Canonical memory writes are short and transactional.
2. Long-running computation never holds canonical storage transactions open.
3. Background learning cannot starve critical workloads.
4. Queues are bounded.
5. Backpressure is explicit.
6. Derived-state failure must not normally destroy canonical memory.
7. Network failure cannot stop core local memory operation.
8. Thermal and power pressure reduce opportunistic work before critical operation is endangered.
9. Safety hardware remains authoritative over runtime scheduling.
10. Every durable asynchronous operation has an identity suitable for idempotency.
11. Retry loops are bounded.
12. Failed jobs can be quarantined.
13. Worker health is observable.
14. Runtime state is recoverable after restart.
15. The runtime does not treat exactly-once execution as an assumption.
16. GPU/CPU resource budgets are measured on target hardware.
17. Derived indexes and embeddings remain rebuildable.
18. Runtime configuration and learned state remain separate.
19. Self-learning cannot modify protected runtime/security boundaries.
20. The runtime must degrade gracefully instead of inventing successful results.

---

## 67. Final Principle

> **Novi's memory must behave like a continuously operating infrastructure system, not like a database that the robot occasionally queries.**

The runtime must keep the cognitive system responsive while sensors stream continuously, models consume heterogeneous compute, memories are admitted and consolidated, maps evolve, knowledge is learned, devices synchronize, backups run and the robot moves through the physical world.

The architecture therefore prioritizes **bounded execution, short transactions, explicit scheduling, graceful degradation, resource awareness, failure isolation and recoverability**.

The implementation should remain as simple as possible until measurements demonstrate that more complexity is necessary.
