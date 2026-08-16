# 19 — Open-Source and NVIDIA Integration

## Status

**DESIGN**

## Purpose

Define how Novi evaluates existing technology instead of rebuilding capabilities unnecessarily.

## Selection Rule

For every capability:

```text
required capability
  ↓
existing mature solution?
  ↓
open-source + acceptable license?
  ↓
local execution?
  ↓
hardware compatible?
  ↓
quality sufficient?
  ↓
latency/resource target met?
  ↓
security/privacy acceptable?
  ↓
maintained?
  ↓
benchmark
  ↓
select best solution
```

## Reference Ecosystems

The project explicitly evaluates, where relevant:

- NVIDIA
- PyTorch
- TensorFlow
- OpenCV
- ONNX Runtime
- Hugging Face
- ROS 2
- NVIDIA Isaac / Isaac ROS / Isaac Sim

This list is a reference set, not an exclusive dependency list.

## NVIDIA Role

NVIDIA is the reference hardware/acceleration ecosystem because the target robot uses Jetson AGX Orin 64GB. JetPack, CUDA, TensorRT, Isaac ROS, Isaac Sim, DeepStream and related technologies should be evaluated where they solve a real requirement.

## Non-NVIDIA Alternatives

A non-NVIDIA solution wins when it provides better overall value for the capability. Examples may include OpenCV for deterministic computer vision, PyTorch or TensorFlow for model development, ONNX Runtime for portable inference, or another open-source project with better local performance or functionality.

## Local-First

The preferred deployment is local and offline-capable. Cloud services are exceptional dependencies and require an explicit documented justification.

## Cloud Exception Record

Any cloud dependency must document:

- why local alternatives were insufficient
- data transmitted
- privacy impact
- availability dependency
- cost
- latency
- fallback
- removal/migration plan

## Adapter Principle

External technologies should be isolated behind Novi interfaces. Vendor-specific code must not leak into cognitive domain contracts.

## Benchmark Requirement

Technology selection is not final until benchmark results are available on representative target hardware or a documented development proxy. Benchmarks should include quality, latency, memory, power where measurable, and failure behavior.

## Acceptance Criteria

Novi can adopt the best existing open-source technology for each cognitive capability without becoming dependent on a single vendor.
