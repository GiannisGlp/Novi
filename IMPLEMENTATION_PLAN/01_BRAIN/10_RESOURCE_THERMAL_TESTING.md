# Brain — Resource and Thermal Testing

## Objective

Determine whether the complete neural workload can run sustainably on candidate hardware rather than only during short benchmark bursts.

## Metrics

- peak and sustained memory;
- GPU/accelerator utilization;
- CPU utilization;
- power draw;
- temperature;
- thermal throttling;
- sustained throughput;
- latency degradation over time;
- out-of-memory and watchdog events.

## Test modes

1. Idle baseline.
2. Individual model warm run.
3. Individual model sustained run.
4. Concurrent perception.
5. Full neural workload.
6. Long-duration soak.
7. Recovery after overload.

## Mac role

Mac tests validate resource-reporting interfaces and deterministic handling, not NVIDIA power/thermal characteristics.

## NVIDIA role

Actual power, thermal and accelerator measurements are collected on the candidate deployment platforms.

## Acceptance

The chosen deployment configuration must maintain required latency and reliability without unsafe thermal behavior, memory exhaustion or uncontrolled degradation.
