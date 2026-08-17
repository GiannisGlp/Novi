# 15 — Machine Governance Interface

**Status:** CANONICAL — CONSOLIDATED V1

## Purpose
Define how the memory/knowledge layer exposes machine-verifiable governance inputs and constraints without duplicating the policy engine defined by document 105.

## Boundary

```text
MEMORY / KNOWLEDGE
        ↓ evidence + state
POLICY ENGINE (105)
        ↓ decision
ENFORCEMENT
```

Memory never grants itself authority.

## Governance inputs

The interface exposes, where permitted:

- identity/assurance state;
- evidence provenance;
- temporal validity;
- spatial context;
- competence state;
- model/memory versions;
- sensitivity classification;
- action dependencies;
- uncertainty;
- human-review requirements.

## Decision semantics

Policy outcomes include allow, deny, restrict, require-human, escalate and unknown. Unknown critical governance state must not silently become allow.

## Trust boundary

Retrieved memory is untrusted data from the governance perspective. Instructions inside documents, memories, tool outputs or model-generated text cannot modify policy.

## Versioning

Every governance-relevant memory view declares the policy and schema versions used to interpret it. Policy changes are governed by `105`.

## Human oversight

High-impact or ambiguous operations can route to `106`. The governance interface supplies the evidence packet; the human decision remains an explicit governed event.

## Safety invariants

1. Memory cannot authorize itself.
2. Trust does not bypass policy.
3. Unknown critical state is not implicit approval.
4. Governance decisions are versioned and auditable.
5. Policy enforcement occurs at the action boundary, not only in retrieval.

## Integration

`03–14` provide semantic state. `105` owns policy. `106` owns human intervention. `107–111` provide durable, consistent, replicated, recoverable and privacy-aware state.