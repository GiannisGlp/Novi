# Brain — Nemotron

## Objective

Provide multimodal understanding for Novi while keeping model output behind a structured Brain evidence boundary.

## Current state

**ADAPTER IMPLEMENTED / CI VALIDATED. REAL-MODEL VALIDATION OPEN.**

## Intended capabilities

- image and video understanding;
- multimodal interpretation;
- structured scene descriptions;
- temporal reasoning where supported;
- bounded natural-language or structured responses.

## Implementation rules

The model may interpret evidence but does not own safety, autonomy authorization or actuation. Outputs must carry provenance, confidence/uncertainty where available and invocation correlation.

## Mac validation

Mac tests validate adapter contracts, schemas, lifecycle, malformed responses, timeout handling and deterministic fallback behavior. Local lightweight inference may be added when practical, but Mac test success is not evidence of NVIDIA deployment performance.

## Real validation

On NVIDIA hardware, benchmark actual checkpoint/runtime combinations for capability, latency, memory, throughput, power and thermal behavior. Test both isolated and concurrent execution.

## Acceptance

Real acceptance requires representative Novi multimodal tasks, structured-output correctness, bounded latency/resource use, failure handling and complete evidence provenance.
