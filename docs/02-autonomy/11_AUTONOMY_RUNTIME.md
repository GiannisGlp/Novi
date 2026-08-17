# 11 — Autonomy Runtime Requirements

## Status

**DESIGN**

## Purpose

This document defines the runtime guarantees Autonomy requires. It does **not** define the canonical implementation of Novi's system/Brain runtime.

Brain/system architecture owns process lifecycle, scheduling infrastructure, model execution, service orchestration and resource-management implementation. Autonomy defines the behavioral requirements that those runtime services must satisfy.

## Required Runtime Guarantees

Autonomy requires:

- bounded scheduling latency for consequential tasks;
- asynchronous execution;
- cancellation;
- deadlines/timeouts;
- priority-aware preemption;
- resource-aware admission/degradation;
- service health visibility;
- deterministic autonomy-state transitions;
- graceful degradation;
- startup/shutdown safety;
- reproducible behavioral diagnostics.

## Reference Logical Components

A deployment may expose services such as:

```text
Novi Brain / System Runtime
├── autonomy engine
├── event transport
├── cognition services
├── world-state service
├── memory/knowledge service
├── model runtime
├── capability gateway
├── safety gateway
├── diagnostics
└── API/UI gateway
```

This is a logical architecture, not a mandated process decomposition. Exact process boundaries are determined by profiling, reliability and deployment constraints.

## Concurrency

Autonomy must support concurrent:

- perception-driven events;
- cognitive requests;
- active behavioral tasks;
- outcome monitoring;
- background learning triggers;
- diagnostics.

Shared state requires explicit ownership, synchronization, or message-based contracts.

## Cancellation

Every long-running autonomy operation supports cancellation or explicitly declares why cancellation is impossible. Safety cancellation has priority over ordinary task cancellation.

## Resource Budgets

The Brain/runtime provides telemetry for:

- CPU;
- GPU;
- memory;
- storage;
- battery;
- thermal headroom;
- network;
- model/service availability.

Autonomy uses these signals to admit, delay, downgrade, pause, or cancel behavioral work.

## Model Execution Boundary

Autonomy does not implement model execution.

```text
Autonomy
  → requests cognitive capability

Cognition
  → selects capability/model

Brain/runtime
  → executes selected implementation

Cognition
  → validates/interprets result

Autonomy
  → uses result for behavioral task management
```

On Jetson, NVIDIA-specific inference optimization may use TensorRT and supported Jetson/JetPack runtimes after benchmark validation. The Autonomy contract remains vendor-neutral.

## Health States

Runtime services expose:

- healthy;
- degraded;
- unavailable;
- restarting;
- failed.

Autonomy selects safe behavioral degradation based on these states but cannot override safety controls.

## Watchdogs

Critical services may have watchdogs. A watchdog detects liveness failure; it does not bypass safety or become a second safety authority.

## Startup

The system must establish dependencies before enabling autonomous behavior:

```text
OS / hardware
→ system runtime
→ safety
→ sensors
→ cognition/world state
→ memory/knowledge
→ models
→ capabilities
→ autonomy
→ external interaction
```

The exact sequence is deployment-specific, but no autonomous consequential action may occur before required safety and capability prerequisites are validated.

## Shutdown

Shutdown should:

1. stop new autonomous goals;
2. safely cancel or complete active tasks;
3. stop/park physical systems through the appropriate controller;
4. persist required state through Memory/system services;
5. flush behavioral audit records;
6. release resources.

## Mac Profile

Mac development must implement the same autonomy contracts while using virtual/simulated robot capabilities and available Mac camera/microphone adapters.

## Simulation Profile

The simulation profile may use ROS 2 and NVIDIA Isaac Sim to provide simulated sensors, robot state, environments and physical constraints. Simulation must preserve the same autonomy contracts as other profiles.

## Jetson Profile

The Jetson profile enables physical sensors/actuators and hardware acceleration through selected platform services. JetPack, CUDA, TensorRT and Isaac ROS remain behind Brain/robotics adapters rather than becoming embedded in autonomy semantics.

## Acceptance Criteria

- bounded task scheduling;
- cancellation and deadlines;
- priority-aware interruption;
- resource-aware degradation;
- health monitoring;
- safe startup/shutdown;
- Mac/simulation/Jetson contract parity;
- reproducible autonomy diagnostics;
- no duplicate system-runtime authority inside Autonomy.
