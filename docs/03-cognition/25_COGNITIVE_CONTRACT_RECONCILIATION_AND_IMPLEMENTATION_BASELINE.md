# 25 — Cognitive Contract Reconciliation & Implementation Baseline

**Status:** P0 — critical architectural reconciliation
**Authority:** `docs/03-cognition/`
**Purpose:** Establish the authoritative relationship between the existing Cognition data model, API/contract documents, decision records, and the new implementation schema layer without duplicating semantic ownership.
**Implementation target:** Mac-first; simulation and NVIDIA edge targets later

---

## 1. Executive decision

The Cognition repository contains multiple documents that discuss cognitive data. They are **not** to become competing authorities.

The canonical separation is:

```text
14_COGNITIVE_DATA_MODEL.md
        ↓
semantic model
“What does each cognitive object mean?”
        ↓
22_COGNITIVE_DATA_CONTRACTS_AND_SCHEMAS.md
        ↓
implementation contract
“How is that meaning represented and validated?”
        ↓
existing Cognitive APIs & Contracts
        ↓
transport/interface contract
“How do components exchange it?”
        ↓
23_COGNITIVE_DECISION_RECORDS.md
        ↓
architectural decisions
“Which constraints and choices govern implementation?”
```

No document may redefine another layer's authority without an explicit architecture decision.

---

## 2. Existing documents audited

The following existing artifacts were checked as part of this reconciliation:

- `14_COGNITIVE_DATA_MODEL.md`
- `22_COGNITIVE_DATA_CONTRACTS_AND_SCHEMAS.md`
- `23_COGNITIVE_DECISION_RECORDS.md`
- `24_COGNITION_ARCHITECTURE_AUDIT.md`
- `20_COGNITION_IMPLEMENTATION_ROADMAP.md`
- `21_COGNITION_IMPLEMENTATION_SPECIFICATION.md`
- `12_COGNITIVE_ROUTING_AND_MODEL_SELECTION.md`
- Cognition README and the relevant Brain/Autonomy contract references.

The repository also contains the Brain orchestrator/state specifications and Autonomy continuous-loop specifications that consume Cognition outputs. fileciteturn243file7turn243file8turn243file2

---

## 3. Authority of the semantic data model

`14_COGNITIVE_DATA_MODEL.md` remains the **semantic authority**.

It defines the meaning and conceptual vocabulary of objects such as:

```text
Observation
Event
Entity
Person
Relationship
Place
Object
Activity
Situation
Fact
Hypothesis
Prediction
Goal
Intention
Plan
ActionRequest
Outcome
Memory
KnowledgeCandidate
ContextPackage
ModelDecision
```

It also establishes stable IDs, provenance, confidence, lifecycle, contradiction handling and schema versioning as semantic requirements. fileciteturn245file0

It should not become a programming-language schema catalogue.

---

## 4. Authority of implementation schemas

`22_COGNITIVE_DATA_CONTRACTS_AND_SCHEMAS.md` is the **implementation contract layer**.

It translates the semantic objects into explicit machine-facing contracts including:

- contract envelopes;
- field requirements;
- timestamp semantics;
- coordinate-frame requirements;
- uncertainty representation;
- provenance representation;
- privacy classification;
- serialization/versioning;
- validation rules;
- null/unknown/unavailable semantics;
- structured-model-output validation;
- domain ownership;
- canonical data flow.

Therefore the documents are complementary:

```text
14 = semantic meaning
22 = implementation representation + validation
```

The same object may appear in both documents because it has two different responsibilities. This is **intentional duplication of reference, not duplication of authority**.

---

## 5. Authority of Cognitive Decision Records

`23_COGNITIVE_DECISION_RECORDS.md` remains the authority for **architectural decisions**, not data schemas.

Its current decisions include:

- vendor neutrality;
- local-first execution;
- stable capability interfaces;
- models not being the source of truth;
- structured actions;
- immutable safety boundaries;
- evidence/provenance requirements;
- silence as a valid outcome. fileciteturn244file0

A schema change that materially changes one of these decisions must create or update a decision record.

A normal field-level schema change does not belong in the decision-record document unless it changes an architectural constraint.

