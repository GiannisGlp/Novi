# 26 — Cognitive Typed Model Implementation Baseline

**Status:** P0 — implementation baseline
**Authority:** `docs/03-cognition/`
**Depends on:** 14 Cognitive Data Model, 15 Cognitive APIs and Contracts, 21 Cognition Implementation Specification, 22 Cognitive Data Contracts and Schemas, 25 Cognitive Contract Reconciliation, System Architecture contract standard
**Target:** Mac-first semantic core; later simulation and edge/robot deployment

---

## 1. Purpose

This document defines the first executable representation of Novi's canonical cognitive contracts.

It does **not** introduce new semantic objects. It turns the already-approved contracts into an implementation pattern that can be instantiated, validated, serialized, replayed and tested on the Mac.

The first implementation should be strongly typed and local. Distributed transport, ROS 2 adapters and hardware-specific serialization are later layers.

---

## 2. Implementation decision

The initial Python implementation should use **Pydantic v2 models** as the typed boundary, with JSON Schema generated from those models for interoperability.

Pydantic is selected here as an implementation mechanism, not as a semantic authority. Its models must conform to Novi's canonical contracts. Pydantic v2 provides typed validation and JSON Schema generation, making it suitable for this first contract layer. citeturn1search0turn1search2

The architecture remains language-neutral:

```text
Novi semantic contract
        ↓
Python/Pydantic implementation
        ↓
JSON Schema
        ↓
other-language adapters
        ↓
ROS 2 / transport / persistence
```

A future Rust, C++, TypeScript or ROS representation must preserve the same semantics.

---

## 3. Canonical implementation package

When source code is introduced, the initial package should follow a structure equivalent to:

```text
cognition/
  contracts/
    __init__.py
    common.py
    observation.py
    evidence.py
    entity.py
    relation.py
    world_state.py
    situation_state.py
    person_context.py
    attention.py
    intent.py
    prediction.py
    decision.py
    events.py
    schemas.py
  validation/
    structural.py
    semantic.py
    provenance.py
    cross_contract.py
  replay/
    loader.py
    runner.py
  tests/
    contracts/
    validation/
    replay/
```

The exact repository source location is deferred until the project source tree is created. This document must not imply that documentation files are themselves runtime code.

---

## 4. Common contract types

The implementation must establish reusable types for:

```text
SchemaVersion
ContractEnvelope
Identifier
Timestamp
ClockDomain
Provenance
Uncertainty
PrivacyClassification
SpatialReference
LifecycleState
CorrelationId
CausationId
```

These types should be defined once and reused rather than reimplemented in every cognitive object.

---

## 5. Strict validation policy

Incoming model/runtime data is untrusted until validation succeeds.

The validation sequence is:

```text
raw input
   ↓
parse
   ↓
structural validation
   ↓
semantic validation
   ↓
provenance validation
   ↓
ownership/reference validation
   ↓
accepted cognitive object
```

Malformed data must be rejected with a typed validation error. It must not be silently coerced into an authoritative cognitive state.

Strictness should be strongest at domain boundaries and persistence boundaries. Convenience coercion may be used inside carefully controlled application code, but canonical serialized contracts should have deterministic semantics.

---

## 6. Canonical typed objects

The first implementation set is:

| Type | Owner | Purpose |
|---|---|---|
| `Observation` | Perception/Brain boundary | raw observation reference |
| `Evidence` | Cognition | interpreted evidence |
| `Entity` | Cognition | tracked world entity |
| `Relation` | Cognition | typed relationship between entities |
| `WorldState` | Cognition | current semantic world state |
| `SituationState` | Cognition | current contextual interpretation |
| `PersonContext` | Cognition | current person-specific context |
| `AttentionCandidate` | Cognition → Autonomy | candidate salience |
| `IntentHypothesis` | Cognition | uncertain intent interpretation |
| `Prediction` | Cognition | future-state hypothesis |
| `CognitiveDecisionRecord` | Cognition | structured interpretation/recommendation |
| `CognitiveEvent` | Cognition runtime | observable cognitive transition |

`MemoryRecord`, `SoulState` and `ActionProposal` are referenced but remain owned by their respective domains.

---

## 7. Contract envelope

Every persisted or independently exchanged canonical object should expose:

```python
schema_version
contract_type
id
created_at
updated_at
source
provenance
privacy
trace
```

The envelope is metadata. It must not be used to hide semantic fields that belong to the canonical object itself.

---

## 8. Observation implementation

`Observation` must preserve sensor/runtime provenance and avoid semantic overclaiming.

Minimum implementation fields:

