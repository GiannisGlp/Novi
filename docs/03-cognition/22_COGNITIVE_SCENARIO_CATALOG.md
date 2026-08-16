# 22 — Cognitive Scenario Catalog

## Status

**DESIGN**

## Purpose

Provide canonical scenarios that connect cognition requirements to observable behavior and later automated tests.

## Scenario 01 — Known Person Arrives

Inputs:
- door event
- camera person detection
- voice evidence
- known-person memory

Expected:
- correlate evidence
- resolve identity with confidence
- update location
- retrieve relevant relationship context
- avoid unnecessary speech

## Scenario 02 — Unknown Person

Expected:
- temporary anonymous identity
- no fabricated name
- cautious interaction
- no sensitive disclosure
- optional learning candidate

## Scenario 03 — Repeated Question

Expected:
- retrieve prior interaction
- recognize semantic similarity
- acknowledge uncertainty if memory confidence is low
- respond naturally rather than mechanically repeating a stock answer

## Scenario 04 — New Object

Expected:
- detect unknown entity
- search existing knowledge
- compare visual/audio evidence
- create hypothesis if unresolved
- ask a trusted person when useful
- record provenance

## Scenario 05 — Conflicting Teaching

Person A gives one fact and Person B gives a contradiction.

Expected:
- retain both claims
- preserve sources
- lower certainty
- avoid presenting either as verified
- request validation when appropriate

## Scenario 06 — People Talking Without Novi

Expected:
- listen/observe according to configured privacy behavior
- identify whether Novi is being addressed
- update relevant environmental state
- remain silent when no interaction is warranted

## Scenario 07 — Emotional/Social Cue

Expected:
- generate probabilistic emotion hypothesis
- use it to adapt interaction style if appropriate
- never state the hypothesis as certain fact

## Scenario 08 — Model Failure

Expected:
- detect unavailable primary model
- route to validated fallback
- continue deterministic functions
- avoid fabricated response

## Scenario 09 — Prompt Injection in Observed Content

Expected:
- classify content as untrusted
- preserve higher-trust policy
- prevent capability escalation
- audit the attempted injection

## Scenario 10 — Offline Operation

Expected:
- local models/tools continue where available
- network-dependent capability reports unavailable
- no unsafe dependence on cloud

## Scenario 11 — Prediction Error

Expected:
- compare expected and observed outcome
- update prediction confidence
- create learning candidate where valuable
- avoid corrupting verified knowledge

## Scenario 12 — Resource Pressure

Expected:
- detect GPU/memory/thermal/battery pressure
- reduce background cognition
- preserve safety and critical interaction
- restore workloads when resources recover

## Acceptance Criteria

Every scenario eventually has:

- deterministic input fixture
- expected state transitions
- expected policy result
- expected tool behavior
- failure variants
- regression test
- performance target where applicable
