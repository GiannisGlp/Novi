# Benchmark Manifest

## Purpose

A benchmark manifest fixes the workload so candidate models and hardware can be compared fairly.

## Manifest identity

Each manifest has:

- `benchmark_id`;
- semantic `version`;
- dataset/scenario version;
- modality;
- input resolution;
- expected output type;
- evaluation metrics;
- warm-up count;
- measured sample count;
- timeout/deadline;
- environment requirements.

## Example conceptual record

```yaml
benchmark_id: novi-rtdetr-v1
version: 1.0.0
modality: image
input_resolution: 1280x720
warmup_runs: 20
measured_runs: 200
timeout_ms: 500
metrics:
  - detection_quality
  - p50_latency_ms
  - p95_latency_ms
  - p99_latency_ms
  - throughput_fps
  - peak_memory_mb
```

## Fairness rule

Changing resolution, model precision, confidence thresholds, batching, runtime or concurrency changes the benchmark configuration and must produce a distinct evidence record.

## First manifests

1. RT-DETR detection baseline.
2. ESS stereo depth baseline.
3. FoundationStereo depth baseline.
4. Nemotron multimodal baseline.
5. Cosmos Reason2 physical-reasoning baseline.
6. Combined neural pipeline.

## Mac compatibility

Manifest parsing, validation and deterministic benchmark execution must work on Mac/CI without the real models.
