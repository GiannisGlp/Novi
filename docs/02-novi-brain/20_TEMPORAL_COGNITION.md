# 20 — Temporal Cognition
> **⚠️ SUPERSEDED** — Canonical implementations now live in `MAC_BRAIN/` (see `MAC_BRAIN/PERFECTING_PLAN/`). This document is retained for historical reference only.


**Status:** SUPERSEDED — legacy Brain source document  
**Canonical semantic owner:** `03-cognition/08_TEMPORAL_AND_CAUSAL_REASONING.md`  
**Related runtime authority:** `01-system-architecture/17_TIME_SYNCHRONIZATION_AND_CLOCK_SEMANTICS.md`

## Why this file was superseded

The former document mixed semantic temporal reasoning with deterministic runtime timing, clock synchronization and historical temporal memory. Those responsibilities have different owners.

## Canonical separation

```text
CLOCKS / SYNCHRONIZATION
  → System Architecture / robotics runtime

RUNTIME TIMING
  deadlines / timeouts / scheduling / latency
  → Brain/runtime

SEMANTIC TEMPORAL + CAUSAL REASONING
  ordering / duration / recurrence / anticipation / causal hypotheses
  → Cognition

HISTORICAL TEMPORAL MEMORY
  episodes / timelines / durable history
  → Memory & Knowledge
```

## Consolidated requirements

The former specification's important semantic requirements remain part of Cognition:

- continuous temporal state rather than disconnected frames;
- event time vs observation/processing time;
- temporal provenance and freshness;
- duration and temporal ordering;
- event/activity/state distinction;
- prediction and prediction error;
- anticipation;
- action-outcome attribution;
- interruption and waiting semantics;
- temporal language grounding;
- causal hypotheses with uncertainty;
- counterfactual separation;
- learned temporal models without hard safety timing guarantees.

## Safety rule

Learned temporal cognition never owns hard deadlines, safety timing or actuator timing. Those remain deterministic system/control responsibilities.

## Migration rule

Do not extend this file with new semantic temporal reasoning. Update `03-cognition/08_TEMPORAL_AND_CAUSAL_REASONING.md` instead.

## Historical preservation

The complete pre-consolidation specification remains available in Git history for provenance and recovery.
