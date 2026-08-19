# B1.8 — Simulated Execution and Hardware Capability Boundary

## Status

IMPLEMENTED — deterministic simulated baseline; CI validation pending.

## Purpose

B1.8 establishes the first explicit execution boundary after proposal, authorization, and safety decisions. It produces the canonical `novi.action-execution/1.0.0` shape without commanding real hardware.

## Pipeline

```text
ActionProposal
    ↓
AuthorizationDecision
    ↓
SafetyDecision
    ↓
SimulatedCapabilityGateway
    ↓
ActionExecution record
    ↓
ActionOutcome / replay
```

## Safety invariants

1. Execution requires explicit authorization and safety approval references.
2. A rejected proposal cannot enter the execution boundary.
3. The gateway is simulation-only.
4. No motor, actuator, GPIO, serial, CAN, or physical device API is called.
5. Execution identity is deterministic for the same proposal and decision references.
6. The execution record retains proposal, authorization, safety, capability, runtime, operation, and provenance references.

## Contract alignment

The implementation mirrors the repository's existing `novi.action-execution/1.0.0` contract. The contract requires `execution_id`, `proposal_ref`, `authorization_ref`, `safety_ref`, `capability`, `started_at`, `execution_attempt`, `status`, `operation_id`, `runtime_version`, and `provenance`.

## Why simulation first

The execution boundary must be validated independently from physical hardware. This lets Novi test authorization, safety references, idempotency, provenance, and outcome handling before introducing actuator-specific failure modes.

## Acceptance criteria

- denied execution raises before execution record creation;
- approved execution creates a canonical execution record;
- proposal/authorization/safety references are preserved;
- execution identity is deterministic;
- direct hardware control remains impossible through this component;
- GitHub Actions validates the complete B1.8 test set.

## Next

After CI validation, integrate B1.8 into the B1 end-to-end simulated cycle. Physical hardware control remains a later gated stage and must use the same execution contract rather than bypassing it.
