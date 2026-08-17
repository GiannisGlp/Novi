# 12 — Schema and Knowledge Evolution

**Status:** CANONICAL — CONSOLIDATED V1

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

A new fact normally requires no schema change. fileciteturn212file0

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

Forbidden to autonomous Novi. Administrator/developer-controlled processes only. fileciteturn212file0

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

A migration is invalid if it preserves values but loses:

- provenance;
- identity;
- validity intervals;
- privacy classification;
- retention/deletion semantics;
- security policy;
- derivation lineage;
- compatibility with replicas/indexes.

This follows the architecture audit's requirement that schema evolution preserve the semantics of the entire memory state, not only stored values. fileciteturn215file0

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

A model-generated proposal cannot grant itself permission to modify these assets.

## Dynamic data versus schema change

Flexible metadata should be used where it is sufficient. Structural schema changes should be rare, justified and observable.

The system should record proposal reason, affected objects, compatibility impact, policy decision, migration version, execution result and verification result.

## Source consolidation

Merged into this canonical document:

- `07_MEMORY_SCHEMA_AND_STORAGE.md` — semantic schema aspects;
- `10_MEMORY_SCHEMA_EVOLUTION_AND_DYNAMIC_DATA.md`;
- schema evolution requirements identified by Document 96.

Physical database migration mechanics belong to the system/implementation architecture rather than this semantic contract. fileciteturn212file0