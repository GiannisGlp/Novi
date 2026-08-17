# 103 — Memory Knowledge Schema Migration, Compatibility and Evolution Architecture

## Status

**NORMATIVE ARCHITECTURE — CRITICAL / V1**

## Purpose

Define how Novi evolves memory and knowledge schemas without silently corrupting meaning, provenance, identity, temporal state, spatial state, causal models, skills, privacy controls or historical records.

This document resolves the P0 schema-migration gap identified by document 96 and builds on documents 95–102.

## 1. Core Principle

> **A schema change is a semantic change unless proven otherwise. Novi must version the schema, assess compatibility, preserve provenance, migrate data deliberately, validate the result, and retain enough lineage to explain how old meaning became new meaning.**

Research on schema evolution consistently treats schema and data migration as coupled problems rather than independent operations. Recent work also emphasizes the relationship between schema evolution and provenance. [1][2][3] citeturn0search0turn0search2turn0search5

## 2. Schema Is More Than Storage Shape

Novi schema includes:

```text
STRUCTURE
SEMANTICS
CONSTRAINTS
IDENTIFIERS
RELATIONSHIPS
TEMPORAL MEANING
PROVENANCE
PRIVACY
SECURITY
LIFECYCLE
```

Changing a field type, relationship, identifier semantics or validity rule can change the meaning of existing memories.

## 3. Schema vs Data

```text
SCHEMA
→ rules describing valid representations

DATA
→ instances represented under those rules
```

A schema migration may require transforming both.

## 4. Schema Version Identity

Every normative schema must have a stable identifier and version:

```text
SCHEMA_ID
SCHEMA_VERSION
RELEASE_TIME
VALIDITY
COMPATIBILITY_POLICY
```

A version must be immutable once released.

## 5. Schema Registry

Novi should maintain a registry containing:

- schema identifiers;
- versions;
- dependencies;
- compatibility declarations;
- migration plans;
- validation status;
- deprecation state;
- provenance;
- owners/authorities.

## 6. Canonical Schema

For each memory type, one schema version is authoritative for new writes.

Historical records may remain encoded under older schemas while being interpreted through controlled compatibility mechanisms.

## 7. Versioning Is Not Migration

```text
VERSIONING
→ identifies different schemas

MIGRATION
→ transforms or interprets data between versions
```

Creating schema V2 does not imply that all V1 data has already been migrated.

## 8. Compatibility Dimensions

Novi must evaluate at least:

```text
READ COMPATIBILITY
WRITE COMPATIBILITY
SEMANTIC COMPATIBILITY
PROVENANCE COMPATIBILITY
SECURITY COMPATIBILITY
PRIVACY COMPATIBILITY
TEMPORAL COMPATIBILITY
IDENTITY COMPATIBILITY
```

## 9. Backward Compatibility

A newer reader can interpret data written under an older schema.

```text
V1 DATA
 ↓
V2 READER
```

This is useful for rolling upgrades and lazy migration.

## 10. Forward Compatibility

An older reader can safely interpret data written under a newer schema, usually with controlled loss of new optional semantics.

```text
V2 DATA
 ↓
V1 READER
```

Forward compatibility must not silently discard decision-critical information.

## 11. Full Compatibility

Where operationally necessary, Novi may require both backward and forward compatibility.

Compatibility policies must be explicit rather than assumed.

Schema registries commonly distinguish backward, forward, full and transitive compatibility. [4] citeturn0search9

## 12. Transitive Compatibility

A schema may need compatibility with all supported historical versions, not only its immediate predecessor.

```text
V1 ←→ V2 ←→ V3
```

must not be assumed equivalent to:

```text
V3 ←→ V1
```

unless transitive compatibility is actually validated.

## 13. Semantic Compatibility

Two schemas can be structurally compatible while semantically incompatible.

Example:

```text
V1: temperature = Celsius
V2: temperature = Fahrenheit
```

The field remains numeric, but its meaning changed.

## 14. Compatibility Classification

Every schema change should be classified as:

```text
NON-BREAKING
CONDITIONALLY COMPATIBLE
BREAKING
SEMANTICALLY BREAKING
UNKNOWN
```

