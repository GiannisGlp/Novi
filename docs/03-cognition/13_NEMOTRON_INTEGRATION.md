# 13 — Primary Reasoning Model Integration

## Status

**DESIGN — CANDIDATE: NVIDIA NEMOTRON**

## Purpose

Define how Novi integrates a primary general-purpose reasoning model without making the cognitive architecture dependent on that model.

## Role

The primary reasoning model handles tasks such as:

- semantic interpretation
- complex reasoning
- conversational generation
- multi-step planning proposals
- tool selection proposals
- synthesis of retrieved evidence
- explanations and user-facing language

It does not own:

- authoritative memory
- identity
- authorization
- safety decisions
- raw hardware control
- unrestricted filesystem/database access

## Context Boundary

Novi builds a structured context package. The model receives only the information required for the current task and permitted by policy.

## Structured Output

Model outputs should use typed schemas for:

- answer
- clarification request
- plan proposal
- tool request
- knowledge candidate
- memory candidate
- uncertainty statement
- no-action recommendation

Free-form text is not accepted as a physical action command.

## Tool Calling

```text
model
 ↓
typed tool proposal
 ↓
capability validator
 ↓
authorization/policy
 ↓
safety
 ↓
execution
 ↓
result
 ↓
model/context
```

## Reasoning Mode

Where supported, the integration may use model reasoning modes appropriate to task complexity. Simple conversational responses should not incur unnecessary expensive reasoning.

## Model Independence

The integration must be behind a `ReasoningModel` capability interface. Nemotron can be replaced by another local model without changing the World Model, Memory, Autonomy, or Tool contracts.

## Local Deployment

The target architecture prefers local inference. Model artifacts, runtime, quantization, acceleration, context limits, concurrency, and thermal/resource behavior must be benchmarked on the target Jetson before production selection.

## Hardware Optimization

NVIDIA TensorRT or other local runtimes may be evaluated when they improve actual target performance. Optimization is not assumed merely because a model originates from NVIDIA.

## Failure Modes

If the primary reasoning model is unavailable:

- use deterministic logic where possible;
- use specialized local models where appropriate;
- fall back to a smaller local reasoning model if validated;
- continue safety and basic robotics;
- do not fabricate unavailable model results.

## Acceptance Criteria

The model can participate in complex reasoning and planning while remaining a replaceable component behind stable interfaces and strict capability/safety boundaries.
