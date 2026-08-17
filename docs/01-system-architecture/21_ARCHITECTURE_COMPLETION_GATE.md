# 21 — Architecture Completion Gate

**Status:** Normative gate
**Priority:** P1

## 1. Purpose

This document defines when `docs/01-system-architecture/` may be considered complete enough to hand implementation to the next documentation domain.

"Complete" means that architectural intent, boundaries, contracts, technology assumptions, validation strategy and known implementation dependencies are explicitly documented. It does **not** mean that the robot has already been built.

## 2. Completion Conditions

Architecture is complete only when all conditions below are satisfied.

### A. System definition

- system purpose documented;
- system context documented;
- major subsystems documented;
- runtime topology documented;
- data flow documented;
- autonomy lifecycle documented.

### B. Boundaries

- component ownership defined;
- dependency direction defined;
- forbidden dependencies documented;
- hardware boundary defined;
- model boundary defined;
- safety boundary defined;
- control-plane boundary defined.

### C. Contracts

- canonical event envelope defined;
- observation/evidence semantics defined;
- world-model state contract defined;
- memory/knowledge contract defined;
- goal/plan/action contracts defined;
- authorization/safety decision contracts defined;
- model invocation contract defined;
- hardware-health contract defined;
- deployment manifest contract defined.

### D. Durability and distributed semantics

- event semantics defined;
- state classes defined;
- transactions defined;
- consistency classes defined;
- concurrency/conflict semantics defined;
- replication semantics defined;
- recovery semantics defined;
- privacy lifecycle integration defined.

### E. Time

- event time separated from processing time;
- monotonic time semantics defined;
- simulation time defined;
- sensor synchronization requirements defined;
- stale/out-of-order data behavior defined;
- clock-drift handling defined.

### F. Runtime profiles

- Mac profile defined;
- simulation profile defined;
- Jetson profile defined;
- HIL profile defined;
- physical profile defined;
- promotion path defined;
- failure/degradation behavior defined.

### G. NVIDIA validation

- official NVIDIA evidence identified for vendor-dependent claims;
- current Jetson reference tuple recorded;
- ROS 2/Isaac compatibility assessed;
- TensorRT/JetPack compatibility rule recorded;
- DeepStream/other acceleration candidates classified correctly;
- model candidates separated from architecture contracts;
- Novi-specific benchmark requirement documented.

NVIDIA's current AGX Orin documentation identifies JetPack 7.2 / L4T r39.2 as the latest JetPack baseline for the Developer Kit. citeturn1search0 NVIDIA's Isaac Sim documentation recommends ROS 2 Humble and Jazzy, while current Isaac ROS documentation states its packages are designed and tested with ROS 2 Jazzy. citeturn0search9turn0search2 NVIDIA's current TensorRT migration guidance states that Jetson deployments should remain on the TensorRT 10.x release supported by their JetPack version rather than TensorRT 11.2.1. citeturn0search3

### H. Security and safety

- adaptive intelligence cannot directly alter protected safety state;
- authorization is separate from identity;
- model output is untrusted input;
- physical action requires policy and safety gates;
- emergency stop is independent of the reasoning model;
- protected credentials/configuration are outside adaptive state;
- failure-safe behavior is documented.

### I. Observability

- trace identity defined;
- event lineage defined;
- model invocation records defined;
- tool/action records defined;
- policy/safety decisions recorded;
- deployment tuple recorded;
- performance metrics defined.

### J. Resource governance

- CPU budget model defined;
- GPU budget model defined;
- memory budget model defined;
- storage budget model defined;
- queue/backpressure model defined;
- thermal/power measurement requirements defined;
- model residency policy defined.

### K. Validation

- architecture invariants have test IDs;
- contract tests are defined;
- integration tests are defined;
- simulation gates are defined;
- HIL gates are defined;
- physical safety gates are defined;
- soak tests are defined;
- evidence requirements are defined.

## 3. What Remains After Architecture Freeze

Architecture freeze does not mean implementation is finished.

The following become implementation-domain work:

```text
schema files
database implementation
event bus implementation
model adapters
ROS packages
Isaac Sim assets
Jetson image
safety controller
hardware drivers
benchmarks
test automation
physical robot
```

The architecture documents define the contracts those implementations must satisfy.

## 4. No Silent Architecture Changes

After freeze, an implementation may not silently weaken an architectural invariant.

A conflict requires an ADR containing:

- problem;
- proposed change;
- alternatives;
- evidence;
- risk;
- migration impact;
- test impact;
- approval/status.

## 5. Current Gate Status

### CLOSED

- high-level architecture;
- detailed system topology;
- architectural principles;
- component boundaries;
- runtime profiles;
- cross-cutting requirements;
- durable state semantics;
- concurrency/consistency semantics;
- replication semantics;
- recovery semantics;
- privacy/data lifecycle semantics;
- canonical contract direction;
- time/clock architecture;
- NVIDIA validation policy;
- executable validation strategy;
- deployment manifest semantics.

### IMPLEMENTATION-DEPENDENT

The architecture deliberately does not claim the following are already implemented:

- executable canonical schemas;
- actual event store;
- actual transaction engine;
- actual replication engine;
- actual recovery engine;
- actual privacy erasure engine;
- physical safety controller;
- Jetson deployment image;
- validated model benchmark;
- full simulation environment;
- HIL environment.

These are implementation work governed by this architecture.

## 6. Handoff Rule

The next documentation domain may begin once:

1. this completion gate is reviewed;
2. the architecture files are internally cross-referenced;
3. the canonical contracts are turned into implementation issues/tasks;
4. the first platform compatibility tuple is recorded;
5. no unresolved P1 architectural contradiction remains.

At that point architecture becomes a controlled baseline rather than an unfinished documentation gap.