---

## 6. Authority of Cognitive APIs & Contracts

The existing API/contract layer owns **component-to-component interfaces**.

It must reference the canonical schemas rather than redefining their semantics.

The relationship is:

```text
Semantic Data Model
       ↓
Implementation Schema
       ↓
API Contract
       ↓
Runtime Adapter
```

An API may select a subset of fields, impose transport-specific constraints, or add protocol metadata, but it must not silently redefine the meaning of a canonical cognitive object.

---

## 7. Authority of the Brain

Brain is the runtime/orchestration layer.

Brain may:

- transport cognitive objects;
- schedule cognitive processing;
- maintain runtime caches;
- correlate events;
- enforce lifecycle/resource policies;
- expose health/diagnostic information.

Brain must not redefine:

- what an Observation means;
- what Evidence means;
- what a SituationState means;
- what an IntentHypothesis means;
- what a CognitiveDecisionRecord means.

The Brain orchestrator and state model are therefore consumers of Cognition contracts, not semantic authorities. fileciteturn243file7turn243file8

---

## 8. Authority of Autonomy

Autonomy consumes Cognition outputs and decides whether/how to act.

The key boundary is:

```text
Cognition
“What is probably happening?”
        ↓
Autonomy
“What should Novi do about it?”
```

Therefore:

- `AttentionCandidate` is a Cognition proposal/input to Autonomy;
- `IntentHypothesis` is not an action;
- `Prediction` is not a commitment;
- `CognitiveDecisionRecord` is not authorization;
- `ActionProposal` belongs to Autonomy.

The existing Autonomy continuous-loop architecture remains responsible for operational attention/action decisions. fileciteturn243file2

---

## 9. Authority of Soul

Soul remains the authority for:

- identity;
- personality;
- values;
- motivations;
- social disposition;
- affect semantics;
- behavioral continuity.

Cognition may consume Soul state to interpret situations, but must not redefine Soul semantics.

In particular:

```text
PersonContext
    ≠
Relationship memory
    ≠
Soul personality
```

Cognition interprets current social evidence. Memory preserves durable history. Soul defines the character-level meaning of relationships and social behavior.

---

## 10. The canonical pipeline after reconciliation

```text
SENSORS / EXTERNAL INPUT
        ↓
Observation
        ↓
Evidence
        ↓
Entity + Relation
        ↓
WorldState revision
        ↓
SituationState
        ↓
Intent / Prediction / Attention candidates
        ↓
CognitiveDecisionRecord
        ↓
AUTONOMY
        ↓
ActionProposal
        ↓
POLICY / SAFETY
        ↓
BRAIN
        ↓
EXECUTION
        ↓
OUTCOME
        ↓
Observation / Evidence
        ↺
```

Memory and Soul participate through explicit contracts and must not be mutated implicitly by arbitrary model output.

---

## 11. Model output boundary

Neural model output is always treated as **untrusted candidate data** until it passes validation.

```text
Model
 ↓
raw output
 ↓
parse
 ↓
schema validation
 ↓
semantic validation
 ↓
provenance attachment
 ↓
uncertainty handling
 ↓
cognitive state update
```

This is consistent with current NVIDIA documentation describing structured outputs through typed schemas and explicit validation, including JSON Schema/Pydantic-based structures and validation/scoring primitives. citeturn0search0turn0search1turn0search6

A model must never be allowed to bypass the schema layer merely because it is a high-quality or trusted model.

---

## 12. Schema implementation policy

The Mac-first implementation should begin with strongly typed in-process representations.

Recommended sequence:

```text
Canonical semantic model
        ↓
Python typed models / equivalent
        ↓
JSON Schema / serialization contract
        ↓
validation tests
        ↓
replay fixtures
        ↓
process boundary where required
        ↓
ROS 2 / transport adapters
```

The implementation must not begin with distributed transport complexity.

The first milestone is **correct semantics + deterministic validation**, not maximum throughput.

---

## 13. Required validation layers

Every canonical cognitive object should have:

### Structural validation

- required fields;
- field types;
- enums;
- array/object constraints;
- schema version.