```text
id
modality
sensor_id
sensor_time
receive_time
clock_domain
frame_id
payload_ref
quality
calibration_version
provenance
```

An observation may say:

```text
camera detected pixels consistent with a person
```

It must not silently become:

```text
Vano is present
```

That transformation belongs to evidence/identity interpretation.

---

## 9. Evidence implementation

`Evidence` represents a bounded interpreted claim.

It must include:

```text
id
type
subject_ref
attributes
confidence
uncertainty
source_observation_ids
valid_from
valid_until
provenance
```

Confidence and probability must remain separate fields. A confidence value must not be presented as a calibrated probability unless its calibration status supports that interpretation.

---

## 10. Entity and relation implementation

Entities use stable internal IDs independent of model-generated names.

Relations reference entity IDs rather than embedding duplicate entity descriptions.

Example:

```text
Entity(person_123)
Entity(robot_001)

Relation(
  subject_ref=person_123,
  predicate="looking_at",
  object_ref=robot_001
)
```

This allows names, recognition hypotheses and labels to change without changing the identity of the internal entity record.

---

## 11. WorldState implementation

`WorldState` must be revisioned.

```text
revision
 → entities
 → relations
 → active_events
 → spatial_state
 → temporal_context
 → uncertainty_summary
 → source_event_ids
```

A consumer must be able to record which world revision it used.

A new world revision does not erase historical evidence. Historical persistence belongs to Memory/Knowledge.

---

## 12. SituationState implementation

`SituationState` is a derived context object.

It should reference a specific `world_revision` and contain:

- participants;
- likely addressees;
- current activity;
- salient events;
- social context;
- goal hypotheses;
- risks;
- uncertainty;
- expiration/validity.

It must remain possible to reconstruct why a situation was inferred from the underlying WorldState and evidence.

---

## 13. PersonContext implementation

Person context is intentionally **not** a complete person profile.

It should contain only the current information Cognition needs:

```text
person_ref
presence_confidence
identity_confidence
attention cues
speech/addressee cues
relationship category/confidence
authorized interaction context
current context
evidence references
```

Durable relationship history belongs to Memory, canonical relationship behavior belongs to Soul, and authorization belongs to the policy/permission authority.

---

## 14. AttentionCandidate and IntentHypothesis

These are proposals for downstream autonomy, not commands.

```text
Cognition
  ↓
AttentionCandidate
  ↓
Autonomy
  ↓
attention decision
```

and:

```text
Cognition
  ↓
IntentHypothesis
  ↓
Autonomy/context
  ↓
possible response
```

Neither object may grant authorization or directly trigger an actuator.

---

## 15. CognitiveDecisionRecord

The record captures a structured cognitive result:

```text
situation_ref
interpretation
alternatives
uncertainty
rationale_refs
recommended_next_states
model_refs
policy_constraints_observed
```

It is deliberately different from an `ActionProposal`.

```text
CognitiveDecisionRecord
        ≠
ActionProposal
```

The first describes Cognition's interpretation/recommendation. The second is owned by Autonomy and subsequently governed by Policy/Safety.

---

## 16. CognitiveEvent

Meaningful state transitions must be observable as typed events.

At minimum:

```text
observation_received
evidence_created
world_updated
situation_updated
prediction_created
interpretation_created
decision_recorded
cognitive_error
```

Every event carries correlation and causation identifiers where applicable.

Events are the foundation for deterministic replay and cross-domain observability.

---

## 17. Semantic validators

Structural validation alone is insufficient.

Semantic validators must verify at least:

### References

- referenced entity exists or is explicitly unresolved;
- world revision exists;
- situation references a valid world revision;
- evidence references valid observations;
- decisions reference a valid situation.

### Time

- timestamps are parseable;
- validity intervals are coherent;
- clock domain is declared;
- impossible ordering is rejected or explicitly marked uncertain.

### Uncertainty

- confidence is within the defined range;
- probability is within the defined range;
- calibration status is explicit;
- alternatives are compatible with the hypothesis.

### Ownership

- Cognition cannot create a Soul-authoritative personality mutation;
- Cognition cannot create an authorization grant;
- Cognition cannot create a physical action command.

### Privacy

- sensitive person/biometric fields carry appropriate classification;
- downstream context cannot silently downgrade classification.

---

## 18. Provenance validator

Every derived object must be traceable.

Minimum chain:

```text
source
 → observation
 → evidence
 → derived object
```

For model-derived results:

```text
input references
 + model ID/version
 + runtime
 + timestamp
 + transformation
 → result
```

Missing provenance must cause rejection for objects designated as decision-relevant or durable.

