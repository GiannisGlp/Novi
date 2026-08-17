# 05 — Cross-Cutting Requirements

**Status:** P0 normative requirements

These requirements apply across Novi rather than to one subsystem. Every implementation specification must either satisfy them or document an approved exception through an ADR.

## 1. Reliability and Health

Every service/capability exposes health and lifecycle state:

```text
STARTING
READY
RUNNING
DEGRADED
RECOVERING
FAILED
STOPPING
STOPPED
```

Health must be queryable without the primary reasoning model.

## 2. Time Semantics

Events distinguish:

```text
event_time / occurred_at
received_time
processed_time / recorded_at
```

Temporal reasoning must use event time where possible. Clock source, synchronization and uncertainty must be documented by the relevant hardware/robotics domain.

## 3. Identity

Identity results include confidence, source, timestamp and verification status. Identity does not imply authentication or authorization.

## 4. Provenance

Important state, knowledge and decisions retain source information and transformation lineage.

Minimum provenance classes include:

```text
sensor_observation
model_inference
user_statement
owner_verification
external_document
system_generated
simulation
human_decision
```

## 5. Uncertainty

Uncertainty must be explicit where material. A confidence score is not a substitute for required verification.

## 6. Auditability

At minimum audit:

- model invocations;
- tool invocations;
- important knowledge/memory changes;
- schema changes;
- privileged actions;
- policy/safety decisions;
- configuration changes;
- authentication/authorization;
- hardware diagnostics;
- recovery operations;
- data deletion/retention actions.

## 7. Privacy

Sensitive information is classified before storage or processing where practical. Retention, deletion, access and replication behavior are policy-controlled.

## 8. Resource Limits

Every autonomous subsystem has configurable limits for:

- CPU;
- GPU;
- memory;
- storage;
- concurrency;
- queue depth;
- network usage;
- model context;
- action duration;
- retry budget.

## 9. Backpressure

High-frequency streams must not overwhelm cognitive processing. Use queues, sampling, prioritization, aggregation and explicit drop policies.

Dropped data must be observable where it affects correctness.

## 10. Cancellation

Long-running model/tool operations support cancellation. A cancelled/stale operation must not later execute a physical action without fresh authorization and state validation.

## 11. Idempotency

State-changing operations use stable operation IDs where retries are possible. Non-idempotent physical actions require reconciliation/compensation semantics.

## 12. Configuration

Configuration is:

- typed;
- validated;
- versioned;
- environment-specific;
- observable;
- protected from unauthorized mutation.

Secrets must not be committed to source control.

## 13. Schema Versioning

Persistent schemas have explicit versions and migrations. Event history is immutable; migrations preserve historical meaning.

## 14. API Compatibility

Cross-domain APIs define compatibility rules and versioning before breaking changes are introduced.

## 15. Testing

Cross-cutting requirements require automated validation wherever practical, plus failure-injection tests for critical paths.

## 16. Performance

Measure:

- sensor-to-event latency;
- event-to-attention latency;
- retrieval latency;
- model TTFT/throughput;
- tool latency;
- planning latency;
- action latency;
- end-to-end latency;
- recovery time;
- queue depth;
- resource utilization;
- power/thermal behavior on edge hardware.

NVIDIA's DeepStream documentation provides component-level latency measurement guidance, reinforcing component-level instrumentation rather than only end-to-end timing. citeturn0search10

## 17. Determinism and Reproducibility

Tests should control or record:

- clocks;
- random seeds;
- event ordering;
- model versions/settings;
- tool responses;
- simulator version;
- world/asset version;
- feature flags;
- configuration.

## 18. Security

Never treat model-generated content as trusted input. Validate outputs before use as:

- commands;
- SQL;
- file paths;
- configuration;
- tool parameters;
- network requests.

## 19. Operational Explanation

Novi must expose operational evidence such as:

```text
Observed X
→ evidence Y
→ retrieved Z
→ selected capability A
→ policy result B
→ safety result C
→ execution result D
```

This is an audit/explanation record, not a requirement to expose hidden chain-of-thought.

## 20. Upgradeability

Models, runtimes, ROS 2 distributions, JetPack, CUDA/TensorRT, NVIDIA components and hardware adapters are version-pinned and tested before promotion.

NVIDIA's current documentation demonstrates why this is necessary: DeepStream 9.1's Jetson package is tied to JetPack 7.2/L4T r39.2 and uses a specific TensorRT 10.x line. citeturn0search1turn0search9

## 21. Local-First Requirement

Core operation must not require an external API. Cloud integrations are optional capabilities.

## 22. Data Integrity

Critical writes are transactional/atomic as appropriate. Corrupt or partially written data cannot silently become authoritative state.

## 23. Graceful Degradation

Examples:

```text
VLM unavailable
 → lower-cost/local perception continues if safe

Reasoner unavailable
 → deterministic capabilities continue

Knowledge store unavailable
 → bounded local buffer / degraded mode

Navigation unavailable
 → no autonomous movement

Network unavailable
 → offline core continues
```

## 24. Safety Priority

Safety takes precedence over task completion, personality, curiosity, latency and convenience.

## 25. Resource/Power/Thermal Coupling

On edge hardware, compute scheduling must consider thermal and power state. A capability may be throttled, deferred or disabled when resource constraints threaten system stability.

## 26. Observability Integrity

Telemetry must distinguish:

```text
MEASURED
DERIVED
ESTIMATED
SIMULATED
PREDICTED
```

A simulated or predicted metric must not be reported as measured physical performance.

## 27. Failure Semantics

Every critical interface defines:

```text
success
failure
unknown
partial
cancelled
rejected
reconciling
```

Unknown is a first-class state after uncertain external effects.

## 28. Security/Privacy Boundary

Diagnostic and observability systems must not become an uncontrolled side channel for sensitive audio, video, location, identity or memory data.

## 29. Documentation Requirement

Each cross-cutting requirement must map to:

```text
requirement ID
 ↓
architecture document
 ↓
implementation owner
 ↓
test
 ↓
evidence
```

The architecture validation document is authoritative for this traceability.
