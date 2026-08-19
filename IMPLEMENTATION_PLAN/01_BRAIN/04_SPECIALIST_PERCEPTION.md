# Brain — Specialist Perception

## Objective

Provide replaceable specialist neural perception providers for object detection and stereo/depth while preserving a common Novi evidence contract.

## Current state

**ADAPTERS IMPLEMENTED / CI VALIDATED. REAL-MODEL VALIDATION OPEN.**

## Candidates

- RT-DETR — primary object-detection candidate.
- ESS — real-time stereo-depth candidate.
- FoundationStereo — higher-quality stereo-depth candidate.

Candidate status is not production acceptance.

## Output boundary

Specialists produce normalized `ObjectEvidence` and `DepthEvidence` with frame/timestamp provenance and validity/confidence information. They do not directly modify autonomy or actuator state.

## Mac validation

Mac tests cover output validation, lifecycle, malformed evidence, timestamps, confidence/validity rules and deterministic test doubles.

## NVIDIA validation

Run real checkpoints on the available NVIDIA platform and measure task quality, p50/p95/p99 latency, throughput, memory, utilization, power and thermal behavior. Compare candidates under identical datasets/configurations.

## Acceptance

A specialist is accepted only if its evidence quality and operational performance meet the requirements of the intended robot workload.
