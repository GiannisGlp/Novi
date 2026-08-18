# 21 — Runtime Resource Budgets & Deterministic Execution

**Status:** P0 normative architecture standard  
**Owner:** System Architecture  
**Scope:** Brain runtime, Cognition, Autonomy, Perception, Memory, Safety, Hardware and NVIDIA/ROS 2 execution  
**Purpose:** define how Novi remains responsive, safe and predictable when compute, memory, GPU, thermal, power, I/O or scheduling resources are constrained.

---

## 1. Executive decision

Novi MUST be designed around **bounded latency, explicit resource budgets, graceful degradation and measured end-to-end performance**.

No subsystem may assume that compute is infinite or that an inference request will complete on time merely because the model normally does so.

The central invariant is:

> **A slow component must not silently consume the time, memory, GPU or execution capacity required by safety-critical behavior.**

Real-time requirements are assigned by function. Novi is not declared globally hard-real-time simply because some loops have deadlines.

---

## 2. Execution classes

Every recurring or event-driven workload MUST declare one execution class.

| Class | Meaning | Examples | Failure policy |
|---|---|---|---|
| S0 Safety-critical | Must remain available within a bounded deadline | emergency stop, safety watchdog | independent fallback / safe state |
| S1 Control-critical | Tight bounded latency required | motor command/control interface | hold/stop/degrade |
| S2 Reactive | Fast response required but not necessarily hard real-time | obstacle reaction, person proximity | fallback behavior |
| S3 Perception | periodic sensing/inference | camera, depth, detection | drop/degrade stale work |
| S4 Cognitive | reasoning and interpretation | multimodal reasoning, planning proposal | timeout / use simpler path |
| S5 Background | opportunistic | consolidation, indexing, diagnostics | pause/throttle |

Execution class is a **system property**, not a property inferred from whether a neural network is used.

---

## 3. Budget dimensions

Every production component MUST define applicable budgets for:

```text
CPU
GPU
RAM
GPU memory
storage I/O
network/DDS traffic
power
thermal headroom
latency
jitter
throughput
queue depth
concurrency
startup time
shutdown/recovery time
```

A component without a declared budget is not production-ready.

---

## 4. Deadline model

For each deadline-sensitive workload:

```text
release time
      ↓
execution
      ↓
completion deadline
      ↓
result validity window
```

A result arriving after its validity window is **late**, not successful.

Novi MUST measure at least:

- execution time;
- queue wait time;
- transport time;
- end-to-end latency;
- deadline misses;
- jitter;
- dropped/stale work.

Average latency alone is insufficient.

---

## 5. End-to-end latency is the primary robotics metric

For perception-to-action paths, measure the entire path:

```text
sensor capture
 → transport
 → preprocessing
 → inference
 → postprocessing
 → cognition/autonomy
 → safety authorization
 → controller
 → actuator
```

Optimizing one node while increasing transport or queue latency is not considered an improvement.

NVIDIA explicitly recommends realistic whole-graph benchmarking for ROS workloads because node-only measurements omit ROS transport costs and do not represent real deployment performance. citeturn0search9

---

## 6. Frequency targets are requirements, not guarantees

A requested rate such as `30 Hz` means:

```text
TARGET = 30 Hz
```

It does not mean Novi has achieved 30 Hz.

The runtime MUST expose:

```text
requested_rate
achieved_rate
deadline
miss_count
jitter
queue_depth
stale_count
```

NVIDIA's Isaac Sim documentation notes that actual ROS publish rates can fall below target rates under CPU/GPU load and that heavy camera data can create transport or DDS bottlenecks. citeturn0search0turn0search5

---

## 7. Queue policy

Every asynchronous queue MUST declare:

- maximum depth;
- overflow policy;
- ordering policy;
- stale-data policy;
- priority policy;
- cancellation policy.

Allowed overflow strategies include:

```text
DROP_OLDEST
DROP_NEWEST
COALESCE
BLOCK_WITH_DEADLINE
REJECT
DEGRADE
```

An unbounded queue is prohibited for production runtime paths.

---

