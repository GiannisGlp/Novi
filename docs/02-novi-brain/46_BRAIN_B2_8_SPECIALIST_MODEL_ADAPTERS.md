# B2.8 — Specialist Perception Model Adapters

**Status:** IMPLEMENTED — adapter baseline
**Canonical role:** specialist perception capability
**Hardware:** intentionally undecided

## 1. Decision

B2.8 introduces replaceable specialist perception adapters for the first two physical capabilities Novi needs:

1. object detection — RT-DETR candidate;
2. stereo depth/disparity — ESS and FoundationStereo candidates.

The repository does not yet declare any of these candidates the permanent production model. Selection requires benchmark evidence on the actual Novi sensor configuration and candidate hardware.

## 2. Architecture

```text
Camera
  |
  +--> RT-DETR adapter
  |       |
  |       +--> ObjectEvidence
  |
  +--> ESS adapter
  |       |
  |       +--> DepthEvidence
  |
  +--> FoundationStereo adapter
          |
          +--> DepthEvidence
                 |
                 v
             World State
```

The specialist models only produce evidence. They do not own cognition, memory, autonomy, safety authorization, planning authority or actuator access.

## 3. RT-DETR

NVIDIA provides an Isaac ROS RT-DETR package and an Isaac Sim tutorial for running RT-DETR object detection. The current NVIDIA workflow demonstrates a ROS 2 graph receiving simulated camera data and publishing 2D detections.

RT-DETR is therefore the first detection candidate to benchmark, not a permanent architectural dependency.

## 4. Stereo depth candidates

### ESS

ESS is NVIDIA's Efficient Semi-Supervised stereo disparity network. NVIDIA describes it as appropriate where compute is limited or real-time speed is required.

### FoundationStereo

FoundationStereo is NVIDIA's transformer-based stereo foundation model. NVIDIA describes it as robust across diverse scenes and camera conditions, but explicitly characterizes it as a heavy model better suited to applications that do not require real-time performance.

Therefore the two candidates serve different hypotheses:

```text
ESS
  -> real-time / compute-efficient hypothesis

FoundationStereo
  -> maximum depth-quality / generalization hypothesis
```

Neither hypothesis is accepted until measured on Novi's workload.

## 5. Common contracts

`RTDETRAdapter` exposes:

- `load()`;
- `unload()`;
- `health()`;
- `infer()` returning `ObjectEvidence`.

`StereoDepthAdapter` exposes the same lifecycle boundary and returns `DepthEvidence`. Its explicit model identifier is either `ess` or `foundationstereo`.

This keeps the downstream World State independent of the selected model.

## 6. Evidence validation

Object evidence validates:

- confidence in `[0,1]`;
- normalized bounding-box coordinates;
- positive box dimensions;
- frame identity;
- source timestamp;
- model/backend provenance.

Depth evidence validates:

- positive dimensions;
- exact disparity-map cardinality;
- non-negative disparity values;
- frame identity;
- source timestamp;
- model/backend provenance.

Invalid neural output is rejected at the perception boundary rather than silently entering world state.

## 7. CI strategy

CI uses deterministic backends only. They intentionally do not execute RT-DETR, ESS or FoundationStereo.

This ensures Brain CI remains:

- reproducible;
- hardware independent;
- network independent;
- fast;
- deterministic.

Actual neural inference belongs in the hardware/model evaluation environment.

## 8. NVIDIA integration path

The intended future NVIDIA deployment path is:

```text
ROS 2 camera
   |
NITROS / Isaac ROS
   |
TensorRT / supported backend
   |
RT-DETR / ESS / FoundationStereo
   |
Novi adapter
   |
PerceptionEvidence
```

NVIDIA's current Isaac ROS DNN inference stack supports Jetson and x86_64 NVIDIA GPU environments and provides TensorRT and Triton integrations. The exact production platform remains an open Novi decision.

## 9. Hardware neutrality

No B2.8 code selects Jetson AGX Orin 64GB or Jetson AGX Thor.

The eventual decision must compare the complete workload, including:

- specialist perception;
- Nemotron;
- Cosmos Reason2;
- ROS 2 / Isaac ROS overhead;
- world-state processing;
- sensor I/O;
- memory headroom;
- latency and deadline misses;
- power;
- thermal behavior.

## 10. Benchmark gate

B2.8 is not production-complete until the real models are measured on representative hardware.

Minimum benchmark matrix:

| Workload | Accuracy/quality | p50 | p95 | memory | power | thermal |
|---|---|---:|---:|---:|---:|---:|
| RT-DETR | required | required | required | required | required | required |
| ESS | required | required | required | required | required | required |
| FoundationStereo | required | required | required | required | required | required |

The same sensor data and evaluation cases must be used when comparing candidate models and hardware.

## 11. Evidence from NVIDIA

NVIDIA publishes Isaac ROS performance data demonstrating that RT-DETR and stereo-disparity workloads can have materially different performance characteristics depending on graph, input resolution, runtime and hardware. Those figures are reference data only; Novi must measure its own end-to-end workload.

## 12. Next step

The next gate is **B2.9 — real specialist-model evaluation and full B2 integration**.

Before B2 can be declared complete, Novi must demonstrate the real neural stack under measured conditions and prove that perception evidence can travel through:

```text
Perception
  -> World State
  -> Nemotron
  -> Cosmos Reason2
  -> Cognition
  -> Memory
  -> Autonomy
  -> Safety
  -> Simulated Execution
  -> Outcome / Replay
```

The model and hardware decisions remain evidence-driven.
