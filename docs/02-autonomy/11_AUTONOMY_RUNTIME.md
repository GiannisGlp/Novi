# 11 — Autonomy Runtime

## Status

**DESIGN**

## Purpose

The runtime manages lifecycle, concurrency, scheduling, resource budgets, service health, model invocation, cancellation, and graceful degradation.

## Processes

A reference deployment may contain:

```text
wheely-runtime
├── autonomy engine
├── event bus
├── world model service
├── memory/knowledge service
├── model runtime
├── capability gateway
├── safety gateway
├── diagnostics
└── API/UI gateway
```

The exact process split may change after profiling.

## Concurrency

Independent work should execute concurrently:

- perception ingestion;
- audio processing;
- world-state updates;
- active plan execution;
- background learning;
- diagnostics.

Shared state requires explicit synchronization or message-based ownership.

## Cancellation

Every long-running operation supports cancellation or an explicit statement that cancellation is impossible. Safety cancellation has priority.

## Resource Budgets

The runtime tracks:

- CPU;
- GPU;
- unified memory;
- storage;
- battery;
- thermal headroom;
- network;
- model availability.

Tasks can be admitted, delayed, downgraded, or cancelled based on budgets.

## Model Runtime

The model runtime should support model health, warm/cold start, timeouts, structured output validation, batching where beneficial, and resource-aware scheduling.

On Jetson, NVIDIA-specific inference optimization should be evaluated using TensorRT and appropriate Jetson/JetPack-supported runtimes. Do not assume every model benefits equally from conversion.

## Health States

Services expose:

- healthy;
- degraded;
- unavailable;
- restarting;
- failed.

The autonomy engine chooses safe behavior based on health state.

## Watchdogs

Critical services have watchdogs. A watchdog detects liveness failure but cannot itself bypass safety controls.

## Startup

Startup order should verify dependencies before enabling autonomous action:

```text
OS/hardware
→ core services
→ safety
→ sensors
→ world model
→ models
→ capabilities
→ autonomy
→ external interaction
```

## Shutdown

Shutdown should:

1. stop new goals;
2. safely cancel/complete actions;
3. park/stop physical systems;
4. persist critical state;
5. flush audit records;
6. release resources.

## Mac Profile

The Mac runtime uses hardware adapters for camera/microphone/audio and simulated adapters for robot hardware. It must support the same autonomy API contracts.

## Simulation Profile

The simulation profile uses ROS 2 and NVIDIA Isaac Sim where available to provide simulated sensors, robot state, environment events, and physical constraints.

## Jetson Profile

The Jetson profile enables hardware-specific acceleration and physical interfaces. NVIDIA JetPack, CUDA, TensorRT and Isaac ROS should be treated as platform services rather than embedded into core cognition.

## Acceptance Criteria

- clean startup/shutdown;
- service isolation;
- bounded resource use;
- cancellation;
- graceful degradation;
- health monitoring;
- Mac/simulation/Jetson profile parity;
- reproducible runtime diagnostics.
