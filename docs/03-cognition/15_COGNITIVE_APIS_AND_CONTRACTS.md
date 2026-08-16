# 15 — Cognitive APIs and Contracts

## Status

**DESIGN**

## Purpose

Define stable boundaries between cognition and the rest of Novi so implementation details and vendors can change without rewriting the cognitive architecture.

## Core Interfaces

```text
PerceptionProvider
WorldModel
IdentityService
MemoryService
KnowledgeService
ContextEngine
ReasoningModel
ModelRouter
PersonalityService
PredictionService
ToolRegistry
PolicyService
AuditService
```

## Cognitive Request

Every major reasoning request should identify:

- request ID
- task type
- actor/context
- current situation
- goal if applicable
- required capabilities
- latency budget
- privacy scope
- risk class
- cancellation deadline

## Cognitive Result

Results should contain:

- request ID
- result type
- structured payload
- confidence where applicable
- provenance references
- model/capability used
- timing metadata
- fallback status
- errors/warnings

## Model Contract

Models are invoked through a common contract. The caller should not depend on vendor-specific APIs outside the adapter.

## Tool Contract

Tools expose typed capabilities. Examples:

```text
navigate
query_knowledge
store_memory
control_iot
speak
show_on_screen
capture_image
play_audio
request_user_confirmation
```

Tool arguments must be schema validated before execution.

## Capability Discovery

The model router can query available capabilities, constraints, cost, latency, and current health without exposing unrestricted implementation details.

## Error Contract

Errors must be typed:

- unavailable
- invalid_request
- unauthorized
- policy_denied
- safety_denied
- timeout
- resource_exhausted
- dependency_failure
- model_failure
- data_conflict
- degraded

## Versioning

Interfaces are versioned. Breaking changes require explicit migration. Capability adapters may expose compatibility layers.

## Vendor Boundary

NVIDIA, PyTorch, TensorFlow, OpenCV, ONNX Runtime, Hugging Face, ROS 2, Isaac and other technologies must be integrated behind adapters where practical. The cognitive contracts are owned by Novi.

## Acceptance Criteria

A model, database, perception engine, or vendor-specific runtime can be replaced without changing consumers that depend only on the stable cognitive contracts.
