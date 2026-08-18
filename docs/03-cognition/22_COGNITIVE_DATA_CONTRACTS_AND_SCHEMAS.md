# 22 — Cognitive Data Contracts & Schemas

**Status:** IN PROGRESS — P0 / critical
**Authority:** `docs/03-cognition/`
**Depends on:** System Architecture contract standard, Cognition Implementation Specification, World Model, Cognitive APIs & Contracts, Brain Implementation Blueprint, Soul Constitution, Memory and Autonomy specifications
**Implementation target:** Mac-first; simulation and NVIDIA edge targets later

---

## 1. Purpose

This document defines the canonical typed data objects that cross the Cognition boundary.

The purpose is to prevent implementation from inventing incompatible representations for observations, evidence, world state, situations, people, uncertainty, predictions, cognitive decisions and cognitive events.

These contracts are semantic contracts. Runtime serialization, transport and programming-language representations must conform to them but must not redefine their meaning.

Structured model output must be validated against explicit schemas before entering authoritative cognitive state. NVIDIA documentation similarly treats structured outputs and typed schemas as a mechanism for enforcing machine-readable contracts rather than relying on free-form model output. citeturn0search0turn0search4

---

## 2. Contract principles

1. Every canonical object has one owner.
2. Every object has a stable identifier where identity across events is required.
3. Every time-sensitive observation carries timestamp semantics.
4. Uncertainty is explicit; absence of evidence is not certainty.
5. Provenance travels with evidence and derived state.
6. Model-generated claims are never authoritative merely because a model produced them.
7. Raw observations, interpreted evidence and world state remain distinguishable.
8. Mutable state is versioned or revisioned where concurrent updates are possible.
9. Schema versions are explicit for persisted or independently deployed contracts.
10. Unknown, unavailable and not-applicable are distinct states.
11. Contracts must be language- and vendor-neutral.
12. Serialization must not silently change units, coordinate frames, timestamps or confidence semantics.
13. Safety and authorization state must never be inferred from a generic cognitive claim.
14. Sensitive identity and relationship data require explicit privacy classification.

---

## 3. Canonical object hierarchy

```text
CognitiveEvent
    │
    ├── Observation
    │       ↓
    │   Evidence
    │       ↓
    │   Entity / Relation / Event hypothesis
    │       ↓
    │   WorldState
    │       ↓
    │   SituationState
    │       ↓
    │   Prediction / Interpretation
    │       ↓
    │   CognitiveDecisionRecord
    │
    └── Provenance / Uncertainty / Timing metadata
```

No layer may silently collapse another layer.

---

## 4. Contract envelope

All cross-domain cognitive objects should share a common envelope:

```yaml
schema_version: "1.0"
contract_type: "<canonical-type>"
id: "<stable-id>"
created_at: "<timestamp>"
updated_at: "<timestamp>"
source:
  component: "<producer>"
  instance: "<optional-instance>"
  software_version: "<version>"
provenance:
  source_ids: []
  derivation_chain: []
privacy:
  classification: "PUBLIC|INTERNAL|PERSONAL|SENSITIVE|RESTRICTED"
trace:
  correlation_id: "<id>"
  causation_id: "<id|null>"
```

Fields may be omitted only where a domain-specific contract explicitly declares them unnecessary.

---

## 5. Observation

An **Observation** represents sensor/runtime evidence before semantic interpretation.

```yaml
Observation:
  id: string
  modality: camera|microphone|imu|depth|lidar|touch|system|other
  sensor_id: string
  timestamp:
    sensor_time: timestamp
    receive_time: timestamp
    clock_domain: string
  frame_id: string|null
  payload_ref: string
  quality:
    score: float|null
    flags: []
  calibration_version: string|null
  provenance: Provenance
```

Observation must not claim that a person, object, intention or event exists unless a separate interpretation layer has established that claim.

---

## 6. Evidence

**Evidence** is an interpreted, bounded claim derived from one or more observations.

```yaml
Evidence:
  id: string
  type: person_detection|object_detection|speech|gesture|gaze|audio_event|motion|pose|text|other
  subject_ref: string|null
  attributes: object
  confidence: float
  uncertainty: object
  source_observation_ids: []
  valid_from: timestamp
  valid_until: timestamp|null
  provenance: Provenance
```

Confidence is not a probability unless the producer explicitly declares calibration semantics.

Evidence may be contradictory. Contradictions must be represented, not silently discarded.

---

## 7. Entity reference

Entities represent persistent or temporally tracked things in the world model.

