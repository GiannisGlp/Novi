# 18 — NVIDIA Platform Validation Matrix

**Status:** Normative architecture evidence
**Priority:** P1 — required for NVIDIA-dependent implementation decisions
**Scope:** Jetson AGX Orin, JetPack, CUDA, TensorRT, Isaac Sim, Isaac ROS, DeepStream, NVIDIA model/runtime options

## 1. Purpose

This document defines how Novi validates claims about NVIDIA hardware and software. It prevents architecture documents from treating remembered capabilities, blog posts, third-party tutorials, or unpinned package combinations as authoritative platform facts.

NVIDIA documentation establishes vendor capability and compatibility. Novi-specific benchmarks and integration tests establish whether a capability is suitable for Novi's workload.

Therefore:

```text
NVIDIA documentation
        ↓
Vendor capability / compatibility claim
        ↓
Pinned Novi platform tuple
        ↓
Novi integration test
        ↓
Novi benchmark
        ↓
ADR / adoption decision
```

A vendor-supported component is not automatically a Novi-approved component.

## 2. Authoritative Source Policy

For NVIDIA-specific claims, preferred evidence order is:

1. NVIDIA official product documentation.
2. NVIDIA official release notes and support matrices.
3. NVIDIA official developer documentation and reference implementations.
4. Official NVIDIA model cards / deployment documentation.
5. Novi-controlled experiments using the exact target hardware and software tuple.
6. Other sources only when the preceding sources do not provide the required information, and such use must be explicitly marked.

A third-party article must not override an official NVIDIA compatibility statement.

## 3. Current Reference Platform

The current physical edge target remains **Jetson AGX Orin 64GB**.

NVIDIA's current AGX Orin Developer Kit documentation identifies **JetPack 7.2** with **L4T r39.2** as the current JetPack release for that developer kit. citeturn1search0

The architecture therefore treats the following as the current validation baseline, not as an eternal dependency:

```text
Hardware: Jetson AGX Orin 64GB
JetPack: 7.2
L4T: r39.2
OS: NVIDIA-supported JetPack userspace
ROS 2: Jazzy candidate
```

Exact CUDA/TensorRT component versions must be read from the installed JetPack/SDK manifest rather than independently pinned from a generic CUDA or TensorRT page.

## 4. ROS 2 / Isaac Sim

NVIDIA Isaac Sim 6.0 documentation recommends ROS 2 Humble and Jazzy and documents Ubuntu 24.04 with ROS 2 Jazzy. citeturn0search9

Novi therefore adopts:

```text
ROS 2 Jazzy = primary architecture candidate
ROS 2 Humble = compatibility candidate only where a required component mandates it
```

The final choice must be validated against the exact Isaac Sim release, Jetson runtime, ROS packages, and robot drivers used by Novi.

NVIDIA Isaac ROS documentation for release 4.3 states that its packages are designed and tested with ROS 2 Jazzy. citeturn0search2

However, the Isaac ROS release page currently exposes platform-specific instructions that must be checked against the actual target hardware. Novi must not infer that every Isaac ROS package/release is automatically supported on AGX Orin simply because ROS 2 Jazzy is supported.

## 5. TensorRT

NVIDIA's current TensorRT documentation states that TensorRT 11.2.1 does not support JetPack and that Jetson deployments must remain on the TensorRT 10.x release supplied by their JetPack version. citeturn0search3

Therefore Novi must follow this rule:

> Never independently upgrade TensorRT on the Jetson target outside the TensorRT version supplied and supported by the selected JetPack tuple without an explicit compatibility validation and ADR.

TensorRT is an implementation dependency behind the model-runtime contract, not a cognitive API dependency.

## 6. DeepStream

NVIDIA's current DeepStream documentation lists Jetson Orin among supported platforms and documents JetPack 7.2 / L4T 39.2 for the current Jetson installation path. citeturn1search2

DeepStream is therefore an approved **candidate** for high-throughput video pipelines, subject to Novi-specific measurements.

Novi must benchmark at minimum:

- camera-to-observation latency;
- throughput at target resolutions;
- CPU/GPU utilization;
- memory footprint;
- pipeline recovery;
- synchronization behavior;
- interaction with ROS 2 and perception workers.

