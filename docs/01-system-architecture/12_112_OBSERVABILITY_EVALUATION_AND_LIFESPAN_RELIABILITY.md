# 112 — Observability, Evaluation & Lifespan Reliability

**Status:** P1 normative architecture foundation  
**Depends on:** 00–111

## 1. Purpose

Define how Novi measures what it is doing, whether it is healthy, whether it is meeting requirements, and whether behavior remains reliable over long periods.

Observability is not only logs. It must connect runtime measurements to architecture, cognition, hardware, models, safety and recovery.

## 2. Core telemetry model

```text
SENSOR
 ↓
PERCEPTION
 ↓
EVIDENCE
 ↓
WORLD MODEL
 ↓
MEMORY / RETRIEVAL
 ↓
REASONING
 ↓
POLICY
 ↓
SAFETY
 ↓
ACTION
 ↓
OUTCOME
```

A consequential operation should be traceable across this chain where privacy permits.

## 3. Telemetry classes

### Metrics

- latency;
- throughput;
- queue depth;
- CPU;
- GPU;
- memory;
- storage;
- power;
- thermal;
- network;
- error rate;
- retry rate;
- recovery time;
- sensor health.

### Logs

Structured operational events with severity, component, version, correlation and relevant context.

### Traces

Cross-component causal execution paths.

### Audit records

Security, authorization, policy, safety, data lifecycle and consequential-action records.

## 4. Measured vs derived

Every metric should be classifiable as:

```text
MEASURED
DERIVED
ESTIMATED
SIMULATED
PREDICTED
```

Physical performance claims require measured evidence.

## 5. NVIDIA runtime observability

NVIDIA DeepStream documentation includes component-level latency measurement facilities, supporting the architecture's requirement to instrument internal pipeline stages rather than only measuring end-to-end latency. citeturn0search10

NVIDIA Jetson/Isaac ROS tooling also exposes platform health and diagnostics that should be integrated into Novi's hardware-health model where adopted. citeturn1search4

## 6. Health model

Every important component reports:

```text
HEALTHY
DEGRADED
FAILED
RECOVERING
DISABLED
UNKNOWN
```

Hardware health additionally tracks:

- thermal limitation;
- power limitation;
- calibration required;
- communication loss.

## 7. SLO/acceptance model

Each production capability should define:

- availability target;
- latency target;
- correctness target;
- resource budget;
- recovery target;
- safety requirement;
- privacy requirement.

Numbers are workload-specific and must come from benchmarks rather than invented global constants.

## 8. Lifespan reliability

Long-duration evaluation must measure:

- memory growth;
- event growth;
- storage growth;
- model/runtime leaks;
- sensor drift;
- thermal drift;
- repeated restart behavior;
- degradation/recovery transitions;
- autonomous goal continuity;
- data integrity.

## 9. Evaluation runs

Every evaluation run has:

```text
run_id
scenario/version
source commit
model versions
runtime versions
hardware
configuration
seed
start/end
raw artifacts
metrics
verdict
limitations
```

## 10. Regression evaluation

A new software/model/hardware version must be compared against a known baseline.

Regression suites should cover:

- cognition;
- memory;
- perception;
- navigation;
- tools;
- safety;
- recovery;
- resource usage.

## 11. Alerting

Alerts must be tied to actionable conditions, e.g.:

- safety controller fault;
- thermal runaway risk;
- storage exhaustion;
- sensor synchronization failure;
- model latency exceeding bound;
- repeated action rejection;
- recovery loop;
- unauthorized access.

## 12. Privacy-aware observability

Telemetry must not become an uncontrolled copy of personal data.

Use:

- metadata-first traces;
- payload minimization;
- redaction;
- access control;
- retention policies;
- privacy-aware sampling.

## 13. Evaluation hierarchy

```text
UNIT
 ↓
INTEGRATION
 ↓
SYSTEM
 ↓
SIL
 ↓
HIL
 ↓
CONTROLLED PHYSICAL
 ↓
LONG-DURATION AUTONOMY
```

## 14. Reliability evidence

A reliability claim requires repeated evidence. A single successful execution is not a reliability demonstration.

## 15. Failure observability

Failures must expose:

- detection time;
- classification;
- affected scope;
- last known good state;
- recovery action;
- recovery result;
- remaining degradation;
- operator escalation if required.

## 16. Final rule

> **If Novi cannot measure a critical behavior, it cannot reliably claim that behavior works.**