Unknown changes require review rather than optimistic classification.

## 15. Change Types

Schema changes include:

- add field;
- remove field;
- rename field;
- split field;
- merge fields;
- change type;
- change units;
- change cardinality;
- change nullability;
- change enum values;
- change relationship semantics;
- change identifier rules;
- change temporal semantics;
- change provenance requirements;
- change privacy classification.

## 16. Additive Changes

Adding an optional field can often be compatible.

However, if consumers interpret absence as a meaningful state, the change may still be semantic.

## 17. Removing Fields

Removing a field is not safe merely because old code no longer reads it.

The field may be required for:

- provenance;
- audit;
- deletion;
- identity resolution;
- temporal reconstruction;
- causal reasoning.

## 18. Rename Operations

A rename must preserve semantic identity where the field represents the same concept.

```text
old_name → new_name
```

must not be represented as unrelated deletion + creation when lineage matters.

## 19. Split Operations

```text
FULL_NAME
 ↓
FIRST_NAME + LAST_NAME
```

requires a deterministic or uncertainty-aware transformation and provenance indicating the derivation.

## 20. Merge Operations

```text
LATITUDE + LONGITUDE
 ↓
LOCATION
```

may be irreversible if precision or semantics are lost.

Loss must be explicit.

## 21. Type Changes

Type changes require semantic and representational analysis.

```text
INTEGER → STRING
```

may be safe only if all valid values and downstream semantics are preserved.

## 22. Unit Changes

Units must never be changed silently.

```text
meters → feet
Celsius → Fahrenheit
seconds → milliseconds
```

must carry an explicit transformation.

## 23. Identifier Changes

Changing an identifier is a high-risk operation because documents 97 and 92 depend on stable identity and lineage.

Identifier migration must preserve an old-to-new mapping with validity and provenance.

## 24. Entity Identity Must Survive Migration

```text
ENTITY_ID
```

must not change merely because its representation schema changes.

A schema migration is not an entity merge or split.

## 25. Temporal Semantics Must Survive

Migration must preserve distinctions established by 98:

```text
EVENT TIME
VALID TIME
TRANSACTION TIME
OBSERVATION TIME
REVISION TIME
```

A migration must not collapse these into one timestamp merely for convenience.

## 26. Spatial Semantics Must Survive

Migration must preserve spatial precision, coordinate reference systems, topology and uncertainty where applicable.

A coordinate-system transformation must be recorded as a transformation, not a simple field rename.

## 27. Causal Semantics Must Survive

Migration of causal records must preserve:

- causal model version;
- assumptions;
- intervention semantics;
- validity regime;
- evidence lineage;
- uncertainty.

A causal claim cannot be safely migrated as generic text alone.

## 28. Cross-Modal Provenance Must Survive

Migration of multimodal memories must retain links to original evidence and derived representations.

```text
RAW IMAGE
 ↓
DERIVED FEATURE
 ↓
MEMORY
```

must remain traceable after migration.

## 29. Skill Semantics Must Survive

Skill and competence records from 102 must retain:

```text
SKILL ID
VERSION
AGENT / EMBODIMENT
ENVIRONMENT
EVIDENCE
VALIDATION
SAFETY STATUS
```

A schema migration must not accidentally promote an old competence claim to a new environment.

## 30. Provenance Is Part of Migration

Schema evolution and provenance should be managed together. Recent research specifically proposes joining schema-evolution provenance with data provenance to preserve the history of transformations. [1] citeturn0search0

## 31. Migration as an Activity

Every migration should be represented as a provenance-bearing activity:

```text
OLD DATA
   ↓
MIGRATION ACTIVITY
   ↓
NEW DATA
```

This aligns with provenance models in which entities and activities are linked through generation, usage and derivation histories. citeturn1search1turn1search2

## 32. Migration Provenance

Record:

- source schema;
- target schema;
- migration version;
- code/configuration;
- operator or automation;
- start/end time;
- input/output counts;
- validation results;
- exceptions;
- rollback information.

## 33. Deterministic Migration

Where possible, migrations should be deterministic and reproducible.

Given:

```text
DATA V1 + MIGRATION M1→M2
```

