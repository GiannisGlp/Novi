# 17 — Cognition Testing

## Status

**DESIGN**

## Purpose

Cognition must be testable independently of physical hardware and large language model nondeterminism.

## Test Layers

1. unit tests
2. contract tests
3. deterministic scenario tests
4. model evaluation tests
5. multimodal fusion tests
6. replay tests
7. adversarial tests
8. simulation tests
9. hardware-in-loop tests
10. endurance tests

## Deterministic Scenarios

Scenarios should provide controlled observations and expected cognitive state transitions.

Example:

```text
camera: known person enters kitchen
IoT: kitchen light on
recent memory: person usually makes coffee here

expected:
identity resolved
world updated
routine hypothesis retrieved
no unnecessary speech
```

## Model Evaluation

LLM/VLM/model behavior should be evaluated using fixed datasets and scenario suites for:

- factual grounding
- tool selection
- planning quality
- uncertainty calibration
- refusal/safety compliance
- context relevance
- personality consistency
- social appropriateness
- latency
- resource usage

## Regression

Every production change to models, prompts, routing, retrieval, schemas, or policies must run regression scenarios.

## Replay

Recorded structured events should allow a scenario to be replayed without live sensors. Raw private media should not be required unless specifically authorized for the test.

## Adversarial Tests

Include:

- conflicting sensor evidence
- ambiguous identity
- misleading user statements
- hallucinated tool results
- stale memory
- malicious tool arguments
- unavailable models
- malformed model output
- resource exhaustion
- rapid event bursts
- repeated duplicate events

## Acceptance Criteria

Cognition has automated tests for correctness, safety, uncertainty, latency, fallback, and regression before hardware integration.
