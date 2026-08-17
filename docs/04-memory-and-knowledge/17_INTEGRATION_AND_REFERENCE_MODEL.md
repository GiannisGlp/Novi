# 17 — Integration and Reference Model

**Status:** CANONICAL — CONSOLIDATED V1.1

## Purpose
Provide the single reference pipeline connecting memory semantics to governance and infrastructure.

## Reference pipeline

```text
OBSERVATION / INPUT
        ↓
EVIDENCE + PROVENANCE (03)
        ↓
IDENTITY / ENTITY (06)
        ↓
TIME / SPACE (07–08)
        ↓
CAUSAL / MULTIMODAL REASONING (09–10)
        ↓
MEMORY / KNOWLEDGE (01–05)
        ↓
SKILL / COMPETENCE (11)
        ↓
SCHEMA EVOLUTION (12)
        ↓
MODEL / MEMORY CO-EVOLUTION (13)
        ↓
PRIVACY (14)
        ↓
GOVERNANCE (15)
        ↓
HUMAN OVERSIGHT (16)
        ↓
DURABLE EXECUTION
```

This is a responsibility map, not a mandatory serial execution order. Systems may bypass irrelevant stages but must not bypass required ownership boundaries.

## Authority hierarchy

1. Current authenticated identity and authorization.
2. Machine-verifiable policy.
3. Protected infrastructure controls.
4. Provenance-bearing evidence.
5. Derived memory and knowledge.
6. Model inference and recommendation.

No lower layer may silently override a higher layer.

## State transition

Every consequential transition has an input state, proposed change, policy evaluation, execution result, provenance and outcome. Physical durability, consistency, replication, recovery and system-wide erasure are defined by system architecture.

## Canonical distinctions

```text
EVIDENCE ≠ CLAIM ≠ BELIEF
ENTITY ≠ AUTHENTICATED PRINCIPAL
TIME ≠ CAUSALITY
LOCATION ≠ PLACE IDENTITY
CORRELATION ≠ CAUSATION
COMPETENCE ≠ AUTHORIZATION
MEMORY ≠ POLICY
MODEL OUTPUT ≠ FACT
DELETE SOURCE ≠ AUTOMATIC MODEL UNLEARNING
RETRIEVAL ≠ TRUTH
CONFIDENCE ≠ VERIFICATION
```

## Reference scenarios

### 1. User preference

```text
user statement
→ evidence/provenance
→ identity scope
→ admission
→ preference memory
→ retrieval
→ governed use
```

### 2. Current physical state

```text
historical memory + current sensor
→ evidence arbitration
→ current-state precedence
→ reasoning
→ governance
```

Historical memory cannot override authoritative current state.

### 3. Contradictory evidence

```text
source A + source B
→ conflict set
→ temporal/scope/independence analysis
→ resolve / revalidate / abstain
```

### 4. Identity ambiguity

```text
observations
→ candidate entities
→ unresolved/ambiguous
→ no consequential forced merge
```

### 5. Multimodal disagreement

```text
vision + audio + telemetry
→ alignment
→ dependency analysis
→ fusion/conflict
→ uncertainty
```

### 6. Causal hypothesis

```text
observations
→ association
→ causal hypothesis
→ assumptions
→ intervention/validation
→ causal knowledge
```

### 7. Skill degradation

```text
skill verified
→ environment/model change
→ evaluation
→ degraded/suspended
→ revalidation
```

### 8. Schema migration

```text
proposal
→ compatibility
→ migration plan
→ staged validation
→ cutover
→ audit / rollback if needed
```

### 9. Privacy deletion

```text
privacy request
→ identify source + derivatives
→ restrict/delete
→ propagate dependencies
→ recovery/replica verification
→ erasure confirmation
```

### 10. Model upgrade

```text
new model
→ offline evaluation
→ compatibility
→ canary
→ longitudinal observation
→ promote / rollback
```

### 11. Human approval

```text
high-impact action
→ governance decision
→ review packet
→ human review
→ scoped approval/denial
→ execution
→ audit
```

### 12. Recovery/rebuild

```text
failure
→ recovery
→ rebuild derived views from durable evidence where feasible
→ integrity verification
→ resume governed operation
```

## Rebuildability

Derived views should be rebuildable from durable evidence/state where practical. When exact rebuild is impossible, the limitation and dependencies are recorded.

## Completion criterion

A subsystem is architecturally integrated only when its state, provenance, temporal semantics, privacy dependencies, authorization boundary, versioning, recovery behavior, evaluation hooks and failure/abstention behavior are explicit.