# Brain — Combined Neural Pipeline

## Objective

Validate the neural components as a concurrent system rather than as isolated demos.

## Target flow

```text
Sensors
  ↓
RT-DETR + Depth
  ↓
Normalized perception evidence
  ↓
World state
  ↓
Nemotron / Cosmos reasoning
  ↓
Bounded Brain proposals
```

## Measurements

- sensor-to-perception latency;
- perception-to-world-state latency;
- reasoning latency;
- end-to-end latency;
- queueing and contention;
- deadline misses;
- peak memory;
- sustained utilization;
- power and thermal behavior;
- provenance continuity.

## Concurrency

Models must be tested concurrently under representative sensor rates. Individual-model benchmark results are insufficient to claim the complete pipeline is viable.

## Acceptance

The pipeline passes only when evidence remains valid and traceable under concurrent operation while meeting the defined timing/resource envelope and preserving deterministic safety/authority boundaries.