```yaml
Entity:
  id: string
  type: person|object|place|robot|device|organization|other
  labels: []
  attributes: object
  state: object
  spatial_ref: string|null
  confidence: float
  provenance: Provenance
  lifecycle:
    first_seen: timestamp
    last_seen: timestamp
    status: active|lost|unknown|retired
```

Person identity is especially sensitive and must carry privacy classification and identification confidence.

---

## 8. Relation

Relations connect entities or contextual concepts.

```yaml
Relation:
  id: string
  subject_ref: string
  predicate: string
  object_ref: string
  confidence: float
  temporal_scope:
    valid_from: timestamp
    valid_until: timestamp|null
  evidence_ids: []
  provenance: Provenance
```

Examples:

```text
Alice --looking_at--> Novi
Alice --speaking_to--> Bob
Novi --located_near--> table
Alice --knows--> Novi
```

Relationship interpretation belongs to Cognition; durable relationship history belongs to Memory; Soul defines the behavioral meaning of relationships.

---

## 9. WorldState

WorldState is Cognition's current structured representation of relevant external reality.

```yaml
WorldState:
  revision: integer
  timestamp: timestamp
  entities: []
  relations: []
  active_events: []
  spatial_state: object
  temporal_context: object
  uncertainty_summary: object
  source_event_ids: []
```

WorldState must be revisioned. Consumers must be able to identify which revision they observed when making a decision.

WorldState is not a permanent memory store.

---

## 10. SituationState

SituationState represents Cognition's interpretation of what is currently happening.

```yaml
SituationState:
  id: string
  world_revision: integer
  context_type: string
  participants: []
  likely_addressees: []
  current_activity: string|null
  salient_events: []
  social_context: object
  goals_hypotheses: []
  risks: []
  uncertainty: object
  valid_until: timestamp|null
```

Examples:

- five people are having a private conversation;
- a person is directly addressing Novi;
- someone appears to need assistance;
- the room is noisy and speech attribution is uncertain.

SituationState is an interpretation, not ground truth.

---

## 11. PersonContext

PersonContext is the current cognitive interpretation of a person relevant to the situation.

```yaml
PersonContext:
  person_ref: string
  presence_confidence: float
  identity_confidence: float
  attention:
    looking_toward_novi: float|null
    body_orientation: float|null
    engagement: float|null
  speech:
    active: boolean
    addressee_hypothesis: string|null
  relationship:
    category: string|null
    confidence: float|null
  interaction_permissions: []
  current_context: object
  evidence_ids: []
```

Cognition must not invent relationship or permission facts. Durable evidence comes from Memory and authorization state comes from the appropriate policy/permission authority.

---

## 12. AttentionCandidate

```yaml
AttentionCandidate:
  id: string
  target_ref: string
  reason: direct_address|salience|task|safety_signal|curiosity|continuity|other
  score: float
  urgency: low|medium|high|critical
  evidence_ids: []
  expires_at: timestamp|null
```

Cognition supplies evidence and candidate salience. Autonomy owns the decision to allocate attention or act.

---

## 13. IntentHypothesis

```yaml
IntentHypothesis:
  id: string
  actor_ref: string|null
  target_ref: string|null
  intent_type: string
  probability: float|null
  confidence: float
  evidence_ids: []
  alternatives: []
  assumptions: []
  expires_at: timestamp|null
```

The system must distinguish:

```text
observed fact
vs
inferred interpretation
vs
hypothesis
```

Intent is inherently uncertain and must not be treated as fact merely because the model is confident.

---

## 14. Prediction

```yaml
Prediction:
  id: string
  target: string
  predicted_outcome: object
  horizon:
    start: timestamp
    end: timestamp
  confidence: float
  assumptions: []
  evidence_ids: []
  model_ref: string|null
```

Predictions are disposable hypotheses unless promoted into another authoritative state through an explicit contract.

---

## 15. CognitiveDecisionRecord

This records a cognitive interpretation or recommendation without becoming an autonomy action command.

```yaml
CognitiveDecisionRecord:
  id: string
  timestamp: timestamp
  situation_ref: string
  interpretation: object
  alternatives: []
  uncertainty: object
  rationale_refs: []
  recommended_next_states: []
  model_refs: []
  policy_constraints_observed: []
```

Cognition must not directly command motors, grant permissions or mutate Soul identity.

---

## 16. CognitiveEvent

All meaningful cognitive transitions should be observable through events.

```yaml
CognitiveEvent:
  id: string
  type: observation_received|evidence_created|world_updated|situation_updated|prediction_created|interpretation_created|decision_recorded|cognitive_error|other
  timestamp: timestamp
  payload_ref: string
  source_component: string
  correlation_id: string
  causation_id: string|null
  schema_version: string
```

