# B2.6 — Specialist Neural Perception Boundary

**Status:** IMPLEMENTED — contract/integration baseline
**Domain:** Brain
**Stage:** B2.6

## 1. Purpose

B2.6 introduces a dedicated specialist perception boundary for learned sensor interpretation. The boundary intentionally separates low-level neural perception from multimodal reasoning, world-state management, autonomy, safety, and physical control.

## 2. Why specialist models

Novi should not force Nemotron or Cosmos Reason2 to perform every perception task. Robotics perception often benefits from purpose-built networks for object detection, segmentation, depth/disparity and pose estimation. NVIDIA Isaac ROS provides DNN inference packages for these categories and supports TensorRT and Triton backends. citeturn0search0turn0search2

## 3. Implemented contract

`brain/b2_perception.py` defines:

- `Detection` — normalized object detection evidence.
- `DepthEstimate` — normalized metric/depth evidence.
- `SegmentationResult` — normalized semantic mask evidence.
- `PerceptionEvidence` — provenance-bearing sensor evidence envelope.
- `PerceptionBackend` — replaceable learned-inference backend boundary.
- `SpecialistPerception` — validation and normalization layer.

The default backend is deterministic and performs no learned inference. Real model backends are introduced only after model selection and hardware benchmarking.

## 4. Validation invariants

The perception boundary rejects:

- confidence values outside `[0, 1]`;
- inverted bounding boxes;
- malformed specialist evidence.

The boundary records sensor ID, frame ID, timestamp and backend provenance.

## 5. NVIDIA alignment

NVIDIA Isaac ROS DNN Inference supports pre-trained DNN inference for image, video, audio and sensor data, with TensorRT and Triton execution paths. NVIDIA explicitly documents object detection, segmentation, stereo/deep depth and pose-estimation packages. citeturn0search0turn0search2

NVIDIA's NITROS architecture is designed to reduce unnecessary copies between ROS nodes and accelerator memory through type adaptation/negotiation, which is relevant to the future hardware implementation. citeturn0search3turn0search4

## 6. Intended future pipeline

```text
Camera / depth / lidar / other sensors
                 |
                 v
        preprocessing / encoding
                 |
                 v
       specialist neural model
                 |
                 v
        normalized evidence
                 |
                 v
       world state / cognition
```

For NVIDIA deployment, the future implementation may use Isaac ROS DNN Inference with TensorRT or Triton and NITROS-accelerated message transport. Current Isaac ROS documentation lists Jetson Thor and NVIDIA GPU x86_64 platforms in the supported/tested matrix for the current DNN inference release. citeturn0search0

This does **not** select Thor as Novi hardware. Orin 64GB remains an open candidate and must be benchmarked separately.

## 7. Model classes to evaluate

B2.6 is a boundary, not a final model selection. Candidate specialist classes include:

1. object detection;
2. semantic/instance segmentation;
3. stereo/depth estimation;
4. pose estimation;
5. tracking;
6. later, optical flow and visual odometry where measured requirements justify them.

Model selection must consider accuracy, latency, memory, power, robustness, licensing/provenance, input resolution and compatibility with the intended deployment hardware.

## 8. Relationship to Nemotron and Cosmos

Specialist perception supplies structured evidence.

Nemotron 3 Nano Omni remains responsible for broad multimodal interpretation, while Cosmos Reason2 remains responsible for physical/spatiotemporal reasoning. The specialist layer should reduce the amount of low-level visual work those foundation models must perform.

No specialist model may directly authorize or execute an action.

## 9. Tests

`brain/tests/test_b2_perception.py` verifies:

- deterministic evidence generation;
- detection normalization;
- confidence validation;
- bounding-box validation;
- backend replacement.

The test backend is intentionally model-free so CI remains deterministic and does not require a GPU or downloaded checkpoint.

## 10. Next work

The next step is not to randomly add models. We should select a minimal specialist perception set from measured robot requirements and benchmark candidate models on the same evaluation harness used by B2.4.

The first likely candidates are object detection and depth because they directly support navigation and physical scene understanding. Isaac ROS already provides DNN infrastructure for both categories. citeturn0search0turn0search4

## 11. Acceptance boundary

B2.6's architectural acceptance means specialist perception now has a stable, testable, backend-neutral interface. It does **not** claim that a production perception model has been selected or that real-time robot perception has been validated.
