# 01 — Memory Taxonomy and Core Model

**Status:** CANONICAL — CONSOLIDATED V1.1

## Purpose

Define Novi's semantic memory model, memory classes, ownership boundaries, and the distinction between active context and durable memory.

The canonical architecture treats memory as a governed, evidence-linked state system. Experience is not automatically memory; memory is not automatically knowledge; knowledge is not automatically truth.

## Core architecture

```text
Perception / User / Tools / Other Agents
              ↓
        Observation / Event
              ↓
        Memory Write Gate
              ↓
       Episode / Candidate
              ↓
      Durable Memory / Knowledge
              ↓
        Indexes / Retrieval
              ↓
       Context / Cognition
```

The Memory Manager owns persistence and memory lifecycle. Cognition interprets retrieved information. Memory cannot directly authorize an action.

## Memory classes

### Working memory

Temporary task state needed for current reasoning: active entities, recent observations, tool results and hypotheses. Presence here does not imply durable persistence.

### Session/conversation memory

Short-lived interaction state: recent turns, current topic, unresolved questions and active commitments.

### Episodic memory

Meaningful experiences and events, preserving who/what/where/when, sequence, context, evidence and outcome.

### Semantic memory / knowledge

Durable concepts, relationships and claims about people, objects, devices, places, routines and the wider world.

### Procedural memory

Validated procedures and reusable ways of performing tasks. Procedures carry preconditions, steps, expected outcomes, failure handling and authorization requirements.

### Prospective memory

Future-directed intentions and commitments. Intention, action and completion remain separate states.

### Relationship memory

Evidence and state associated with relationships between Novi and people/entities, including interaction history and confirmed preferences.

### Spatial memory

Locations, maps, landmarks, room/object relationships and persistent spatial associations. Historical spatial memory must remain distinct from current localization.

### Temporal memory

Time-dependent patterns, routines, schedules, event sequences and validity intervals.

### Preference memory

Explicit or strongly supported preferences. Preferences retain source, scope and confidence and remain reversible.

### Operational memory

Validated information about Novi's own devices, software, capabilities, sensors, battery behavior, IoT devices and environment configuration.

### Metamemory

Information about memory availability, reliability, completeness and limitations. Retrievable, known, true, current and verified are separate properties.

## Typed memory over embeddings

Embeddings are retrieval indexes, not the semantic memory model. Durable records must have typed semantics, stable identity and appropriate lifecycle/provenance metadata. A single experience may produce several derived memories, but each derivative retains links to its originating episode/evidence.

```text
Episode
 ├── temporal pattern candidate
 ├── relationship evidence
 ├── routine candidate
 └── episodic record
```

## Canonical MemoryRecord contract

Every durable memory object should be representable by a stable, typed semantic record. The exact physical schema may vary by implementation, but the semantic contract must remain stable.

```text
MemoryRecord
├── memory_id
├── memory_type
├── subject_refs
├── content_or_claim
├── source_refs
├── evidence_refs
├── provenance_ref
├── epistemic_status
├── confidence
├── verification_state
├── temporal_scope
├── spatial_scope
├── privacy_class
├── access_policy_ref
├── retention_policy_ref
├── dependency_refs
├── derivation_refs
├── lifecycle_state
├── version
└── integrity_metadata
```

Required fields must not be fabricated. Unknown values are represented explicitly as unknown/unavailable where the schema permits.

## Common metadata

Where applicable, persistent objects should support:

```text
ID
TYPE
OWNER
SOURCE
CREATED_AT
UPDATED_AT
VALID_TIME
CAPTURE_TIME
PROVENANCE
VERSION
CONFIDENCE
EPISTEMIC_STATUS
SENSITIVITY
ACCESS_POLICY
RETENTION_POLICY
DEPENDENCIES
DERIVATIONS
INTEGRITY_METADATA
```

## Memory authority matrix

Memory is evidence-bearing state, not an authority mechanism.

| State/source | May inform reasoning | May authorize action | May override current authoritative state |
|---|---:|---:|---:|
| Historical memory | Yes | No | No |
| Verified knowledge | Yes | No | No |
| Current authoritative telemetry | Yes | No | Only within its defined domain |
| Policy/governance decision | Yes | Yes | Within policy scope |
| Authenticated human authorization | Yes | Yes | Policy-dependent |
| Model-generated hypothesis | Only as labeled hypothesis | No | No |

## Epistemic separation

```text
Observation ≠ Evidence
Evidence ≠ Claim
Claim ≠ Belief
Belief ≠ Decision
Decision ≠ Authorization
Authorization ≠ Safety
```

A model-generated derivative is not independent evidence of its own source.

## Active versus durable memory

```text
ACTIVE
working state
current conversation
current situation
recent relevant memories
        ↓
     retrieval
        ↓
DURABLE
episodes / knowledge / procedures / relationships / spatial / temporal state
```

The model context window is not the durable memory store.

## Current-state precedence

Historical memory cannot override current authoritative state where current truth matters. Current telemetry, authorization, location, device state and safety conditions take precedence over historical memory.

## Abstention and insufficient knowledge

Memory consumers must support explicit epistemic outcomes rather than forcing every request into an answer:

```text
ANSWER
ANSWER_WITH_UNCERTAINTY
REQUEST_CLARIFICATION
REVALIDATE
ABSTAIN
ESCALATE_TO_HUMAN
```

A memory subsystem must prefer abstention or revalidation when evidence is insufficient for the consequence of the requested operation.

## Canonical boundaries

- Memory semantics live in this domain.
- Physical storage mechanics belong to system/storage architecture.
- Distributed transaction and replication semantics belong to system architecture.
- Authorization is governed by the machine-governance layer.
- Human escalation and accountability belong to the human-oversight layer.
- Retrieval is a capability, not a memory type.

## Research and validation basis

The architecture follows current agent-memory research that treats memory as a distinct subsystem requiring explicit design and evaluation, rather than merely an embedding store or prompt extension. Retrieval-augmented systems also require separate evaluation of retrieval relevance, generation accuracy/faithfulness and trustworthiness characteristics.

## Source consolidation

The historical corpus remains preserved in `archive/`. The active authority is this document and the other canonical 01–18 documents.