the same input should produce the same semantic output unless nondeterminism is explicitly part of the transformation.

## 34. Idempotence

Migration operations should be idempotent where feasible:

```text
M(M(data)) = M(data)
```

If not idempotent, the operation must be explicitly guarded against repeated execution.

## 35. Dry Run

Before production migration:

```text
SCHEMA DIFF
 ↓
DRY RUN
 ↓
IMPACT ANALYSIS
 ↓
VALIDATION
 ↓
APPROVAL
```

Automated approaches to schema evolution can generate migration strategies and detect impossible transformations, supporting this principle. [2][3] citeturn0search2turn0search10

## 36. Impact Analysis

A schema change must identify affected:

- readers;
- writers;
- indexes;
- embeddings;
- graph relationships;
- caches;
- provenance records;
- policies;
- evaluators;
- models;
- downstream services.

## 37. Dependency Graph

```text
SCHEMA
 ↓
DATA
 ↓
INDEXES
 ↓
MODELS
 ↓
MEMORIES
 ↓
RETRIEVAL
 ↓
DECISIONS
```

Migration planning must account for dependency propagation.

## 38. Lazy Migration

Old data may be migrated at read time:

```text
V1 RECORD
 ↓
UPCAST / ADAPTER
 ↓
V2 VIEW
```

This reduces migration downtime but increases runtime complexity.

## 39. Eager Migration

All affected records are transformed before or during a controlled deployment.

This simplifies runtime behavior but can be expensive and operationally risky.

## 40. Hybrid Migration

Novi should support:

```text
HOT DATA → eager
COLD DATA → lazy
```

when this meets latency, reliability and compliance requirements.

Research on adaptive migration demonstrates that migration strategy involves tradeoffs among migration cost, latency and data quality, and that strategy should depend on workload and requirements. [3] citeturn0search3

## 41. Event-Sourced Memory

If memory is represented as events, schema evolution must preserve the historical event stream.

Research with practitioners identifies versioned events, weak schemas, upcasting, in-place transformation and copy-and-transform as established tactics for evolving event-sourced systems. [5] citeturn0search1turn0search11

## 42. Event Upcasting

Older events may be interpreted through an adapter:

```text
EVENT V1
 ↓
UPCAST
 ↓
EVENT V2 VIEW
```

The original event remains unchanged where preservation is required.

## 43. Copy-and-Transform

Where transformation is irreversible or audit-critical:

```text
OLD DATA
 ↓
COPY
 ↓
TRANSFORM
 ↓
NEW DATA
```

The source remains available for verification and rollback according to retention policy.

## 44. In-Place Transformation

In-place migration may be used where:

- transformation is proven safe;
- rollback is available;
- provenance is retained;
- privacy rules permit it.

It must not be the default merely because it is operationally convenient.

## 45. Weak Schema

Schema-flexible historical records may remain readable through adapters while the canonical schema evolves.

However, schema flexibility must not become uncontrolled structural entropy.

## 46. Dual Read / Dual Write

During rolling migration:

```text
WRITE
 ↙   ↘
V1   V2

READ
↙     ↘
V1     V2
```

Dual-write periods require consistency checks and explicit end-of-life criteria.

## 47. Expand-and-Contract

For distributed systems, prefer staged changes where appropriate:

```text
EXPAND
 ↓
MIGRATE
 ↓
VALIDATE
 ↓
CONTRACT
```

Do not remove old representations until all supported consumers have migrated.

## 48. Compatibility Gates

A schema release should fail automated validation when required compatibility checks fail.

```text
SCHEMA CHANGE
 ↓
COMPATIBILITY TESTS
 ↓
PASS / BLOCK
```

## 49. Semantic Migration Tests

Tests must verify more than serialization.

Examples:

```text
identity preserved?
temporal meaning preserved?
spatial meaning preserved?
causal meaning preserved?
provenance preserved?
privacy preserved?
deletability preserved?
```

## 50. Round-Trip Testing

Where reversible transformations are claimed:

```text
V1 → V2 → V1
```

should preserve all required semantics.

If round-trip fidelity is impossible, the information loss must be documented and approved.