## 7. Camera and Timestamping Considerations

NVIDIA's current Jetson Linux documentation includes camera support, Argus, SIPL, generic timestamping, and PTP-related platform capabilities. citeturn1search4

Novi must distinguish:

```text
sensor timestamp
capture timestamp
transport timestamp
host receipt timestamp
processing timestamp
world/event timestamp
```

The platform implementation must preserve the strongest timestamp available and never fabricate precision that the sensor path does not provide.

## 8. Holoscan / Sensor Integration

NVIDIA's current Holoscan Sensor Bridge documentation explicitly includes AGX Orin support and JetPack 7.2 dependencies, and documents PTP configuration and hardware-accelerated sensor paths. citeturn1search1turn1search3

Holoscan is therefore a candidate for specialized sensor pipelines, not a mandatory dependency for the entire cognitive architecture.

The abstraction boundary is:

```text
NVIDIA sensor implementation
        ↓
Novi Sensor Adapter
        ↓
Canonical Observation/Event
```

## 9. Nemotron

NVIDIA's current Nemotron 3 Nano 30B-A3B model card describes a 30B-parameter hybrid Mamba2/Transformer MoE model and documents reasoning and non-reasoning use cases. citeturn0search5

NVIDIA's current deployment page provides self-hosted NIM deployment for the model. citeturn0search1

This validates Nemotron as a serious **model candidate**, but does not establish that a 30B model is appropriate for sustained AGX Orin edge autonomy.

Novi must benchmark:

- resident memory;
- load time;
- TTFT;
- tokens/sec;
- context length actually usable at edge;
- tool-calling reliability;
- structured-output reliability;
- thermal/power impact;
- concurrency with perception;
- recovery after model failure.

The architecture therefore retains `ModelRuntime` abstraction and does not make Nemotron a hard architectural dependency.

## 10. Validation Tuple

Every physical deployment must record a machine-readable tuple containing at least:

```text
hardware SKU
RAM
JetPack version
L4T version
CUDA version
TensorRT version
ROS 2 distribution
Isaac ROS version
Isaac Sim version
DeepStream version, if used
model/runtime versions
container image digests
kernel / firmware versions where relevant
```

A benchmark without this tuple is not a reproducible architecture result.

## 11. Change Policy

A platform component is considered changed when any of the following changes:

- hardware revision;
- JetPack/L4T;
- CUDA;
- TensorRT;
- ROS 2 distribution;
- Isaac ROS release;
- Isaac Sim release;
- DeepStream release;
- camera driver/firmware;
- model weights or quantization;
- container digest;
- kernel/firmware affecting timing or hardware behavior.

Such a change reopens the relevant validation gates.

## 12. Acceptance Criteria

The NVIDIA platform is architecture-approved only when:

1. the complete software tuple is recorded;
2. official NVIDIA compatibility evidence exists for each vendor-dependent component;
3. Novi integration tests pass;
4. resource budgets are measured;
5. thermal/power behavior is measured;
6. failure and recovery behavior is tested;
7. the resulting configuration is captured in an ADR;
8. deployment artifacts are pinned to immutable versions/digests where practical.

## 13. Current Evidence Summary

| Area | Current evidence | Novi status |
|---|---|---|
| Jetson AGX Orin | NVIDIA Jetson documentation | Supported reference hardware |
| JetPack 7.2 / L4T r39.2 | NVIDIA AGX Orin documentation | Current baseline |
| ROS 2 Jazzy | NVIDIA Isaac Sim / Isaac ROS docs | Primary candidate |
| TensorRT 10.x on Jetson | NVIDIA TensorRT migration docs | Required compatibility rule |
| DeepStream on Orin | NVIDIA DeepStream docs | Candidate |
| Holoscan Sensor Bridge | NVIDIA docs | Candidate |
| Nemotron 3 Nano 30B-A3B | NVIDIA model/deployment docs | Model candidate |

## 14. Important Limitation

This document is evidence of architecture validation status. It is not evidence that the final robot has achieved the target performance.

Hardware performance claims require Novi benchmarks on the actual target hardware and exact software tuple.
