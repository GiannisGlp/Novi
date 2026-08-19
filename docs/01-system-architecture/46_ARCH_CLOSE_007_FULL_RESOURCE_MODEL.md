# 46 — ARCH-CLOSE-007 Full Robot Resource & Autonomy Model

**Status:** MODEL DEFINED — hardware measurements pending  
**Priority:** P0  
**Authority:** System Architecture  
**Scope:** Full Novi robot resource accounting, including 8–10 hour mobile operation and stationary operation.

## 1. Purpose

Compute is only one part of Novi's resource envelope. The final robot budget must account for compute, sensors, storage, networking, audio, power conversion, thermal management and locomotion, with enough reserve to remain stable over the intended operating period.

## 2. Power accounting model

Total electrical demand is:

```text
P_total = P_compute
        + P_sensors
        + P_audio
        + P_network
        + P_storage
        + P_control
        + P_actuation
        + P_thermal
        + P_conversion_loss
        + P_auxiliary
```

For battery sizing, use measured average power and explicitly model peak power separately.

```text
E_required = P_average × runtime_hours
E_battery_nominal >= E_required / usable_fraction
```

Then add engineering reserve rather than treating 100% of nominal battery energy as usable.

## 3. 8–10 hour mobile target

The mobile architecture target is **8–10 hours** of useful autonomous operation under a defined representative workload.

We must report at least:

- average power;
- peak power;
- idle/standby power;
- compute-heavy power;
- sensor-heavy power;
- locomotion power;
- thermal-system power;
- conversion losses;
- battery usable energy;
- reserve energy;
- measured runtime.

The final battery size is intentionally deferred until these values are measured on the selected compute and drive system.

## 4. Stationary mode

A stationary Novi configuration may be continuously mains powered. In this configuration:

- battery capacity is not the primary operating constraint;
- UPS/ride-through may still be required;
- thermal and peak electrical load remain first-class constraints;
- compute selection may favor higher sustained performance;
- power supply, cabling, grounding and cooling must be sized for sustained peak workloads.

Thor remains a viable candidate for this profile without forcing the mobile robot to adopt the same compute envelope.

## 5. Sensor resource accounting

The planned sensor set must include, where applicable:

- GNSS/GPS;
- IMU: accelerometer + gyroscope + magnetometer where appropriate;
- LiDAR;
- multiple RGB/depth cameras;
- thermal camera/sensor;
- night-vision camera;
- wheel/actuator encoders;
- speakers;
- multiple microphones for direction-of-arrival/localization;
- ambient/environmental sensors as required;
- network and time-synchronization interfaces.

For each sensor record:

```text
quantity
interface
nominal power
peak power
data rate
compute load
storage rate
latency
synchronization requirements
physical/thermal constraints
```

## 6. Storage accounting

Storage follows the mandatory 2× planning rule established by ARCH-CLOSE-007:

```text
primary storage requirement × 2 = minimum planned storage capacity
```

The primary requirement must include:

- durable Novi state;
- models;
- logs/audit data;
- telemetry;
- retained sensor recordings;
- maps;
- replay/simulation data;
- caches and temporary data;
- filesystem/database overhead.

After applying the 2× rule, select the next practical SSD tier. The existing 1 TB NVMe recommendation remains a starting platform recommendation, not a final capacity decision. 

## 7. Thermal accounting

Thermal design must cover:

- sustained compute load;
- peak compute load;
- SSD heat;
- power-conversion heat;
- motor/controller heat;
- enclosure ambient temperature;
- airflow or passive conduction;
- fan power if used;
- thermal throttling thresholds;
- sensor operating-temperature limits.

Thermal validation must measure steady-state and transient behavior, not only idle temperature.

## 8. Compute resource accounting

The current provisional baseline remains:

| Resource | Target | Minimum acceptable | Degraded |
|---|---:|---:|---:|
| CPU sustained | <=70% | <=80% | >80% |
| GPU sustained | <=75% | <=85% | >85% |
| Unified RAM | <=12 GB | <=13 GB | >13 GB |
| Model/inference allocation | <=10 GB | <=12 GB | >12 GB |
| Active runtime storage | <=200 GB | <=300 GB | >300 GB |
| Compute power | 25 W | 40 W test envelope | throttling |
| SoC temperature | <80 C | <90 C | >=90 C |

These are provisional and will be measured/replaced after hardware selection. fileciteturn386file0

## 9. Network and communication budget

Account for:

- Ethernet/Wi-Fi;
- camera/LiDAR transport;
- sensor buses;
- actuator buses;
- time synchronization;
- telemetry;
- remote diagnostics where enabled.

Record bandwidth, peak bandwidth, latency, packet loss tolerance and power draw.

## 10. Locomotion budget

For a mobile robot, actuation is potentially the largest energy consumer and cannot be estimated from compute power.

Measure or model:

- motors at idle;
- straight cruise;
- acceleration;
- turning;
- obstacle negotiation;
- maximum-load case;
- expected duty cycle;
- motor-controller losses.

Battery sizing must use a representative mission profile rather than a compute-only duty cycle.

## 11. Mission-profile calculation

Define at least three profiles:

### M1 — Idle/observation

High sensor availability, low locomotion, normal cognition.

### M2 — Typical autonomous mission

Representative movement, perception, audio and cognition.

### M3 — Stress mission

High perception rate, active locomotion, elevated inference, communication and logging.

The 8–10 hour claim must be tied to a declared mission profile; it must not mean that every conceivable worst-case load runs for ten hours.

## 12. Measurement matrix

Before final hardware selection, collect:

| Dimension | Measurement |
|---|---|
| Compute | CPU/GPU utilization, clocks, memory |
| AI | model latency, throughput, memory, accelerator utilization |
| Sensors | count, data rate, power, latency |
| Storage | write/read rate, capacity growth, temperature |
| Network | bandwidth, latency, packet loss |
| Audio | microphones/speakers power and processing load |
| Actuation | average/peak/duty-cycle power |
| Conversion | DC/DC and PSU efficiency |
| Thermal | temperatures, fan/pump power, throttling |
| Battery | usable energy, current, voltage, temperature |
| Runtime | actual mission duration |

## 13. Hardware comparison rule

AGX Orin 64 GB and Thor remain candidate platforms. The same workload and accounting model must be applied to both.

Do not compare only TOPS or RAM. Compare:

```text
AI workload capacity
+ sensor workload
+ storage
+ power
+ thermal
+ battery consequence
+ physical volume
+ future expansion
```

## 14. Definition of done

ARCH-CLOSE-007 becomes validated only when:

1. a concrete hardware configuration is selected for the tested profile;
2. the full resource telemetry model is implemented;
3. representative mission profiles are benchmarked;
4. CPU/GPU/RAM/storage limits pass;
5. power and thermal limits pass;
6. storage is sized using the 2× backup rule;
7. battery runtime is measured against the declared mission profile;
8. degraded/fault behavior is validated;
9. long-duration soak shows bounded resource growth.

## 15. Architectural invariant

> **Novi's robot budget is a system budget, not a compute budget: energy, thermal capacity, storage recovery reserve, sensors, networking and actuation are first-class resources.**
