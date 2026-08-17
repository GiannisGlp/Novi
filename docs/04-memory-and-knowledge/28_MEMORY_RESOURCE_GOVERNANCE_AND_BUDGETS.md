# 28 — Memory Resource Governance and Budgets

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi allocates, protects, monitors and dynamically governs CPU, GPU, RAM, storage, I/O, power, thermal headroom, queues, model memory and memory-service capacity.

This document turns the runtime architecture in `27_MEMORY_RUNTIME_AND_EXECUTION_MODEL.md` into explicit resource-governance rules.

The objective is not to maximize utilization.

> **The objective is to maximize useful autonomous capability while preserving safety, responsiveness, memory integrity, thermal stability, battery life and recovery capacity.**

Exact numeric budgets remain prototype-validation parameters. They must be measured on the final Jetson AGX Orin 64GB configuration rather than guessed from nominal hardware specifications.

---

## 1. Governing Principles

1. Safety has the highest resource priority.
2. Core perception, state estimation, control and memory durability must retain protected capacity.
3. Interactive cognition must remain responsive under normal load.
4. Background learning is opportunistic and preemptible.
5. No single workload may consume all shared resources.
6. Memory admission must consider storage and compute cost, not only semantic value.
7. Thermal and power state can reduce non-critical workloads.
8. Resource exhaustion must degrade gracefully rather than crash the entire robot.
9. Network availability must not determine whether core resource governance works.
10. Budgets are policies, not assumptions about hardware capability.

---

## 2. Resource Domains

Novi governs at least:

```text
CPU
GPU
RAM
GPU memory / unified device memory pressure
Storage capacity
Storage I/O
Network bandwidth
IPC / message queues
Inference concurrency
Embedding concurrency
Database concurrency
Power
Temperature / thermal headroom
Battery state
```

Because Jetson Orin uses shared system resources and hardware-managed frequency/power controls, CPU, GPU, memory bandwidth, thermal and power behavior must be evaluated together rather than as independent counters. NVIDIA documents dynamic memory-controller frequency scaling and thermal effects on available performance. citeturn0search0turn0search4

---

## 3. Resource Classes

Every workload belongs to a resource class.

### Class A — Safety / Critical

Examples:

- emergency handling;
- safety controller interfaces;
- actuator safety monitoring;
- critical thermal protection;
- battery protection;
- essential localization/state estimation;
- durable memory commit required to preserve safety state.

These workloads receive protected capacity and must not be starved by AI workloads.

### Class B — Core Autonomy

Examples:

- obstacle perception;
- navigation;
- sensor fusion;
- world-state updates;
- critical speech interaction;
- core memory retrieval.

### Class C — Interactive Cognition

Examples:

- conversational reasoning;
- planning;
- user-facing responses;
- contextual retrieval;
- short-term inference.

### Class D — Background Intelligence

Examples:

- embedding generation;
- memory consolidation;
- knowledge promotion analysis;
- graph maintenance;
- retrospective learning;
- map optimization;
- analytics.

### Class E — Opportunistic

Examples:

- bulk indexing;
- nonessential model optimization;
- deep historical replay;
- synchronization when no urgency exists;
- housekeeping.

---

## 4. Protected Capacity

Novi must maintain a protected reserve for critical workloads.

Conceptually:

```text
Total resources
├── Critical reserve
├── Core autonomy reserve
├── Interactive budget
├── Background budget
└── Opportunistic capacity
```

The percentages are intentionally not fixed here.

They must be established through profiling and worst-case testing.

A background workload must never be allowed to consume the reserve required for critical operation.

---

## 5. CPU Governance

CPU budgets should control:

- worker concurrency;
- process priority;
- CPU affinity where justified;
- queue workers;
- background task frequency;
- burst limits.

Linux cgroup v2 provides CPU resource distribution and absolute limits, making it a candidate mechanism for process-level isolation where supported by the final Jetson software stack. citeturn1search7turn1search16

