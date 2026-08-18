# 44 — ARCH-CLOSE-006 Time Validation Evidence

**Status:** PARTIALLY EVIDENCED — executable semantic gate recorded
**Priority:** P0
**Authority:** System Architecture
**Scope:** Objective evidence for the executable portion of ARCH-CLOSE-006 — Time Synchronization.

## 1. Purpose

This document records executable evidence for Novi's clock/time semantics. It does not claim that physical sensor clocks, multi-machine synchronization, or long-duration drift budgets have been empirically validated.

## 2. Normative baseline

The authoritative time architecture defines distinct wall/system, monotonic/steady, ROS, simulation, and hardware/sensor clock domains. It requires explicit temporal semantics, preserved timestamp provenance, monotonic timing for deadlines/timeouts, explicit simulation-time behavior, and conservative handling of unsynchronized clocks.

## 3. Executable evidence

The integration gate is:

`contracts/tests/integration/test_time_semantics.py`

The gate currently validates:

- wall-clock rollback is not treated as monotonic progression;
- monotonic deadline semantics;
- capture/occurrence and receipt provenance remain distinct;
- unsynchronized clock domains cannot establish global order;
- synchronized timestamps within a compatible domain can establish order;
- measurement-age semantics;
- validity-window semantics;
- simulation time and wall time are not silently treated as one domain;
- causal identifiers remain explicit.

## 4. Evidence interpretation

A passing executable semantic gate demonstrates that the encoded invariants execute successfully on the repository revision under test.

It does **not** demonstrate:

- measured oscillator drift;
- actual sensor clock offset;
- synchronization-loss/recovery performance;
- timestamp uncertainty under physical load;
- ROS 2 `/clock` behavior on an actual simulator;
- multi-machine synchronization;
- hardware timestamp accuracy;
- safety-critical worst-case timing budgets.

Those require platform-specific, simulation, HIL, or physical evidence as applicable.

## 5. Required next evidence

To close ARCH-CLOSE-006, the validation campaign must additionally produce recorded evidence for:

1. clock drift and synchronization error on the selected platform;
2. synchronization loss and recovery;
3. sensor capture-versus-receipt timing;
4. out-of-order and delayed samples;
5. stale-data rejection;
6. ROS `/clock` and `use_sim_time` behavior in the selected simulator profile;
7. pause/resume/reset/replay behavior;
8. watchdog/deadline timing;
9. action expiry;
10. restart/recovery with persisted timestamps;
11. measured timing/resource overhead;
12. explicit error-budget acceptance criteria.

## 6. Closure decision

**ARCH-CLOSE-006 is not COMPLETE.** The semantic/executable layer is evidenced, while empirical synchronization and error-budget evidence remain open.

This matches the architecture closure register: closure requires executed clock/time validation and error-budget evidence, not merely the existence of the architecture document or semantic test.

## 7. Evidence maintenance

Whenever the time-validation gate materially changes, record a successful CI run against the repository revision and update this evidence record with the run/reference, scope, result, and limitations.