Events should be append-only from the event producer's perspective.

---

## 17. Uncertainty contract

Uncertainty must support at least:

```yaml
Uncertainty:
  confidence: float|null
  probability: float|null
  interval: object|null
  competing_hypotheses: []
  calibration_status: calibrated|uncalibrated|unknown
  source: string
```

Do not convert confidence to probability without an explicit calibration method.

A system may state:

> confidence = 0.82

without claiming:

> probability = 0.82

unless the metric is calibrated for that interpretation.

---

## 18. Provenance contract

Every derived cognitive claim must be traceable to its sources.

```yaml
Provenance:
  source_ids: []
  producer: string
  producer_version: string
  model_ref: string|null
  created_at: timestamp
  transformation: string
  parent_revision: string|null
```

The minimum trace should support:

```text
sensor
 → observation
 → evidence
 → interpretation
 → world/situation state
 → decision record
```

This is required for debugging, evaluation, contradiction handling and scientific validation.

---

## 19. Time contract

Cognitive timestamps must distinguish:

- sensor time;
- receive time;
- processing time;
- event time;
- simulation time where applicable.

Every time-sensitive object must declare its clock domain.

Ordering must not rely solely on wall-clock timestamps. Event correlation and causal identifiers are required where ordering matters.

---

## 20. Coordinate and frame contract

Spatial objects must identify their coordinate frame.

```yaml
SpatialReference:
  frame_id: string
  position: [x, y, z]
  orientation: [qx, qy, qz, qw]
  timestamp: timestamp
```

A position without a frame is invalid for authoritative spatial reasoning.

Units must be explicit and standardized by the system architecture. No consumer may silently assume units.

---

## 21. Schema versioning

All independently persisted or deployed contracts must carry `schema_version`.

Compatibility rules:

```text
PATCH
backward-compatible clarification/fix

MINOR
backward-compatible field addition

MAJOR
breaking semantic or structural change
```

Persisted records must remain readable through a migration or compatibility layer before a schema version is retired.

This follows the general principle of explicit contract versioning used in current NVIDIA typed cross-language contracts. citeturn0search4

---

## 22. Structured model outputs

Neural models may produce structured candidate objects, but model output is **untrusted input** to the cognitive runtime until validation succeeds.

Pipeline:

```text
model
 ↓
raw output
 ↓
schema validation
 ↓
semantic validation
 ↓
provenance attachment
 ↓
confidence handling
 ↓
cognitive state update
```

Schema validation must reject malformed outputs rather than allowing arbitrary model text to become authoritative state.

NVIDIA's current NeMo tooling explicitly supports JSON-schema/Pydantic structured outputs and structured-output validation, reinforcing this design pattern. citeturn0search0turn0search6

---

## 23. Null, unknown and unavailable

These values have distinct meanings:

```text
null
= field has no applicable value

unknown
= value may exist but Novi does not know it

unavailable
= capability/data source is currently unavailable

not_observed
= the system has not obtained relevant evidence
```

Do not collapse these into a single null value.

---

## 24. Contradiction handling

Conflicting evidence must remain traceable.

```text
Evidence A: Alice is looking at Novi
Evidence B: Alice is looking at Bob
             ↓
      competing evidence
             ↓
      uncertainty update
             ↓
    situation interpretation
```

Cognition may select a current hypothesis, but the underlying evidence must remain available for audit and revision.

---

## 25. Privacy classification

Cognitive objects can contain highly sensitive information, particularly:

- person identity;
- faces;
- voice identity;
- relationship information;
- inferred intent;
- behavioral patterns;
- private conversation content;
- location history.

Privacy classification is therefore part of the contract envelope, not merely an external database concern.

The cognitive runtime must minimize propagation of sensitive data and only expose the fields required by downstream consumers.

---

## 26. Domain ownership matrix

| Object | Owner | Consumers | Must not own |
|---|---|---|---|
| Observation | Perception/Brain | Cognition | interpretation |
| Evidence | Cognition | World/Situation/Memory | physical action |
| Entity | Cognition | Memory/Autonomy | personality |
| Relation | Cognition | Memory/Autonomy | permissions |
| WorldState | Cognition | Autonomy/Brain | durable memory |
| SituationState | Cognition | Autonomy | action execution |
| PersonContext | Cognition | Autonomy/Soul-facing context | relationship history |
| AttentionCandidate | Cognition | Autonomy | final attention decision |
| IntentHypothesis | Cognition | Autonomy | factual identity/intent |
| Prediction | Cognition | Autonomy/Validation | commitment |
| CognitiveDecisionRecord | Cognition | Autonomy/Validation | action authorization |
| MemoryRecord | Memory | Cognition/Soul/Autonomy | cognitive interpretation |
| SoulState | Soul | Cognition/Autonomy/Brain | runtime state |
| ActionProposal | Autonomy | Policy/Brain | cognitive truth |

