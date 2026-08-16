# Novi Technology Reference

## Purpose

This document is the canonical reference list for major technology ecosystems that Novi may evaluate, integrate, or use.

These are **reference ecosystems, not mandatory dependencies**. Novi is vendor-neutral. The project must select the best available solution for each capability based on the solution-selection policy.

## Core Rule

> **Prefer an existing mature open-source solution that runs locally and fits Novi's requirements. Do not reinvent a capability unnecessarily.**

The decision order is generally:

1. Existing mature solution
2. Open-source / permissive or otherwise compatible license
3. Local/offline execution
4. Hardware compatibility
5. Accuracy and robustness
6. Latency
7. Memory and compute requirements
8. Power requirements for edge deployment
9. Security and privacy
10. Maintenance/community health
11. Integration complexity
12. Cloud only when no practical local solution exists

No ecosystem below receives automatic preference merely because it appears in this document.

---

## 1. NVIDIA

### Role

NVIDIA is the primary **reference hardware and accelerated-computing ecosystem** for Novi's planned Jetson deployment, but it is not the exclusive AI/software provider.

### Relevant areas

- Jetson AGX Orin 64GB
- JetPack
- CUDA
- TensorRT
- Isaac ROS
- Isaac Sim
- DeepStream
- TAO Toolkit where applicable
- NeMo/Nemotron where appropriate
- Nsight profiling and diagnostics

### Use when

NVIDIA provides the best practical local solution for GPU acceleration, robotics acceleration, inference optimization, simulation, video pipelines, or Jetson-specific capabilities.

### Do not use automatically

A non-NVIDIA open-source solution should be preferred when it is materially better for the specific capability and integrates cleanly with Novi.

---

## 2. PyTorch

### Role

Primary reference ecosystem for evaluating and running open-source deep-learning models and training/fine-tuning workflows.

### Relevant areas

- computer vision
- audio models
- multimodal models
- model training
- fine-tuning
- research/prototyping
- inference when appropriate

### Use when

A PyTorch-native model or pipeline provides the best local capability, quality, flexibility, or community support.

PyTorch models may subsequently be exported or optimized for another runtime, including ONNX or TensorRT, when beneficial.

---

## 3. TensorFlow

### Role

Reference ML ecosystem to evaluate when an existing TensorFlow/TFLite model or pipeline provides a better solution for a particular task.

### Relevant areas

- computer vision
- mobile/edge inference
- lightweight models
- classification/detection
- specialized pretrained models
- TFLite deployments where appropriate

### Use when

A mature TensorFlow/TFLite solution is demonstrably better suited to the target capability than available alternatives.

Novi must not choose TensorFlow merely because it is listed here, and must not reject it merely because PyTorch is used elsewhere.

---

## 4. OpenCV

### Role

Reference computer-vision toolkit for classical and modern vision operations that can be solved without unnecessarily deploying a large neural model.

### Relevant areas

- image/video processing
- camera calibration
- geometric vision
- feature extraction
- tracking primitives
- transformations
- filtering
- optical-flow-related operations
- image quality checks
- preprocessing/postprocessing

### Use when

A deterministic or classical computer-vision operation is sufficient. Novi should avoid using an LLM or neural network where a robust local OpenCV operation is the appropriate solution.

---

## 5. ONNX Runtime

### Role

Reference portable local inference runtime and model-interoperability layer.

### Relevant areas

- portable model execution
- ONNX model deployment
- CPU/GPU/accelerator execution
- cross-framework model serving
- fallback inference
- benchmarking different execution providers

### Use when

Portability or an existing ONNX model makes ONNX Runtime the best option. It can also be evaluated against TensorRT and other runtimes for the same workload.

---

## 6. Hugging Face

### Role

Reference ecosystem for discovering, evaluating, downloading, versioning, and integrating open-source models and datasets.

### Relevant areas

- language models
- vision models
- vision-language models
- speech/audio models
- embeddings
- tokenizers
- datasets
- evaluation
- model metadata

### Use when

A suitable open model or dataset is available through the ecosystem and its license, provenance, quality, and local deployment requirements are acceptable.

Hugging Face is a model ecosystem rather than a guarantee that a model is open-source, safe, local, or production-ready. Every model must be evaluated individually.

---

## 7. ROS 2

### Role

Reference robotics middleware and communication architecture for the physical robot.

### Relevant areas

- robot nodes
- sensor interfaces
- actuator interfaces
- topics
- services
- actions
- lifecycle management
- transforms
- navigation integration
- simulation integration

### Use when

A capability belongs to the robotics/middleware layer. Novi Cognition and Autonomy should communicate through stable interfaces rather than depending directly on hardware drivers.

---

## 8. NVIDIA Isaac / Isaac ROS / Isaac Sim

### Role

Reference NVIDIA robotics ecosystem layered around ROS 2 for accelerated perception, robotics workloads, and simulation.

### Isaac ROS

Evaluate for:

- hardware-accelerated perception
- image processing
- visual SLAM
- depth processing
- object detection/tracking pipelines
- navigation-related acceleration
- Jetson deployment

### Isaac Sim

Evaluate for:

- robot simulation
- synthetic environments
- sensor simulation
- ROS 2 integration
- navigation testing
- synthetic-data generation
- hardware/software integration testing before physical deployment

### Rule

Use Isaac components when they provide the best fit. Do not make Novi Cognition dependent on Isaac-specific APIs when a stable vendor-neutral interface is sufficient.

---

## Relationship Between These Ecosystems

They are complementary and can coexist:

```text
                         NOVI
                           │
                 Vendor-neutral APIs
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   AI / Models         Vision / Data       Robotics
        │                  │                  │
 ┌──────┼──────┐      ┌────┴────┐      ┌────┴─────┐
 │      │      │      │         │      │          │
PyTorch TF Hugging   OpenCV   ONNX   ROS 2    Isaac ROS
            Face     │         │               │
            Models   │         │               │
                     └────┬────┘               │
                          │                    │
                     Local inference     Jetson / Sim
                          │                    │
                          └────────┬───────────┘
                                   │
                              Novi runtime
```

## Example Selection Scenarios

### Face detection

Evaluate existing local OpenCV, PyTorch, TensorFlow/TFLite, Hugging Face model, or NVIDIA-accelerated solution. Select based on real benchmark results and licensing.

### Object detection

Evaluate available pretrained local models first. If a model is PyTorch-native but TensorRT provides substantially better Jetson latency, consider a PyTorch → ONNX → TensorRT deployment path.

### Speech recognition

Evaluate mature local open-source speech models/runtimes before considering cloud speech APIs.

### Navigation

Prefer established ROS 2/Navigation2/Isaac components rather than implementing a navigation stack from scratch unless a genuine Novi-specific requirement is missing.

### General reasoning

Evaluate local open models, including Nemotron and other suitable models, against Novi's latency, memory, reasoning, tool-use, licensing, and Jetson constraints.

## Required Evaluation Record

Every significant external technology selected for Novi should eventually have a corresponding evaluation record containing:

- capability being solved
- candidate solutions
- license
- local/offline support
- supported platforms
- model/runtime size
- quality metrics
- latency benchmarks
- memory usage
- power/thermal implications
- maintenance status
- security considerations
- privacy considerations
- integration requirements
- fallback option
- reason for selection
- date/version tested

## Non-Negotiable Project Preference

Novi is intended to operate locally and preserve user privacy. Therefore:

**Local open-source solution first.**

Cloud services are exceptional dependencies and require explicit architectural justification. Safety-critical functionality must not depend on cloud availability.

## Status

This document is a living reference. Candidate ecosystems can be added when they become relevant. Existing entries do not imply adoption.
