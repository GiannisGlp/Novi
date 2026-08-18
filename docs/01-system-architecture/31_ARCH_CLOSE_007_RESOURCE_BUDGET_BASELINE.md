# 31 — ARCH-CLOSE-007 Resource Budget Baseline

**Status:** Baseline defined — hardware validation pending  
**Priority:** P0  
**Authority:** System Architecture  
**Scope:** Stage-1 local/offline Novi runtime and first small autonomous robot target

## 1. Purpose

Turn the existing runtime resource architecture into an explicit, measurable Stage-1 budget envelope.

These values are **engineering targets**, not claims of achieved performance. They become validated only after measurement on the selected hardware under representative load.

The governing architecture requires bounded latency, explicit CPU/GPU/RAM/storage/queue/power/thermal budgets, graceful degradation and end-to-end measurement.

## 2. Recommended compute target

For the first AI-capable physical Novi prototype, the recommended compute class is **NVIDIA Jetson Orin NX 16GB**.

Rationale:

- 16GB unified LPDDR5 is materially safer for concurrent robotics + perception + local AI than an 8GB target.
- Current NVIDIA specifications list up to 157 INT8 TOPS in Super mode.
- Current supported reference power modes include 10W, 15W, 25W and 40W/MAXN SUPER modes depending on software configuration.
- The module is designed for small-form-factor autonomous machines.

The Orin Nano Super 8GB remains a useful lower-cost development option, but it is not the baseline target for the full Novi runtime because memory headroom is the limiting resource before raw AI throughput.

The first production-like budget should therefore be validated against Orin NX 16GB rather than optimized around the development Mac.

## 3. Stage-1 resource envelope

| Resource | Target | Minimum acceptable | Degraded threshold | Failure threshold |
|---|---:|---:|---:|---:|
| CPU total | <=70% sustained | <=80% | >80% sustained | >90% sustained |
| GPU utilization | <=75% sustained | <=85% | >85% | >95% with critical work affected |
| Unified RAM | <=12GB working set | <=13GB | >13GB | >14GB / allocation failure |
| GPU/model memory allocation | <=10GB | <=12GB | >12GB | >14GB / OOM risk |
| Runtime storage | <=200GB active | <=300GB | >300GB | <50GB free |
| Critical queue depth | bounded per contract | no unbounded growth | repeated saturation | overflow affecting S0/S1 |
| Compute module power | 25W sustained target | 40W test envelope | thermal/power throttling | unsafe thermal/power state |
| SoC temperature | <80C target | <90C | >=90C | hardware protection threshold |

The memory values deliberately leave substantial headroom for the OS, ROS 2, drivers, caches, model loading, sensor buffers and recovery.

## 4. Execution-class latency budgets

Initial targets for the first physical prototype:

| Class | Representative workload | Target frequency | p99 latency | Maximum tolerated latency | Queue |
|---|---|---:|---:|---:|---:|
| S0 | safety watchdog / safety boundary | 100 Hz | <=2 ms | 5 ms | 1 |
| S1 | control command interface | 50 Hz | <=5 ms | 10 ms | 1 |
| S2 | reactive obstacle/person response | 20 Hz | <=25 ms | 50 ms | 2 |
| S3 | perception pipeline | 30 Hz | <=80 ms | 120 ms | 2 |
| S4 | cognition/planning proposal | 1–5 Hz | <=500 ms | 1000 ms | 1 |
| S5 | indexing/logging/consolidation | best effort | no hard deadline | bounded by scheduler | bounded |

These numbers are not safety certification values. They are initial acceptance targets to be replaced or tightened after functional and physical measurements.

## 5. CPU reservation policy

Until measured otherwise, preserve approximately 30% CPU capacity as system/safety headroom.

Recommended scheduling intent:

```text
S0/S1: reserved capacity; never compete directly with background work
S2/S3: bounded worker pools
S4: elastic, deadline-aware
S5: opportunistic and throttled
```

A benchmark must record per-process and per-thread CPU utilization, not only system-wide utilization.

## 6. GPU policy

GPU capacity is treated as shared infrastructure.

Target:

```text
steady-state GPU <= 75%
short bursts <= 85%
critical workload admission before optional workload
```

No large-model inference, mapping, rendering or background workload may be admitted solely because free GPU memory exists.

Admission requires latency, GPU utilization, memory, power, thermal and concurrency evidence.

## 7. Memory calculation

For the 16GB unified-memory target:

```text
16GB total
- 12GB runtime working-set ceiling
= 4GB recovery/system reserve
```

The model/runtime allocation target is:

```text
<=10GB for model + inference-related GPU memory
>=6GB remaining for OS, ROS 2, buffers, caches and other processes
```