## 51. Golden Records

Maintain representative records covering:

- minimal cases;
- maximal cases;
- historical cases;
- ambiguous identities;
- multimodal memories;
- temporal intervals;
- spatial uncertainty;
- causal hypotheses;
- sensitive records;
- deleted records.

These become migration regression fixtures.

## 52. Migration Invariants

Before and after migration, validate invariants such as:

```text
record count where applicable
identity referential integrity
provenance connectivity
temporal ordering
relationship integrity
privacy labels
security constraints
causal dependency links
skill validation state
```

Counts alone are insufficient because a migration can preserve row count while corrupting meaning.

## 53. Referential Integrity

All migrated references must resolve according to the target schema.

Broken references must fail validation rather than being silently dropped.

## 54. Orphan Detection

After migration detect:

- orphan memories;
- orphan entity IDs;
- orphan provenance nodes;
- orphan relationships;
- stale embeddings;
- obsolete indexes.

## 55. Embedding Migration

Schema changes affecting semantic content may invalidate embeddings.

Novi must distinguish:

```text
STORAGE-ONLY CHANGE
→ embedding may remain valid

SEMANTIC CHANGE
→ embedding may require regeneration
```

Embedding model/version must be recorded.

## 56. Index Migration

Indexes are derived structures and should be rebuildable from canonical data.

Never treat an index as the authoritative source of memory semantics.

## 57. Cache Migration

Caches must have explicit invalidation or compatibility rules.

Stale caches must not reintroduce pre-migration semantics after canonical data has moved forward.

## 58. Graph Migration

Graph schema evolution must preserve:

```text
NODE IDENTITY
EDGE SEMANTICS
EDGE VALIDITY
PROVENANCE
TEMPORAL QUALIFIERS
```

Relationship renames must not accidentally become new unrelated relationships.

## 59. Privacy During Migration

Migration jobs inherit the source data's privacy requirements.

Temporary copies, logs, staging tables and failure artifacts are all data and must be governed accordingly.

## 60. Deletion During Migration

Erasure requests must remain effective across migration boundaries.

```text
DELETED DATA
 ≠
DATA RESTORED BY MIGRATION
```

Migration systems must check deletion/tombstone state before materializing legacy data.

## 61. Security During Migration

Migration tooling is a privileged attack surface.

Threats include:

- unauthorized schema changes;
- malicious migration code;
- data exfiltration through staging;
- provenance forgery;
- rollback to vulnerable schema;
- malicious compatibility bypass.

## 62. Migration Authorization

High-impact migrations require explicit authorization and separation of duties where appropriate.

```text
AUTHOR
 ≠
APPROVER
 ≠
EXECUTOR
```

Automation may combine roles only when risk policy explicitly permits it.

## 63. Rollback

Every migration plan must define:

```text
ROLLBACK POSSIBLE?
ROLLBACK METHOD
ROLLBACK WINDOW
DATA LOSS RISK
DEPENDENCY IMPACT
```

Some migrations are irreversible; those require stronger preconditions.

## 64. Roll-Forward

If rollback is unsafe after new writes occur, Novi may prefer a corrective forward migration.

The choice must be made before deployment where possible.

## 65. Migration Checkpoints

Large migrations should use checkpoints:

```text
BATCH 1
 ↓
VALIDATE
 ↓
BATCH 2
 ↓
VALIDATE
```

This limits blast radius.

## 66. Partial Failure

A failed migration must leave the system in a known state:

```text
COMMITTED
ROLLED BACK
PARTIALLY MIGRATED / QUARANTINED
```

The last state must never be mistaken for successful completion.

## 67. Quarantine

Records that cannot be safely transformed should enter a quarantine path with:

- source record;
- error;
- migration version;
- reason;
- retry status;
- ownership;
- privacy/security controls.

## 68. Observability

Track:

- migration throughput;
- latency;
- failures;
- retries;
- transformed records;
- quarantined records;
- validation failures;
- schema-version distribution.

## 69. Migration Audit

The audit log must permit reconstruction of:

```text
WHAT CHANGED?
WHO / WHAT CHANGED IT?
WHEN?
WHY?
FROM WHICH VERSION?
TO WHICH VERSION?
WHICH DATA?
WHAT VALIDATION OCCURRED?
```

