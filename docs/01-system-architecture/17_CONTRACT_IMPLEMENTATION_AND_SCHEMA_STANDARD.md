# 17 — Contract Implementation & Schema Standard

**Status:** P0 normative implementation standard  
**Owner:** System Architecture  
**Canonical semantic authority:** `16_CANONICAL_SYSTEM_CONTRACTS.md`

## 1. Purpose

`16_CANONICAL_SYSTEM_CONTRACTS.md` defines the meaning of Novi's shared contracts. This document defines how those contracts become executable, versioned, validated schemas and interfaces.

It does **not** redefine contract semantics.

The rule is:

> One semantic contract may have multiple transport/storage representations, but every representation MUST trace back to the canonical contract identity and version.

## 2. Contract layers

```text
CANONICAL SEMANTICS
        │
        ↓
CONTRACT SCHEMA
        │
   ┌────┼─────────┐
   ↓    ↓         ↓
 JSON  Protobuf  ROS 2
Schema          message
   │    │         │
   └────┼─────────┘
        ↓
 runtime adapters / persistence / APIs
```

A wire format is an implementation of the contract, not its owner.

## 3. Canonical contract identity

Every executable contract MUST expose:

- `contract_id`;
- `schema_version`;
- semantic owner;
- compatibility policy;
- provenance/version metadata;
- validation status.

The implementation MUST reject an unknown major semantic version rather than silently guessing.

## 4. Required schema artifacts

For each production contract, maintain:

```text
/contracts/<domain>/<contract-id>/
    schema.json        # machine-readable JSON Schema where applicable
    examples/           # positive examples
    invalid/            # negative examples
    compatibility/      # migration/compatibility fixtures
    README.md           # implementation notes only
```

If another schema language is required, its artifact must reference the same canonical `contract_id` and semantic version.

## 5. JSON Schema

JSON Schema is the baseline validation representation for contracts that cross JSON/API boundaries or need language-neutral fixtures.

The schema MUST encode structural constraints that can be mechanically validated, including:

- required fields;
- field types;
- enumerations;
- nullability;
- array constraints;
- nested object structure;
- additional-property policy;
- format constraints where appropriate.

Semantic constraints that cannot be represented reliably in JSON Schema remain in the canonical contract and MUST have executable tests.

## 6. Protobuf

Protobuf may be used for high-throughput or strongly typed service/event interfaces.

Rules:

- never reuse a field number for a different semantic meaning;
- reserve removed field numbers/names;
- preserve backward compatibility within the declared compatibility policy;
- map protobuf messages to canonical contract IDs explicitly;
- do not allow protobuf defaults to silently change semantic meaning.

## 7. ROS 2 interfaces

ROS 2 messages/services/actions are transport/runtime representations.

A ROS interface MUST identify:

- canonical contract ID;
- semantic version;
- timestamp semantics;
- coordinate/frame semantics where applicable;
- QoS assumptions;
- ownership/source;
- conversion/adapter behavior.

ROS message definitions must not become an accidental second semantic authority.

## 8. API contracts

HTTP/gRPC/API schemas MUST reference the canonical contract.

An API may expose a purpose-specific projection, but the documentation MUST state:

```text
canonical_contract
projection
omitted_fields
transformed_fields
compatibility_policy
```

## 9. Event contracts

Event implementations MUST preserve the `EventEnvelope` semantics from the canonical contract.

Events MUST distinguish:

```text
occurred_at
recorded_at
causation_id
correlation_id
producer_id
schema_version
```

Committed historical events are immutable.

## 10. Contract registry

Novi requires a machine-readable contract registry before production implementation.

Minimum registry fields:

```text
contract_id
name
owner_domain
semantic_version
schema_artifacts
compatibility_policy
status
introduced_at
supersedes
superseded_by
validation_suite
security_classification
```

The registry is metadata about contracts; `16_CANONICAL_SYSTEM_CONTRACTS.md` remains the semantic authority.

## 11. Versioning

### Major

Use a major version when meaning, required behavior, interpretation, or compatibility changes incompatibly.

### Minor

Use a minor version for backward-compatible semantic extensions.

### Patch

Use a patch version for corrections that do not change the contract's intended meaning or compatibility.

Implementations MUST declare which compatibility levels they support.

