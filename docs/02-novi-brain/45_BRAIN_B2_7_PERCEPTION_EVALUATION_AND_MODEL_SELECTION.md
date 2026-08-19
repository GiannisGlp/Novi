# B2.7 — Perception Evaluation & Model Selection

**Status:** IMPLEMENTED — evaluation baseline
**Owner:** Brain / Perception
**Hardware decision:** OPEN — Jetson AGX Orin 64GB vs Jetson AGX Thor

## Purpose

B2.7 establishes the evidence boundary for selecting specialist neural perception models. It deliberately separates the perception contract from any particular model, accelerator or vendor runtime.

Novi must select models from measured requirements, not popularity or raw benchmark scores.

## Evaluation contract

`PerceptionCase` describes a reproducible evaluation scenario:

- case identifier;
- input modality;
- expected semantic labels;
- minimum acceptable confidence;
- scenario metadata.

`PerceptionEvaluation` records:

- case identifier;
- pass/fail status;
- measured latency;
- detected labels;
- confidence;
- explicit failure reasons.

The deterministic backend exists only for CI. It does not represent production model quality.

## Initial specialist capabilities

The first Novi perception candidates should cover:

1. object detection;
2. depth / stereo disparity;
3. free-space or obstacle understanding;
4. semantic segmentation where it materially improves navigation;
5. object tracking;
6. 3D pose only when a concrete robot task requires it.

This ordering avoids forcing the multimodal foundation models to perform every low-level perception task.

## NVIDIA alignment

NVIDIA Isaac ROS currently provides DNN inference packages for object detection, image segmentation, stereo depth/disparity and pose estimation. Its DNN inference architecture uses encoder → inference → decoder stages, with TensorRT for high-performance inference and Triton when backend/model flexibility is required. NITROS is used to optimize ROS message transport. The current Isaac ROS documentation also lists camera, LiDAR and RADAR among supported DNN input classes.

Reference: NVIDIA Isaac ROS DNN Inference documentation, current 2026 release.

## Selection criteria

Every production candidate must be evaluated on the target workload for:

- detection/segmentation accuracy;
- false-positive and false-negative behavior;
- depth error where applicable;
- p50/p95/p99 latency;
- sustained FPS;
- cold-start time;
- memory consumption;
- GPU utilization;
- CPU utilization;
- power consumption;
- thermal stability;
- frame drops and deadline misses;
- robustness to lighting, motion blur and partial occlusion;
- output confidence calibration;
- model/license provenance;
- TensorRT compatibility;
- fallback behavior.

## Hardware policy

No hardware winner is selected by B2.7.

The same evaluation cases and model configuration must be run on candidate hardware when available:

```text
Jetson AGX Orin 64GB  ─┐
                      ├── identical workload → evidence
Jetson AGX Thor       ─┘
```

A future decision must consider the complete workload, not a single model:

```text
specialist perception
+
Nemotron
+
Cosmos Reason2
+
ROS 2 / Isaac ROS
+
world state / memory
+
logging / observability
```

## Runtime policy

The model-selection layer must remain independent of the inference implementation. Candidate backends may use TensorRT, Triton, ONNX Runtime, PyTorch or another validated runtime. The semantic output must be normalized into Novi `PerceptionEvidence`.

For NVIDIA deployment, TensorRT is the preferred first benchmark for supported models because NVIDIA positions it as the high-performance path. Triton is the fallback where model/backend flexibility requires it.

## Initial benchmark scenarios

The evaluation corpus should begin with:

- person detection;
- chair/furniture detection;
- common obstacle detection;
- small-object detection at useful navigation distance;
- low-light scene;
- motion-blurred scene;
- partial occlusion;
- cluttered room;
- corridor/free-space scene;
- depth discontinuity;
- moving person crossing the robot path.

Simulation-generated cases should later be supplemented with real sensor captures before a production hardware decision.

## Acceptance criteria

B2.7 is structurally complete when:

- specialist perception can be evaluated without a production model dependency;
- pass/fail semantics are explicit;
- latency is captured;
- confidence thresholds are explicit;
- missing detections are explicit failures;
- invalid measurements are rejected;
- evaluation is reproducible;
- hardware selection remains open;
- production model selection is based on evidence.

## Next

The next step is to select and benchmark the first real specialist models, beginning with **object detection and depth**. The final model choices should be made only after the target sensor configuration and available benchmark hardware are established.
