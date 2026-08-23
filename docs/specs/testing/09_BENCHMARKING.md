# Mac Benchmarking

## Purpose

Measure software behavior and algorithmic changes locally without presenting Mac measurements as NVIDIA deployment evidence.

## Useful measurements

- execution latency;
- p50/p95/p99 latency;
- throughput;
- memory usage where measurable;
- test duration;
- regression against a baseline commit.

## Exclusions

Do not use Mac CPU/GPU numbers to select Orin or Thor. Hardware selection requires the dedicated NVIDIA benchmark environment.

## Reproducibility

Pin workload, fixture version, commit, configuration and environment metadata.