## 12. Compatibility matrix

Every deployed component consuming a contract MUST declare:

```text
contract_id
supported_major
supported_minor_range
producer/consumer role
migration strategy
```

A deployment is invalid if a required producer/consumer pair has no compatible contract version.

## 13. Validation pipeline

Every contract implementation must pass:

```text
canonical definition
      ↓
schema generation/authoring
      ↓
positive fixtures
      ↓
negative fixtures
      ↓
serialization round-trip
      ↓
compatibility tests
      ↓
security/privacy tests
      ↓
persistence/recovery tests where applicable
      ↓
consumer integration tests
```

## 14. Provenance requirements

Derived contracts MUST retain sufficient provenance to answer:

- where did this value originate?
- which model produced it?
- which observations supported it?
- under which configuration?
- under which policy?
- with which contract version?

Provenance must not be stripped merely because a value crosses a transport boundary.

## 15. Time requirements

Every time-bearing contract MUST explicitly identify the meaning of its timestamp.

At minimum distinguish:

```text
world/event time
recorded time
processing time
validity interval
```

Clock synchronization is owned by system/runtime architecture; contract schemas only encode the resulting semantics.

## 16. Coordinate/frame requirements

Contracts containing spatial values MUST identify the coordinate/frame convention where ambiguity is possible.

Examples include:

- world frame;
- map frame;
- odometry frame;
- robot/base frame;
- sensor frame.

Frame IDs must not be inferred from field names alone.

## 17. Privacy and security

Contracts containing user, human, environmental or security-sensitive information MUST carry the appropriate privacy/security classification defined by the system architecture.

Serialization layers MUST NOT silently remove classification metadata.

Authorization and safety decisions remain separate contracts; a field such as `authorized=true` inside an arbitrary payload MUST NOT be treated as authoritative authorization.

## 18. Error contracts

Errors MUST be structured where they cross domain boundaries.

Minimum concepts:

```text
error_code
error_class
retryable
source
contract_id
schema_version
correlation_id
causation_id
severity
safe_state
recovery_hint
```

An error response MUST NOT imply successful execution.

## 19. Unknown and partial states

Schemas must permit explicitly defined unknown/partial states where the canonical semantics require them.

Do not encode uncertainty by silently substituting:

- zero for unknown;
- empty string for unknown;
- false for unknown;
- stale value for current value.

## 20. Contract ownership rules

### Brain

Owns runtime representations and adapters for execution, scheduling and embodied state interfaces.

### Cognition

Owns semantic interpretation of cognitive contracts but uses System Architecture's canonical contract definitions.

### Autonomy

Owns behavioral use of Goal, Plan and ActionProposal semantics but does not redefine them.

### Memory/Knowledge

Owns persistence-specific representations of MemoryRecord and KnowledgeRecord while preserving canonical semantics.

### Hardware/Control

Owns physical execution interfaces and hardware-specific mappings.

## 21. Generated artifacts

Generated schemas, code, message bindings and client types MUST be reproducible from version-controlled source definitions.

Generated files must include:

```text
contract_id
schema_version
source_revision
```

Generated artifacts are implementation outputs, not semantic authorities.

## 22. Contract change process

A contract change requires:

1. identify affected canonical contract;
2. classify major/minor/patch impact;
3. update canonical semantics if required;
4. update machine-readable schemas;
5. update positive/negative fixtures;
6. run compatibility tests;
7. update consumers/producers;
8. update deployment compatibility metadata;
9. record migration/deprecation information;
10. update architecture indexes.

No consumer should silently adapt to a breaking change in production.

## 23. Definition of done

The contract implementation layer is complete when:

- all P0 contracts have machine-readable schemas;
- every schema maps to exactly one canonical contract;
- every contract has positive and negative fixtures;
- compatibility rules are executable;
- producers and consumers declare supported versions;
- ROS/API/event representations map explicitly to canonical semantics;
- provenance survives transformations;
- timestamps have defined semantics;
- spatial frames are explicit where required;
- privacy/security metadata survives transport;
- unknown states are represented explicitly;
- generated artifacts are reproducible;
- deployment manifests identify the contract versions in use.

## 24. Architectural invariant

> **The semantic contract is the authority. Schemas, messages, APIs, databases and generated code are implementations that must remain traceable to it.**