## 8. Stale work policy

For continuously refreshed data, old work MUST NOT accumulate indefinitely.

Examples:

```text
camera frame N
camera frame N+1
camera frame N+2
```

If frame N is still waiting after N+2 has arrived and its result is no longer useful, Novi should normally discard or cancel N rather than process obsolete work merely to clear a queue.

This is especially important for perception and reactive behavior.

---

## 9. Backpressure

Backpressure MUST be explicit.

A high-rate producer must not force an unbounded consumer backlog.

The preferred pattern for disposable sensor data is:

```text
producer
   ↓
bounded buffer
   ↓
latest-valid sample
   ↓
consumer
```

For durable events, use durable queues/persistence according to the canonical event and memory architecture instead of pretending a sensor queue is durable storage.

---

## 10. Priority model

Resource contention MUST resolve according to safety and execution priority.

Default ordering:

```text
S0 Safety
 ↓
S1 Control
 ↓
S2 Reactive
 ↓
S3 Perception
 ↓
S4 Cognition
 ↓
S5 Background
```

A lower-priority workload MUST NOT starve a higher-priority workload.

Priority inversion MUST be detectable and mitigated where applicable.

---

## 11. Neural-network workloads

Neural inference is treated as a bounded resource consumer, not as a privileged workload.

Every deployed model MUST declare:

```text
model_id
version
precision
expected input rate
expected latency
worst observed latency
CPU usage
GPU usage
GPU memory
RAM usage
startup cost
power impact
thermal impact
fallback model/path
```

A model that misses its deadline MUST have an explicit response:

```text
SKIP
USE_LAST_VALID
USE_LIGHTWEIGHT_MODEL
USE_CLASSICAL_FALLBACK
DEGRADE_CAPABILITY
STOP/SAFE_STATE
```

The choice depends on execution class and safety requirements.

---

## 12. GPU resource governance

GPU workloads MUST be measurable as shared resources.

The system MUST avoid allowing one large inference, mapping workload or planning workload to silently starve critical perception/control functions.

Where supported, separate workloads through:

- process isolation;
- scheduling priorities;
- dedicated execution contexts/streams;
- bounded batch sizes;
- memory limits;
- workload admission control;
- reduced-resolution/degraded modes.

NVIDIA Isaac ROS uses GPU-accelerated processing and NITROS to reduce unnecessary CPU/GPU copies and improve throughput; this should be considered during pipeline design, but it does not remove the need for end-to-end measurement. citeturn0search8turn0search10

---

## 13. CPU resource governance

CPU-heavy work MUST be prevented from starving control, transport or safety infrastructure.

Long-running background work should use isolated worker pools where practical.

Examples:

```text
S0/S1
reserved execution capacity

S2/S3
bounded worker pools

S4
elastic but deadline-aware

S5
opportunistic
```

Exact CPU reservation values are hardware-specific and MUST be established through benchmarks rather than guessed here.

---

## 14. Memory budgets

Every long-lived process MUST define:

```text
baseline RAM
working-set budget
peak RAM
GPU memory budget
cache budget
queue budget
recovery margin
```

Memory exhaustion MUST trigger controlled degradation rather than uncontrolled allocation growth.

Examples:

```text
reduce perception resolution
pause background processing
limit memory retrieval size
stop optional model
flush/reclaim caches
enter degraded mode
```

---

## 15. Thermal and power budgets

Thermal and power state are runtime constraints.

The runtime MUST expose sufficient telemetry to determine whether performance degradation is caused by:

- thermal throttling;
- power limits;
- GPU saturation;
- CPU saturation;
- memory pressure;
- I/O pressure.

Performance benchmarks MUST record relevant power mode and clock configuration because performance comparisons without controlled hardware state can be misleading. NVIDIA guidance in current Isaac ROS performance discussions similarly recommends fixed Jetson power modes/clocks when benchmarking. citeturn0search7

---

## 16. Graceful degradation

Novi MUST have an explicit degradation ladder.

Example:

```text
FULL
  ↓
REDUCED_PERCEPTION
  ↓
LIGHTWEIGHT_MODELS
  ↓
REDUCED_COGNITION
  ↓
LIMITED_AUTONOMY
  ↓
SAFE_STOP / SAFE_STATE
```

The exact transitions are capability-specific and MUST be documented in the corresponding subsystem.

Safety-critical functions must remain available even when optional intelligence is disabled.

---

## 17. Brain runtime responsibility

Brain owns execution orchestration, not semantic policy.

Brain MUST:

- schedule workloads;
- enforce runtime deadlines;
- expose resource telemetry;
- cancel obsolete work;
- enforce queue limits;
- coordinate model execution;
- detect runtime degradation;
- preserve safety-critical execution capacity;
- report execution failures to canonical contracts.

Brain MUST NOT silently change Cognition's semantic interpretation merely because resources are constrained.

Instead it reports:

```text
capability_available = false
reason = RESOURCE_CONSTRAINT
```

and Cognition/Autonomy respond according to their contracts.

---

## 18. Cognition responsibility

Cognition MUST distinguish:

```text
no evidence
wrong/ambiguous evidence
late evidence
missing computation
resource-degraded computation
```

A model timeout MUST NOT be interpreted as evidence that an object/person/event does not exist.

Cognition may select a simpler reasoning path when notified of degraded capability, but it must preserve uncertainty.

---

## 19. Autonomy responsibility

Autonomy MUST account for computational feasibility when selecting behavior.

Examples:

```text
Plan A requires unavailable capability
        ↓
reject/defer/replan
```

Autonomy MUST NOT create a plan whose required runtime capability is known to be unavailable without an explicit degraded strategy.

---

## 20. Memory responsibility

Memory operations MUST have bounded retrieval and write behavior for runtime-critical paths.

Large historical retrieval, indexing, consolidation and maintenance belong to background execution unless explicitly required by a bounded cognitive request.

Memory MUST NOT block safety/control execution.

---

## 21. Safety interaction

Safety remains authoritative.

Resource exhaustion MUST be treated as a potential safety condition when it affects the ability to verify or execute an action safely.

Example:

```text
required obstacle perception unavailable
        ↓
action safety cannot be established
        ↓
authorization denied/deferred
```

The robot must not infer that absence of a perception result means absence of an obstacle.

---

## 22. Real-time classification

Each subsystem MUST declare whether its timing requirement is:

```text
HARD_REAL_TIME
SOFT_REAL_TIME
BEST_EFFORT
ASYNC_BACKGROUND
```

The classification must be justified by the safety/functional requirement.

Novi's high-level LLM reasoning is expected to be soft-real-time or asynchronous, not hard-real-time.

Low-level safety/control paths may require substantially stronger timing guarantees and should remain independent from large-model inference.

---

## 23. Model admission control

A model/workload MUST NOT be deployed merely because it fits in memory.

Admission requires:

```text
functional correctness
+ latency budget
+ resource budget
+ thermal/power budget
+ safety impact
+ fallback behavior
+ concurrency behavior
```

A workload that is acceptable in isolation may be unacceptable when combined with the complete Novi graph.

---

## 24. Benchmark methodology

Benchmarking MUST be representative of the deployed workload.

Minimum benchmark modes:

### B1 — Unit
Single component.

### B2 — Pipeline
Relevant perception/inference chain.

### B3 — End-to-end
Sensor-to-action path.

### B4 — Full-load
All expected concurrent workloads.

### B5 — Degraded-load
Thermal/resource pressure and intentionally constrained resources.

### B6 — Fault injection
Dropped messages, delayed inference, process restart, sensor loss, GPU failure, memory pressure.

### B7 — Soak
Long-duration operation to expose leaks, queue growth and thermal behavior.

---

## 25. Required performance metrics

Every benchmark MUST report where applicable:

- p50 latency;
- p95 latency;
- p99 latency;
- maximum observed latency;
- jitter;
- throughput;
- deadline miss percentage;
- dropped work;
- stale work;
- CPU utilization;
- GPU utilization;
- RAM usage;
- GPU memory usage;
- power;
- thermal state;
- queue depth;
- recovery time.