However, cgroups are an implementation mechanism, not the architectural policy. Novi's scheduler remains responsible for semantic priority.

---

## 6. GPU Governance

GPU resources must be budgeted by:

- concurrent inference count;
- model size;
- activation memory;
- execution context count;
- CUDA stream count;
- expected latency;
- background GPU jobs.

TensorRT documentation notes that multiple streams can improve throughput but create contention for compute, registers, cache and DRAM bandwidth, and can increase memory use. Therefore unlimited concurrency is explicitly prohibited. citeturn0search1

---

## 7. GPU Memory Governance

GPU/device memory allocation must be bounded.

Every model service should declare approximately:

```text
weights
activation peak
workspace
context memory
stream overhead
expected transient allocation
```

Before admitting a new concurrent inference, the runtime should determine whether sufficient memory headroom remains.

An out-of-memory event must not be allowed to terminate unrelated critical services.

---

## 8. TensorRT Memory Strategy

Where TensorRT is used, Novi should evaluate:

- engine memory requirements;
- execution-context count;
- CUDA stream count;
- workspace requirements;
- batching;
- CUDA graphs;
- weight streaming where appropriate.

NVIDIA documents TensorRT weight streaming as a way to trade device memory for execution performance, and explicitly notes that the budget must be tuned because insufficient or excessive streaming can affect performance and memory use. citeturn0search2turn0search5

The architecture therefore treats model memory as a governed budget rather than an unlimited pool.

---

## 9. RAM Governance

RAM is shared by:

- operating system;
- ROS/IPC infrastructure;
- perception;
- models;
- database/page cache;
- embeddings;
- maps;
- applications;
- logs;
- temporary buffers.

Novi must maintain a safety margin rather than targeting near-total RAM utilization.

Linux cgroup v2 provides memory limits and protections that can be used for process groups where appropriate. citeturn1search7turn1search14

Critical services must receive stronger protection than background workers.

---

## 10. Storage Capacity Budget

Storage must be divided conceptually into:

```text
OS / runtime
Models
Canonical memory
Event history
Spatial maps
Indexes
Embeddings
Logs / telemetry
Backups
Recovery reserve
Temporary space
```

A minimum recovery reserve must always remain available.

If storage approaches critical thresholds, Novi must proactively reduce:

- raw media retention;
- temporary artifacts;
- nonessential logs;
- redundant derived indexes;
- background indexing.

It must not wait until the filesystem is completely full.

---

## 11. Storage I/O Governance

SQLite, sensor logging, map updates, embeddings and backups can compete for storage I/O.

Background jobs must therefore be throttled when interactive or durable workloads need the device.

Linux cgroup v2 supports I/O limits such as maximum BPS/IOPS, making it a candidate implementation mechanism for isolating heavy background workloads. citeturn1search7

---

## 12. Database Budget

The memory database requires protected capacity for:

- short durable writes;
- reads required by cognition;
- checkpointing;
- recovery;
- schema maintenance.

Large analytical queries must not monopolize the database.

Memory compaction and maintenance should run under controlled scheduling.

---

## 13. Queue Budgets

Every asynchronous queue must have:

- maximum depth;
- item-size limit;
- memory limit;
- priority;
- timeout/lifespan where appropriate;
- overflow policy;
- observability.

An unbounded queue is prohibited for production-critical services.

Overflow policies may include:

```text
block
coalesce
sample
expire
spill to durable queue
reject
escalate
```

The policy must be domain-specific.

---

## 14. Sensor Data Budget

High-rate sensors can generate enormous data volumes.

Novi must distinguish:

```text
raw stream
↓
measurement
↓
observation
↓
memory candidate
```

Not every raw sample should be persisted indefinitely.

Retention should depend on:

- sensor type;
- safety relevance;
- diagnostic value;
- privacy;
- learning value;
- storage budget.

---

## 15. ROS 2 Communication Budgets

If ROS 2 is used, communication must use appropriate QoS rather than assuming one profile fits every topic.

