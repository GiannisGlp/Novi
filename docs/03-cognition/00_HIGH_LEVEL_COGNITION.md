# 00 — High-Level Cognition

## Status

**DESIGN**

## Purpose

Cognition gives Novi a structured internal understanding of the world and the ability to reason over that understanding. It must support the behavior of an embodied system that continuously observes, remembers, predicts, interacts socially, learns, and acts.

## What Cognition Is

Cognition is the coordinated system of:

- world representation;
- situation interpretation;
- identity and relationship understanding;
- multimodal evidence fusion;
- memory/context retrieval;
- semantic knowledge access;
- temporal reasoning;
- causal reasoning;
- prediction;
- uncertainty management;
- reasoning-model invocation;
- personality/social interpretation;
- cognitive state maintenance.

## What Cognition Is Not

Cognition is not:

- the entire autonomy system;
- the LLM itself;
- the database;
- raw perception;
- motor control;
- safety authorization;
- unrestricted code execution.

## Cognitive Pipeline

```text
OBSERVATIONS
     ↓
EVIDENCE NORMALIZATION
     ↓
ENTITY / EVENT RESOLUTION
     ↓
WORLD MODEL UPDATE
     ↓
SITUATION INTERPRETATION
     ↓
MEMORY + KNOWLEDGE RETRIEVAL
     ↓
COGNITIVE CONTEXT
     ↓
REASONING / PREDICTION
     ↓
COGNITIVE OUTPUT
     ↓
AUTONOMY / PLANNING
```

## Cognitive Outputs

Cognition may produce:

- interpreted observations;
- entity references;
- situation hypotheses;
- predictions;
- relationships;
- questions;
- explanations;
- candidate goals;
- candidate plans;
- tool recommendations;
- response context;
- learning candidates.

These outputs are typed and confidence-aware. They do not automatically authorize actions.

## Core Invariants

### C1 — Model is not memory

A language model may reason over context but cannot be treated as the authoritative store of facts about Novi's world.

### C2 — Inference is not fact

The system distinguishes observation, inference, hypothesis, prediction, and verified knowledge.

### C3 — Evidence follows important claims

Cognitive claims that can influence decisions retain references to their supporting observations, memories, knowledge, or tools.

### C4 — Contradictions remain visible

When sources disagree, Novi preserves the conflict and evaluates it rather than silently overwriting one source.

### C5 — Context is bounded

Only relevant information is packaged for each reasoning operation. Context selection is itself an auditable operation.

### C6 — Deterministic controls remain deterministic

Authorization, safety, resource limits, and critical state transitions are not delegated to probabilistic reasoning.

### C7 — Local-first

Cognitive functions should run locally using mature open-source components whenever technically practical. Cloud services require an explicit exception.

### C8 — Vendor neutrality

NVIDIA acceleration is evaluated alongside other open-source ecosystems. No cognition API should require an NVIDIA implementation.

## Cognitive Time Scales

Cognition operates at several timescales:

- milliseconds/seconds: immediate interpretation and context updates;
- seconds/minutes: active conversation and task reasoning;
- minutes/hours: situation tracking and routine detection;
- days/weeks: memory consolidation, relationship changes, learning;
- long-term: knowledge evolution and validated behavioral adaptation.

## Degradation

Cognition must degrade gracefully:

- no VLM → use available perception signals;
- no face recognition → treat identity as uncertain;
- no speech recognition → use other interaction channels;
- reasoning model unavailable → deterministic capabilities remain operational;
- memory unavailable → explicitly mark reduced context rather than fabricate continuity.

## Acceptance Criteria

The cognition architecture is acceptable when Novi can maintain a coherent world representation, combine multiple modalities, retrieve relevant prior experience, distinguish fact from hypothesis, reason using a local model, explain the provenance of consequential derived state, handle contradictions, and operate without requiring cloud connectivity for core cognition.
