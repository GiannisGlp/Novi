# 10 — Memory Schema Evolution and Dynamic Data

## Status

**DESIGN — V1**

## Purpose

This document defines how Novi can continuously learn, create new knowledge structures, extend its data model, and evolve its local memory system without becoming an uncontrolled self-modifying system.

This is one of the highest-risk boundaries in Novi.

Novi is intended to evolve continuously. It must be able to encounter concepts that were not explicitly anticipated by its original designers, represent useful new information, and create new data where existing structures are insufficient.

However:

> **Learning is not the same thing as modifying the system that performs learning.**

Novi may evolve its knowledge and memory contents within defined boundaries. It must not autonomously rewrite its safety model, authorization model, protected core, executable control plane, or security boundaries.

---

# 1. Core Principles

## 1.1 Learn continuously, modify cautiously

The default autonomous operation is:

```text
observe
  ↓
interpret
  ↓
learn candidate
  ↓
represent using existing schema if possible
  ↓
validate
  ↓
store
  ↓
consolidate
  ↓
retrieve later
```

Structural modification is a separate operation:

```text
new concept
  ↓
existing representation insufficient?
  ↓
schema proposal
  ↓
validation
  ↓
policy evaluation
  ↓
migration plan
  ↓
controlled execution
  ↓
verification
```

A new fact should normally require **no schema change**.

A genuinely new concept may require a new entity type, relationship predicate, attribute, index, document type, or table. Such changes require additional controls.

## 1.2 Existing schema first

Before creating a new table, Novi must attempt to represent the information using existing structures.

The preferred order is:

1. existing entity type;
2. existing attribute;
3. existing relationship;
4. existing event/memory type;
5. existing flexible metadata/JSON field where appropriate;
6. existing extension table;
7. new schema proposal only when the above are inadequate.

This prevents schema explosion caused by every new observation becoming a new database structure.

## 1.3 The model never owns the schema

Nemotron or another reasoning model may propose a schema change.

It does not have direct authority to execute arbitrary:

- SQL;
- DDL;
- filesystem operations;
- migration scripts;
- extension loading;
- code execution;
- permission changes;
- policy changes.

The Memory/Schema Manager owns schema operations and validates model proposals against explicit rules.

## 1.4 The protected core is outside autonomous evolution

Novi must maintain a physically/logically separated protected area containing critical instructions, safety policy, authorization policy, trust roots, migration engine code, signing material, and other administrator-controlled assets.

Autonomous memory evolution cannot modify this area.

A model-generated proposal cannot grant itself permission to modify the protected area.

---

# 2. What May Evolve

Novi's autonomous evolution is divided into levels.

## Level 0 — Runtime state

Fully autonomous within resource limits.

Examples:

- current location hypotheses;
- current sensor state;
- temporary conversation state;
- active attention state;
- transient predictions.

## Level 1 — Memory content

Autonomous admission subject to the Memory Write and Admission Policy.

Examples:

- experiences;
- observations;
- preferences proposed by repeated evidence;
- routines as hypotheses;
- interaction history;
- learned associations.

## Level 2 — Knowledge content

Controlled promotion from memory into durable semantic knowledge.

Examples:

- new entities;
- verified facts;
- relationships;
- concepts;
- definitions;
- household information.

## Level 3 — Non-structural metadata

May be created autonomously within quotas and validation rules.

Examples:

- tags;
- labels;
- annotations;
- confidence metadata;
- embedding references;
- learned categories.

## Level 4 — Schema extension

Requires a schema proposal and validation pipeline.

Examples:

- new entity type;
- new relationship predicate;
- new extension table;
- new column;
- new index;
- new schema version.

## Level 5 — Runtime/software changes

**Not autonomously permitted.**

Examples:

- modifying executable code;
- changing safety logic;
- changing authorization logic;
- changing migration engine;
- installing arbitrary packages;
- replacing the model router;
- changing system startup behavior.

These belong to a controlled development/deployment process.

## Level 6 — Protected core changes

**Forbidden to autonomous Novi.**

Only explicit administrator/developer processes may change this area.

---

# 3. Knowledge Evolution vs System Evolution

This distinction is foundational.

### Allowed

```text
Novi learns:
"This object is called a moka pot."
```

### Potentially allowed

```text
Novi discovers a new category:
"household brewing device"
```

The system can represent it as a new knowledge entity/type if the existing schema cannot represent the concept adequately and the schema policy allows it.

