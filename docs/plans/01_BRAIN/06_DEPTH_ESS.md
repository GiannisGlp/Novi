# Brain — ESS Depth

## Role

Real-time stereo-depth candidate for compute-constrained Novi deployments.

## Current state

**ADAPTER IMPLEMENTED / CI VALIDATED. REAL CHECKPOINT VALIDATION OPEN.**

## Test strategy

Mac/CI validates normalized depth evidence, validity, timestamps, lifecycle and failure behavior using deterministic test doubles.

Real hardware validates depth quality against reference data, invalid-pixel rate, near/far accuracy, edge behavior, p50/p95/p99 latency, throughput, memory, utilization, power and thermal behavior.

## Acceptance

ESS passes when depth quality is sufficient for the intended navigation/perception workload and its sustained operational envelope is compatible with the selected platform.
