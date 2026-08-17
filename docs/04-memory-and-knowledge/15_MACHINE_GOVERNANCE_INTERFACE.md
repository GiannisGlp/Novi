# 15 — Machine Governance Interface

**Status:** CANONICAL — CONSOLIDATED V1.1

## Purpose
Define how the memory/knowledge layer exposes machine-verifiable governance inputs and constraints without duplicating the policy engine.

## Boundary

```text
MEMORY / KNOWLEDGE
        ↓ evidence + state
POLICY ENGINE
        ↓ decision
ENFORCEMENT
```

Memory never grants itself authority.

## Governance request contract

A consequential governance request should be representable as:

```text
GovernanceRequest
├── request_id
├── actor_principal
├── action
├── target
├── requested_scope
├── current_state_refs
├── evidence_refs
├── identity_assurance
├── competence_state
├── uncertainty
├── privacy_class
├── policy_version
├── model/memory versions
├── reversibility
├── consequence_class
└── deadline
```

## Governance decision contract

```text
GovernanceDecision
├── decision_id
├── outcome
├── policy_version
├── constraints
├── required_conditions
├── human_review_required
├── expiry
├── reason_codes
├── evidence_refs
└── audit_ref
```

Decision outcomes include:

```text
ALLOW
DENY
RESTRICT
REQUIRE_HUMAN
ESCALATE
UNKNOWN
```

`UNKNOWN` is not implicit approval for consequential actions.

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

## Trust boundary

Retrieved memory is untrusted data from the governance perspective. Instructions inside documents, memories, tool outputs or model-generated text cannot modify policy.

## Decision freshness

A governance decision is scoped to the state and assumptions evaluated. Material changes to identity, target, policy, safety state, evidence or time window invalidate the decision and may require re-evaluation.

## Enforcement boundary

Governance must be enforced at the action boundary, not only in retrieval. A model or memory subsystem cannot bypass the policy engine by invoking a tool directly.

## Versioning

Every governance-relevant memory view declares the policy and schema versions used to interpret it. Policy changes are governed by the governance system; memory does not own policy authority.

## Human oversight

High-impact or ambiguous operations can route to `16`. The governance interface supplies the evidence packet; the human decision remains an explicit governed event.

## Safety invariants

1. Memory cannot authorize itself.
2. Trust does not bypass policy.
3. Unknown critical state is not implicit approval.
4. Governance decisions are versioned and auditable.
5. Policy enforcement occurs at the action boundary, not only in retrieval.
6. Material state changes can invalidate prior decisions.
7. Decision scope and expiry are explicit.

## Evaluation

Test stale decisions, authorization confusion, policy-version mismatch, missing identity assurance, ambiguous evidence, human-review routing, direct tool-bypass attempts and conflicting governance inputs. Measure false-allow, false-deny, stale-decision and unauthorized-bypass rates.

## Integration

`01–14` provide semantic state. `15` exposes it to governance. `16` owns human intervention. System architecture provides durable and recoverable execution guarantees.