A model that requires the full available memory is therefore not admitted as a default runtime model.

## 8. Storage calculation

Baseline physical storage:

```text
1TB NVMe recommended
```

Suggested allocation:

```text
200GB active runtime + models + logs
200GB reserved for datasets/test artifacts
600GB free/recovery/rotation/headroom
```

The runtime must rotate logs and reject uncontrolled growth before storage exhaustion.

## 9. Queue policy

No production queue may be unbounded.

Initial queue targets:

```text
S0 safety events       depth 1
S1 control commands    depth 1
S2 reactive samples    depth 2
S3 camera/perception   depth 2
S4 cognitive requests  depth 1
S5 background          bounded and throttled
```

For disposable sensor data, prefer `DROP_OLDEST` or `COALESCE` so the system processes the latest valid state rather than stale frames.

For safety/control data, overflow is a failure condition rather than permission to grow the queue.

## 10. Power calculation

The Orin NX 16GB currently has reference modes up to 40W in Super mode, while the conventional 25W mode is the preferred initial sustained target.

Compute-only electrical requirement at a nominal 12V rail:

```text
25W / 12V = 2.08A
40W / 12V = 3.33A
```

With 25% electrical headroom:

```text
25W × 1.25 = 31.25W
31.25W / 12V = 2.60A
```

For a 40W stress envelope:

```text
40W × 1.25 = 50W
50W / 12V = 4.17A
```

Therefore the compute power rail should initially be designed for **at least 12V / 5A (60W)**, independently of the motor power rail.

This is intentionally not the total robot power supply rating. Motors, motor drivers, sensors, USB devices and DC/DC losses must be added separately after their actual specifications are selected.

## 11. Battery impact

For a hypothetical 12V 10Ah battery (120Wh nominal), compute-only runtime would be approximately:

```text
120Wh / 25W = 4.8h
120Wh / 40W = 3.0h
```

Real runtime will be lower because the robot also powers motors, sensors, regulators and other electronics.

This calculation is included to establish the method; the actual battery must be sized from measured motor duty cycle plus the compute/sensor budget.

## 12. Thermal policy

NVIDIA's Orin NX thermal guidance requires the system thermal solution to keep the SoC below its specified operating limit. Novi therefore uses a substantially lower software engineering target:

```text
<80C      normal target
80–90C    thermal warning / monitor closely
>=90C     enter degradation policy
>=99C     not an acceptable sustained operating point
105C      hardware shutdown/protection region; never a normal target
```

The robot enclosure and cooling system must be validated under sustained 25W compute load and representative ambient conditions.

## 13. Hardware required to close the budget

Minimum measurement hardware:

1. Jetson Orin NX 16GB compute module or equivalent evaluation platform.
2. Compatible carrier board with required USB, Ethernet, CSI, GPIO, CAN and PCIe connectivity.
3. Active thermal solution sized for sustained compute load.
4. NVMe SSD, target 1TB.
5. Independent compute-rail voltage/current measurement.
6. At least one board/SoC temperature telemetry path plus enclosure/ambient temperature measurement.
7. Camera/perception sensor representative of the intended runtime workload.
8. IMU and wheel/odometry input for representative control/perception load.
9. Motor controller interface for end-to-end timing tests; physical actuation remains behind the existing safety boundary.
10. Host tooling to record CPU, GPU, memory, storage, queue, latency, power and thermal telemetry.

## 14. What is still unknown

The following cannot be honestly finalized from architecture documents alone:

- motor peak/continuous power;
- motor driver power;
- battery voltage/capacity;
- sensor power;
- camera/LiDAR bandwidth;
- actual model latency;
- actual model memory footprint;
- ROS 2/DDS transport overhead;
- enclosure thermal resistance;
- real motor duty cycle;
- total robot runtime.

These require actual component selection and measurement.

## 15. Acceptance methodology

ARCH-CLOSE-007 progresses through:

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

Each stage records p50/p95/p99/max latency, jitter, deadline misses, throughput, dropped/stale work, CPU/GPU/RAM usage, power, temperature, queue depth and recovery time.

## 16. Definition of done

ARCH-CLOSE-007 becomes `VALIDATED` only when:

- the selected hardware is documented;
- machine-readable budgets exist;
- runtime telemetry reports every required dimension;
- critical queue limits are enforced;
- deadline misses are detected;
- resource admission/degradation is executable;
- representative full-load benchmarks pass;
- thermal/power behavior is measured;
- fault and recovery scenarios are tested;
- long-duration soak shows bounded memory and queue growth.

Until then this document is a **calculated engineering baseline**, not a claim that the robot has achieved these numbers.
