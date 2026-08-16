# 03 — Multimodal Cognition

## Status

**DESIGN**

## Purpose

Novi must combine evidence from vision, audio, speech, touch, IMU, navigation, IoT, text, and internal state without assuming that one modality is always correct.

## Modalities

Initial modalities:

- RGB vision
- depth
- LiDAR
- microphone/audio
- speech recognition
- speaker identification
- face identity
- body pose/gesture
- IMU
- wheel odometry
- battery/thermal telemetry
- screen input
- IoT state
- user text

Additional modalities can be added behind stable observation contracts.

## Fusion Pipeline

```text
sensor outputs
    ↓
modality adapters
    ↓
normalized observations
    ↓
temporal alignment
    ↓
entity association
    ↓
spatial alignment
    ↓
evidence fusion
    ↓
world/situation update
```

## Evidence Fusion

Fusion may use deterministic rules, probabilistic filters, learned models, or hybrid methods. The choice is capability-specific and must be benchmarked.

Example:

```text
camera: person detected
face model: likely Vano, 0.91
speaker model: likely Vano, 0.86
location history: Vano usually enters here

→ identity belief: Vano, high confidence
```

The result retains all evidence rather than deleting individual observations.

## Temporal Alignment

Sensors have different sampling rates and latencies. Every observation includes capture and receive timestamps where possible. Fusion uses bounded temporal windows and rejects stale evidence when it can no longer affect the current state.

## Spatial Alignment

Coordinate transforms connect:

- camera frames;
- LiDAR frame;
- IMU frame;
- robot base frame;
- map frame;
- semantic room/zone frame.

The robotics stack should own authoritative transform infrastructure where available.

## Model Selection

For each modality we prefer:

1. mature open-source local solution;
2. hardware-compatible accelerated local solution;
3. another mature local solution;
4. cloud only if no practical local solution exists.

NVIDIA, PyTorch, TensorFlow, OpenCV, ONNX Runtime, Hugging Face, ROS/Isaac, or other ecosystems may be selected based on measured fitness rather than brand preference.

## Vision

Vision cognition may consume outputs from:

- object detection;
- tracking;
- segmentation;
- pose estimation;
- face detection/recognition;
- OCR;
- depth estimation;
- visual embeddings;
- VLMs.

Novi should avoid invoking a heavyweight VLM for every frame. Fast perception produces candidate events; semantic vision is invoked when attention or reasoning requires it.

## Audio

Audio cognition may consume:

- voice activity detection;
- speech transcription;
- speaker identification;
- sound event detection;
- music recognition;
- acoustic anomaly detection;
- direction-of-arrival information where supported.

## Cross-Modal Events

A single event can require multiple modalities.

Example:

```text
door sensor → opened
microphone → door sound
camera → Vano leaving

→ high-confidence departure event
```

## Conflict Handling

When modalities disagree:

- preserve each observation;
- assess reliability;
- assess timestamp freshness;
- assess environmental conditions;
- avoid false certainty;
- trigger additional perception if valuable;
- escalate to user when necessary.

## Privacy

Raw audio/video should remain local by default. Derived representations must inherit appropriate privacy classifications. Cloud transmission is disabled unless explicitly authorized by the applicable policy.

## Failure Modes

Examples:

- camera obscured;
- microphone noisy;
- lighting poor;
- face not visible;
- speaker overlap;
- LiDAR unavailable;
- sensor clock drift;
- model unavailable;
- GPU memory pressure.

The cognition system must continue using remaining evidence.

## Acceptance Criteria

Demonstrate correct fusion of at least two independent modalities for selected scenarios, graceful degradation when one fails, confidence/provenance preservation, temporal alignment, and deterministic replay of multimodal scenarios.
