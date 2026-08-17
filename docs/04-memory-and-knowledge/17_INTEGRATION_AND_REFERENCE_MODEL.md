# 17 — Integration and Reference Model

**Status:** CANONICAL — CONSOLIDATED V1

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
DURABLE EXECUTION (107+)
```

## Authority hierarchy

1. Current authenticated identity and authorization.
2. Machine-verifiable policy.
3. Protected infrastructure controls.
4. Provenance-bearing evidence.
5. Derived memory and knowledge.
6. Model inference and recommendation.

No lower layer may silently override a higher layer.

## State transition

Every consequential transition has an input state, proposed change, policy evaluation, execution result, provenance and outcome. Durable execution semantics are defined in 107; consistency and distribution in 108/109; recovery in 110; privacy lifecycle in 111.

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
```

## Rebuildability

Derived views should be rebuildable from durable evidence/state where practical. When exact rebuild is impossible, the limitation and dependencies are recorded.

## Reference scenarios

The architecture must support offline operation, conflicting observations, human correction, model updates, schema migration, privacy deletion, distributed synchronization, recovery and high-impact authorization without changing the meaning of the canonical entities.

## Completion criterion

A subsystem is architecturally integrated only when its state, provenance, temporal semantics, privacy dependencies, authorization boundary, versioning and recovery behavior are explicit.