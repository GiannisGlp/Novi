# 16 — Canonical System Contracts

**Status:** P0 normative contract baseline  
**Purpose:** Define the minimum semantic contracts shared by architecture domains. Serialization, transport and storage implementations remain replaceable.

## 1. Contract principle

The contract describes **meaning**, not implementation.

A JSON schema, protobuf definition, database table or ROS message may implement a contract, but none becomes the semantic authority merely because it is the wire format.

Every contract has:

- stable identity;
- version;
- required fields;
- semantics;
- provenance;
- time semantics;
- authorization expectations;
- failure behavior.

## 2. EventEnvelope

Represents a durable or operationally significant event.

```text
EventEnvelope
├── event_id                 required, globally unique within deployment
├── event_type               required, semantic type
├── schema_version           required
├── occurred_at              required, event/world time
├── recorded_at              required, durable-record time when applicable
├── producer_id              required
├── actor_context            optional/required by event class
├── authority_context        required for consequential actions
├── subject_refs[]            required where subjects exist
├── causation_id             optional
├── correlation_id           optional
├── parent_event_refs[]      optional
├── state_revision            optional
├── payload                   required
├── provenance_refs[]         required for derived/consequential events
├── policy_context            optional/required for governed actions
├── model_context             optional
└── integrity_metadata       required for durable records
```

Invariant: committed historical events are immutable.

## 3. Observation

Represents information acquired from a sensor, human input or external source before higher-level interpretation.

```text
Observation
├── observation_id
├── observed_at
├── source_type
├── source_id
├── subject_refs[]
├── modality
├── value
├── unit / representation
├── quality
├── uncertainty
├── calibration_ref
├── location_ref
├── frame_ref
├── privacy_class
└── provenance
```

Observation must not imply truth.

## 4. Evidence

Represents an interpretation or derived signal supported by one or more observations.

```text
Evidence
├── evidence_id
├── created_at
├── evidence_type
├── source_observation_refs[]
├── source_model_ref (optional)
├── claim
├── confidence
├── uncertainty
├── validity_interval (optional)
├── provenance
└── verification_status
```

Evidence may support a claim without making it verified knowledge.

## 5. WorldStateChange

Represents a change to current structured world state.

```text
WorldStateChange
├── change_id
├── entity_ref
├── field/path
├── previous_value/version
├── new_value/version
├── effective_at
├── recorded_at
├── evidence_refs[]
├── confidence
├── state_revision
└── provenance
```

Historical state must remain reconstructable where the domain requires it.

## 6. Entity

Represents a persistent semantic identity.

```text
Entity
├── entity_id
├── entity_type
├── canonical_attributes
├── aliases
├── identity_evidence[]
├── confidence
├── validity
├── privacy_class
└── provenance
```

Entity identity does not grant authorization.

## 7. Relationship

Represents a typed relationship between entities.

```text
Relationship
├── relationship_id
├── subject_entity
├── relationship_type
├── object_entity
├── validity_interval
├── confidence
├── evidence_refs[]
├── provenance
└── verification_status
```

Relationships may change over time without rewriting historical evidence.

## 8. MemoryRecord

Represents durable experience or contextual memory.

```text
MemoryRecord
├── memory_id
├── memory_type
├── created_at
├── event_refs[]
├── entity_refs[]
├── content
├── semantic_index_ref (optional)
├── temporal_context
├── spatial_context
├── confidence
├── verification_status
├── privacy_class
├── retention_policy_ref
├── dependency_refs[]
├── revision
└── provenance
```

A vector representation is a projection of memory, not memory authority by itself.

## 9. KnowledgeRecord

Represents structured knowledge.

```text
KnowledgeRecord
├── knowledge_id
├── subject
├── predicate
├── object/value
├── validity_interval
├── evidence_refs[]
├── authority/source
├── confidence
├── verification_status
├── privacy_class
├── revision
└── provenance
```

Knowledge can be retracted/corrected through new governed records rather than destructive historical rewriting.

## 10. Goal

```text
Goal
├── goal_id
├── owner
├── description
├── source
├── priority
├── status
├── constraints
├── deadline (optional)
├── dependencies[]
├── authorization_scope
├── resource_budget
├── created_at
├── updated_at
└── provenance
```

