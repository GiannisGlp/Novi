# B2.3 — Real Inference and Benchmark Gate

**Status:** IMPLEMENTED — runtime boundary ready for real backend
**Domain:** Novi Brain
**Stage:** B2.3

## Purpose

B2.3 converts the B2 model adapter from a contract-only integration into an operational real-inference boundary. The semantic Brain layer remains independent of the concrete inference engine.

## Architecture

```text
Novi Brain
   ↓
ModelInvocationRequest
   ↓
RealModelInvoker
   ↓
Injected backend
   ├── vLLM
   ├── TensorRT-LLM
   ├── TensorRT Edge-LLM
   ├── llama.cpp
   └── other validated backend
   ↓
ModelResult
```

The first production candidate is NVIDIA Nemotron 3 Nano Omni 30B-A3B. NVIDIA's current model card lists video, audio, image and text input, 256K maximum context, JSON output, tool calling, and NVFP4 weights of roughly 21 GB. It lists vLLM, TensorRT-LLM, TensorRT Edge-LLM, llama.cpp, Ollama and SGLang as supported inference engines. citeturn0search0turn0search6

## Safety boundary

The inference layer cannot:

- authorize physical actions;
- invoke motors;
- modify authoritative world state directly;
- bypass provenance;
- bypass the ActionProposal/Safety boundary.

A model result remains inference evidence or a candidate cognitive output.

## Operational policy

The real invoker introduces an explicit deadline policy and structured-output requirement. Backend failures are contained as `ModelResult(status="failed")`. Deadline overruns become `timeout`. Outputs that do not satisfy the required structured representation become `invalid_output`.

This is deliberately conservative: free-form model text cannot silently become a control command.

## Real checkpoint strategy

Do not download model weights in CI. CI validates the runtime contract with an injected deterministic/fake backend. Real weights belong in benchmark environments because the current NVFP4 checkpoint is about 22.4 GB and the model requires a suitable NVIDIA GPU for the supported optimized path. citeturn0search4turn0search0

NVIDIA currently lists minimum GPU guidance of H100 80GB for BF16, L40S 48GB for FP8, and RTX 5090 32GB / DGX Spark / Jetson Thor support for NVFP4. This means the hardware decision remains open and must be measured rather than inferred from model size alone. citeturn0search0turn0search1

## Benchmark gate

Before B2.3 can be marked complete, run the real model on a controlled benchmark host and record:

### Startup

- environment installation time;
- model download size;
- cold load time;
- warm readiness time;
- peak memory during load.

### Inference

- text-only latency p50/p95/p99;
- image latency p50/p95/p99;
- multimodal latency p50/p95/p99;
- tokens/sec where applicable;
- output length;
- structured-output success rate;
- timeout rate;
- backend error rate.

### Resource envelope

- GPU memory peak;
- system RAM peak;
- GPU utilization;
- CPU utilization;
- power;
- temperature;
- sustained throughput;
- thermal throttling.

### Novi relevance

Evaluate controlled scenarios for:

- object identification;
- scene description;
- temporal change detection;
- human/robot interaction interpretation;
- obstacle interpretation;
- instruction grounding;
- uncertainty reporting;
- structured cognitive evidence generation.

### Hardware comparison

Where hardware is available, benchmark the same checkpoint and configuration on candidate systems, including **Jetson AGX Orin 64GB** and **Jetson AGX Thor**. Do not select either platform until the full workload is measured.

## Reproducibility requirements

Every benchmark result must record:

- exact model repository and revision;
- artifact digest;
- precision/quantization;
- inference backend and version;
- driver/CUDA/TensorRT/vLLM versions;
- hardware model;
- power mode;
- input dataset/scenario version;
- prompt/template version;
- generation parameters;
- context length;
- concurrency;
- result schema version.

## Current NVIDIA configuration reference

The current Nemotron model card recommends thinking-mode settings around temperature 0.6, top-p 0.95, reasoning budget 16,384 and maximum output around 20,480 tokens for long multimodal reasoning. These settings are a benchmark starting point, not a Novi runtime default. citeturn0search0

## Acceptance criteria

B2.3 is complete only when:

1. a real Nemotron checkpoint loads through the adapter;
2. health is observable;
3. real inference produces validated structured output;
4. provenance is complete;
5. deadlines are enforced;
6. failures are contained;
7. benchmark data is reproducible;
8. robotics-relevant scenarios are evaluated;
9. hardware resource usage is recorded;
10. no actuator authority is introduced;
11. at least one credible alternative configuration is compared;
12. the hardware decision remains evidence-based.

## Next

B2.4 — provenance and evaluation harness. The harness will turn the benchmark requirements into repeatable datasets, scenario definitions, scoring, artifact capture and regression comparison.
