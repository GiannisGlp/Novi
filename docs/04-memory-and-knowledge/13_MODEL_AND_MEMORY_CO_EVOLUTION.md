# 13 — Model and Memory Co-Evolution

**Status:** CANONICAL — CONSOLIDATED V1

## Purpose
Define how model changes and memory changes interact without allowing either to silently invalidate the other.

## Core principle

```text
MODEL VERSION + MEMORY VERSION + SCHEMA VERSION + POLICY VERSION
                         ↓
                  COMPATIBILITY CONTRACT
```

A model update is not automatically compatible with existing memory, schemas, embeddings, skills or governance assumptions.

## Change classes

- model replacement;
- model fine-tuning/update;
- embedding-model replacement;
- tokenizer change;
- prompt/policy change;
- memory schema change;
- retrieval/index change;
- consolidation algorithm change;
- skill/evaluation change.

Each change receives a version and compatibility assessment.

## Compatibility

Compatibility must be evaluated for representation, retrieval, semantics, safety, provenance, privacy, performance and skill behavior.

## Derived representations

Embeddings, summaries, classifications and model-generated claims are derived state. Their source dependencies must remain traceable. A model change may require re-embedding or re-derivation; such work must be versioned and reversible where practical.

## Promotion pipeline

```text
CHANGE PROPOSAL
 ↓
OFFLINE EVALUATION
 ↓
COMPATIBILITY CHECK
 ↓
POLICY REVIEW
 ↓
CANARY
 ↓
OBSERVATION
 ↓
PROMOTE / ROLLBACK
```

## Memory poisoning and contamination

New model behavior must not silently rewrite trusted historical memory. Reinterpretation is a new derived view unless explicit migration is approved.

## Unlearning and deletion

Deleting source data does not automatically establish model forgetting. Dependency-aware deletion follows `14`/`111`; model retraining or targeted remediation is a separate controlled process.

## Rollback

Rollback must identify which memory and derived artifacts were produced under the changed model. Recovery uses `110` and governance uses `105/106`.

## Evaluation

Compare old/new models on retrieval correctness, factual consistency, identity resolution, causal behavior, skill performance, privacy leakage, policy compliance and longitudinal memory stability.

## Safety invariants

1. Model updates are versioned.
2. Memory and model versions are traceable.
3. Reinterpretation is not silent historical mutation.
4. Derived artifacts identify their producing model/version.
5. Rollback considers dependent memory artifacts.
6. Deletion obligations survive model changes.
7. Self-improvement proposals are not automatically approved changes.