Goals do not grant physical authority.

## 11. Plan

```text
Plan
├── plan_id
├── goal_ref
├── steps[]
├── preconditions
├── expected_outcomes
├── risks
├── resource_budget
├── policy_context
├── status
├── version
└── provenance
```

A plan is a proposal until governance/action validation accepts its relevant steps.

## 12. ActionProposal

```text
ActionProposal
├── proposal_id
├── capability
├── semantic_intent
├── target_refs[]
├── parameters
├── constraints
├── expected_effects
├── risks
├── requester_id
├── goal_ref
├── plan_ref
├── authorization_context
├── expires_at
├── idempotency_key
└── provenance
```

It must not contain unchecked raw actuator authority unless the capability contract explicitly requires it and safety controls remain outside the proposer.

## 13. AuthorizationDecision

```text
AuthorizationDecision
├── decision_id
├── subject/principal
├── capability
├── target
├── purpose
├── scope
├── policy_version
├── state_revision
├── decision
├── conditions
├── valid_from
├── valid_until
├── approver/source
└── provenance
```

A stale authorization must not silently remain valid after material policy/state changes.

## 14. SafetyDecision

```text
SafetyDecision
├── decision_id
├── proposal_ref
├── safety_policy_version
├── hardware_health_revision
├── environment_state_revision
├── decision
├── constraints
├── reason_codes
├── valid_until
└── audit_ref
```

Safety decisions are generated by the protected safety layer, not by the general model.

## 15. ActionExecution

```text
ActionExecution
├── execution_id
├── proposal_ref
├── authorization_ref
├── safety_ref
├── capability
├── started_at
├── execution_attempt
├── status
├── operation_id
├── runtime_version
├── hardware_target
└── provenance
```

Creation of `ActionExecution` does not mean the physical action succeeded.

## 16. ActionOutcome

```text
ActionOutcome
├── outcome_id
├── execution_ref
├── completed_at
├── status
├── observed_effects
├── expected_effect_comparison
├── sensor_evidence_refs[]
├── error_code (optional)
├── recovery_state
└── provenance
```

Unknown outcome is a valid state.

## 17. ModelInvocation

```text
ModelInvocation
├── invocation_id
├── model_id
├── model_version
├── artifact_digest
├── runtime
├── runtime_version
├── hardware
├── input_schema_version
├── output_schema_version
├── started_at
├── completed_at
├── latency
├── token/compute usage where available
├── request/result references
├── policy context
└── provenance
```

This is essential for reproducibility and model/memory lineage.

## 18. HardwareHealth

```text
HardwareHealth
├── device_id
├── device_type
├── observed_at
├── state
├── temperature
├── power
├── utilization
├── communication_state
├── calibration_state
├── firmware_version
├── driver_version
├── health_metrics
├── fault_codes[]
└── provenance
```

Hardware health is an input to governance/safety; it is not generated by the LLM.

## 19. DeploymentManifest

```text
DeploymentManifest
├── deployment_id
├── source_commit
├── application_version
├── OS
├── ROS 2 version
├── JetPack (optional)
├── CUDA (optional)
├── TensorRT (optional)
├── simulator (optional)
├── container digests
├── model artifact digests
├── schema versions
├── configuration digest
├── hardware target
├── calibration versions
├── test-suite version
└── creation/verification metadata
```

The manifest is the minimum reproducibility identity for a deployed runtime.

## 20. Contract versioning

Breaking semantic changes require a new major contract version or explicit migration mechanism.

Compatible extensions may add optional fields without changing existing meaning.

## 21. Contract validation

Every contract requires:

- positive examples;
- negative examples;
- malformed examples;
- version compatibility tests;
- authorization tests where applicable;
- privacy classification tests;
- serialization round-trip tests;
- persistence/recovery tests for durable contracts.

## 22. Final invariants

```text
Observation ≠ Evidence ≠ Knowledge

Proposal ≠ Authorization ≠ SafetyDecision ≠ Execution ≠ Outcome

ModelInvocation ≠ ModelAuthority

Embedding ≠ MemoryAuthority

SimulationResult ≠ PhysicalMeasurement

Identity ≠ Authentication ≠ Authorization
```

These distinctions are foundational to Novi's architecture.