### Semantic validation

- valid references;
- valid lifecycle transitions;
- valid confidence/probability semantics;
- valid timestamps;
- valid coordinate frames;
- valid privacy classification;
- valid ownership.

### Provenance validation

- source references exist;
- derivation chain is coherent;
- model/tool identity is recorded where relevant.

### Cross-contract validation

- WorldState references valid entities;
- SituationState references a valid WorldState revision;
- CognitiveDecisionRecord references the relevant situation;
- Autonomy receives a valid cognitive record;
- ActionProposal does not masquerade as a cognitive interpretation.

### Replay validation

A recorded event sequence must be replayable into equivalent cognitive state under the same software/schema versions.

---

## 14. Reconciliation of object names

Where older and newer documents use different names, the following policy applies:

| Conceptual meaning | Canonical implementation name | Rule |
|---|---|---|
| raw sensor input | `Observation` | do not call this Evidence |
| interpreted sensor claim | `Evidence` | provenance required |
| tracked world object | `Entity` | stable ID |
| connection between entities | `Relation` | typed predicate |
| current external representation | `WorldState` | revisioned |
| current contextual interpretation | `SituationState` | explicitly uncertain |
| person in current context | `PersonContext` | not durable relationship memory |
| possible attention target | `AttentionCandidate` | Autonomy decides |
| possible intent | `IntentHypothesis` | never treated as fact |
| expected future | `Prediction` | disposable unless promoted |
| cognitive recommendation/interpretation | `CognitiveDecisionRecord` | not action authorization |
| runtime transition | `CognitiveEvent` | append-oriented |

Legacy names may remain in historical documents but new implementation code must use the canonical names unless an explicit compatibility adapter exists.

---

## 15. Reconciliation with implementation roadmap

The Cognition implementation roadmap and specification now have a clear dependency order:

```text
21 Cognition Implementation Specification
        ↓
22 Cognitive Data Contracts & Schemas
        ↓
25 Contract Reconciliation  ← this document
        ↓
typed schema implementation
        ↓
validation + replay fixtures
        ↓
World Model runtime
        ↓
Situation Model runtime
        ↓
attention/social interpretation
        ↓
reasoning/prediction
        ↓
Autonomy integration
```

The roadmap remains the sequencing authority; this document is the **boundary/reconciliation authority** for cognitive data.

---

## 16. Completion gates

This reconciliation is complete when:

- [x] `14_COGNITIVE_DATA_MODEL.md` is designated semantic authority.
- [x] `22_COGNITIVE_DATA_CONTRACTS_AND_SCHEMAS.md` is designated implementation-schema authority.
- [x] `23_COGNITIVE_DECISION_RECORDS.md` is designated architectural-decision authority.
- [x] API contracts are subordinate to canonical semantics.
- [x] Brain is subordinate to Cognition semantics.
- [x] Autonomy owns action selection.
- [x] Soul owns identity/personality semantics.
- [x] model outputs are untrusted until validated.
- [x] canonical object names are established.
- [x] replay/validation is identified as an implementation requirement.

Remaining implementation work:

- [ ] implement the typed models;
- [ ] generate/maintain machine-readable schemas;
- [ ] implement structural and semantic validators;
- [ ] create replay fixtures;
- [ ] implement compatibility/migration tests;
- [ ] validate performance on the Mac-first environment.

---

## 17. Research basis

The structured-output and validation approach is supported by current NVIDIA NeMo documentation. NeMo documents typed structured outputs using Pydantic/JSON Schema and validation mechanisms for generated structured data. NeMo Evaluator also provides JSON-schema validation as an explicit scoring primitive. citeturn0search0turn0search5turn0search1

These sources support the implementation pattern; they do **not** dictate Novi's semantic architecture. Novi's semantic ownership remains defined by the repository's own architecture documents.

---

## 18. Final architectural rule

> **14 defines what cognitive data means. 22 defines how that meaning is represented and validated. API contracts define how it crosses interfaces. 23 records architectural decisions. Brain executes the runtime. Autonomy decides actions. Soul defines identity and character. No implementation layer may silently become a competing semantic authority.**
