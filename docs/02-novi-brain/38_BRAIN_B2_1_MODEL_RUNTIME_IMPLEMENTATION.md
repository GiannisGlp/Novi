# B2.1 — Model Runtime Implementation

**Status:** IMPLEMENTED — B2.1 baseline
**Branch:** `main`
**Owner:** Brain Runtime
**Canonical contract:** `novi.model-invocation` `1.0.0`

## 1. Purpose

B2.1 establishes the first executable, backend-neutral model runtime boundary for Novi. It does not introduce a learned model. The implementation provides the contract-facing lifecycle and invocation path required before real model backends are admitted.

The runtime is an execution component. It is not a reasoning authority, memory authority, autonomy authority, safety authority, or motor-control authority.

## 2. Implemented components

`brain/b2_model_runtime.py` provides:

- `ModelArtifact` — immutable model artifact identity and backend metadata.
- `ModelCapabilities` — declared model execution capabilities and schema versions.
- `ModelDescriptor` — admitted model description and resource/safety/privacy classification.
- `ModelInvocationRequest` — normalized invocation request.
- `ModelResult` — normalized execution result.
- `ModelHealth` — runtime readiness state.
- `ModelRuntime` — backend-neutral registration, load, unload, health and invocation orchestration.
- `DeterministicModelBackend` — test backend with no learned inference.
- explicit admission and invocation failure classes.

## 3. Architectural boundary

```text
Brain Orchestrator
      |
      | ModelInvocationRequest
      v
ModelRuntime
      |
      +--> admission / compatibility checks
      |
      +--> backend adapter
      |
      v
Model backend
```

No model runtime interface grants access to motors, safety authorization, durable memory, credentials, arbitrary filesystem paths or arbitrary network endpoints.

## 4. Contract alignment

The implementation consumes the canonical `novi.model-invocation` `1.0.0` contract through the existing `brain.contracts` registry and validator. It does not create a second semantic contract.

The invocation path records:

- invocation identity;
- model identity/version;
- artifact digest;
- runtime/backend identity;
- hardware metadata;
- input/output schema versions;
- timestamps;
- latency;
- provenance.

## 5. Admission rules

A model must have:

1. unique runtime identity;
2. semantic model version;
3. `sha256:` artifact digest;
4. backend identity;
5. runtime version;
6. declared input/output schema versions.

Registration rejects duplicate model IDs and malformed artifact digests.

## 6. Invocation rules

Before backend execution the runtime verifies:

- model version;
- artifact digest;
- input schema version;
- output schema version.

A mismatch is a runtime error and is never silently coerced.

Backend failures are contained and returned as a structured failed `ModelResult` rather than escaping as an uncontrolled runtime failure.

## 7. Deterministic baseline

The deterministic backend echoes its input. This is intentional.

It proves the runtime boundary, lifecycle, validation, provenance and failure isolation without coupling B2.1 to a particular neural framework, accelerator or model family.

The next learned-model implementation must use the same runtime boundary.

## 8. Tests

`brain/tests/test_b2_model_runtime.py` covers:

- registration;
- loading;
- invalid artifact admission;
- successful invocation;
- artifact mismatch;
- model version mismatch;
- schema mismatch;
- unloaded-model failure isolation;
- unload/readiness behavior.

The existing Brain CI workflow discovers `brain/tests/test_*.py`, so the B2.1 test suite is included in the Brain validation gate.

## 9. Deliberate non-goals

B2.1 does not yet implement:

- TensorRT;
- Triton;
- ONNX Runtime;
- PyTorch execution;
- GPU scheduling;
- dynamic batching;
- streaming inference;
- real cancellation;
- model registry service;
- durable artifact storage;
- production telemetry;
- learned inference.

Those are subsequent runtime capabilities and must be admitted only after their contracts, resource behavior and benchmarks are defined.

## 10. Relationship to runtime resource architecture

Novi's runtime architecture requires bounded latency, explicit resource budgets, bounded queues, stale-work handling, graceful degradation and end-to-end measurement. B2.1 therefore intentionally avoids pretending that a deterministic test backend constitutes production performance.

Real model admission must later provide measured latency, CPU/GPU/RAM usage, accelerator memory, thermal/power impact, concurrency behavior and fallback behavior.

## 11. Acceptance criteria

B2.1 is accepted when:

- the canonical ModelInvocation contract resolves at version `1.0.0`;
- a model can be registered and loaded;
- health can be queried;
- invocation identity and artifact identity are checked;
- schema compatibility is checked;
- successful results are structured;
- backend failures are contained;
- unload changes readiness state;
- tests execute through the existing Brain test discovery path;
- no semantic authority is duplicated in the runtime.

## 12. Next step

**B2.2 — Real local model backend.**

Select and integrate the first actual local learned model only after evaluating its capability, license/provenance, hardware compatibility, latency/resource envelope and fallback behavior. The model must remain replaceable behind `ModelRuntime` and must not become the architectural definition of Novi's intelligence.