ROS 2 QoS supports history/depth, reliability, durability, deadline, lifespan and liveliness, allowing sensor streams and critical state channels to be governed differently. citeturn1search1

Example conceptual policy:

```text
high-rate camera:
  bounded history
  best effort may be appropriate

critical state:
  reliable
  bounded queue
  explicit deadline

transient state:
  short lifespan
```

Exact QoS must be validated per sensor and workload.

---

## 16. Deadline Governance

Important workloads should declare expected execution or publication deadlines where meaningful.

Missed deadlines become observable events rather than silent degradation.

ROS 2 exposes deadline-missed events for publishers/subscriptions, which provides a useful foundation for runtime monitoring. citeturn1search1turn1search10

A deadline miss does not automatically mean system failure; repeated or safety-relevant misses can trigger escalation.

---

## 17. Power Budget

Power is a first-class runtime resource because Novi is mobile.

The runtime must consider:

- battery state of charge;
- battery temperature;
- estimated remaining energy;
- current draw;
- charging state;
- power mode;
- expected workload cost.

NVIDIA's Jetson documentation provides `nvpmodel` for power-mode selection and documents Orin AGX 64GB reference profiles including 15W, 30W and 50W modes. Actual Novi profiles must be validated on the final carrier board, cooling solution and battery system. citeturn0search0

---

## 18. Thermal Budget

Thermal headroom must be treated as a dynamic resource.

Conceptually:

```text
thermal headroom high
    ↓
normal workload

thermal headroom declining
    ↓
reduce background workload

thermal warning
    ↓
reduce interactive/background concurrency

critical thermal state
    ↓
protect hardware
    ↓
safe/degraded operation
```

NVIDIA documents that thermal throttling can dynamically reduce system performance to control temperature. Novi should therefore detect and respond to thermal pressure rather than assuming fixed performance. citeturn0search0

---

## 19. Battery-Aware Scheduling

Suggested conceptual modes:

```text
BATTERY_HIGH
  normal

BATTERY_MEDIUM
  reduce opportunistic work

BATTERY_LOW
  pause expensive background learning

BATTERY_CRITICAL
  preserve navigation, safety, memory durability
  reduce nonessential cognition

CHARGING
  allow deferred maintenance according to thermal limits
```

Thresholds must be experimentally determined from the actual battery/BMS system.

---

## 20. Thermal-Aware Scheduling

Thermal control must be predictive where possible.

The scheduler should consider:

- current temperature;
- temperature trend;
- workload intensity;
- cooling capacity;
- ambient temperature;
- fan state;
- battery temperature;
- expected workload duration.

A rapidly increasing temperature can justify throttling before reaching a hard thermal limit.

---

## 21. Resource Pressure States

Novi should maintain a unified resource-pressure state:

```text
NORMAL
ELEVATED
CONSTRAINED
CRITICAL
EMERGENCY
```

The state can be derived from multiple domains.

Example:

```text
RAM = normal
GPU = normal
storage = normal
thermal = constrained
battery = low
       ↓
SYSTEM PRESSURE = CONSTRAINED
```

---

## 22. Workload Admission

Before starting expensive work, the runtime should ask:

```text
Is this work necessary?
Is it urgent?
What resources will it consume?
What protected resources remain?
Could it be deferred?
What happens if it fails?
```

Background work should be admitted only when sufficient budget exists.

---

## 23. Workload Cost Declarations

Workers should expose resource estimates such as:

```text
cpu_class
estimated_cpu_time
gpu_required
gpu_memory_peak
ram_peak
io_estimate
storage_growth
network_required
power_class
thermal_class
latency_class
```

These estimates can initially be conservative and later be refined using telemetry.

---

## 24. Adaptive Budgets

Budgets should adapt within protected policy limits.

Example:

```text
quiet robot
   ↓
background learning budget increases

navigation active
   ↓
background budget decreases

thermal pressure
   ↓
background budget decreases sharply
```

