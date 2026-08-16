# 16 — Solution Selection Policy

## Status

**DESIGN** — cross-cutting engineering policy.

## Purpose

Novi should not reinvent mature capabilities. Before implementing a subsystem, library, model, runtime, or algorithm from scratch, the project must evaluate existing solutions that can run locally and satisfy the requirements.

The policy applies equally to NVIDIA and non-NVIDIA ecosystems.

## Core Rule

> **Use the best existing open-source local solution that meets the requirement; build custom software only where no suitable solution exists or where Novi-specific orchestration/integration is itself the differentiator.**

NVIDIA is a preferred ecosystem for the Jetson target when its solution is the best fit, but there is no blanket NVIDIA-only rule.

## Candidate Ecosystems

Depending on the problem, evaluate relevant solutions from:

- NVIDIA / CUDA / TensorRT / Isaac / DeepStream / NeMo
- ROS 2 / Nav2
- PyTorch
- TensorFlow
- OpenCV
- Hugging Face ecosystem
- ONNX / ONNX Runtime
- FFmpeg / GStreamer
- widely adopted open-source speech/audio projects
- established SLAM/navigation projects
- established databases and storage engines
- other actively maintained open-source projects with compatible licensing

The list is illustrative, not exhaustive.

## Evaluation Order

For each capability:

1. define the exact requirement;
2. identify mature existing solutions;
3. verify license and redistribution constraints;
4. verify local/offline execution;
5. verify target hardware compatibility;
6. benchmark latency and throughput;
7. measure memory and power implications;
8. evaluate accuracy/quality;
9. assess maintenance/community health;
10. assess security and privacy;
11. assess integration complexity;
12. assess operational failure modes;
13. select the best option;
14. wrap it behind a Novi interface;
15. document rejected alternatives and why.

## Example: Face Security / Recognition

If Novi needs face-related capabilities, the team must separately evaluate:

- face detection
- face embedding
- identity matching
- face tracking
- liveness / anti-spoofing
- pose estimation
- facial landmark detection

There is no requirement that all of these come from the same vendor or model family.

For example, an open-source local TensorFlow, PyTorch, or OpenCV implementation may be preferable for one capability, while an NVIDIA-accelerated implementation may be preferable for another.

The correct choice is determined by benchmarks and requirements, not brand preference.

## Local-First Requirement

A solution is preferred when it can operate fully on the local machine/robot without an external network connection.

Local operation provides:

- privacy
- predictable latency
- offline resilience
- lower recurring cost
- control over model/data lifecycle
- reduced external dependency

## Open-Source Requirement

The default implementation should use genuinely open-source software with licenses compatible with Novi's intended use and distribution model.

License review must consider:

- source availability
- commercial use
- modification
- redistribution
- model-weight licensing
- dataset restrictions
- patent terms where relevant
- attribution requirements
- copyleft obligations

A project must not call something “open source” solely because its repository is publicly visible.

## Cloud Exception

Cloud is an exception, not a normal architecture dependency.

A cloud service can be selected when there is no sufficiently capable local open-source alternative or when a temporary research dependency is justified.

The decision must document:

- why local alternatives failed;
- what data leaves the robot;
- encryption/security controls;
- retention and provider policy;
- latency;
- cost;
- availability requirements;
- vendor lock-in;
- fallback behavior;
- migration plan if a local replacement becomes viable.

Core safety functions must never depend exclusively on cloud availability.

## Custom Implementation Criteria

Build a custom solution when:

- no suitable existing solution exists;
- existing solutions cannot meet a critical requirement;
- licensing is incompatible;
- integration boundaries are fundamentally wrong;
- required latency/footprint cannot be achieved;
- the custom component represents core Novi-specific orchestration or domain logic.

Do not build custom software merely because an existing library is inconvenient.

## Benchmark Requirement

“Better” must be measurable for important components.

Benchmarks should include, as applicable:

- accuracy
- false positive rate
- false negative rate
- latency p50/p95/p99
- throughput
- startup time
- RAM/VRAM use
- GPU utilization
- CPU utilization
- power consumption
- thermal behavior
- failure recovery
- offline behavior

For Jetson components, benchmark on the actual target hardware before declaring the choice final.

## Architecture Requirement

Every adopted external component must sit behind an explicit Novi abstraction when practical.

```text
Novi capability interface
        │
        ├── NVIDIA implementation
        ├── PyTorch implementation
        ├── TensorFlow implementation
        └── Open-source alternative
```

This prevents the cognitive architecture from becoming coupled to one vendor.

## Decision Records

Important selections must have an architecture decision record containing:

- requirement
- candidates considered
- versions/commits
- license
- hardware target
- benchmark results
- security/privacy assessment
- decision
- rationale
- rejected alternatives
- migration/replacement considerations

## Change Policy

A selected component can be replaced when:

- a better open-source local solution appears;
- performance materially improves;
- security changes;
- licensing becomes unsuitable;
- maintenance stops;
- hardware requirements change;
- the component creates unacceptable operational risk.

Novi's interfaces should make replacement an engineering decision rather than an architectural rewrite.

## Acceptance Criteria

The policy is considered implemented when every major technical capability in Novi has:

1. a documented requirement;
2. an existing-solution survey;
3. a local/open-source assessment;
4. benchmark evidence where applicable;
5. a documented selection decision;
6. an explicit reason for any custom implementation;
7. a cloud exception record when cloud is used;
8. a stable integration interface where practical.
