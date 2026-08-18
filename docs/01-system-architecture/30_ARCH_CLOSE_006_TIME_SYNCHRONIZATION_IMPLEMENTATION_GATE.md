# 30 — ARCH-CLOSE-006 Time Synchronization Implementation Gate

**Status:** Implementation gate defined — runtime integration pending  
**Priority:** P0  
**Authority:** System Architecture

## Purpose

Turn Novi's existing time architecture into executable invariants before timing-sensitive runtime work begins. This gate validates deterministic software semantics; it does not claim physical clock synchronization accuracy, sensor timestamp accuracy, or ROS/Isaac Sim timing behavior.

## Stage-1 clock policy

| Clock/domain | Novi use | Rule |
|---|---|---|
| Wall/system | external-world and human/audit timestamps | never use for elapsed-time deadlines |
| Monotonic/steady | durations, deadlines, watchdogs, latency | authoritative for elapsed-time decisions |
| Event/occurrence | when an event/measurement occurred | preserve source semantics |
| Receipt/record | when Novi received/committed data | never overwrite occurrence time |
| ROS/simulation | simulated world and ROS time | explicit configuration at runtime boundary |
| Sensor/hardware | device-generated measurement time | preserve source and synchronization status |

## Required invariants

- **T-001:** Every time-bearing runtime value identifies its clock domain or semantic role.
- **T-002:** Timeouts, watchdogs and elapsed durations use monotonic time.
- **T-003:** Wall-clock adjustment cannot alter an established monotonic deadline.
- **T-004:** Occurrence/capture time remains distinct from receipt/processing/record time.
- **T-005:** Unknown/degraded synchronization is never treated as synchronized.
- **T-006:** Time-sensitive consumers reject or classify data when compatible age cannot be established.
- **T-007:** Arrival order is not assumed to equal occurrence order.
- **T-008:** Explicit causation/correlation/sequence metadata takes precedence when timestamps cannot establish global order.
- **T-009:** Validity windows use a compatible clock and reject expired state.
- **T-010:** Simulation time is never silently substituted for wall or monotonic time.

## Failure states

```text
SYNCHRONIZED
DEGRADED
UNSYNCHRONIZED
UNKNOWN
```

For safety-sensitive timing, `UNSYNCHRONIZED` and `UNKNOWN` are fail-closed unless the owning safety specification explicitly permits degraded behavior.

## Runtime interface shape

```text
ClockProvider
 ├── wall_now()
 ├── monotonic_now()
 ├── domain_now(domain)
 └── synchronization_status(domain)
```

Direct platform-clock access outside the adapter becomes an architecture violation once runtime implementation exists.

## Measurement model

Preserve at least:

```text
occurrence/capture time
receipt time
processing time
record/commit time
clock domain/source
synchronization status
uncertainty where material
```

## Physical/simulation follow-up

Separate validation is required for platform clock characterization, sensor timestamp accuracy, synchronization protocol accuracy, ROS `/clock` and `use_sim_time`, simulation pause/reset/replay, hardware clock drift and physical safe-stop timing.

## Definition of done

ARCH-CLOSE-006 can move from `DEFINED` to `VALIDATED` only when the executable semantic gate passes, the runtime clock adapter exists, canonical contracts preserve provenance, stale/expiry behavior is tested, simulation/ROS behavior has dedicated integration coverage, consequential timing error budgets are measured, and evidence is recorded.
