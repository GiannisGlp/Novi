# 18 — Cognition Observability

## Status

**DESIGN**

## Purpose

Provide enough structured telemetry to understand what the cognitive system did, why an action was selected at the policy level, how long it took, and where failures occurred.

## Trace

A cognitive trace should connect:

```text
input event
→ context build
→ retrieval
→ model/capability selection
→ structured result
→ policy outcome
→ action request
→ outcome
```

## Metrics

Track at minimum:

- inference latency
- context-build latency
- retrieval latency
- model selection frequency
- fallback frequency
- tool failure rate
- confidence distribution
- contradiction rate
- stale-data rate
- cognitive queue depth
- memory retrieval quality
- prediction error
- task completion rate

## Privacy

Telemetry should contain references and structured metadata rather than unnecessary raw audio/video or sensitive personal content.

## Model Telemetry

Record model name/version, runtime, hardware profile, token counts where appropriate, latency, errors, and fallback. Do not record private chain-of-thought.

## Auditability

Consequential decisions must be reconstructable from structured evidence and policy metadata. The system should be able to answer operational questions such as:

- Which capability was selected?
- Which data sources were used?
- Was an action denied?
- Which safety rule applied?
- What outcome was observed?

## Debugging

A trace ID should propagate across services so a single event can be followed through cognition, autonomy, tools, and hardware adapters.

## Acceptance Criteria

Engineers can diagnose latency, model failures, incorrect routing, stale context, policy denials, and action outcomes without requiring unrestricted access to private raw media or hidden model reasoning.