The scheduler may optimize inside the policy envelope but cannot remove protected reserves.

---

## 25. Priority Inversion Protection

A low-priority workload must not indefinitely block a high-priority workload.

Potential mechanisms:

- priority-aware queues;
- short transactions;
- lock discipline;
- bounded resource ownership;
- priority inheritance where applicable;
- separate worker pools.

This is particularly important for database and IPC resources shared by critical and background workloads.

---

## 26. Memory Learning Budget

Continuous learning must be resource-bounded.

Learning workloads include:

- embedding generation;
- clustering;
- consolidation;
- replay;
- graph maintenance;
- knowledge promotion;
- model adaptation.

Learning must yield to real-time physical-world demands.

```text
world interaction
       >
learning
```

unless a safety or explicit policy requires otherwise.

---

## 27. Spatial-Memory Budget

Maps can become large over long-term outdoor use.

The spatial subsystem should manage:

- active local map;
- recent maps;
- persistent place summaries;
- compressed historical maps;
- semantic landmarks;
- map indexes.

Novi should not retain maximum-resolution representations of every location forever by default.

---

## 28. Media Budget

Camera and audio data can dominate storage.

The system should prefer event-driven retention:

```text
ordinary stream
    ↓
short-lived buffer

important event
    ↓
retain selected segment

important long-term memory
    ↓
retain derived evidence + approved media reference
```

Privacy policies remain authoritative.

---

## 29. Network Budget

Network bandwidth is optional and must not be required for core operation.

When Wi-Fi/Bluetooth is available, bandwidth should be prioritized approximately as:

```text
control / safety-related communication
        ↓
synchronization
        ↓
user interaction
        ↓
maintenance
        ↓
bulk transfer
```

If connectivity disappears, queues should persist only within bounded storage budgets.

---

## 30. Model Concurrency Budget

Novi must not run every available model simultaneously simply because memory permits it.

Concurrency should account for:

- GPU contention;
- RAM;
- thermal load;
- latency;
- power;
- sensor deadlines.

For example:

```text
vision inference
+ speech recognition
+ LLM
+ embedding generation
```

may be individually feasible but collectively unsafe for the desired latency/thermal envelope.

---

## 31. Large-Model Governance

Large models must declare resource requirements before activation.

The runtime should support:

- preflight memory checks;
- controlled loading;
- unloading when idle;
- quantized variants;
- weight streaming where beneficial;
- bounded context sizes;
- concurrency limits;
- fallback models.

A large model is not allowed to consume resources required by safety or core autonomy.

---

## 32. Graceful Degradation

When resources become constrained, Novi should degrade in stages.

```text
FULL
 ↓
REDUCED_BACKGROUND
 ↓
REDUCED_INFERENCE
 ↓
LIMITED_COGNITION
 ↓
CORE_AUTONOMY
 ↓
SAFE_MODE
```

The system should preserve the most important capabilities first.

---

## 33. Capability Shedding

When necessary, Novi may temporarily disable:

- bulk synchronization;
- deep retrospective learning;
- high-resolution media retention;
- nonessential map optimization;
- low-priority indexing;
- optional visual effects;
- secondary model inference.

It must not silently disable:

- safety;
- required actuator protection;
- critical state estimation;
- durable memory guarantees required by policy;
- required user privacy controls.

---

## 34. Resource Reservation

Critical services should have reserved capacity where practical.

Examples:

```text
memory commit reserve
sensor ingestion reserve
navigation reserve
safety telemetry reserve
storage recovery reserve
```

Reservation must be tested under simultaneous worst-case workloads.

---

## 35. Resource Accounting

Every major worker should report:

- CPU time;
- RAM high-water mark;
- GPU time where available;
- GPU memory peak;
- queue latency;
- I/O volume;
- storage growth;
- power impact where measurable;
- thermal impact where attributable.

Resource telemetry feeds the evaluation system and future budget tuning.

---

