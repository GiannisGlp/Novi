# 30 — ARCH-CLOSE-006 Time Synchronization Implementation Gate

**Status:** Implementation gate defined — runtime integration pending  
**Priority:** P0  
**Authority:** System Architecture  
**Normative source:** `19_TIME_SYNCHRONIZATION_AND_CLOCK_SEMANTICS.md`

## 1. Purpose

Turn Novi's existing time architecture into executable invariants before timing-sensitive runtime work begins.

The architecture already distinguishes wall/system time, monotonic/steady time, ROS/simulation time and hardware/sensor time. It also requires preservation of capture/occurrence time separately from receipt, processing and commit time. fileciteturn195file0

This gate validates the deterministic software semantics. It is **not** evidence of physical clock synchronization accuracy, sensor hardware timestamp accuracy, or ROS/Isaac Sim timing behavior.

## 2. Stage-1 clock policy

| Clock/domain | Novi use | Rule |
|---|---|---|
| Wall/system | external-world and human/audit timestamps | never use for elapsed-time deadlines |
| Monotonic/steady | durations, deadlines, watchdogs, latency | authoritative for elapsed-time decisions |
| Event/occurrence | when an event/measurement occurred | preserve source semantics |
| Receipt/record | when Novi received/committed data | never overwrite occurrence time |
| ROS/simulation | simulated world and ROS time | explicit configuration at the runtime boundary |
| Sensor/hardware | device-generated measurement time | preserve source and synchronization status |

## 3. Required invariants

### T-001 — Clock-domain explicitness
Every time-bearing runtime value must identify its clock domain or semantic role.

### T-002 — Monotonic deadlines
Timeouts, watchdogs and elapsed durations must be evaluated from monotonic time.

### T-003 — Wall-clock immunity
A wall-clock adjustment must not alter an already-established monotonic deadline.

### T-004 — Timestamp provenance
Occurrence/capture time must remain distinguishable from receipt/processing/record time.

### T-005 — Unknown synchronization is not synchronized
An unknown or degraded clock relationship must not be treated as synchronized.

### T-006 — Stale-data rejection
A time-sensitive consumer must reject or classify data as unknown when compatible clock age cannot be established.

### T-007 — Out-of-order tolerance
Arrival order must not be assumed to equal occurrence order.

### T-008 — Causality over ambiguous timestamps
When clocks are insufficiently synchronized, explicit causation/correlation/sequence metadata takes precedence over inferred global timestamp ordering.

### T-009 — Expiry
Validity windows must be evaluated against a compatible clock and must reject expired authorization/action state.

### T-010 — Simulation separation
Simulation time must not be silently substituted for wall or monotonic time, and vice versa.

## 4. Failure states

The runtime must expose at least:

```text
SYNCHRONIZED
DEGRADED
UNSYNCHRONIZED
UNKNOWN
```

For safety-sensitive timing, `UNSYNCHRONIZED` and `UNKNOWN` are fail-closed unless the owning safety specification explicitly permits a degraded behavior.

## 5. Runtime interface shape

The implementation layer should expose a narrow clock adapter rather than allowing arbitrary modules to select clocks independently:

```text
ClockProvider
 ├── wall_now()
 ├── monotonic_now()
 ├── domain_now(domain)
 └── synchronization_status(domain)
```

Consumers should receive a clock view appropriate to their responsibility. Direct platform-clock access outside the adapter should be treated as an architecture violation once the runtime implementation exists.

## 6. Measurement model

For sensor/event data, preserve at least:

```text
occurrence/capture time
receipt time
processing time
record/commit time
clock domain/source
synchronization status
uncertainty where material
```

The architecture explicitly warns that a timestamp without a defined clock domain is insufficient evidence of temporal ordering. fileciteturn195file0

## 7. Physical/simulation follow-up

The following remain separate validation layers:

- platform clock characterization;
- sensor timestamp accuracy;
- synchronization protocol accuracy;
- ROS `/clock` and `use_sim_time` behavior;
- simulation pause/reset/replay;
- hardware clock drift;
- physical safe-stop timing.

Those cannot be closed by a unit test alone.

## 8. Definition of done

ARCH-CLOSE-006 can move from `DEFINED` to `VALIDATED` only when:

1. the executable semantic gate passes;
2. the runtime clock adapter exists;
3. canonical time-bearing contracts preserve required provenance;
4. stale/expiry behavior is tested;
5. simulation/ROS behavior has a dedicated integration test;
6. measured timing/synchronization error budgets exist where consequential;
7. validation evidence is recorded.

Until then, ARCH-CLOSE-006 remains open in the architecture closure register.
