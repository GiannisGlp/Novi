# B2.2 — Nemotron 3 Nano Omni Adapter

**Status:** IMPLEMENTED — adapter baseline
**Domain:** Novi Brain
**Stage:** B2.2

## Purpose

B2.2 introduces the first model-specific adapter behind Novi's generic `ModelRuntime`. The selected model is NVIDIA Nemotron 3 Nano Omni 30B-A3B.

NVIDIA describes Nemotron 3 Nano Omni as a unified multimodal model for image, video, audio and text understanding, built as a 30B-A3B MoE architecture. NVIDIA documents local deployment paths including vLLM, SGLang, Ollama, llama.cpp and LM Studio, plus NVIDIA-optimized inference paths. citeturn0search0turn0search5

## Architectural rule

The adapter does not expose a model-specific semantic authority. It translates Novi's normalized multimodal input into the existing `ModelInvocationRequest` boundary and returns a `ModelResult`.

```text
Novi Cognition
      ↓
NemotronInput
      ↓
NemotronAdapter
      ↓
ModelRuntime
      ↓
local backend
      ↓
ModelResult
```

No NVIDIA SDK, CUDA API, TensorRT API or hardware-specific control path is required by the semantic adapter.

## Implemented

`brain/b2_nemotron.py` provides:

- canonical Nemotron model identity;
- immutable model version metadata;
- `NemotronInput` normalization for text/image/audio/video;
- adapter invocation through `ModelRuntime`;
- deterministic CI backend for schema and boundary validation.

## Why the deterministic backend remains

CI must not download a 30B multimodal model. The deterministic backend verifies the adapter contract and multimodal payload normalization without making model inference a prerequisite for repository validation.

A real local backend is the next runtime integration step and will be benchmarked separately.

## Current model artifact strategy

The model artifact digest is supplied by deployment configuration rather than embedded as a mutable implementation constant. This is deliberate: the artifact must be pinned to an immutable digest once a specific checkpoint is selected for a benchmark run.

Current NVIDIA Hugging Face material exposes BF16, FP8 and NVFP4 variants. The current NVFP4 reasoning checkpoint is substantially smaller on disk than BF16, but model storage size is not treated as equivalent to runtime memory usage. citeturn0search6turn0search9

## Acceptance tests

B2.2 tests verify:

- multimodal input normalization;
- canonical model identity;
- invocation through the generic runtime;
- deterministic CI behavior;
- no model-specific execution path outside `ModelRuntime`.

## Real-model integration gate

The adapter is **not yet B2 complete** merely because the boundary works.

The next real-model gate must establish:

1. exact checkpoint identifier;
2. immutable artifact digest;
3. supported inference engine;
4. hardware target;
5. model load success;
6. image/video/audio/text invocation;
7. structured output validation;
8. p50/p95/p99 latency;
9. memory usage;
10. sustained thermal behavior;
11. timeout/cancellation behavior;
12. failure recovery;
13. robotics-relevant evaluation scenarios.

NVIDIA reports support for optimized inference with vLLM and TensorRT-LLM on NVIDIA GPU architectures, and local runtimes including llama.cpp and Ollama. citeturn0search0

## Hardware neutrality

B2.2 does not select Jetson Orin 64GB or Jetson Thor. The model adapter is intentionally independent of that decision.

The hardware decision remains an evidence-based benchmark between candidate platforms after the actual model stack and robotics workload are characterized.

## Next

**B2.3 — Model lifecycle, health, resource accounting and real backend integration.**

B2.3 will turn the adapter baseline into an operational local inference capability and begin the real performance evaluation.
