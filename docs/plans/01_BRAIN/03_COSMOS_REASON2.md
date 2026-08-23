# Brain — Cosmos Reason2

## Objective

Provide physical, spatial and temporal reasoning over validated observations without allowing a foundation model to become the robot's safety or control authority.

## Current state

**ADAPTER IMPLEMENTED / CI VALIDATED. REAL-MODEL VALIDATION OPEN.**

## Intended capabilities

- spatial relationships;
- temporal event interpretation;
- physical reasoning;
- object localization/grounding where supported;
- structured physical hypotheses and uncertainty.

## Implementation boundary

Cosmos receives normalized evidence and returns structured reasoning evidence. The deterministic world-state and safety layers remain authoritative.

## Mac validation

Validate contracts, schemas, correlation, invalid output handling, timeouts and deterministic test doubles on Mac/CI.

## Real validation

Create controlled physical-reasoning scenarios with known ground truth. Evaluate spatial facts, temporal relationships, physical predictions, uncertainty and end-to-end latency. Test resource behavior independently and under concurrency.

## Acceptance

Cosmos is accepted only when it demonstrates useful task-specific physical reasoning within the operational latency/resource envelope and does not bypass governance boundaries.
