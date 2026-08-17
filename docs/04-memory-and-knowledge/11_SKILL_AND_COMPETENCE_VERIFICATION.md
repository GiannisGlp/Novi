# 11 — Skill and Competence Verification

**Status:** CANONICAL — CONSOLIDATED V1

## Purpose
Define how Novi represents capabilities, verifies competence, scopes autonomy, detects degradation and separates capability claims from authorization.

## Core distinction

```text
CAN DO ≠ AUTHORIZED TO DO
```

A skill record says what Novi may be capable of doing; `105` determines what it is permitted to do.

## Skill object

A skill contains identity, version, domain, prerequisites, evidence, evaluation history, environment/regime, limitations, confidence, validity interval and revocation state.

## Competence evidence

Evidence may include benchmark results, real-world outcomes, human evaluation, simulation, tool-specific tests, regression tests and longitudinal performance. Synthetic evaluation is not automatically equivalent to real-world competence.

## Scope

Competence is scoped by:

- task;
- environment;
- modality;
- toolchain;
- model version;
- data regime;
- risk level;
- temporal validity.

A skill demonstrated in one regime must not silently generalize to another.

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

Competence may be downgraded after regression, repeated intervention, environment change, model change, tool change, anomalous outcomes or stale evidence.

## Revocation

Capability revocation must be enforceable independently of the model. Distributed revocation follows `109`; emergency suspension follows `105/106`.

## Human evaluation

Human assessments are evidence with reviewer identity, scope and provenance. A human correction is not automatically ground truth.

## Skill composition

Composite skills inherit prerequisites and limitations. A composed skill must not exceed the authority or competence of its components.

## Safety invariants

1. Competence never grants authorization.
2. Skill claims are scope- and regime-bound.
3. Promotion requires evidence.
4. Stale or degraded skills cannot silently authorize high-risk action.
5. Revocation propagates to enforcement points.
6. Model confidence is not competence evidence by itself.

## Integration

`03` provides provenance. `09` supplies causal evaluation where relevant. `12/13` govern skill/schema/model evolution. `105/106` govern authorization and oversight. `112` evaluates longitudinal competence.