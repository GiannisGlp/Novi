# 04 — Reasoning Engine

## Status

**DESIGN**

## Purpose

The Reasoning Engine converts structured cognitive context into interpretations, predictions, candidate plans, answers, questions, or tool requests. It is a hybrid system, not an LLM-only component.

## Reasoning Classes

### Deterministic reasoning

Use for:

- state validation;
- arithmetic where exact computation is required;
- policy checks;
- temporal calculations;
- schema validation;
- authorization;
- safety constraints;
- deterministic state transitions.

### Retrieval/ranking

Use for:

- memory selection;
- knowledge retrieval;
- semantic similarity;
- evidence ranking.

### Specialized ML

Use for:

- perception interpretation;
- classification;
- embeddings;
- speech;
- vision;
- other domain-specific inference.

### General reasoning model

Use the primary local LLM for:

- semantic reasoning;
- complex conversation;
- synthesis of multiple evidence sources;
- open-ended planning;
- tool selection;
- explanations;
- creative/social responses.

## Model Boundary

The model receives a structured context package, not arbitrary access to internal storage.

```text
Context Builder
      ↓
Model Adapter
      ↓
Reasoning Model
      ↓
Structured Output Parser
      ↓
Validator
      ↓
Cognitive Result
```

## Structured Output

Preferred result types:

- `Answer`
- `ObservationInterpretation`
- `Hypothesis`
- `Question`
- `PlanProposal`
- `ToolRequest`
- `KnowledgeProposal`
- `MemoryProposal`
- `NoAction`

Free-form model text may exist for conversation but consequential system operations require structured representations.

## Tool Calling

A tool request includes:

- tool identifier;
- typed arguments;
- reason/category;
- originating goal;
- expected result;
- timeout;
- authorization context.

The model cannot invent a new privileged tool at runtime.

## Hallucination Containment

The model must be told which context is:

- verified knowledge;
- observation;
- hypothesis;
- user statement;
- uncertain memory;
- tool result.

The validator rejects claims that require unsupported certainty where the task demands evidence.

## Planning

For multi-step tasks the model proposes a plan, but deterministic validators check:

- required fields;
- available capabilities;
- preconditions;
- dependencies;
- timeouts;
- resource requirements;
- safety category.

## Context Budget

Context selection prioritizes:

1. current user request/directive;
2. safety constraints;
3. current world state;
4. active goal;
5. immediate recent events;
6. relevant identity/relationship state;
7. verified knowledge;
8. relevant memory;
9. lower-priority background information.

Large historical context is summarized/retrieved rather than automatically inserted.

## Model Failure

If the reasoning model fails, times out, returns invalid output, or becomes unavailable:

- retry within a bounded policy;
- use a simpler model if configured;
- use deterministic fallback;
- ask the user when required;
- continue safety/robotics operation.

The system must never fabricate a successful model result.

## Multiple Models

Multiple models are allowed when a benchmark demonstrates value. The architecture supports:

- one primary general model;
- small fast model for classification/routing;
- specialized reasoning model;
- VLM;
- domain model.

There is no requirement to use multiple general-purpose LLMs.

## Local-First Requirement

The default deployment must support local reasoning. Model selection considers:

- open-source license/weights;
- local execution;
- Jetson compatibility;
- Mac development compatibility;
- latency;
- quality;
- memory;
- power;
- context length;
- tool calling;
- maintenance.

## Acceptance Criteria

The Reasoning Engine must support structured local inference, validated tool calls, bounded context construction, graceful model failure, provenance-aware reasoning, and deterministic integration tests.
