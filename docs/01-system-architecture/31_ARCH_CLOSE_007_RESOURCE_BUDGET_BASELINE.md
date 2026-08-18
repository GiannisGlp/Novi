# 31 — ARCH-CLOSE-007 Resource Budget Baseline

**Status:** Baseline defined — hardware validation pending  
**Priority:** P0  
**Authority:** System Architecture  
**Scope:** Stage-1 local/offline Novi runtime and first autonomous robot target

## Purpose

Turn Novi's runtime resource architecture into explicit, measurable budgets. These are engineering targets, not achieved-performance claims. Final hardware selection is deliberately deferred until functional Novi has been validated on the Mac and its actual workload measured.

## Hardware decision

The compute platform is **deferred**. AGX Orin 64GB and Jetson Thor remain candidate architectures; this document must not lock Novi to the older Orin NX 16GB assumption from the recovered branch.

## Stage-1 resource envelope

| Resource | Target | Minimum acceptable | Degraded threshold |
|---|---:|---:|---:|
| CPU sustained utilization | <=70% | <=80% | >80% sustained |
| GPU sustained utilization | <=75% | <=85% | >85% |
| Unified RAM working set | <=12GB | <=13GB | >13GB |
| Model/inference allocation | <=10GB | <=12GB | >12GB |
| Active runtime storage | <=200GB | <=300GB | >300GB |
| Compute power | 25W target | 40W test envelope | throttling |
| SoC temperature | <80C | <90C | >=90C |

These values are provisional acceptance targets and must be replaced or tightened after measurements on the selected hardware.

## Execution-class latency budgets

| Class | Representative workload | Frequency | p99 | Maximum | Queue |
|---|---|---:|---:|---:|---:|
| S0 | safety/watchdog | 100 Hz | <=2 ms | 5 ms | 1 |
| S1 | control interface | 50 Hz | <=5 ms | 10 ms | 1 |
| S2 | reactive obstacle/person response | 20 Hz | <=25 ms | 50 ms | 2 |
| S3 | perception | 30 Hz | <=80 ms | 120 ms | 2 |
| S4 | cognition/planning | 1–5 Hz | <=500 ms | 1000 ms | 1 |
| S5 | background work | best effort | no hard deadline | bounded | 32 |

## Memory and storage policy

For a future 16GB-class development target, the initial working-set ceiling leaves explicit system/recovery headroom. For higher-memory candidates the same principle applies: never design the runtime around total available memory.

Recommended initial storage is 1TB NVMe, with controlled log rotation and substantial recovery/dataset headroom.

## Queue policy

Production queues must be bounded. Disposable sensor work should prefer `DROP_OLDEST` or `COALESCE`; safety/control overflow is a failure condition rather than permission to grow indefinitely.

## Power and thermal policy

The recovered branch's 25W/40W compute calculations remain useful as a **methodology**, but the actual compute rail, battery, DC/DC and cooling system must be recalculated after AGX Orin/Thor selection. Compute power is not total robot power: motors, drivers, sensors, networking and conversion losses must be included.

## Required measurements

Before validation, record CPU/GPU utilization, memory, storage, queue depth, p50/p95/p99/max latency, jitter, deadline misses, throughput, stale/dropped work, power, temperature and recovery behavior under representative and constrained loads.

## Acceptance sequence

```text
B1 unit benchmark
  ↓
B2 pipeline benchmark
  ↓
B3 sensor-to-action benchmark
  ↓
B4 full concurrent load
  ↓
B5 constrained/degraded load
  ↓
B6 fault injection
  ↓
B7 long-duration soak
```

## Definition of done

ARCH-CLOSE-007 becomes `VALIDATED` only when the selected hardware is documented, machine-readable budgets are enforced, runtime telemetry covers every required dimension, representative full-load benchmarks pass, thermal/power behavior is measured, fault/recovery scenarios pass, and long-duration soak demonstrates bounded resource growth.