### Not allowed

```text
Novi learns:
"I should be allowed to modify my safety policy."
```

That is not knowledge. It is an attempted change to a control boundary and must be rejected.

---

# 4. Schema Proposal Lifecycle

Every autonomous structural change follows a state machine.

```text
DISCOVERED
    ↓
PROPOSED
    ↓
ANALYZING
    ↓
VALIDATING
    ↓
POLICY_REVIEW
    ↓
PLANNED
    ↓
APPROVED
    ↓
MIGRATING
    ↓
VERIFYING
    ↓
ACTIVE
```

Failure states:

```text
REJECTED
DEFERRED
ROLLED_BACK
QUARANTINED
```

A proposal must never jump directly from model output to production schema mutation.

---

# 5. Schema Proposal Object

A proposal should contain structured metadata such as:

```json
{
  "proposal_id": "schema-proposal-uuid",
  "type": "new_entity_type",
  "name": "brewing_device",
  "reason": "existing object categories cannot represent the discovered concept adequately",
  "requested_by": "cognitive_system",
  "evidence_refs": ["evidence-123", "evidence-456"],
  "existing_schema_review": {
    "entity_types_checked": true,
    "extension_fields_checked": true,
    "relationship_types_checked": true
  },
  "risk_class": "low",
  "estimated_storage": "small",
  "migration": {},
  "rollback": {},
  "validation_plan": {},
  "status": "proposed"
}
```

The `reason` field is an operational explanation. It must not depend on exposing private model chain-of-thought.

---

# 6. Schema Proposal Rules

A proposal should be rejected or deferred when:

- an existing schema can represent the concept adequately;
- it creates redundant structures;
- it is based on weak or unverified evidence when verification is required;
- it would weaken an authorization boundary;
- it would weaken a safety boundary;
- it would modify protected storage;
- it requires arbitrary code execution;
- it exceeds storage/resource quotas;
- it creates uncontrolled recursive schema growth;
- it would make existing data ambiguous;
- it cannot be migrated safely;
- it has no rollback or recovery strategy where rollback is required;
- it cannot pass integrity validation;
- its purpose is not sufficiently understood.

---

# 7. Dynamic Entity Types

New concepts should preferably begin as knowledge entities rather than immediate physical database tables.

For example:

```text
entity
├── entity_id
├── entity_type
├── name
├── attributes
├── provenance
└── confidence
```

A newly discovered concept can initially use an extensible representation.

Only if repeated use demonstrates that a dedicated structure is valuable should Novi consider promoting it into a more specialized schema representation.

This creates a two-stage evolution model:

```text
concept discovery
      ↓
flexible representation
      ↓
usage/evidence accumulates
      ↓
schema promotion candidate
```

This reduces unnecessary migrations.

---

# 8. Dynamic Attributes

A new attribute should normally be represented using an existing extensibility mechanism before adding a physical column.

A physical column becomes justified when the attribute is:

- frequently queried;
- semantically stable;
- used in constraints;
- required for indexing;
- important for joins;
- important for retrieval/ranking;
- large enough that the flexible representation becomes inefficient;
- governed by a distinct lifecycle or privacy policy.

---

# 9. Dynamic Relationships

New relationship predicates are usually safer than new tables.

Example:

```text
Vano --uses--> coffee_machine
coffee_machine --located_in--> kitchen
Vano --prefers--> coffee_type
```

A relationship should contain provenance, confidence, temporal validity, and privacy classification where appropriate.

The relationship layer must not allow arbitrary references into protected resources.

---

# 10. SQLite Constraints and Migration Strategy

SQLite has intentionally limited direct schema alteration support. Current SQLite supports table/column rename, column addition/removal, and newer releases also support changing certain NOT NULL constraints, but many arbitrary schema changes require a controlled table-rebuild migration procedure. SQLite documents that schema changes modify the stored schema text and that complex changes must preserve indexes, triggers, views, constraints, and data integrity. citeturn1search1

Therefore Novi must **never generate arbitrary `PRAGMA writable_schema=ON` changes as a normal autonomous operation**.

The migration engine should use versioned, reviewed migration code and the documented safe table-rebuild procedure where required.

## Migration sequence

```text
proposal
  ↓
preflight on isolated copy
  ↓
integrity validation
  ↓
backup/checkpoint
  ↓
transaction
  ↓
apply migration
  ↓
foreign-key/integrity checks
  ↓
rebuild required indexes
  ↓
reconcile vector/FTS indexes
  ↓
commit
  ↓
post-migration verification
```