---

## 27. Canonical data flow

```text
Sensors / external inputs
        ↓
Observation
        ↓
Evidence
        ↓
Entity + Relation updates
        ↓
WorldState revision
        ↓
SituationState
        ↓
Intent / Prediction / Attention candidates
        ↓
CognitiveDecisionRecord
        ↓
Autonomy
        ↓
Policy / Safety
        ↓
Brain execution
        ↓
Outcome evidence
        ↺
```

Memory and Soul are connected through explicit contracts rather than hidden mutation.

---

## 28. Mac-first implementation requirements

The first implementation should use strongly typed in-process representations before introducing distributed transport.

Recommended progression:

```text
Python typed models / equivalent
        ↓
validation tests
        ↓
event serialization
        ↓
process boundary where required
        ↓
ROS 2/message adapters in simulation/robot profiles
```

The semantic contract must remain identical across these profiles.

Do not prematurely distribute the Mac Brain into multiple network services.

---

## 29. Required implementation artifacts

Before Cognition implementation is marked ready, the repository must contain:

1. canonical schema definitions;
2. serialization format decision;
3. validation library choice;
4. schema versioning policy;
5. migration policy;
6. example valid objects;
7. example invalid objects;
8. contract unit tests;
9. round-trip serialization tests;
10. backward-compatibility tests;
11. provenance tests;
12. timestamp/frame tests;
13. uncertainty tests;
14. privacy classification tests;
15. model-output validation tests;
16. contract documentation generated from the authoritative definitions where practical.

---

## 30. Acceptance tests

### AT-01 — Observation provenance

Given an observation, the system can identify its sensor, clock domain, timestamp and payload source.

### AT-02 — Evidence derivation

Given observations, an evidence object references its source observations and records confidence/provenance.

### AT-03 — World revision

Given new evidence, WorldState increments revision and consumers can identify the source revision.

### AT-04 — Situation uncertainty

Given ambiguous social evidence, SituationState represents competing hypotheses instead of claiming certainty.

### AT-05 — Structured model rejection

Given malformed model output, schema validation rejects it before authoritative state mutation.

### AT-06 — Provenance chain

Given a cognitive decision, the system can trace it back to source observations.

### AT-07 — Time correctness

Given delayed sensor data, event ordering remains explainable through timestamps, clock domains and causal identifiers.

### AT-08 — Frame correctness

Given observations from different sensors, spatial state cannot be merged without compatible frame information.

### AT-09 — Schema compatibility

A supported older schema can be migrated or read according to the declared compatibility policy.

### AT-10 — Domain boundary

Cognition cannot directly mutate Soul identity, grant permissions, execute physical actions or create durable memory without the appropriate contract.

---

## 31. Research basis

The contract design is grounded in established engineering requirements for typed, structured and traceable AI systems.

NVIDIA NeMo documentation currently supports structured outputs using explicit schemas such as Pydantic models and JSON schemas, and NVIDIA's evaluation tooling includes explicit structured-output validation. citeturn0search0turn0search6

NVIDIA NeMo Fabric also documents typed cross-language contracts, explicit schema/contract versions and stable runtime request/result/event schemas, which supports the use of explicit versioned contracts for Novi's cross-component interfaces. citeturn0search2turn0search4

These sources validate the **engineering pattern**. They do not dictate Novi's domain semantics or automatically justify adoption of a particular NVIDIA component.

---

## 32. Completion gate

This document is **not complete** until:

- canonical schema definitions exist in the implementation repository;
- every P0 object has an owner;
- serialization and versioning are decided;
- validation is executable;
- examples and negative cases exist;
- provenance and timing semantics are tested;
- model-generated objects cannot bypass validation;
- all Cognition APIs reference these canonical contracts;
- Memory, Autonomy, Soul and Brain interfaces are reconciled against them;
- Mac-first implementation can instantiate the contracts without semantic invention.

**Current state: SPECIFICATION DRAFT — implementation contract work in progress.**

---

## 33. Architectural invariant

> **No observation, inference, world-state update, prediction or cognitive decision becomes authoritative merely because a model produced it. Every cross-domain cognitive object must have an explicit schema, owner, provenance, uncertainty semantics, temporal semantics and validation path.**
