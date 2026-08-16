# 02 — Autonomy Data and Events

## Status

**DESIGN** — detailed contract baseline.

## Purpose

This document defines the common data vocabulary used by the autonomy engine. Concrete database schemas may differ between runtime implementations, but semantic meaning and required fields must remain stable.

## Observation

An observation is raw or directly derived evidence from a sensor or external source.

Required concepts:

```json
{
  "observation_id": "uuid",
  "source_id": "camera.front",
  "modality": "vision",
  "captured_at": "timestamp",
  "received_at": "timestamp",
  "confidence": 0.0,
  "privacy_class": "private",
  "payload_ref": "..."
}
```

An observation must not claim more certainty than its source supports.

## Event

An event is a semantically meaningful occurrence derived from one or more observations.

Example:

```json
{
  "event_id": "uuid",
  "type": "person.entered_room",
  "occurred_at": "timestamp",
  "location": "living_room",
  "entities": ["person:vano"],
  "confidence": 0.94,
  "evidence": ["observation:1", "observation:2"]
}
```

Events are immutable historical records. Corrections are represented by later events rather than destructive rewriting where practical.

## Situation

A situation is the current interpreted context around Novi.

Examples:

- `quiet_home`
- `person_in_conversation`
- `navigation_active`
- `unknown_event_under_investigation`

Situations have start/end times, confidence, participating entities, and supporting events.

## Goal

A goal describes a desired state.

```json
{
  "goal_id": "uuid",
  "type": "navigate",
  "target": "kitchen",
  "source": "user_request",
  "priority": 80,
  "status": "active",
  "created_at": "timestamp"
}
```

Goals must identify their source and authorization level.

## Intention

An intention is an internal candidate to pursue a goal. It is not executable authority.

```text
Goal → Intention → Plan → Policy → Action Request
```

## Plan

A plan is a structured sequence or graph of steps with preconditions, expected outcomes, timeout, retry policy, and cancellation semantics.

## Action Request

An action request is a typed request to a capability service.

It must contain:

- request ID
- capability name
- arguments
- goal ID
- plan ID
- risk class
- authorization context
- deadline/timeout
- idempotency key where applicable

## Outcome

An outcome records what happened after an action request.

It must distinguish:

- accepted
- started
- completed
- partially completed
- rejected
- timed out
- cancelled
- failed
- safety interrupted

## Learning Candidate

A learning candidate is a proposed change to knowledge, memory, relationship state, preference, or routine.

It must contain:

- candidate ID
- proposed change
- evidence references
- confidence
- source
- verification state
- created time
- expiration/review policy

## Event Ordering

Events use timestamps and monotonic sequence metadata where available. The system must tolerate:

- out-of-order arrival
- duplicate delivery
- clock skew
- missing observations
- delayed inference

No component may assume transport order equals real-world order.

## Event Correlation

Correlators may use:

- temporal proximity
- spatial proximity
- shared entities
- causal relationships
- sensor agreement
- source reliability

Correlation results must retain links to all supporting evidence.

## Confidence

Confidence is not truth. A high-confidence observation can still be wrong. Confidence values must be interpreted within the source/model calibration and never used alone to authorize dangerous actions.

## Privacy Classification

Every persistent event or observation must carry a privacy classification appropriate to the data:

- public
- household
- private
- sensitive
- restricted

Raw audio/video should generally be referenced rather than embedded in broad event records.

## Retention

Retention is determined by data type and policy. High-frequency telemetry may be summarized or expired; significant experiences and verified knowledge may be retained longer. Retention must be auditable.

## Idempotency

Commands and persistence operations that may be retried must use idempotency keys. A duplicate event must not create duplicate irreversible actions.

## Audit

Every autonomy decision of consequence must link to:

```text
trigger → context → decision → policy → action → outcome
```

The audit system records structured rationale metadata, not unrestricted hidden model reasoning.

## Schema Evolution

Autonomy data contracts must be versioned. New fields should be additive where possible. Breaking changes require migration plans and replay/regression tests.
