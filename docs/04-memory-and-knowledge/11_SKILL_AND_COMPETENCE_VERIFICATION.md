# 11 — Skill and Competence Verification

**Status:** CANONICAL — CONSOLIDATED V1.1

## Purpose
Define how Novi represents capabilities, verifies competence, scopes autonomy, detects degradation and separates capability claims from authorization.

## Core distinction

```text
CAN DO ≠ AUTHORIZED TO DO
```

A skill record says what Novi may be capable of doing; `15` determines what it is permitted to do.

## Skill object

A skill contains identity, version, domain, prerequisites, evidence, evaluation history, environment/regime, limitations, confidence, validity interval and revocation state.

## Competence evidence

Evidence may include benchmark results, real-world outcomes, human evaluation, simulation, tool-specific tests, regression tests and longitudinal performance. Synthetic evaluation is not automatically equivalent to real-world competence.

## Competence evaluation matrix

Where material, evaluate:

```text
task
environment
modality
toolchain
model_version
data_regime
risk_level
evidence_volume
success_rate
failure_rate
human_intervention_rate
recovery_behavior
longitudinal_stability
```

The evidence threshold must be appropriate to consequence. High average performance does not justify ignoring rare catastrophic failures.

## Scope

Competence is scoped by task, environment, modality, toolchain, model version, data regime, risk level and temporal validity.

A skill demonstrated in one regime must not silently generalize to another.

## Competence state machine

```text
CANDIDATE
   ↓
EVALUATING
   ↓
VERIFIED
   ↓
PROMOTED
   ↓
DEGRADED
   ↓
SUSPENDED
   ↓
REVOKED
```

Transitions require evidence and policy. A skill can return from degraded/suspended state only through explicit revalidation.

## Promotion

```text
OBSERVATION
 ↓
CANDIDATE SKILL
 ↓
EVALUATION
 ↓
VALIDATION
 ↓
PROMOTION
```

Promotion requires explicit evidence thresholds and policy. Autonomous skill creation cannot modify protected execution or authorization logic.

## Degradation

Competence may be downgraded after regression, repeated intervention, environment change, model change, tool change, anomalous outcomes, stale evidence or distribution shift.

## Revocation

Capability revocation must be enforceable independently of the model. Revocation must propagate to relevant enforcement points. Emergency suspension follows `15`/`16`.

## Human evaluation

Human assessments are evidence with reviewer identity, scope and provenance. A human assessment is not automatically ground truth; reviewer authority and evaluation method are recorded.

## Skill composition

Composite skills inherit prerequisites, limitations and uncertainty. A composed skill must not exceed the competence or authorization constraints of its components.

## Evaluation and monitoring

Longitudinal evaluation should measure regression, drift, intervention rate, recovery behavior, calibration and rare high-impact failures. Evaluation artifacts are versioned and traceable to the skill/model/schema/policy versions used.

## Safety invariants

1. Competence never grants authorization.
2. Skill claims are scope- and regime-bound.
3. Promotion requires evidence.
4. Stale or degraded skills cannot silently authorize high-risk action.
5. Revocation propagates to enforcement points.
6. Model confidence is not competence evidence by itself.
7. Rare high-impact failures cannot be hidden by aggregate averages.

## Integration

`03` provides provenance. `09` supplies causal evaluation where relevant. `12/13` govern skill/schema/model evolution. `15/16` govern authorization and oversight. `18` defines cross-system evaluation and audit requirements.