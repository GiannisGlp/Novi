# 14 — Autonomy NVIDIA Integration

## Status

**DESIGN** — NVIDIA reference-platform integration.

## Principle

Novi should use an NVIDIA component when it provides a mature, supported solution that materially improves the target workload. We should not reimplement NVIDIA capabilities merely to avoid vendor tooling. At the same time, core autonomy contracts remain vendor-neutral.

## Target Hardware

Primary physical target: **NVIDIA Jetson AGX Orin 64GB**.

The target deployment must be validated against a pinned JetPack release and the exact supported versions of CUDA, TensorRT, ROS 2, Isaac ROS, and other dependencies selected for the project.

## NVIDIA Stack Candidates

### JetPack

Use JetPack as the base Jetson software stack for the physical deployment. It provides the platform-level components required for CUDA/GPU acceleration and Jetson hardware support.

### CUDA

Use CUDA where direct GPU acceleration is justified and where a higher-level supported component does not already provide the required capability.

### TensorRT

Use TensorRT for supported inference workloads when benchmarking shows meaningful latency, throughput, memory, or power benefits. Model conversion must be validated per model; unsupported operations or accuracy regressions are release blockers.

### Isaac ROS

Prefer Isaac ROS for suitable hardware-accelerated ROS 2 perception and robotics workloads rather than creating custom GPU ROS nodes. Examples may include visual perception, image processing, localization, and other supported accelerated components.

### Isaac Sim

Use Isaac Sim for high-fidelity robotics simulation, sensor simulation, navigation experiments, synthetic scenarios, and regression testing where its capabilities materially improve fidelity.

### Nav2

Use the established ROS 2 Navigation Stack for navigation orchestration rather than implementing a new navigation framework. Isaac ROS can provide accelerated perception/localization components around it where appropriate.

### DeepStream

Evaluate DeepStream for high-throughput multi-camera/video pipelines. Use it only when its pipeline architecture is a better fit than a simpler Isaac ROS/OpenCV/custom path.

### Nemotron

Nemotron 3 Nano 30B-A3B is the primary general-purpose reasoning-model candidate. The autonomy layer must treat the model as a replaceable implementation behind a model contract. Jetson deployment is subject to actual benchmark validation.

## Responsibility Boundary

```text
Novi Core
  ├── autonomy
  ├── cognition
  ├── memory
  ├── personality
  ├── knowledge
  └── capability contracts

NVIDIA / robotics layer
  ├── JetPack
  ├── CUDA
  ├── TensorRT
  ├── Isaac ROS
  ├── Isaac Sim
  └── other selected NVIDIA acceleration

ROS 2 ecosystem
  ├── middleware
  ├── Nav2
  └── hardware/robotics interfaces
```

## Selection Rule

For every subsystem, evaluate in this order:

1. Does NVIDIA provide a supported component that directly fits the requirement?
2. Does it improve measurable performance, reliability, development speed, or simulation fidelity?
3. Is its lifecycle/support acceptable?
4. Does adopting it preserve a clean Novi interface?
5. Is there a simpler open component that is materially better for this exact workload?

If NVIDIA wins, use NVIDIA. If not, use the better component behind the same abstraction.

## No Forced NVIDIA Rule

Do not introduce an NVIDIA product merely because it exists. Unnecessary dependencies increase image size, maintenance burden, upgrade coupling, and debugging complexity.

## Mac Development

Mac development must not depend on Jetson-only libraries for core autonomy tests. NVIDIA-specific adapters should be optional and activated by the Jetson runtime profile.

## Simulation

Where Isaac Sim is selected, the simulation boundary should expose the same ROS 2 and Novi capability contracts used by the physical system.

## Performance Validation

Every NVIDIA acceleration decision must have a benchmark covering:

- latency;
- throughput;
- memory;
- accuracy;
- power where applicable;
- thermal stability;
- concurrent workload behavior.

A component is not considered adopted solely because a benchmark works in isolation.

## Acceptance Criteria

- Jetson deployment is reproducible from pinned dependencies;
- NVIDIA-specific code is isolated behind adapters/contracts;
- Isaac ROS/ROS 2 components can be replaced in tests;
- TensorRT conversions have accuracy/performance tests;
- simulation scenarios are reproducible;
- core autonomy remains runnable on Mac without Jetson hardware.
