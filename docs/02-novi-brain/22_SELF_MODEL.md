# 22 — Self Model

**Status:** SUPERSEDED — legacy cross-domain source document  
**Canonical semantic owner:** `03-cognition/01_COGNITIVE_ARCHITECTURE.md`  
**Physical/runtime authorities:** Brain, hardware and system architecture  
**Historical self-memory:** `04-memory-and-knowledge`

## Why this file was superseded

The former document attempted to make Brain the owner of every aspect of Novi's self model. The audit determined that self representation is inherently cross-domain and must be split by authority.

## Canonical separation

```text
PHYSICAL SELF
  body configuration / pose / joints / sensors / actuators / power / thermal
  → hardware + Brain/runtime authority

SEMANTIC SELF MODEL
  capabilities / limitations / self-related reasoning / capability confidence
  → Cognition authority

AUTOBIOGRAPHICAL SELF HISTORY
  previous actions / experiences / learned competencies / historical configurations
  → Memory & Knowledge authority

CURRENT BEHAVIORAL STATE
  active goals / tasks / plans / interruptions
  → Autonomy authority
```

## Critical invariants

```text
language capability ≠ physical capability
physical capability ≠ authorization
authorization ≠ safe-now capability
installed ≠ validated
validated ≠ currently available
commanded ≠ executed
executed ≠ world outcome
```

The Self Model must be grounded in authoritative telemetry and typed evidence rather than generated prose.

## Consolidated requirements

The former specification's important requirements remain valid:

- explicit capability registry;
- distinction between installed, available, validated, safe-now and authorized-now capabilities;
- current activity representation;
- grounded self-location;
- commanded-vs-observed action verification;
- action provenance and outcome attribution;
- resource-aware cognitive state;
- degraded modes and recovery;
- grounded self-knowledge and explicit unknown capability;
- self-aware active perception;
- continuity across interruption and recovery;
- durable identity/configuration separated from recoverable and ephemeral runtime state;
- deterministic safety and hardware limits that ordinary learning cannot rewrite;
- simulation competence remaining distinct from physical validation.

## Safety boundary

The Self Model may report state and recommend constraints. It never becomes the final safety controller and never directly commands actuators.

## Migration rule

Do not create another single-owner Self Model. Extend the canonical Cognition self-model boundary, Brain state model, Memory/Knowledge history and Autonomy state as appropriate.

## Historical preservation

The complete pre-consolidation specification remains available in Git history for provenance and recovery.
