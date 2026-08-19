# Evidence Schema

## Purpose

Every real-model or hardware experiment must produce a structured evidence record that can be independently traced to its inputs, implementation and environment.

## Required fields

```text
run_id
benchmark_id
benchmark_version
scenario_manifest_version
model.name
model.version
model.digest
runtime.name
runtime.version
backend
hardware.platform
hardware.memory
software.environment
configuration
start_time
sample_count
warmup_count
metrics
failures
status
conclusion
```

## Metrics

Metrics are benchmark-specific but may include:

- accuracy;
- precision/recall/mAP;
- depth error;
- p50/p95/p99 latency;
- throughput/FPS;
- tokens/sec;
- time-to-first-token;
- peak memory;
- CPU/GPU utilization;
- power;
- temperature;
- deadline misses.

## Status values

- `PASS`
- `FAIL`
- `BLOCKED`
- `INCONCLUSIVE`

`BLOCKED` means the experiment could not be run for a documented external reason. It must never be treated as a pass.

`INCONCLUSIVE` means the run completed but did not produce sufficient evidence for a decision.

## Evidence rules

1. No hand-edited benchmark number without a recorded source/run.
2. Model digest is required for real checkpoint evidence.
3. Hardware identity is required for accelerator evidence.
4. Conclusions must reference the measurements that support them.
5. Raw logs remain separate from summarized conclusions.
