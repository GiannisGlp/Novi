# Brain — FoundationStereo Depth

## Role

Higher-quality stereo-depth candidate for Novi where depth accuracy/generalization is worth additional compute cost.

## Current state

**ADAPTER IMPLEMENTED / CI VALIDATED. REAL CHECKPOINT VALIDATION OPEN.**

## Test strategy

Mac/CI validates the common depth contract and failure behavior with deterministic test doubles.

Real hardware evaluates reference depth error, invalid pixels, edge/occlusion behavior, near/far accuracy, p50/p95/p99 latency, throughput, memory, utilization, power and thermal behavior.

## Decision policy

FoundationStereo is compared directly with ESS under the same benchmark suite. Higher quality does not automatically win if latency, memory or power make it unsuitable for Novi's operational envelope.

## Acceptance

Accepted only if measured depth quality and operational performance satisfy the intended workload and the resulting evidence supports its role in the final system.
