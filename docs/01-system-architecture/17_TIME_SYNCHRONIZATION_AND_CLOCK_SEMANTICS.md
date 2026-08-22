# 17 — Time Synchronization & Clock Semantics

**Status:** SUPERSEDED — see `19_TIME_SYNCHRONIZATION_AND_CLOCK_SEMANTICS.md` (canonical authority)  
**Date:** 2026-08-18 (superseded 2026-08-22)  
**Purpose:** Define time semantics across sensors, ROS 2, cognition, simulation, logging, memory, hardware and future distributed execution.
**Reason for supersession:** duplicate time-sync authority consolidated (gap-analysis Step 0). Exact-path references to this file must be updated to the canonical document; this file is retained for historical traceability only.

## 1. Why time is architectural

Novi is a multimodal autonomous system. Incorrect timestamps can create false causality, bad sensor fusion, incorrect temporal memory, unsafe control decisions and invalid evaluation results.

Time is therefore part of every important data contract.

## 2. Time domains

Novi must distinguish:

```text
WALL / UTC TIME
MONOTONIC PROCESS TIME
SYSTEM CLOCK
SENSOR CLOCK
HARDWARE TIMESTAMP
ROS TIME
SIMULATION TIME
EVENT TIME
RECORDING TIME
```

These are not interchangeable.

## 3. Event time vs recording time

Every consequential event should distinguish:

```text
occurred_at
recorded_at
processed_at
```

`occurred_at` represents when the represented event happened. `recorded_at` represents when Novi durably recorded it.

## 4. Monotonic time

Durations, timeout and latency measurement should use a monotonic clock where the platform supports it.

Wall-clock adjustments must not create negative elapsed durations.

## 5. UTC/wall-clock time

Wall-clock timestamps are required for:

- human-visible dates;
- external event correlation;
- legal/audit records where applicable;
- cross-system records.

Clock synchronization status must be observable.

## 6. Sensor timestamps

Each sensor should expose its native timestamp where available.

The acquisition pipeline must record:

```text
sensor_time
host_receive_time
processing_time
```

The system must not silently replace a sensor timestamp with host receipt time without recording the transformation.

## 7. Calibration/time relationship

Calibration records must identify the timing assumptions under which calibration was obtained.

A calibration or synchronization change is a versioned configuration event.

## 8. Camera synchronization

Multi-camera workloads must define whether they require:

- frame-level synchronization;
- bounded timestamp skew;
- hardware triggering;
- hardware timestamps;
- software alignment.

The required level is workload-specific and must be measured.

## 9. LiDAR/IMU synchronization

Sensor fusion must account for:

- timestamp offset;
- drift;
- transport latency;
- sensor update rate;
- dropped samples.

A fusion algorithm must not assume perfect synchronization unless validated.

## 10. Audio timing

Audio events must retain enough timing metadata to correlate speech/acoustic events with visual and motion events.

## 11. ROS 2 time

ROS time must be treated as an explicit runtime time domain.

Simulation may use simulated time; physical operation must define its relationship to system time and sensor timestamps.

## 12. Simulation time

Simulation records must identify:

- simulation clock mode;
- simulator version;
- scenario/world version;
- seed;
- simulation start/end;
- mapping to wall-clock execution time where needed.

A simulated timestamp must never be presented as historical physical time.

## 13. Time synchronization strategy

The physical design must evaluate:

```text
Software clock synchronization
Hardware timestamping
PTP
NTP
Sensor-trigger synchronization
ROS time
```

PTP should be considered where sensor fusion bandwidth/precision requires sub-millisecond synchronization, but adoption requires a measured requirement and hardware support.

## 14. Clock hierarchy

The eventual physical architecture should document a clear hierarchy such as:

```text
trusted system/reference clock
        ↓
edge host clock
        ↓
ROS time
        ↓
sensor acquisition timestamps
```

The actual hierarchy is hardware-dependent and must be frozen by the hardware/time-sync ADR.

## 15. Drift detection

Novi should monitor synchronization quality using:

- offset;
- drift rate;
- missed synchronization;
- timestamp discontinuity;
- stale samples;
- out-of-order samples.

## 16. Stale data

Every time-sensitive input should have a freshness policy.

```text
FRESH
 ↓
STALE
 ↓
INVALID
```

A stale sensor must not be silently treated as current evidence.

## 17. Out-of-order data

The event layer must support out-of-order arrival.

Ordering should use semantic timestamps and causal metadata rather than transport arrival order alone.

## 18. Time uncertainty

Where timing precision is uncertain, the uncertainty should be represented rather than hidden.

Example:

```text
measurement_time = T
uncertainty = ±ΔT
```

## 19. Distributed time

Future distributed Novi nodes must not assume perfectly synchronized clocks.

Causality must use event metadata/causal mechanisms from 107–109 where necessary.

## 20. Timeout semantics

Timeouts should use monotonic elapsed time and include:

- start time;
- deadline;
- cancellation state;
- timeout reason.

## 21. Performance measurement

Latency measurements should specify boundaries, e.g.:

```text
sensor capture → perception output
perception output → evidence
request → model first token
request → model completion
proposal → policy
policy → safety
safety → actuator command
command → observed outcome
```

## 22. Time and safety

Safety decisions requiring freshness must validate both:

- state version;
- state age.

A current version with an expired timestamp can still be unsafe.

## 23. Time and memory

Temporal memory must retain:

- event time;
- recording time;
- validity interval;
- temporal uncertainty where relevant.

## 24. Time and evaluation

Benchmarks must record synchronized timing metadata so latency and ordering comparisons are meaningful.

## 25. NVIDIA validation

NVIDIA Isaac Sim's ROS 2 documentation explicitly addresses ROS 2 distribution compatibility and environment setup, while Isaac ROS provides platform-specific robotics software with tested ROS 2 configurations. citeturn0search4turn0search6

NVIDIA documentation is therefore used to validate the **software compatibility layer**; the exact physical synchronization design remains a Novi hardware requirement to be validated against the selected sensors and compute platform.

## 26. Final rule

> **A timestamp is data with semantics, not just a field containing a date.**

Every critical subsystem must document which clock it uses, what the timestamp means, its uncertainty, synchronization assumptions and freshness policy.