## 36. Budget Violations

A budget violation should generate an explicit event.

Example:

```text
embedding_worker
GPU memory budget exceeded
       ↓
worker suspended
       ↓
incident recorded
       ↓
core workloads unaffected
```

Repeated violations should trigger configuration review rather than endless retries.

---

## 37. Runaway Workloads

The runtime must detect workloads that:

- exceed deadlines repeatedly;
- grow memory indefinitely;
- generate unbounded output;
- consume excessive GPU;
- create queue explosions;
- repeatedly crash.

Possible responses:

```text
throttle
cancel
restart
quarantine
fallback
escalate
```

---

## 38. Crash Isolation

A failed background worker must not bring down canonical memory or safety services.

Processes should be separated where the failure impact justifies it.

Recovery should preserve:

- committed state;
- pending durable events;
- audit information;
- resource state.

---

## 39. Startup Budgeting

Startup can create a resource spike because several services may initialize simultaneously.

Novi should stage startup:

```text
hardware safety
 ↓
core OS/runtime
 ↓
sensor ingestion
 ↓
memory database
 ↓
localization
 ↓
core perception
 ↓
interactive cognition
 ↓
background services
```

Large background models and indexes should not all load before core operation becomes available.

---

## 40. Shutdown Budgeting

Shutdown should prioritize durable state.

```text
stop new background work
 ↓
finish/abort safe operations
 ↓
flush critical events
 ↓
commit required memory state
 ↓
checkpoint as policy permits
 ↓
close services
 ↓
power down
```

Emergency shutdown may skip noncritical work but must preserve the strongest available durability guarantees.

---

## 41. Resource Governance Without Network

All budgets, limits and fallback rules must be locally available.

Novi must not require a remote service to decide:

> "My GPU is overloaded."

or:

> "I need to stop background learning because the battery is critical."

---

## 42. Configuration Governance

Resource budgets are protected configuration.

Ordinary learning must not rewrite them arbitrarily.

Adaptive tuning may operate inside approved bounds:

```text
minimum reserve
        │
        ├── adaptive operating range
        │
maximum safe allocation
```

Changing the safety envelope requires an administrative/engineering process and validation.

---

## 43. Benchmarking Requirements

Resource budgets must be established from measurements on the target robot.

Test dimensions should include:

- idle;
- conversation;
- navigation;
- obstacle avoidance;
- simultaneous camera streams;
- LiDAR;
- thermal camera;
- audio interaction;
- mapping;
- memory retrieval;
- learning;
- synchronization;
- backup;
- low battery;
- high ambient temperature;
- charging;
- storage pressure;
- worst-case concurrent inference.

The benchmark must measure both average and tail behavior.

---

## 44. Worst-Case Capacity

A budget is not validated merely because average utilization is low.

Novi must determine whether simultaneous expected workloads fit within safe limits.

Example workload:

```text
navigation
+ 4 cameras
+ LiDAR
+ thermal camera
+ microphone array
+ speech recognition
+ conversational model
+ memory retrieval
+ logging
```

This combined scenario is more important than isolated model benchmarks.

---

## 45. Tail Latency

Resource governance must track p95/p99 or other appropriate tail metrics for latency-sensitive operations.

A system that is fast 99% of the time but misses safety-relevant deadlines during overload is not acceptable.

---

## 46. Resource Governance and Evaluation

Resource changes must be evaluated alongside cognition quality.

Example:

```text
new model
 ↓
better answers
but
 ↓
thermal +15%
GPU contention +25%
navigation latency +40%
```

This is not automatically an improvement.

The evaluation system must consider the complete robot.

---

## 47. Resource Governance and Memory Quality

Resource pressure may cause:

- skipped observations;
- delayed consolidation;
- reduced retrieval depth;
- lower-resolution maps;
- deferred embeddings.

These effects must be observable so Novi does not mistake resource-driven missing evidence for absence of evidence.

---

## 48. Resource Governance and Uncertainty

