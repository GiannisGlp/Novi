# 21 — Situation Model
> **⚠️ SUPERSEDED** — Canonical implementations now live in `MAC_BRAIN/` (see `MAC_BRAIN/PERFECTING_PLAN/`). This document is retained for historical reference only.


**Status:** SUPERSEDED — legacy Brain source document  
**Canonical semantic owner:** `03-cognition/01_COGNITIVE_ARCHITECTURE.md` and `03-cognition/09_CONTEXT_ENGINE.md`

## Why this file was superseded

The former document defined the semantic Situation Model inside Brain. That duplicated Cognition's responsibility for interpreting current world state into meaningful contexts.

## Canonical boundary

```text
Perception / fusion
  → structured evidence

World Model
  → current semantic world state

Situation Model
  → current interpretation of what matters and what is happening

Context Engine
  → bounded context package for a specific cognitive operation

Autonomy
  → goal pursuit and behavioral decisions
```

The Situation Model does not own the task planner, safety controller, memory persistence or motor control.

## Consolidated requirements

The former specification's important requirements remain valid:

- situation continuity across time;
- physical, semantic, social, goal/task and predictive layers;
- explicit provenance and uncertainty;
- relevance and urgency assessment;
- social-context hypotheses without claiming private mental states as facts;
- intent hypotheses with evidence and expiration;
- active tasks as context rather than planner ownership;
- hazards and opportunities as cognitive context, not sole safety authority;
- counterfactual situations remaining explicitly hypothetical;
- active perception when situation uncertainty is operationally important;
- freshness/decay and explicit unknown states;
- deterministic state transitions around learned semantic interpretations;
- model escalation only when the situation actually requires it;
- immediate reactive handling without requiring an LLM-generated explanation.

These requirements are now expressed through the canonical Cognition architecture and Context Engine, with Autonomy consuming the resulting cognitive state.

## Migration rule

Do not add a second Situation Model here. Extend the canonical Cognition documents.

## Historical preservation

The complete pre-consolidation specification remains available in Git history for provenance and recovery.
