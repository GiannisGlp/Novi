# 16 — Solution Selection Policy

**Status:** DESIGN — cross-cutting engineering policy
**Owner:** `01-system-architecture`
**Scope:** All Novi subsystems and implementation domains
**Supersedes:** earlier autonomy-scoped solution-selection policy; the exact historical path is not retained as a current authority.

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

## Local-First Requirement

A solution is preferred when it can operate fully on the local machine/robot without an external network connection.

## Open-Source Requirement

The default implementation should use genuinely open-source software with licenses compatible with Novi's intended use and distribution model. License review must consider source availability, commercial use, modification, redistribution, model-weight licensing, dataset restrictions, patent terms, attribution and copyleft obligations.

## Cloud Exception

Cloud is an exception, not a normal architecture dependency. A cloud service requires an explicit decision documenting why local alternatives failed, what data leaves the robot, security/retention controls, latency, cost, availability, vendor lock-in and fallback/migration behavior.

Core safety functions must never depend exclusively on cloud availability.

## Custom Implementation Criteria

Build custom software only when:

- no suitable existing solution exists;
- existing solutions cannot meet a critical requirement;
- licensing is incompatible;
- integration boundaries are fundamentally wrong;
- required latency/footprint cannot be achieved; or
- the custom component represents core Novi-specific orchestration or domain logic.

Do not build custom software merely because an existing library is inconvenient.

## Benchmark Requirement

Important selections must be measurable. Benchmarks should include, as applicable, accuracy, false-positive/false-negative rates, p50/p95/p99 latency, throughput, startup time, RAM/VRAM, CPU/GPU utilization, power, thermal behavior, failure recovery and offline behavior.

For Jetson components, benchmark on the actual target hardware before declaring the choice final.

## Architecture Requirement

Every adopted external component should sit behind an explicit Novi abstraction when practical. This prevents the cognitive architecture from becoming coupled to one vendor.

## Decision Records

Important selections must have an ADR containing:

- requirement;
- candidates considered;
- versions/commits;
- license;
- hardware target;
- benchmark results;
- security/privacy assessment;
- decision and rationale;
- rejected alternatives;
- migration/replacement considerations.

## Acceptance Criteria

The policy is implemented when every major technical capability has a documented requirement, existing-solution survey, local/open-source assessment, benchmark evidence where applicable, selection decision, explicit reason for any custom implementation, and cloud exception record when cloud is used.
