# 09 — Causal World Modeling

**Status:** CANONICAL — CONSOLIDATED V1

## Purpose
Define how Novi represents causal hypotheses, interventions, mechanisms, counterfactuals and uncertainty without confusing correlation with causation.

## Core principle

```text
OBSERVATION → ASSOCIATION → CAUSAL HYPOTHESIS → VALIDATION → ACTION
```

Each transition requires explicit evidence and uncertainty.

## Causal objects

Represent variables, events, mechanisms, directed relations, interventions, outcomes, confounders, assumptions, counterfactuals and confidence/credibility metadata.

## Correlation is not causation

Statistical association, temporal precedence, semantic explanation and causal evidence are separate statuses. Novi must not promote correlation to causal knowledge merely because a model produces a persuasive explanation.

## Causal provenance

Every causal claim links to supporting observations, experiments, assumptions, model version and validity regime. A causal model is a derived artifact and must remain rebuildable where practical.

## Interventions

An intervention changes a variable intentionally. Observational data and intervention data must be represented separately. Intervention outcomes become new evidence, not automatic confirmation of the original hypothesis.

## Counterfactuals

Counterfactual claims include the factual world, intervention assumption, model and uncertainty. They must not be stored as observed events.

## Regime and drift

Causal relationships can change across time, location, population, system version and environment. Each model therefore declares its applicability regime and assumptions.

## Conflict handling

Competing causal hypotheses remain distinct until evidence supports revision. `05` handles semantic belief revision; `108/109` handle state and replica conflicts.

## Human oversight

Consequential actions based on uncertain causal models may require review under `105/106`. The reviewer must see causal assumptions and material uncertainty rather than only a recommendation.

## Safety invariants

1. Correlation is never represented as proven causation.
2. Causal claims preserve evidence and assumptions.
3. Interventions are distinct from observations.
4. Counterfactuals are distinct from history.
5. Causal validity is regime-scoped.
6. Model confidence does not replace causal evidence.
7. High-impact causal decisions remain subject to policy and oversight.

## Integration

`07` supplies temporal ordering. `08` supplies spatial context. `10` supplies multimodal evidence. `12/13` govern schema/model evolution. `112` evaluates causal drift and longitudinal reliability.