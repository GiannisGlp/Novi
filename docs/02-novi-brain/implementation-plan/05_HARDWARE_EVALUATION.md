# 05 — Hardware Evaluation

## Decision status

**OPEN:** Jetson AGX Orin 64GB and Jetson AGX Thor are candidates. Neither is selected.

## Decision principle

The board is selected against Novi's measured workload, not peak theoretical compute.

## Required workload

The comparison must include, as supported by the final model set:

- specialist object detection;
- stereo/depth;
- Nemotron multimodal inference;
- Cosmos physical reasoning;
- world-state and Brain runtime;
- ROS 2/Isaac ROS middleware;
- logging/telemetry;
- concurrent operation.

## Metrics

- capability/accuracy;
- p50/p95/p99 latency;
- throughput;
- peak and sustained memory;
- CPU/GPU utilization;
- power;
- temperature;
- throttling;
- deadline misses;
- degraded-mode behavior;
- physical dimensions and I/O suitability;
- cost and availability;
- future model headroom.

## Fair comparison

Both platforms must use equivalent model versions, equivalent input data, equivalent quality settings and equivalent workload definitions. Platform-specific optimization is allowed only when it is documented and reproducible.

## Decision gate

A formal decision record must state:

1. requirements;
2. benchmark configuration;
3. Orin evidence;
4. Thor evidence;
5. trade-offs;
6. decision;
7. rejected alternatives;
8. follow-up risks.

Until that record is accepted, documentation must refer to both as candidates.
