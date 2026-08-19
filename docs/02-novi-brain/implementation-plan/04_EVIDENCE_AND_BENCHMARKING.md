# 04 — Evidence and Benchmarking

## Objective

Turn real-model experiments into reproducible engineering evidence that can support model, runtime and hardware decisions.

## Required provenance

Every benchmark run records:

- benchmark identifier and version;
- scenario/dataset version;
- model name/version/digest;
- runtime/backend and version;
- CUDA/TensorRT/Isaac ROS/ROS versions where applicable;
- hardware and firmware/software versions;
- power mode;
- input resolution and sensor configuration;
- relevant model configuration;
- timestamp and run identifier.

## Core measurements

### Neural perception

- detection precision/recall/mAP where ground truth exists;
- false positives/negatives;
- depth error and invalid-pixel rate;
- tracking continuity where applicable;
- p50/p95/p99 latency;
- FPS;
- memory and utilization.

### Foundation models

- task accuracy/structured-fact accuracy;
- multimodal grounding;
- spatial/temporal reasoning;
- instruction adherence;
- uncertainty behavior;
- time-to-first-token;
- tokens/sec;
- end-to-end latency;
- memory/resource envelope.

### Full pipeline

Measure sensor-to-evidence and sensor-to-decision latency, deadline misses, queueing, resource contention and degraded-mode behavior.

## Benchmark sequence

```text
Individual model
      ↓
Individual model under load
      ↓
Pairwise neural pipeline
      ↓
Full neural pipeline
      ↓
Full Brain workload
      ↓
Hardware comparison
```

## Evidence artifact principle

Raw logs and measurements must be retained separately from conclusions. A conclusion document may summarize results but must reference the underlying run identifiers.

## No benchmark theater

Published NVIDIA benchmark numbers are useful references, not Novi acceptance evidence. Novi must measure its own sensor configuration, model versions, runtime versions and complete workload.