## 70. Schema Deprecation

Deprecation should follow:

```text
ACTIVE
 ↓
DEPRECATED
 ↓
READ-ONLY
 ↓
UNSUPPORTED
 ↓
RETIRED
```

Deprecation dates and consumer requirements must be explicit.

## 71. Retention of Old Schemas

Historical schemas may need to remain available when required to interpret retained records, provenance or legal/audit obligations.

Retiring a schema must not make retained data semantically uninterpretable.

## 72. Compatibility Windows

Each migration should define how long old readers/writers remain supported.

Distributed deployments must not assume instantaneous upgrade.

## 73. Schema Negotiation

Cross-agent and cross-service exchanges should negotiate supported schema versions where required:

```text
SUPPORTED: V1,V2,V3
SELECT: V2
```

Negotiation must not silently select a version that loses required semantics.

## 74. Cross-Agent Memory Contracts

Document 108 will eventually define broader cross-agent contracts, but 103 establishes the prerequisite:

```text
SCHEMA ID
VERSION
CAPABILITIES
COMPATIBILITY
PROVENANCE
```

must travel with exchanged memory where necessary.

## 75. Schema Translation Across Systems

Translation between different paradigms is not merely version migration:

```text
RELATIONAL → GRAPH
DOCUMENT → RELATIONAL
GRAPH → VECTOR INDEX
```

These are semantic transformations and require explicit mapping and loss analysis.

## 76. No Silent Loss

If target schema cannot represent source information:

```text
LOSS DETECTED
 ↓
BLOCK / QUARANTINE / EXPLICIT LOSS POLICY
```

Never silently discard information required by downstream semantics.

## 77. Unknown Fields

Readers may preserve unknown fields when safe so future schema evolution does not cause accidental data destruction.

Preservation must respect security and privacy rules.

## 78. Schema Evolution and AI Models

Models consuming memory must declare supported schema semantics where necessary.

A model trained or validated against V1 cannot automatically be assumed safe for V2 semantic changes.

## 79. Model Compatibility

A schema change affecting model inputs requires evaluation of:

- performance;
- calibration;
- safety;
- bias;
- retrieval behavior;
- downstream decisions.

This prepares for document 104 on model/memory co-evolution.

## 80. Migration and Memory Consolidation

Consolidated memories must retain links to source memories and migration lineage.

A migration must not turn derived knowledge into apparently original observations.

## 81. Migration and Temporal Reconstruction

When historical data is migrated, its original validity and transaction semantics must remain reconstructible.

Migration time is not the same as event time.

## 82. Migration and Causal Models

If a causal model depends on a schema version that is retired, the model must retain either:

```text
ORIGINAL SCHEMA
```

or a validated semantic translation sufficient to interpret its evidence.

## 83. Migration and Competence

Skill validation evidence tied to a previous schema must remain interpretable.

A schema migration must not reset or silently preserve competence status without checking semantic equivalence.

## 84. Formal Migration Contract

Every production migration should define:

```text
SOURCE SCHEMA
TARGET SCHEMA
TRANSFORMATION
PRECONDITIONS
POSTCONDITIONS
COMPATIBILITY
LOSS POLICY
PROVENANCE
VALIDATION
ROLLBACK / ROLLFORWARD
AUTHORIZATION
```

## 85. Migration State Machine

```text
DRAFT
 ↓
ANALYZED
 ↓
TESTED
 ↓
APPROVED
 ↓
DEPLOYED
 ↓
VALIDATING
 ↓
COMPLETED
```

Failure states:

```text
BLOCKED
QUARANTINED
ROLLED_BACK
RETIRED
```

## 86. Schema Evolution Evaluation

Evaluate:

- structural compatibility;
- semantic preservation;
- provenance preservation;
- referential integrity;
- privacy preservation;
- deletion correctness;
- model behavior;
- retrieval behavior;
- latency/cost;
- rollback behavior.

## 87. Migration Testing Matrix

At minimum test:

```text
V1 → V2
V2 → V3
V1 → V3 where supported
V3 reader ← V1 data
V1 reader ← V3 data where supported
```

