# Novi — Hardware Validation & Testing Baseline

**Date:** 2026-08-17  
**Status:** P0 validation baseline

## 1. Purpose

Define the validation program required before Novi moves from software/simulation to physical actuation.

Hardware validation is not a final checkbox. It is a progressive gate from component testing through long-duration autonomous operation.

---

# 2. Validation hierarchy

```text
Component
   ↓
Subsystem
   ↓
Hardware-in-the-loop
   ↓
System integration
   ↓
Controlled physical operation
   ↓
Safety validation
   ↓
Long-duration autonomy
```

---

# 3. Component validation

Every selected component must be tested for:

- interface;
- driver;
- power;
- thermal;
- timing;
- performance;
- failure behavior;
- recovery;
- calibration;
- documentation/license where software is involved.

---

# 4. Sensor validation

For each sensor measure:

- accuracy;
- latency;
- update rate;
- timestamp quality;
- synchronization;
- noise;
- calibration stability;
- environmental sensitivity;
- dropout rate;
- failure detection.

## Sensor fusion validation

Test:

- missing camera;
- missing depth;
- missing LiDAR;
- IMU dropout;
- stale timestamps;
- calibration drift;
- contradictory sensor measurements.

Novi must degrade explicitly rather than silently trusting corrupted data.

---

# 5. Compute validation

Measure the real workload on candidate edge hardware:

- LLM latency P50/P95/P99;
- VLM latency;
- perception throughput;
- sensor processing throughput;
- memory usage;
- GPU utilization;
- CPU utilization;
- storage throughput;
- power;
- thermal throttling;
- startup/recovery time.

The benchmark must run representative Novi workloads rather than synthetic GPU benchmarks alone.

---

# 6. Actuator validation

For every actuator:

- command accuracy;
- position accuracy;
- velocity accuracy;
- current behavior;
- load/torque response;
- temperature;
- limit enforcement;
- watchdog behavior;
- communication loss;
- emergency stop;
- stall detection.

---

# 7. Power validation

Test:

- idle consumption;
- cognition workload;
- perception workload;
- peak actuator load;
- simultaneous compute + actuator load;
- charging;
- low-battery behavior;
- brownout behavior;
- power-rail stability;
- BMS protection;
- emergency shutdown.

---

# 8. Thermal validation

Test:

- idle;
- nominal workload;
- sustained maximum workload;
- charging;
- maximum actuator activity;
- combined worst-case workload;
- ambient temperature variation;
- cooling failure;
- thermal throttling;
- safe shutdown.

The thermal system must protect the robot even if the AI software is unavailable.

---

# 9. Safety validation

The following must be independently tested:

- physical emergency stop;
- motor-power isolation;
- hardware watchdog;
- actuator disable;
- over-current protection;
- over-temperature protection;
- battery protection;
- communication loss;
- ROS 2 process crash;
- cognition process crash;
- GPU failure;
- model failure;
- malformed action proposal;
- stale sensor data;
- localization failure.

A failed AI component must result in a safe state, not unrestricted physical behavior.

---

# 10. HIL validation

HIL should connect real hardware interfaces to simulation/control workloads before full physical autonomy.

Examples:

```text
real motor controller + simulated world
real sensors + simulated cognition
real compute + simulated sensors
real battery/power telemetry + simulated workload
```

HIL should verify interface timing, driver behavior, controller behavior and recovery semantics.

---

# 11. Simulation-to-real validation

For each learned or perception-dependent capability:

```text
Simulation
 ↓
Simulation benchmark
 ↓
Domain variation
 ↓
SIL
 ↓
HIL
 ↓
Controlled physical test
 ↓
Real-world benchmark
 ↓
Drift analysis
 ↓
Promotion / rejection
```

Simulation evidence must remain tagged as simulated and must never be counted as independent real-world evidence.

---

# 12. Fault-injection matrix

Required fault classes:

| Fault | Expected behavior |
|---|---|
| Camera loss | degraded perception |
| LiDAR loss | reduced spatial confidence/navigation degradation |
| IMU loss | degraded localization |
| Encoder loss | conservative/limited motion |
| Microphone loss | voice capability degraded |
| GPU failure | fallback/degraded mode |
| LLM timeout | deterministic fallback / no unsafe action |
| Memory unavailable | safe degraded cognition |
| Storage full | controlled retention/degradation |
| Network loss | offline operation continues |
| ROS node crash | supervised recovery |
| Controller failure | actuator safe state |
| Battery low | reduced workload / safe return or shutdown |
| Thermal high | workload reduction / safe state |
| E-stop | immediate actuator disable |

---

# 13. Long-duration testing

Before physical autonomy is considered reliable, run repeated long-duration tests measuring:

- uptime;
- restart recovery;
- memory growth;
- storage growth;
- event-log growth;
- model-call failures;
- sensor dropouts;
- planner failures;
- action failures;
- thermal drift;
- battery behavior;
- degradation transitions;
- autonomous goal completion.

The benchmark must include days/weeks of simulated or controlled operation before claiming long-term reliability.

---

# 14. Release gates

## Gate H0 — component

All required components pass electrical/interface/driver tests.

## Gate H1 — subsystem

Sensors, compute, power, control and safety subsystems operate independently.

## Gate H2 — HIL

Real hardware interfaces work against controlled simulation.

## Gate H3 — controlled motion

Robot can move under deterministic controller/safety supervision with no autonomous high-level actuation.

## Gate H4 — bounded autonomy

Novi can execute explicitly bounded autonomous tasks under supervision.

## Gate H5 — extended autonomy

Novi demonstrates stable perception, cognition, navigation, recovery and safety over long-duration tests.

---

# 15. Required evidence package

Every hardware release should produce:

- BOM version;
- wiring/harness version;
- firmware versions;
- calibration versions;
- software version;
- model versions;
- test environment;
- test results;
- traces/logs;
- power/thermal results;
- safety results;
- known limitations;
- approval/rejection decision.

---

# 16. Final rule

> **No physical autonomy capability is considered ready because it worked once. It is ready only when its normal behavior, failure behavior, recovery behavior, safety behavior and measured performance are documented and repeatable.**
