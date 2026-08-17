# 113 — Resource Governance, Scheduling & Budgets

**Status:** P1 normative architecture foundation  
**Depends on:** 00–112

## 1. Purpose

Define how Novi allocates limited compute, memory, storage, power, thermal capacity, sensor bandwidth and execution time across competing autonomous workloads.

## 2. Resource classes

```text
CPU
GPU
RAM / unified memory
storage capacity
storage I/O
network bandwidth
sensor bandwidth
model concurrency
queue capacity
power
thermal headroom
actuator availability
```

## 3. Resource ownership

Every component declares:

- expected resource profile;
- peak profile;
- minimum viable resources;
- priority;
- safety class;
- degradations;
- cancellation behavior.

## 4. Priority classes

Suggested baseline:

```text
P0 — safety / hardware protection
P1 — control / localization / critical perception
P2 — core autonomy / world state
P3 — interaction / reasoning
P4 — maintenance / analytics / background learning
```

Safety-critical workloads cannot be starved by background reasoning.

## 5. Admission control

Before launching an expensive workload:

```text
REQUEST
 ↓
RESOURCE CHECK
 ↓
POLICY CHECK
 ↓
PRIORITY CHECK
 ↓
ADMIT / DEFER / REJECT
```

## 6. Model scheduling

Model calls must account for:

- memory residency;
- load/unload cost;
- GPU contention;
- latency budget;
- priority;
- cancellation;
- thermal state;
- power state.

## 7. Sensor scheduling

High-bandwidth sensors may require:

- sampling;
- frame dropping;
- resolution reduction;
- region-of-interest processing;
- batching;
- priority queues.

Any degradation that changes semantic quality must be visible to cognition.

## 8. Power governance

Physical operation requires a power budget covering:

- compute;
- sensors;
- displays;
- audio;
- actuators;
- networking;
- conversion losses;
- thermal system.

Power state may constrain workload admission.

## 9. Thermal governance

Thermal state must affect scheduling before hardware reaches unsafe conditions.

Example:

```text
thermal headroom falls
 ↓
reduce background workloads
 ↓
reduce model concurrency
 ↓
defer non-critical perception
 ↓
protect control/safety
```

## 10. Memory pressure

Memory pressure must trigger deterministic policies:

```text
FREE CACHE
 ↓
EVICT REBUILDABLE DATA
 ↓
REDUCE MODEL RESIDENCY
 ↓
DEFER BACKGROUND WORK
 ↓
ENTER DEGRADED MODE
```

Critical safety/control state is not evicted merely to preserve a model.

## 11. Storage governance

Track:

- event-log growth;
- media growth;
- model artifacts;
- caches;
- backups;
- temporary files.

Retention policy from 111 and storage budgets must interact.

## 12. Queue governance

Every unbounded queue is an architectural risk.

Queues must define:

- capacity;
- priority;
- overflow behavior;
- backpressure;
- drop policy;
- observability.

## 13. Fairness

Background workloads must not monopolize resources, while safety workloads must receive preferential treatment when required.

## 14. Cancellation

Deferred/low-priority tasks should be cancellable when higher-priority work requires resources.

## 15. Scheduling across profiles

Resource budgets differ across:

```text
Development
Simulation
Edge
HIL
Physical
```

The same semantic priority classes remain, but numerical budgets are profile-specific.

## 16. NVIDIA edge considerations

NVIDIA Jetson environments expose power/performance controls and platform telemetry. Isaac ROS documentation includes Jetson-specific monitoring capabilities, which can feed Novi's resource/health layer when adopted. citeturn1search4

DeepStream documentation also demonstrates explicit Jetson performance/power configuration and component-level latency measurement, reinforcing the need for workload-specific edge budgets. citeturn0search5turn0search10

## 17. Budget evidence

A budget is not authoritative until measured.

For each critical workload record:

- average;
- P95/P99;
- peak;
- duration;
- hardware;
- software versions;
- thermal conditions;
- power state;
- dataset/scenario.

## 18. Final rule

> **Novi must protect safety/control resources first, cognitive resources second, and background optimization last.**
