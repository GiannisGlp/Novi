# 24 — Architecture Contract Ownership Reconciliation

**Status:** P0 — reconciliation audit
**Owner:** System Architecture
**Scope:** Cross-domain canonical contracts before executable schema registry creation
**Depends on:** `16_CANONICAL_SYSTEM_CONTRACTS.md`, `17_CONTRACT_IMPLEMENTATION_AND_SCHEMA_STANDARD.md`, `22_ARCHITECTURE_CLOSURE_AND_BASELINE.md`

## 1. Purpose

This document closes the first stage of `ARCH-CLOSE-001`: determine exactly which concepts are system-level canonical contracts, which are domain semantic models, and which are implementation/artifact schemas.

The goal is to prevent duplicate semantic authorities across System Architecture, Brain, Cognition, Memory/Knowledge, Autonomy, Hardware, Safety/Security and Soul.

The existing canonical contract baseline defines meaning; the schema standard defines implementation; this document reconciles ownership before machine-readable schemas are created. fileciteturn362file0 fileciteturn366file0

## 2. Governing rule

> One substantive cross-domain concept has exactly one semantic authority. Other domains may consume, derive, project, cache, persist or transport it, but must not redefine its meaning.

This is consistent with the existing Brain/Autonomy boundary decisions: Brain coordinates runtime, Cognition understands, Memory remembers/knows, Autonomy chooses/pursues, Policy/Safety permits or denies, and Hardware executes. fileciteturn379file0 fileciteturn378file0

## 3. Contract layers

Novi uses three distinct layers:

```text
SYSTEM CONTRACT
  = stable cross-domain meaning/interface

DOMAIN SEMANTIC MODEL
  = meaning specific to Cognition, Memory, Autonomy, Soul, Hardware, etc.

ARTIFACT / IMPLEMENTATION SCHEMA
  = concrete representation, storage, transport or tool artifact
```

A domain model may reference a system contract without becoming a second system contract.

## 4. Canonical system-contract set

The following are confirmed as cross-domain system contracts because they cross architectural boundaries or participate in consequential system state:

| Canonical contract | Semantic authority | Primary role | Status |
|---|---|---|---|
| `EventEnvelope` | System Architecture | event identity, causality, provenance and lifecycle | CANONICAL |
| `Observation` | System Architecture + Cognition semantic use | normalized acquired information | CANONICAL |
| `Evidence` | System Architecture + Cognition semantic use | derived/interpreted support for claims | CANONICAL |
| `Entity` | System Architecture + Cognition/Memory semantics | stable referenced identity | CANONICAL |
| `Relationship` | System Architecture + Memory/Cognition semantics | typed relation between entities | CANONICAL |
| `WorldStateChange` | System Architecture | revisioned change to current world state | CANONICAL |
| `MemoryRecord` | System Architecture contract; Memory semantic owner | durable experience/context | CANONICAL |
| `KnowledgeRecord` | System Architecture contract; Memory/Knowledge semantic owner | structured knowledge | CANONICAL |
| `Goal` | System Architecture contract; Autonomy semantic owner | behavioral objective | CANONICAL |
| `Plan` | System Architecture contract; Autonomy semantic owner | ordered/proposed task strategy | CANONICAL |
| `ActionProposal` | System Architecture contract; Autonomy semantic owner | proposed consequential capability use | CANONICAL |
| `AuthorizationDecision` | System Architecture / Safety boundary | policy authorization result | CANONICAL |
| `SafetyDecision` | System Architecture / Safety boundary | safety evaluation result | CANONICAL |
| `ActionExecution` | System Architecture | execution lifecycle record | CANONICAL |
| `ActionOutcome` | System Architecture | observed execution result | CANONICAL |
| `ModelInvocation` | System Architecture / Brain runtime | reproducible model execution record | CANONICAL |
| `HardwareHealth` | System Architecture / Hardware boundary | authoritative physical health input | CANONICAL |
| `DeploymentManifest` | System Architecture / Deployment | reproducibility identity | CANONICAL |

The first 18 semantic definitions are already established by the canonical system contract document; this reconciliation does not redefine them. fileciteturn362file0

## 5. Naming reconciliation

### 5.1 Authorization vs AuthorizationDecision

The master artifact catalog uses `Authorization`, while the canonical system contract and safety architecture use `AuthorizationDecision`. The latter is the precise canonical name because it represents the result of authorization evaluation rather than the generic concept of authorization.

**Decision:**

```text
Canonical implementation name: AuthorizationDecision
Legacy/catalog term: Authorization
Compatibility: documentation alias only
```

New schemas and code must use `AuthorizationDecision`.

