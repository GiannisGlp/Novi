# 12 — Schema and Knowledge Evolution

**Status:** CANONICAL — CONSOLIDATED V1.1

## Purpose

Define how Novi evolves knowledge and memory structures without allowing autonomous self-modification of its safety, authorization, security or executable control plane.

> Learning is not the same thing as modifying the system that performs learning.

## Core distinction

Knowledge evolution is normal memory operation. Structural schema evolution is a controlled operation.

```text
new information
 ↓
try existing representation first
 ↓
store / consolidate

new concept not representable
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

## Existing-schema-first rule

Before proposing a new structure, evaluate in order:

1. existing entity type;
2. existing attribute;
3. existing relationship;
4. existing event/memory type;
5. flexible metadata/JSON where appropriate;
6. extension table;
7. new schema proposal only when necessary.

This prevents schema explosion.

## Evolution levels

### Level 0 — Runtime state
Autonomous within resource/policy limits: current state, hypotheses, active attention and transient conversation state.

### Level 1 — Memory content
Autonomous admission subject to the memory write gate.

### Level 2 — Knowledge content
Controlled promotion to durable semantic knowledge.

### Level 3 — Non-structural metadata
Tags, labels, annotations, confidence metadata, embedding references and learned categories within quotas.

### Level 4 — Schema extension
Requires proposal, validation and controlled migration: new entity types, relationship predicates, columns, indexes, extension tables or schema versions.

### Level 5 — Runtime/software changes
Not autonomous: executable code, safety logic, authorization logic, migration engine, arbitrary package installation, model router or startup behavior.

### Level 6 — Protected core
Forbidden to autonomous Novi. Administrator/developer-controlled processes only.

## Compatibility matrix

Every schema change must classify compatibility at least as:

```text
COMPATIBLE
CONDITIONALLY_COMPATIBLE
MIGRATION_REQUIRED
REBUILD_REQUIRED
ROLLBACK_REQUIRED
FORBIDDEN
```

Evaluate the change against:

| Surface | Required check |
|---|---|
| semantic meaning | unchanged or explicitly migrated |
| provenance | preserved |
| identity | preserved |
| temporal validity | preserved |
| privacy | preserved/strengthened |
| authorization | preserved/strengthened |
| retrieval/indexes | compatible or rebuilt |
| embeddings | re-derived if representation changed |
| replicas | migration compatibility verified |
| deletion dependencies | preserved |
| audit history | retained |

## Model role

The reasoning model may propose a schema change but never owns schema authority and never executes arbitrary SQL, DDL, filesystem operations, migration scripts, code or permission changes.

```text
Model proposal
 ↓
schema validation
 ↓
compatibility analysis
 ↓
policy authorization
 ↓
migration planning
 ↓
controlled execution
 ↓
verification
 ↓
commit / rollback
```

## Migration invariants

A migration is invalid if it preserves values but loses provenance, identity, validity intervals, privacy classification, retention/deletion semantics, security policy, derivation lineage or compatibility with indexes/replicas.

## Rollback and dual-read safety

For consequential migrations, prefer staged rollout where feasible:

```text
old schema + new schema
        ↓
backfill / validate
        ↓
shadow read comparison
        ↓
controlled cutover
        ↓
verification
        ↓
retire old representation
```

Rollback must preserve the semantic history and must not reintroduce deleted/prohibited data.

## Protected core

Autonomous memory evolution cannot modify:

```text
safety policy
authorization policy
trust roots
migration engine
security boundaries
protected executable control plane
signing material
```

## Evaluation

Schema evolution must be tested for backward/forward compatibility where applicable, provenance preservation, privacy preservation, retrieval correctness, deletion correctness, migration idempotency, rollback and historical reconstruction.

## Integration

`01–11` define semantic structures being evolved. `13` governs model/memory compatibility. `14–16` govern privacy and authorization. Physical migration and distributed execution belong to system architecture.

## Source consolidation

The historical corpus remains preserved in `archive/`. The active authority is this document and the other canonical 01–18 documents.