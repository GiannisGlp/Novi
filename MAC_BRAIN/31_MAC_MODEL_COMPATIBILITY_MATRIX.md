# Mac Brain — Model Compatibility Matrix

## Purpose

The Mac prototype must contain only capabilities that can actually be implemented and exercised on the Mac. Models that are uncertain may remain as explicitly experimental candidates. NVIDIA-only models remain documented for the future robot implementation but are not Mac dependencies.

## Classification

### Tier A — Mac implementation targets

Capabilities must have a practical local implementation on the user's Mac and must be testable through the Mac Brain pipeline.

- Camera input and vision pipeline.
- Speech-to-text.
- Text-to-speech.
- Local object detection using a Mac-compatible runtime/model.
- Local multimodal/language reasoning using a Mac-compatible model/runtime.
- World-state, memory, cognition, planning and bounded autonomy.
- Virtual body/action interfaces.

### Tier B — Experimental Mac candidates

These may be attempted when the exact checkpoint, runtime, memory footprint and Apple Silicon/MPS compatibility are verified. They must never become prerequisites for the prototype until an actual Mac run proves viability.

- RT-DETR variants.
- ESS variants.
- FoundationStereo variants.
- Nemotron variants that can be executed through a Mac-compatible runtime/format.

For each candidate record: exact model/checkpoint, runtime, quantization, memory requirement, startup result, inference result, latency and known limitations.

### Tier C — NVIDIA deployment targets, not Mac dependencies

These remain part of Novi's eventual NVIDIA implementation but are excluded from the Mac prototype's required software path unless a practical Mac execution path is independently demonstrated.

- Cosmos Reason2 configurations requiring NVIDIA GPU acceleration.
- TensorRT-specific model deployments.
- CUDA-specific inference paths.
- Jetson/Isaac ROS hardware-specific acceleration.

## Selection rule

A model is not considered "Mac supported" because its Python package installs. It must successfully execute a representative Novi workload on the actual Mac and produce valid outputs through the canonical capability interface.

## Prototype policy

The Mac Brain is capability-first and model-agnostic:

```text
Required capability
      ↓
Mac-compatible provider
      ↓
Canonical Novi output
      ↓
Brain
```

If a preferred NVIDIA model cannot run on the Mac, use the best practical Mac provider for the prototype and preserve the same interface for later NVIDIA replacement.

## Evidence rule

Every Tier B experiment produces a pass/fail/blocked result with exact environment and model provenance. No experimental model may silently become a required dependency.