### 5.2 ActionRequest vs ActionProposal

Cognition's older semantic model contains `ActionRequest`, while the system safety boundary and Autonomy architecture use `ActionProposal`. The consequential cross-domain object must remain a proposal until authorization and safety evaluation occur. fileciteturn368file0 fileciteturn387file0

**Decision:** `ActionProposal` is the canonical cross-domain contract. `ActionRequest` may remain as a historical/domain term only where its meaning is explicitly narrower and an adapter is provided.

### 5.3 Intention / IntentHypothesis

`Intention` in the artifact catalog and `IntentHypothesis` in Cognition represent different layers and must not be merged:

```text
IntentHypothesis = Cognition's uncertain interpretation of another actor/current situation
Intention = domain concept used by planning/behavior when explicitly modeled
```

Neither is promoted to a system-level action authority.

### 5.4 Relationship / Relation

The system contract uses `Relationship`. Cognition implementation uses `Relation` in places where the object is a typed cognitive relation.

**Decision:**

- `Relationship` = canonical cross-domain contract.
- `Relation` = Cognition-local representation only if it maps explicitly to `Relationship`.

No two independent semantic authorities are permitted.

## 6. Domain-owned semantic models

The following are **not** promoted into the cross-domain system contract set merely because they appear in the master catalog:

| Concept | Owner | Reason |
|---|---|---|
| `SituationState` | Cognition | current contextual interpretation |
| `PersonContext` | Cognition | current social interpretation |
| `AttentionCandidate` | Cognition | semantic salience candidate consumed by Autonomy |
| `IntentHypothesis` | Cognition | uncertain interpretation |
| `Prediction` | Cognition | cognitive prediction/expectation |
| `Belief` | Memory/Knowledge + Cognition use | epistemic state requires domain semantics |
| `Fact` | Memory/Knowledge | verified/managed knowledge |
| `Counterfactual` | Cognition | reasoning artifact |
| `Episode` | Memory/Knowledge | episodic memory semantics |
| `ContextPackage` | Cognition | runtime cognitive context |
| `CognitiveDecisionRecord` | Cognition | cognitive interpretation/decision evidence, not authorization |
| `SoulState` / personality state | Soul | character/identity semantics |
| `AutonomyState` | Autonomy | behavioral task lifecycle |
| `BrainState` | Brain | runtime/embodied operational state |

These models may have executable schemas, but those schemas must explicitly identify their domain authority and must not be presented as competing system-level contracts.

Cognition's own reconciliation already establishes this semantic-model versus implementation-schema separation. fileciteturn368file0

## 7. Artifact and implementation schemas

The following remain artifact/domain schemas rather than canonical system contracts:

- `Model`
- `Dataset`
- `DatasetVersion`
- `Skill`
- `SkillVersion`
- `Sensor`
- `Calibration`
- `SimulationResult`
- robot/URDF/USD asset manifests
- benchmark records
- training/evaluation manifests
- storage-specific records
- ROS/API projections

The master catalog correctly identifies these as required artifacts, but artifact status does not grant them system-contract authority. fileciteturn367file0

## 8. Ownership matrix by domain

| Domain | Owns semantically | Does not own |
|---|---|---|
| System Architecture | cross-domain contract meaning, topology, compatibility and governance | domain-specific cognition/personality semantics |
| Brain | runtime state, orchestration, model execution representation and adapters | cognitive meaning, Soul, durable memory, authorization policy |
| Cognition | world/situation interpretation, reasoning, prediction, social interpretation | physical authority, durable memory authority, final action authorization |
| Memory/Knowledge | durable experience, knowledge, provenance, retention and retrieval semantics | current physical truth, safety authority, runtime scheduling |
| Autonomy | goals, priorities, task lifecycle, behavioral planning and action proposals | world-model truth, personality authority, safety authority, motor control |
| Soul | identity, personality, values, motivations, social character, affect semantics | runtime, factual world state, physical control |
| Safety/Policy | authorization/safety decision semantics and protected constraints | cognitive interpretation, personality, learned memory |
| Hardware/Control | physical state, actuator/controller semantics and physical safety constraints | reasoning, personality, durable semantic memory |
| Deployment | release/runtime artifact identity | semantic authority of the artifacts themselves |

This preserves the existing boundary architecture. fileciteturn380file0

## 9. Canonical action chain

The canonical consequential chain is now fixed as:

```text
Cognition / Autonomy
        ↓
ActionProposal
        ↓
AuthorizationDecision
        ↓
SafetyDecision
        ↓
ActionExecution
        ↓
ActionOutcome
```

No earlier object is permission to execute. The safety architecture explicitly requires this separation. fileciteturn387file0