If verification fails, the migration must not be considered active.

---

# 11. Schema Versioning

Every schema has an explicit version.

Example:

```text
schema_version = 27
```

Every migration has:

- migration ID;
- source version;
- target version;
- timestamp;
- author/system identity;
- proposal ID;
- reason;
- checksum;
- validation results;
- rollback information;
- affected tables/indexes;
- status.

Schema version history is append-only in the audit store.

---

# 12. Migration Isolation

Autonomous schema changes should initially execute against an isolated database copy or snapshot whenever practical.

The system should verify:

- schema parses correctly;
- foreign keys remain valid;
- constraints remain valid;
- indexes are valid;
- triggers/views remain valid where used;
- row counts are consistent where expected;
- critical data hashes match expected invariants;
- protected tables are unchanged;
- FTS indexes can be rebuilt;
- vector indexes can be rebuilt;
- application startup succeeds.

Only after validation may the migration be promoted.

---

# 13. Rollback

Every structural migration must have an explicit recovery strategy.

Possible strategies:

1. transactional rollback before commit;
2. restore from a pre-migration snapshot;
3. reverse migration;
4. rebuild from canonical data.

A reverse migration is not automatically required if restoration from a verified snapshot is safer.

For destructive migrations, the preferred approach is to preserve the old representation until the new schema has been validated.

---

# 14. Data Preservation Rule

Novi must not destroy historical knowledge merely because a schema changes.

Schema migration should preserve:

- memory IDs;
- entity IDs;
- relationship IDs;
- provenance;
- timestamps;
- confidence;
- epistemic state;
- privacy classifications;
- audit references.

When a representation changes, the old representation may be retained in archival storage if required for reconstruction.

---

# 15. Embedding and Index Evolution

A schema change may require secondary index changes.

Examples:

```text
new semantic field
    ↓
new embedding content
    ↓
embedding index update
```

or:

```text
entity type changed
    ↓
FTS document changed
    ↓
FTS reindex
```

Index rebuilds are subordinate to authoritative structured data.

If an index cannot be rebuilt, Novi must continue using the authoritative data and degrade retrieval rather than corrupt the source of truth.

---

# 16. Resource Governance

Autonomous evolution requires resource limits.

Novi should enforce quotas for:

- number of schema proposals per period;
- number of accepted structural changes;
- table count;
- index count;
- database size;
- artifact storage;
- embedding count;
- background CPU time;
- GPU time;
- migration duration;
- migration temporary storage;
- memory usage.

If a quota is reached, Novi should defer the proposal and report the condition rather than circumvent the quota.

---

# 17. Schema Churn Protection

Novi must avoid oscillating schemas.

Example failure:

```text
create field A
    ↓
remove A
    ↓
recreate A
    ↓
rename A
    ↓
repeat
```

The schema manager should maintain historical proposals and reject changes that repeatedly reverse recently accepted changes without strong evidence.

A cooldown may be applied to structural changes.

---

# 18. Novelty Threshold

A new concept does not automatically justify structural evolution.

The system should consider:

- novelty;
- frequency;
- persistence;
- retrieval demand;
- semantic distinctness;
- query workload;
- evidence quality;
- user relevance;
- storage cost;
- schema complexity.

A concept seen once may remain an ordinary memory/entity.

A concept repeatedly encountered and heavily used may become a candidate for schema promotion.

---

# 19. Human Confirmation

Human confirmation should be risk-dependent rather than required for every harmless learning event.

### No confirmation normally required

- temporary observations;
- ordinary low-risk memories;
- non-sensitive tags;
- rebuildable indexes;
- internal candidate entities.

### Confirmation normally required or strongly preferred

- sensitive personal knowledge;
- important identity changes;
- major relationship claims;
- destructive schema changes;
- privacy policy changes;
- data retention changes;
- changes affecting other household members;
- external account changes;
- security-sensitive structures.

### Never delegated to ordinary user-level learning

- safety policy;
- authorization root;
- protected core;
- trusted code-signing material;
- migration engine itself.

---

# 20. Learning From Other People

If another person teaches Novi something, the information enters as a claim with provenance.

```text
person says X
   ↓
claim(source=person)
   ↓
confidence
   ↓
verification policy
   ↓
possible user confirmation
   ↓
knowledge promotion
```