---

## 19. Serialization

JSON is the initial interchange representation because it is portable across Python, future services, test fixtures and model-facing adapters.

JSON Schema should be generated and versioned from the canonical typed implementation rather than independently hand-maintained wherever practical.

NVIDIA's current tooling similarly uses Pydantic/JSON Schema for structured data and explicit JSON-schema validation, supporting this implementation pattern. citeturn0search0turn0search1

Serialization must preserve:

- units;
- clock domain;
- coordinate frame;
- schema version;
- privacy classification;
- provenance;
- uncertainty semantics.

---

## 20. Replay fixtures

The implementation must include deterministic fixtures for at least:

1. unknown person enters room;
2. known person identified with multimodal evidence;
3. five-person conversation where Novi is not addressed;
4. person directly addresses Novi;
5. ambiguous addressee;
6. contradictory camera/audio evidence;
7. stale world-state evidence;
8. reasoning model returns malformed JSON;
9. reasoning model unavailable;
10. memory unavailable;
11. privacy-filtered context;
12. action proposal returned to Autonomy without Cognition bypassing policy.

Fixtures should use structured observations/evidence rather than requiring private raw media.

---

## 21. Property and invariant tests

Tests should verify invariants such as:

```text
No observation becomes a verified fact without an explicit promotion path.
No model output becomes authoritative without validation.
No Cognition object grants authorization.
No Cognition object directly commands hardware.
No world revision silently destroys provenance.
No sensitive context is propagated without classification.
No prediction overwrites observed state.
No schema migration changes semantic meaning silently.
```

These should become automated tests when source implementation begins.

---

## 22. Generated schema policy

The source-of-truth sequence is:

```text
Novi semantic contract
        ↓
typed implementation
        ↓
generated JSON Schema
        ↓
contract fixtures
        ↓
API/transport adapters
```

Do not manually maintain a second incompatible schema hierarchy.

When a breaking schema change is necessary:

1. create/update the relevant decision record;
2. increment the major schema version;
3. add migration/compatibility tests;
4. retain historical fixtures;
5. update consumers deliberately.

---

## 23. Validation error contract

Validation failures should be machine-readable and auditable.

Minimum error categories:

```text
schema_invalid
field_invalid
reference_invalid
time_invalid
coordinate_invalid
provenance_missing
privacy_invalid
ownership_violation
semantic_conflict
unsupported_version
```

Errors should include the contract type, schema version, field/path where possible, correlation ID and safe diagnostic metadata.

Raw sensitive payloads should not be copied into error telemetry unnecessarily.

---

## 24. Performance baseline

The first benchmark should measure:

- model construction latency;
- validation latency;
- serialization latency;
- deserialization latency;
- memory footprint;
- throughput under event bursts;
- replay throughput;
- concurrent validation behavior.

No production latency target is frozen until measured on the Mac-first environment.

The benchmark must include both normal operation and burst conditions.

---

## 25. Mac-first implementation sequence

```text
1. Define typed common primitives
2. Implement Observation/Evidence
3. Implement Entity/Relation
4. Implement WorldState
5. Implement SituationState/PersonContext
6. Implement uncertainty/provenance validators
7. Implement Attention/Intent/Prediction
8. Implement CognitiveDecisionRecord/Event
9. Generate JSON Schemas
10. Build replay fixtures
11. Add contract tests
12. Benchmark on M3 Pro
13. Integrate with Brain/Cognition runtime
```

No physical robot is required for this phase.

---

## 26. Completion gate

This baseline is implementation-complete when:

- every canonical object has one typed representation;
- JSON Schema is generated and versioned;
- structural and semantic validators exist;
- provenance is enforced;
- ownership boundaries are tested;
- replay fixtures exist;
- migrations are tested;
- Mac performance is measured;
- the runtime can consume the contracts without inventing new semantic fields.

Until those conditions are met, Cognition remains **implementation-in-progress**.

---

## 27. Research basis

The implementation pattern is supported by authoritative documentation for the selected tooling approach. NVIDIA NeMo documents structured outputs using Pydantic models or JSON Schema and explicit schema-conforming generation. NeMo Evaluator provides JSON Schema validation as a scoring primitive. citeturn0search0turn0search1

Pydantic's current documentation describes v2 validation/configuration and JSON Schema generation as core mechanisms for typed model validation. citeturn1search0turn1search2

These sources support the engineering mechanism only. Novi's semantic definitions and ownership remain governed by its own architecture documents.

---

## 28. Final rule

> **The typed implementation is a faithful executable representation of Novi's cognitive contracts—not a new architecture.**