## 10. Current physical state vs memory

This reconciliation confirms the invariant:

```text
live physical telemetry
        ≠
historical memory
```

For example, current battery state is authoritative physical/runtime state; a historical battery observation is Memory data. Memory cannot silently override live hardware state. This boundary is already established by the Brain ownership audit. fileciteturn379file0

## 11. Model outputs

A model output is never a canonical authority by itself.

```text
model output
   ↓
parse
   ↓
schema validation
   ↓
semantic validation
   ↓
provenance
   ↓
domain-owned state/contract
```

This follows the contract implementation standard: executable schemas implement canonical semantics; they do not become new authorities. fileciteturn366file0

## 12. Registry scope

The machine-readable registry required by `17_CONTRACT_IMPLEMENTATION_AND_SCHEMA_STANDARD.md` should initially contain the 18 canonical system contracts listed in Section 4.

Each registry entry must contain at least:

```text
contract_id
canonical_name
semantic_owner
semantic_version
schema_artifacts
compatibility_policy
status
introduced_at
supersedes
superseded_by
validation_suite
security_classification
privacy_classification
producer_domains
consumer_domains
time_semantics
provenance_requirements
```

The registry is metadata only. `16_CANONICAL_SYSTEM_CONTRACTS.md` remains semantic authority. fileciteturn366file0

## 13. Existing-document reconciliation findings

### PASS — System Architecture

`16` is the canonical semantic contract authority and `17` is the canonical schema/implementation standard. fileciteturn362file0 fileciteturn366file0

### PASS — Brain

The Brain boundary audit explicitly prevents Brain from becoming a competing semantic owner and separates model execution from cognitive selection. fileciteturn379file0

### PASS — Cognition

Cognition already has an explicit semantic model → implementation schema → API contract separation. fileciteturn368file0

### PASS — Autonomy

Autonomy explicitly owns goals/action lifecycle and consumes Cognition semantics rather than redefining them. fileciteturn378file0

### PASS — Memory/Knowledge

Memory has a dedicated normative architecture for durable memory/knowledge semantics. Its records must map to system-level `MemoryRecord`/`KnowledgeRecord` contracts rather than create competing cross-domain meanings. fileciteturn369file0

### PASS — Safety

The safety architecture explicitly uses `ActionProposal → AuthorizationDecision → SafetyDecision → ActionExecution → ActionOutcome`. fileciteturn387file0

### REVIEW — Hardware

Hardware has a substantial architecture and validation baseline, but its directory currently contains a numbering collision: both `24_GNSS_GPS_AND_GLOBAL_POSITIONING.md` and `24_HARDWARE_SELECTION_AND_BOM_BASELINE.md` exist. This is not a contract-semantic conflict, but it is an `ARCH-CLOSE-010` numbering-integrity issue and must be resolved separately. fileciteturn370file0

### DEFERRED — Multi-agent

The multi-agent architecture is explicitly P2/future and is not included in Stage-1 canonical contract implementation. fileciteturn383file0

## 14. Reconciliation result

The audit establishes the following authoritative hierarchy:

```text
16_CANONICAL_SYSTEM_CONTRACTS.md
        ↓
semantic authority
        ↓
17_CONTRACT_IMPLEMENTATION_AND_SCHEMA_STANDARD.md
        ↓
implementation/schema rules
        ↓
Machine-readable contract registry
        ↓
JSON Schema / Protobuf / ROS 2 / API projections
        ↓
Domain adapters
        ↓
Runtime
```

Domain specifications remain authoritative for domain-specific semantic models.

## 15. ARCH-CLOSE-001 status

**Current status: REVIEW — reconciliation complete, executable registry not yet created.**

Completed:

- canonical cross-domain set identified;
- ownership assigned;
- naming conflicts identified and resolved at semantic level;
- domain models separated from system contracts;
- artifact schemas separated from system contracts;
- action/safety chain confirmed;
- Brain/Cognition/Memory/Autonomy/Soul/Safety boundaries reconciled;
- machine registry requirements defined.

Remaining:

- create machine-readable registry;
- create executable schemas for the 18 canonical contracts;
- create positive/negative fixtures;
- create compatibility fixtures;
- validate schemas against consuming domains;
- record validation evidence;
- update `22_ARCHITECTURE_CLOSURE_AND_BASELINE.md` to mark ARCH-CLOSE-001 complete only after evidence.

## 16. Final decision

> **Do not create another semantic contract document for these concepts. The next artifact is the machine-readable registry and executable schema set derived from this reconciliation and the canonical contract authority.**

This preserves the no-duplication rule and keeps implementation artifacts subordinate to the architecture.