The speaker does not automatically gain authority to change Novi's schema or policies.

Knowledge authority and system authority remain separate.

---

# 21. Model-Generated Proposals

Models can identify potential gaps in the current representation.

Example:

```text
model:
"I cannot represent this concept cleanly using the current entity model."
```

This becomes:

```text
SchemaGapCandidate
```

The model may propose a representation, but deterministic validation decides whether the proposal is technically valid.

The model is therefore an **architectural assistant**, not the database administrator.

---

# 22. Self-Generated Data

Novi may generate data in SQLite or files, but generated data must be labeled correctly.

Examples:

```text
source_type = generated
origin = Novi
model_id = ...
source_evidence = ...
verification = unverified
```

Generated knowledge must never be mistaken for external observation merely because it is stored in an authoritative database.

Synthetic/generated records should remain distinguishable from real-world evidence.

---

# 23. Recursive Self-Modification Prevention

The following pattern is forbidden:

```text
Novi
 ↓
changes memory policy
 ↓
policy allows more changes
 ↓
Novi changes policy again
 ↓
unbounded self-modification
```

The policy engine, migration engine, protected storage, and trust roots are outside the autonomous learning domain.

A memory schema cannot grant permission to modify the permission system.

A knowledge record cannot grant permission to modify the knowledge schema manager.

A model cannot elevate its own authority through generated data.

---

# 24. Protected Core

The protected area should include, at minimum:

- safety policies;
- authorization policies;
- security configuration;
- trusted migration code;
- schema-manager executable code;
- trust roots;
- signing keys or references to them;
- recovery configuration;
- administrator configuration;
- immutable system identity;
- audit integrity configuration.

The protection must be enforced outside the LLM prompt.

A sentence such as:

> "Never modify this directory"

is not a sufficient security boundary.

The operating system, filesystem permissions, process isolation, capability boundaries, and application authorization must enforce it.

---

# 25. SQLite Security

SQLite supports powerful application-defined functions and extensions. SQLite's current security guidance warns that malicious schema content can cause application-defined SQL functions to execute unexpectedly. Novi should therefore disable trusted schema behavior for connections that expose custom functions and use direct-only restrictions for functions with side effects where applicable. citeturn1search0turn1search6

The autonomous schema manager must therefore:

- never expose arbitrary SQL execution to the model;
- avoid arbitrary loadable extensions;
- restrict custom SQL functions;
- use `PRAGMA trusted_schema=OFF` where appropriate;
- use `SQLITE_DIRECTONLY` for dangerous custom functions;
- validate database files before use;
- run integrity checks on security-sensitive recovery paths;
- maintain strict filesystem permissions.

SQLite's extension loading is disabled by default and should remain disabled unless a specific, trusted extension is required and validated. citeturn1search9turn1search8

---

# 26. Guardrails and Policy Integration

Schema evolution must pass the same layered controls as other autonomous actions.

```text
Model proposal
      ↓
Schema validator
      ↓
Memory policy
      ↓
Security policy
      ↓
Authorization
      ↓
Resource policy
      ↓
Migration planner
      ↓
Execution sandbox
      ↓
Verification
```

NVIDIA NeMo Guardrails is relevant as an optional guardrail implementation because it provides programmable input, retrieval, execution and output rails and can sit between an application and its model/tool/retrieval systems. citeturn0search7turn0search16

However, guardrails are not the sole security boundary. Deterministic authorization, process isolation, filesystem permissions and migration validation remain mandatory.

---

# 27. NVIDIA NeMo Integration

NVIDIA NeMo Agent Toolkit provides an extensible memory subsystem with pluggable providers and an automatic memory wrapper. Its memory interfaces are useful reference points for Novi's Memory API, but they do not become Novi's authority model. citeturn0search0turn0search8

Novi should treat NeMo components as adapters/providers where they provide a measurable advantage.

The architecture remains:

```text
Novi Memory / Schema API
          ↓
provider adapter
          ↓
NVIDIA NeMo / other local implementation
```

NVIDIA's current platform also demonstrates explicit authorization and policy-decision patterns, reinforcing the principle that authorization should be evaluated by a policy layer rather than inferred by the model. citeturn0search4turn0search10

---

# 28. Continual Learning Boundary

Novi's continuous learning should initially mean:

- accumulating experiences;
- consolidating memories;
- updating knowledge;
- improving retrieval;
- learning routines and preferences;
- generating hypotheses;
- evaluating prediction errors;
- updating confidence;
- discovering schema gaps.

