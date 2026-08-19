# B1.5 — Autonomy ActionProposal Workflow

**Status:** P0 workflow — implementation complete, validation pending  
**Domain:** Brain / Autonomy boundary  
**Stage:** B1 Closed Simulated Loop  
**Date:** 2026-08-19  
**Authority:** `docs/02-autonomy/05_DECISION_AND_PLANNING.md`, `contracts/autonomy/action-proposal/1.0.0/schema.json`, `contracts/registry.json`

## Purpose

Connect Cognition to the Autonomy boundary by producing a bounded, canonical `ActionProposal` without executing the proposal or authorizing it.

The Autonomy specification defines decision/planning as transforming world state, goals, memory and context into a bounded action proposal, while explicitly separating planning from authorization. fileciteturn129file0L2-L2

## Architecture

```text
World State
    ↓
Cognition
    ↓
CognitiveState
    ↓
Autonomy
    ↓
ActionProposal
    ↓
Safety / Authorization
    ↓
Execution
```

The canonical contract registry identifies `novi.action-proposal/1.0.0` as the autonomy-owned consequential contract. fileciteturn132file0L2-L2

## Implementation baseline

`brain/b1_autonomy.py` implements a deterministic proposal builder.

It deliberately does not invoke an LLM, perform tool execution, control motors, or make authorization decisions.

## Canonical ActionProposal

The proposal includes all required canonical fields:

- proposal ID;
- capability;
- semantic intent;
- parameters;
- constraints;
- expected effects;
- risks;
- requester ID;
- authorization context;
- expiry;
- idempotency key;
- provenance.

The implementation also carries target references where applicable. The canonical schema requires these core fields and permits target, goal and plan references. fileciteturn122file0L2-L2

## Deterministic planning baseline

For B1, the autonomy layer uses the Cognition result as its semantic intent and selects a bounded observation capability. This is intentionally a narrow Stage-0 behavior rather than the final planning engine.

The proposal is constrained by:

```text
requires_safety_authorization = true
no_direct_motor_control       = true
bounded execution duration
```

This ensures the first executable autonomy boundary cannot silently become a body-control path.

## Determinism and idempotency

Proposal identity is derived from the cognitive intent, target set and cycle. Repeating the same cognitive input therefore produces the same proposal ID and idempotency key.

The proposal also carries cognition provenance so downstream Safety and execution layers can trace why it was generated.

## Model strategy

No neural network or LLM is required for B1.5.

The autonomy design permits a reasoning model to propose goals and plans, but explicitly prohibits the model from authorizing itself, bypassing safety, directly commanding motors or altering immutable policy. fileciteturn129file0L2-L2

A future model-assisted implementation will therefore replace or augment the deterministic proposal generator behind the same semantic boundary and must pass the deterministic baseline tests.

## Non-goals

B1.5 does not implement:

- production goal management;
- multi-step planning;
- Nemotron integration;
- tool execution;
- navigation;
- motor commands;
- authorization;
- safety policy evaluation;
- replanning;
- human confirmation flows.

Those are subsequent Autonomy/Safety implementation stages.

## Acceptance criteria

1. proposal uses the canonical `novi.action-proposal/1.0.0` contract;
2. proposal is deterministic for identical cognitive input;
3. idempotency key is explicit;
4. cognition provenance is preserved;
5. constraints are explicit;
6. Safety authorization is required;
7. direct motor control is prohibited;
8. proposal generation does not execute actions;
9. proposal generation does not authorize actions;
10. model execution remains optional and behind the autonomy boundary.

## Validation

The repository Brain CI workflow executes tests under `brain/tests`, including B1.5. B1.5 becomes **VALIDATED** only after the resulting `main` revision passes that CI workflow.

## Architectural boundary

```text
Cognition
  = interpretation + reasoning

Autonomy
  = goals + planning + ActionProposal

Safety / Policy
  = authorization

Execution / Hardware
  = physical or simulated effect
```

This separation remains mandatory as Novi moves from deterministic Stage-0 behavior to learned planning and physical embodiment.
