# B2.5 — Cosmos Reason2 Physical-Reasoning Adapter

**Status:** IMPLEMENTED — adapter baseline
**Domain:** Brain Runtime / Physical Reasoning
**Target model:** NVIDIA Cosmos-Reason2

## Purpose

B2.5 introduces Cosmos-Reason2 as a replaceable physical-reasoning capability behind the Novi model boundary. NVIDIA describes Cosmos-Reason2 as an open reasoning VLM for physical AI and robotics, with spatial-temporal understanding, object localization and long-context reasoning.

## Architectural role

Cosmos Reason2 is a **reasoning/evidence provider**, not an action authority.

```text
Sensors / video
      ↓
Cosmos Reason2
      ↓
Physical reasoning evidence
      ↓
World state / Cognition
      ↓
Autonomy
      ↓
ActionProposal
      ↓
Safety / Authorization
      ↓
Execution
```

The adapter intentionally cannot create an `ActionProposal`, authorize an action, or access hardware.

## Implemented boundary

`brain/b2_cosmos_reason.py` provides:

- `CosmosReasonRequest` for normalized video/question/timestamp context;
- `CosmosReason2Adapter` for backend-neutral invocation;
- failure containment;
- normalized physical-reasoning provenance;
- conversion from a successful result into structured evidence.

## Evidence semantics

The adapter produces evidence with:

- model identity/version;
- evidence kind `physical_reasoning`;
- model output payload;
- adapter provenance.

Failed inference cannot be converted into evidence.

## Hardware position

This stage deliberately does **not** choose Jetson AGX Orin 64GB or Jetson AGX Thor.

NVIDIA's current Cosmos documentation validates Reason2 on Hopper/Blackwell systems and Jetson AGX Thor, with minimum memory of 24GB for Reason2-2B and 32GB for Reason2-8B. This makes hardware benchmarking necessary before deployment selection.

## Runtime position

The production backend remains external to the deterministic CI suite. CI uses a fake backend to validate the semantic boundary. Real Cosmos inference will be benchmarked on candidate hardware using the B2.4 evaluation harness.

## Safety boundary

Cosmos output is advisory evidence. It may inform cognition and planning but cannot bypass:

1. world-state validation;
2. autonomy constraints;
3. authorization;
4. deterministic safety decisions;
5. controller boundaries.

## Tests

`brain/tests/test_b2_cosmos_reason.py` covers:

- successful physical-reasoning evidence;
- explicit absence of motor/action authority;
- backend failure containment;
- rejection of failed results as evidence.

## Acceptance criteria

B2.5 adapter acceptance requires:

- stable backend-neutral interface;
- physical-reasoning provenance;
- failure containment;
- no action or hardware authority;
- deterministic CI coverage;
- real-model benchmark evidence before production admission.

## Next

B2.6 should add specialist neural perception capabilities and connect their evidence into the same world-state/cognition path. Real Cosmos Reason2 performance and hardware measurements remain part of the B2 integration evidence gate.
