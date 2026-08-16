# 12 — Cognitive Routing and Model Selection

## Status

**DESIGN**

## Purpose

Define how Novi decides which computational capability should handle a cognitive task. The router is capability-oriented and vendor-neutral.

## Principle

Novi should not ask one large model to perform every task. It should select the simplest reliable capability that satisfies the requirement.

## Routing Hierarchy

```text
incoming cognitive task
        ↓
Can deterministic logic solve it?
        ↓ no
Can retrieval/lookup solve it?
        ↓ no
Can a specialized local model solve it?
        ↓ no
Can a compact reasoning model solve it?
        ↓ no
Use primary reasoning model
        ↓
Can external/cloud service be justified?
```

Cloud is an exception and requires policy approval.

## Capability Classes

Examples:

- deterministic calculation
- database retrieval
- vector retrieval
- OCR
- object detection
- tracking
- face recognition
- speaker recognition
- speech recognition
- VLM reasoning
- embeddings
- reranking
- TTS
- general reasoning
- planning

## Selection Criteria

Candidate implementations are evaluated on:

- open-source status and license
- local execution
- accuracy/quality
- latency
- memory footprint
- power consumption
- hardware compatibility
- model size
- concurrency
- reliability
- maintenance/community health
- security/privacy
- integration complexity
- fallback availability

## Reference Ecosystems

Novi may evaluate NVIDIA, PyTorch, TensorFlow, OpenCV, ONNX Runtime, Hugging Face, ROS 2, Isaac and other open-source ecosystems. None is automatically preferred solely because it is familiar or vendor-owned.

## Model Registry

Each deployable model/capability should have a registry entry containing:

- capability
- implementation
- version
- artifact/source
- license
- hardware targets
- expected resource requirements
- benchmark results
- limitations
- fallback
- status

## Routing Output

A routing decision should be structured:

```json
{
  "capability": "visual_question_answering",
  "implementation": "local_vlm",
  "reason": "requires semantic visual reasoning",
  "confidence": 0.91,
  "fallback": "detector_plus_llm",
  "latency_budget_ms": 1500
}
```

The reason is operational metadata, not hidden chain-of-thought.

## Fallback

If a selected model fails, the router should choose a compatible fallback rather than silently returning a fabricated result.

## Local-First Rule

Every capability begins with local open-source evaluation. Cloud is considered only when no acceptable local solution exists or when a specific external capability is explicitly authorized.

## Acceptance Criteria

The router chooses appropriate capabilities, avoids unnecessary large-model calls, records selections, supports fallback, and remains independent of any single vendor or model family.