It should **not** initially mean autonomous weight updates to the primary reasoning model.

Model training/fine-tuning is a separate controlled lifecycle:

```text
experience data
    ↓
data curation
    ↓
privacy filtering
    ↓
evaluation
    ↓
dataset/version
    ↓
training/fine-tuning
    ↓
benchmark
    ↓
approval
    ↓
deployment
```

This separation prevents a single bad experience from immediately changing the model that governs future reasoning.

---

# 29. Evolution Tiers

Novi should expose its evolutionary capability as explicit tiers.

### Tier A — Learn

Always available within memory policies.

### Tier B — Consolidate

Background process that turns experiences into durable representations.

### Tier C — Extend knowledge

Controlled creation of entities, relationships and concepts.

### Tier D — Propose structural evolution

Creates schema proposals but does not necessarily execute them.

### Tier E — Execute approved structural evolution

Restricted to validated, low-risk changes under migration controls.

### Tier F — Software evolution

Outside autonomous memory evolution; handled by engineering/deployment workflows.

### Tier G — Protected core

Never autonomously modifiable.

---

# 30. Decision Matrix

| Change | Autonomous? | Validation | Human confirmation |
|---|---|---|---|
| transient state | yes | deterministic | no |
| ordinary memory | yes | admission policy | normally no |
| new entity candidate | yes | schema/type validation | no |
| new relationship | yes | provenance/policy | risk dependent |
| new tag/category | yes | quota/schema validation | no |
| new table | restricted | migration + policy | risk dependent |
| new index | restricted | migration + resource checks | normally no |
| schema destructive change | no by default | migration + recovery | yes |
| retention policy change | no | policy review | yes |
| authorization change | no | security/deployment process | yes |
| safety-policy change | no | engineering process | yes |
| executable code change | no | development pipeline | yes |
| protected-core change | forbidden | administrator-only process | explicit administrator |

---

# 31. Auditability

Every schema proposal and migration must generate an audit record containing:

- proposal ID;
- source evidence;
- proposing component;
- model/version if a model participated;
- validation results;
- policy decision;
- executor identity;
- migration version;
- affected objects;
- start/end timestamps;
- outcome;
- rollback/recovery reference.

The audit record must not rely on the model's private reasoning trace.

---

# 32. Observability

Metrics should include:

- schema proposals per day;
- proposal acceptance rate;
- rejection reasons;
- migration duration;
- migration failures;
- rollback frequency;
- schema churn;
- number of dynamic entity types;
- unused schema structures;
- index rebuild duration;
- database growth;
- memory-to-schema promotion rate;
- false promotion rate;
- human confirmation rate;
- protected-boundary violation attempts.

A rising schema proposal rate is a signal to investigate, not a reason to automatically increase permissions.

---

# 33. Testing Strategy

Schema evolution requires dedicated testing.

## Unit tests

- proposal validation;
- naming rules;
- type validation;
- permission checks;
- quota enforcement.

## Migration tests

- clean database;
- realistic populated database;
- large database;
- interrupted migration;
- corrupt migration;
- rollback;
- restart during migration;
- concurrent readers;
- concurrent writer contention.

## Security tests

- model attempts arbitrary SQL;
- model attempts filesystem escape;
- model attempts protected-area modification;
- malicious schema content;
- malicious custom SQL function;
- malicious extension;
- prompt injection through retrieved memory;
- privilege escalation through generated data.

## Evolution tests

- repeated new concepts;
- duplicate concepts;
- contradictory concepts;
- schema churn;
- invalid schema proposals;
- resource exhaustion;
- stale proposals;
- abandoned migrations.

## Recovery tests

- power loss;
- process crash;
- disk-full condition;
- corrupted index;
- damaged database;
- failed migration;
- failed backup.

---

# 34. Mac → Jetson Deployment

The schema architecture must remain portable.

During Mac development:

- schema proposals can be generated rapidly;
- migration tests can run against large synthetic datasets;
- expensive validation/indexing can use the Mac's resources;
- simulation can generate high event volumes.

On Jetson:

- authoritative memory remains local;
- structural changes are lower-priority background work;
- resource quotas are stricter;
- index rebuilds can be scheduled for idle periods;
- thermal/power pressure can suspend non-critical evolution;
- the robot remains operational using the last known valid schema.