If resource constraints force reduced sensing or inference, the resulting confidence should be adjusted where appropriate.

Example:

```text
camera temporarily unavailable
        ↓
less visual evidence
        ↓
spatial confidence may decrease
```

The memory architecture must preserve this relationship.

---

## 49. Hardware Telemetry

On Jetson, resource governance should integrate available system telemetry such as CPU/GPU activity, memory, power and thermal measurements. NVIDIA documents `tegrastats` for this purpose and `nvpmodel` for power-mode control. citeturn0search0turn0search6

Exact telemetry collectors and sampling intervals belong in implementation documents.

---

## 50. Initial Budget Categories

Before numeric values are known, the configuration should define categories such as:

```yaml
critical:
  cpu: protected
  ram: protected
  gpu: protected
  storage: protected

core_autonomy:
  cpu: reserved
  gpu: reserved
  ram: reserved

interactive:
  cpu: bounded
  gpu: bounded
  ram: bounded

background:
  cpu: opportunistic
  gpu: opportunistic
  ram: bounded

opportunistic:
  cpu: best_effort
  gpu: best_effort
  ram: bounded
```

This is conceptual only. Production configuration must be derived from benchmark data.

---

## 51. Recommended Initial Scheduling Policy

Until measurements justify more sophisticated behavior:

```text
Safety                  → protected
Core autonomy           → high priority
Interactive cognition   → high but preemptible
Memory durability       → protected latency
Perception              → deadline-aware
Synchronization         → background
Backup                  → background
Embedding               → background
Consolidation           → background
Deep learning           → opportunistic
Bulk indexing           → opportunistic
```

This should be validated against actual behavior rather than assumed permanently.

---

## 52. Architectural Invariants

1. No workload may consume the entire shared resource pool.
2. Critical resources have protected capacity.
3. Background learning is preemptible.
4. Resource pressure can reduce noncritical capabilities.
5. Safety does not depend on the scheduler behaving perfectly.
6. Resource budgets are locally enforced.
7. Network loss cannot disable resource governance.
8. Queue limits are finite.
9. Database transactions remain short.
10. GPU concurrency is bounded.
11. Storage recovery reserve is protected.
12. Thermal and battery state can reduce workload budgets.
13. Derived workloads cannot starve canonical memory durability.
14. Resource failures must be observable.
15. Self-learning cannot arbitrarily rewrite resource safety envelopes.
16. Numeric budgets require target-hardware validation.
17. Worst-case concurrent workloads must be tested.
18. Tail latency matters for safety and autonomy.
19. Resource-driven degradation must remain visible to cognition and evaluation.
20. No optimization is accepted solely because it increases utilization.

---

## 53. Cross-Validation Sources

The architecture is informed by multiple independent technical sources:

- NVIDIA Jetson Linux documentation for Orin power modes, DVFS, memory/power behavior, thermal management and `tegrastats`/`nvpmodel`. citeturn0search0turn0search4turn0search6
- NVIDIA TensorRT documentation for batching, CUDA graphs, multi-stream contention and model-memory/weight-streaming tradeoffs. citeturn0search1turn0search2turn0search5
- Linux kernel cgroup v2 documentation for CPU, memory and I/O resource controls and protection mechanisms. citeturn1search7turn1search14turn1search16
- ROS 2 documentation for QoS history, depth, reliability, durability, deadline, lifespan and liveliness semantics. citeturn1search1turn1search2

These sources inform the architecture but do not replace measurements on the final Novi hardware.

---

## 54. Final Principle

> **Novi must spend computation like a robot, not like an unlimited server.**

Every resource decision should answer one question:

> **Does this work improve Novi's ability to safely perceive, remember, reason, act or learn without consuming resources required for more important capabilities?**

If the answer is no, the work should be deferred, reduced, degraded or rejected.

Resource governance is therefore not merely performance engineering. It is part of Novi's autonomy, reliability, safety and ability to continuously evolve on a finite physical machine.