and representative failure cases.

## 88. Research Cross-Validation

The architecture is cross-validated against:

1. **PROV-IDEA (2025)** — schema evolution provenance should be coordinated with data provenance and can use interoperable provenance standards. citeturn0search0
2. **EvolveDB (2025)** — schema evolution can be modeled as differences between versions and transformed into executable migration strategies; empirical work highlights the error-prone nature of schema changes. citeturn0search2
3. **Self-adapting NoSQL migration (2021/2022)** — migration strategy involves workload-dependent tradeoffs among migration cost, latency and data quality. citeturn0search3
4. **Event-sourced systems (2021)** — practitioners report versioned events, upcasting, in-place transformation and copy-and-transform as established evolution tactics. citeturn0search1
5. **2026 systematic mapping study** — schema evolution and migration remain distinct but coupled areas spanning database evolution, data transfer and schema translation. citeturn0search5
6. **W3C PROV** — provenance can represent entities, activities and transformations and provides consistency/validity concepts useful for migration lineage. citeturn1search0turn1search1

These sources support the architecture's emphasis on explicit versions, compatibility policies, migration strategies, provenance, validation and semantic-loss detection. They do not establish one universally optimal migration mechanism.

## 89. Architectural Invariants

1. Schema versions are immutable once released.
2. Schema identity is distinct from storage implementation.
3. Schema versioning is not migration.
4. Structural compatibility does not imply semantic compatibility.
5. Compatibility must be explicitly classified.
6. Unknown compatibility is not assumed safe.
7. Schema and data migration are coupled.
8. Migration is a provenance-bearing activity.
9. Entity IDs survive schema migration unless identity itself is intentionally changed.
10. Temporal semantics must survive migration.
11. Spatial semantics must survive migration.
12. Causal semantics must survive migration.
13. Cross-modal evidence lineage must survive migration.
14. Skill validation state must not be silently promoted or invalidated.
15. Derived indexes are not canonical memory.
16. Embeddings may require regeneration after semantic changes.
17. Privacy and deletion rules apply to migration artifacts.
18. Migration tooling is a privileged security boundary.
19. Irreversible transformations require explicit loss policy.
20. Quarantine is preferable to silent corruption.
21. Migrations must be observable and auditable.
22. Rollback or roll-forward strategy must be explicit.
23. Historical schemas must remain interpretable for retained data.
24. Dual-read/write periods require explicit exit criteria.
25. Migration validation must test semantics, not only row counts.
26. Model behavior must be reevaluated when input semantics change.
27. Provenance must explain source, transformation and target.
28. Migration must never recreate erased data.
29. Old data must never silently acquire new semantic meaning.
30. A successful migration is one that preserves required meaning, not merely one that completes without errors.

## 90. Integration With Document 95

The migration layer sits beneath the reference pipeline:

```text
SCHEMA / VERSION
 ↓
DATA / MEMORY
 ↓
PROVENANCE
 ↓
RETRIEVAL
 ↓
ARBITRATION
 ↓
REASONING
 ↓
ACTION
```

Migration must preserve the invariants of every downstream layer.

## 91. Integration With 97–102

```text
97 Identity
→ preserve canonical entity identity and mappings

98 Temporal
→ preserve validity, observation and transaction time

99 Spatial
→ preserve geometry, topology, precision and coordinate semantics

100 Causal
→ preserve causal model lineage, scope and assumptions

101 Cross-Modal
→ preserve modality lineage and evidence independence

102 Skill
→ preserve competence evidence, scope and validation state
```

## 92. Integration With 96

103 resolves the P0 gap:

**Memory Schema Migration / Compatibility / Evolution.**

It also establishes a prerequisite for:

- 104 model/memory co-evolution;
- 105 machine-verifiable governance;
- 106 human oversight;
- 107 distributed replication;
- 108 cross-agent memory contracts.

## 93. Final Principle

> **Novi must evolve its schemas without losing the history, identity, meaning, provenance, privacy and uncertainty encoded by earlier versions. Every migration is therefore a controlled semantic transformation—not merely a database upgrade.**
