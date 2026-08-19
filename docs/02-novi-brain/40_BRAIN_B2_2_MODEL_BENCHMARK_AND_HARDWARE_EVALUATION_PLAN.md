# B2.2 — Model Benchmark and Hardware Evaluation Plan

**Status:** PLANNING BASELINE
**Date:** 2026-08-19
**Domain:** Novi Brain
**Stage:** B2.2 — Real Local Model Capability

## 1. Purpose

B2.2 evaluates the first real local neural model without prematurely selecting Novi's production edge computer.

The first model target is NVIDIA Nemotron 3 Nano Omni 30B-A3B. The hardware decision between Jetson AGX Orin 64GB, Jetson AGX Thor variants, or another platform remains OPEN until measured requirements justify a decision.

## 2. Non-negotiable architecture rule

Hardware is an implementation choice, not a semantic dependency.

```text
Novi ModelRuntime
       ↓
portable adapter
       ↓
backend
       ├── Mac development
       ├── workstation GPU
       ├── Jetson AGX Orin 64GB candidate
       └── Jetson AGX Thor candidate
```

No B2.2 code may assume that Thor or Orin is the final robot computer.

## 3. Model benchmark stages

### Stage A — functional correctness

Verify:

- model artifact identity;
- model/version compatibility;
- loading and health;
- image input;
- video input;
- audio input where supported by the selected runtime;
- text input;
- multimodal input;
- structured output;
- provenance;
- timeout/failure behavior.

### Stage B — capability benchmark

Use a versioned, reproducible Novi evaluation set containing robot-relevant scenarios:

- obstacle recognition;
- object identification;
- spatial relationships;
- temporal changes;
- human presence and intent cues;
- ambiguous scenes;
- instruction grounding;
- uncertainty and abstention;
- multimodal conflict cases.

Record both correctness and unsafe/confidently-wrong behavior.

### Stage C — runtime benchmark

Measure:

- cold-start latency;
- warm latency;
- p50/p95/p99 latency;
- throughput;
- peak memory;
- steady-state memory;
- CPU utilization;
- GPU utilization;
- accelerator utilization;
- thermal behavior;
- power draw;
- concurrency;
- timeout rate;
- recovery time;
- model reload time.

## 4. Hardware candidates

### Candidate A — Jetson AGX Orin 64GB

NVIDIA currently specifies 64GB LPDDR5 unified memory, 204.8 GB/s memory bandwidth, up to 275 TOPS AI performance and a configurable 15–60W power envelope for AGX Orin 64GB.

Advantages to investigate:

- mature Jetson/JetPack ecosystem;
- 64GB unified memory;
- substantial camera and I/O support;
- established Isaac ROS path;
- lower power envelope than Thor;
- potentially sufficient for a small autonomous robot.

Questions to benchmark:

- whether the chosen multimodal model fits alongside perception, ROS 2, memory and navigation;
- sustained latency under sensor load;
- quantization impact;
- whether 64GB is sufficient for future Cosmos/skill workloads.

### Candidate B — Jetson AGX Thor

Thor is a higher-performance physical-AI platform. NVIDIA currently lists the Jetson Thor family at up to 2070 FP4 TFLOPS with 128GB memory and a 40–130W configurable power envelope, depending on module.

Advantages to investigate:

- substantially larger compute envelope;
- larger memory options;
- stronger foundation-model/physical-AI headroom;
- current NVIDIA direction for advanced robotics and physical AI;
- stronger potential for concurrent multimodal models and learned policies.

Questions to benchmark:

- robot power/thermal budget;
- physical size and cooling;
- whether the additional compute is actually used by Novi;
- total system cost;
- whether current models benefit enough to justify the power envelope.

## 5. Hardware decision matrix

The final score must be evidence-based, not based on TOPS alone.

| Dimension | Weight | Measurement |
|---|---:|---|
| Real-time latency | 20% | p95/p99 end-to-end |
| Model capacity | 15% | concurrent workload fit |
| Memory headroom | 15% | peak + safety margin |
| Power efficiency | 15% | useful inference / watt |
| Thermal sustainability | 10% | sustained workload |
| Sensor I/O | 10% | cameras/LiDAR/IMU bandwidth |
| Isaac/ROS integration | 5% | integration complexity |
| Future learned skills | 5% | GR00T/policy feasibility |
| Cost/availability | 5% | complete deployed system |

A platform does not win merely by having the highest AI compute number.

## 6. Required benchmark configurations

Every model/hardware result must record:

- exact model name;
- model release/version;
- artifact digest;
- quantization;
- runtime/backend;
- TensorRT/vLLM/other version;
- CUDA/JetPack version where applicable;
- prompt/input configuration;
- scenario/evaluation-set version;
- sensor resolution and frame rate;
- power mode;
- thermal environment;
- concurrency;
- random seed where applicable.

## 7. Target deployment profiles

We will benchmark at least three profiles:

### Profile 1 — perception/context

Nemotron 3 Nano Omni + basic deterministic world-state processing.

### Profile 2 — perception + physical reasoning

Nemotron 3 Nano Omni + Cosmos Reason2, sequential invocation.

### Profile 3 — full candidate robot workload

Perception specialists + Nemotron + Cosmos Reason2 + ROS 2/Isaac ROS + world state + memory + navigation/planning + safety.

A fourth profile may later add a learned skill/policy model.

## 8. Acceptance thresholds

Thresholds must be established from robot requirements before declaring a hardware winner. The initial rule is:

- no uncontrolled deadline misses for safety-critical deterministic loops;
- learned-model latency must remain within the cognition deadline allocated by the runtime;
- memory headroom must remain available for peak sensor and middleware activity;
- thermal throttling must not occur during the defined sustained workload;
- power consumption must fit the actual robot energy budget;
- model failure must degrade safely rather than bypassing deterministic control.

Exact numeric thresholds will be set after the robot sensor/control requirements are documented.

## 9. Decision rule

The hardware remains **UNSELECTED** until:

1. the first real model has been integrated;
2. the workload is representative;
3. Orin 64GB and Thor candidates have comparable measurements where practical;
4. the robot power/thermal/mechanical constraints are known;
5. future model requirements have been included;
6. the results are recorded in a reproducible benchmark artifact.

## 10. Current recommendation

Do not purchase or architect the final robot around either platform solely from this document.

The current research position is:

- **Orin 64GB:** credible lower-power, mature baseline candidate.
- **Thor:** credible high-headroom physical-AI candidate.
- **Winner:** not decided.

The benchmark decides.

## 11. Next implementation

Implement the Nemotron 3 Nano Omni adapter behind the existing `ModelRuntime`, first with a deterministic mock and then with the real local runtime. Once functional correctness is established, run the benchmark harness on available development hardware and record the results before making any edge-hardware commitment.