Averages alone are insufficient for safety-sensitive paths.

---

## 26. Simulation and hardware parity

Simulation performance MUST NOT be treated as proof of physical performance.

Isaac Sim can execute simulation time independently of wall time, and actual ROS publication performance depends on available CPU/GPU resources. citeturn0search5

Therefore every important performance claim progresses through:

```text
simulation
  ↓
software-in-the-loop
  ↓
hardware-in-the-loop
  ↓
physical robot
```

with the same measurement definitions where practical.

---

## 27. ROS 2 / Isaac ROS considerations

ROS 2 execution configuration MUST explicitly consider:

- callback groups;
- executor behavior;
- QoS;
- queue depth;
- message serialization/copy costs;
- intra-process communication;
- DDS transport;
- NITROS/type adaptation where applicable;
- sensor publication rates;
- executor starvation.

NVIDIA documents that NITROS can reduce unnecessary CPU/GPU memory copies and that Isaac ROS provides accelerated low-latency packages for autonomous robotics. citeturn0search8turn0search10

Isaac Sim documentation also notes that large image messages can become network/DDS bottlenecks and that execution triggers can affect publish-rate alignment with physics. citeturn0search0turn0search5

---

## 28. Queue and deadline observability

Runtime telemetry MUST make the following queryable:

```text
What is slow?
What is waiting?
What missed its deadline?
What became stale?
What consumed the GPU?
What consumed memory?
What was degraded?
Why was it degraded?
When did recovery occur?
```

A single generic CPU/GPU utilization number is insufficient.

---

## 29. Failure scenarios

At minimum test:

1. perception model exceeds deadline;
2. GPU memory exhausted;
3. CPU saturation;
4. RAM pressure;
5. DDS queue overflow;
6. sensor publishes faster than consumer;
7. consumer becomes unavailable;
8. inference process crashes;
9. model initialization fails;
10. thermal throttling;
11. power constraint;
12. memory retrieval becomes slow;
13. planning exceeds action validity window;
14. safety perception unavailable;
15. repeated deadline misses;
16. recovery after process restart.

Each scenario MUST have a defined degraded/safe behavior.

---

## 30. Implementation rule: measure before optimizing

Novi MUST NOT optimize based solely on intuition.

The optimization loop is:

```text
measure
  ↓
identify bottleneck
  ↓
form hypothesis
  ↓
change one relevant variable
  ↓
benchmark
  ↓
compare end-to-end impact
  ↓
accept/reject
```

NVIDIA's Isaac ROS guidance similarly emphasizes realistic graph-level benchmarking rather than isolated node performance. citeturn0search9

---

## 31. Initial Stage-1 budget policy

Until real hardware measurements exist, Novi MUST use **budget envelopes rather than invented fixed numbers**.

Each subsystem specification should define:

```text
TARGET
MINIMUM_ACCEPTABLE
DEGRADED_THRESHOLD
FAILURE_THRESHOLD
```

The values are populated from:

1. functional requirements;
2. safety requirements;
3. sensor/control characteristics;
4. benchmark evidence;
5. actual target hardware measurements.

This prevents premature optimization for a Jetson platform that has not yet been selected.

---

## 32. Definition of done

Runtime resource architecture is complete when:

- every production workload has an execution class;
- every critical path has a latency/deadline budget;
- queues are bounded;
- stale-data policy exists;
- CPU/GPU/RAM budgets exist;
- power/thermal constraints are observable;
- neural models declare resource requirements and fallbacks;
- degradation paths are documented;
- safety-critical paths remain independent of slow cognition;
- full-graph benchmarks exist;
- p95/p99/max latency are measured;
- fault-injection tests exist;
- simulation and hardware performance claims are separated;
- resource telemetry is queryable;
- budget values are backed by measurements before hardware commitment.

---

## 33. Architectural invariant

> **Novi's intelligence may be probabilistic, but its execution boundaries must be explicit, measurable and bounded.**

A robot that thinks brilliantly but misses the deadline to stop is not intelligent in the engineering sense that matters.