The system must never require an experimental schema migration to remain capable of basic safe operation.

---

# 35. Offline Operation

Schema evolution must work without cloud connectivity.

Cloud must never be required for:

- validating a basic schema;
- writing ordinary memory;
- reading knowledge;
- maintaining the protected core;
- performing recovery;
- enforcing safety.

If an optional cloud-backed analysis would improve a proposal, the proposal can remain deferred until local validation or an authorized cloud path becomes available.

---

# 36. Design Invariants

The following invariants are mandatory:

1. **Learning cannot grant authority.**
2. **A model cannot directly modify the schema.**
3. **A schema cannot modify the policy that governs the schema.**
4. **A memory record cannot modify the protected core.**
5. **New knowledge should use existing structures before creating new ones.**
6. **Structural changes require explicit validation.**
7. **Destructive changes require recovery capability.**
8. **Authoritative data remains independent from rebuildable indexes.**
9. **Generated data remains distinguishable from observed data.**
10. **Provenance survives schema evolution.**
11. **Privacy classifications survive migration.**
12. **The robot must remain operational if an experimental evolution fails.**
13. **Cloud is never required for core safety or recovery.**
14. **The protected core is outside autonomous evolution.**
15. **Continuous learning does not imply autonomous model-weight modification.**

---

# 37. Recommended Initial Implementation

For V1, Novi should implement dynamic evolution conservatively:

```text
Tier 1
Existing schema + flexible attributes

Tier 2
New entities / relationships

Tier 3
Schema proposals

Tier 4
Automatically executable low-risk migrations
```

Initially, automatic migrations should be limited to changes that are:

- additive;
- reversible or recoverable;
- low risk;
- resource-bounded;
- non-security-sensitive;
- non-destructive;
- outside protected storage.

Examples of potentially eligible changes:

- adding an approved metadata field through an extension mechanism;
- creating a rebuildable non-critical index;
- creating a new non-sensitive relationship predicate in an existing relation table;
- creating a new entity category represented through an existing extensible entity structure.

Examples that should remain approval-gated:

- dropping data;
- changing retention;
- changing privacy classification rules;
- changing authorization;
- modifying protected tables;
- changing schema-manager behavior;
- installing executable extensions;
- modifying safety behavior.

---

# 38. Research Basis

This architecture was cross-validated against current primary documentation and established agent-memory approaches.

### NVIDIA NeMo Agent Toolkit

NVIDIA provides extensible memory interfaces and automatic memory capture/retrieval, supporting multiple memory providers. This validates separating Novi's memory API from any particular storage implementation. citeturn0search0turn0search8

### NVIDIA NeMo Guardrails

NVIDIA's guardrail architecture places programmable rails around input, retrieval, dialog, execution and output paths. This supports treating schema evolution and memory writes as policy-controlled operations rather than ordinary model output. citeturn0search12turn0search16

### NVIDIA authorization

NVIDIA's policy architecture separates principals, permissions and policy decisions. Novi adopts the same conceptual separation: a learned fact, identity, or model output does not itself constitute authorization. citeturn0search4turn0search10

### SQLite

SQLite's current documentation confirms that schema changes have important structural constraints and that arbitrary schema modifications require careful table-rebuild procedures. It also documents significant security implications around custom SQL functions, schema trust, and extensions. citeturn1search1turn1search0turn1search6

### Stateful agent architectures

Current stateful-agent systems such as Letta emphasize persistent memory and continual learning as distinct from simply passing an ever-growing conversation history to a model. This supports Novi's separation between active context, durable memory, consolidation, and controlled evolution. citeturn0search3

---

# 39. Final Architectural Rule

Novi should behave like a continuously learning organism **inside a controlled computational environment**.

The goal is not to make Novi static.

The goal is not to let Novi rewrite itself without boundaries.

The goal is:

```text
                    NOVI
                     │
              continuously learns
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
    memories      knowledge      skills
       │             │             │
       └─────────────┼─────────────┘
                     ▼
             proposes evolution
                     │
              policy boundary
                     │
             validation layer
                     │
             controlled migration
                     │
                verification
                     │
                new capability

          ─────────────────────────
          PROTECTED CORE
          never autonomously changed
          ─────────────────────────
```

**Novi may continuously change what it knows. It may carefully improve how it represents that knowledge. It must not autonomously redefine the rules that determine what it is allowed to do.**

That boundary is fundamental to the architecture of Novi.
