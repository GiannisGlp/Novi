# 03 — Testing and Validation Strategy

## Test layers

1. **Contract tests** — schemas, versions, validation and ownership.
2. **Unit tests** — deterministic component behavior.
3. **Integration tests** — boundaries between Brain components.
4. **CI tests** — reproducible repository-wide gates.
5. **Real-model tests** — actual checkpoints and inference runtimes.
6. **Benchmark tests** — latency, throughput, resource and capability measurements.
7. **System tests** — concurrent neural pipeline and closed-loop behavior.
8. **Failure tests** — timeout, unavailable model, stale data, malformed output and resource exhaustion.

## CI rule

CI proves software behavior and contract integrity. It must not be used as evidence that a particular GPU, checkpoint or production workload is performant.

## Real-model rule

Real-model validation must run from a pinned model artifact and reproducible configuration. The test runner records environment metadata before execution.

## Evaluation dimensions

### Functional

- correct input normalization;
- valid structured output;
- expected capabilities;
- schema compatibility;
- deterministic failure handling where applicable.

### Performance

- cold-start latency;
- warm latency;
- p50/p95/p99 latency;
- throughput/FPS or tokens/sec;
- queueing delay;
- deadline misses.

### Resources

- peak memory;
- accelerator memory;
- CPU utilization;
- GPU utilization;
- power;
- temperature;
- sustained performance and throttling.

### Capability

Tests are task-specific. Generic language benchmarks are not sufficient to accept a model for Novi physical intelligence.

### Robustness

Test lighting, occlusion, motion, noise, unusual scenes, missing sensors and malformed inputs where relevant.

## Acceptance principle

A component passes only when it satisfies both capability and operational requirements. A highly capable model that cannot meet Novi's latency/resource envelope is not accepted for that deployment target.
