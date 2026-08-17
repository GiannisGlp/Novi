# 104 — Memory Knowledge Model / Memory Co-Evolution Architecture

## Status

**NORMATIVE ARCHITECTURE — CRITICAL / V1**

## Purpose

Define how Novi's learned models and persistent memory evolve together without silently changing the meaning, reliability, provenance, privacy, or operational consequences of existing memory.

This document resolves the P0 **Model / Memory Co-Evolution** gap identified by document 96. It integrates documents 95–103 and treats model versions, memory versions, derived representations, evaluations, migrations, and runtime behavior as separately versioned but causally connected system state.

## 1. Core Principle

> **A model may change without changing memory, and memory may change without changing a model; whenever one changes the interpretation or behavior of the other, Novi must record, evaluate, and govern that dependency explicitly.**

Continual-learning research identifies catastrophic forgetting and the stability–plasticity trade-off as central challenges when models learn from non-stationary streams. citeturn0academia0turn0academia2

## 2. Model, Memory, and Knowledge Are Different Assets

```text
MODEL
→ parameters / architecture / learned computation

MEMORY
→ retained observations, experiences, facts, relationships, procedures

KNOWLEDGE
→ derived or consolidated claims and abstractions
```

They may depend on each other but must never be treated as one mutable object.

## 3. Independent Versioning

At minimum Novi should version:

```text
MODEL VERSION
MEMORY SCHEMA VERSION
MEMORY CONTENT VERSION / REVISION
KNOWLEDGE VERSION
EMBEDDING / REPRESENTATION VERSION
POLICY VERSION
EVALUATION VERSION
```

A change to one does not implicitly rewrite the others.

## 4. Dependency Graph

```text
RAW EVIDENCE
   ↓
MEMORY
   ↓
DERIVED KNOWLEDGE
   ↓
MODEL TRAINING / ADAPTATION
   ↓
MODEL VERSION
   ↓
DERIVED REPRESENTATIONS
   ↓
RETRIEVAL / REASONING
```

Every consequential dependency should be traceable.

## 5. Model Identity

Each deployed model must have a stable identity and version:

```text
MODEL_ID
MODEL_VERSION
BUILD
WEIGHTS / ARTIFACT DIGEST
CONFIGURATION
TRAINING DATA REFERENCE
CODE VERSION
DEPENDENCIES
```

## 6. Memory Identity

Memory entities retain identity independent of model version.

```text
MEMORY_ID
 ≠
MODEL_ID
```

A model replacement must not create a new memory merely because it interprets the memory differently.

## 7. Representation Identity

Embeddings, summaries, captions, classifications, indexes, and other model-derived representations require their own provenance:

```text
SOURCE MEMORY
 ↓
MODEL M1
 ↓
REPRESENTATION R1
```

If M1 becomes M2, R1 does not automatically become an M2 representation.

## 8. Derived vs Authoritative State

Novi must distinguish:

```text
AUTHORITATIVE SOURCE
DERIVED MEMORY
MODEL-DERIVED REPRESENTATION
INFERENCE
PREDICTION
```

Model output cannot silently become authoritative merely because a new model produced it.

## 9. Model Replacement

Replacing a model should follow:

```text
MODEL M1
 ↓
CANDIDATE M2
 ↓
OFFLINE EVALUATION
 ↓
MEMORY COMPATIBILITY CHECK
 ↓
SHADOW / CANARY
 ↓
PROMOTION
```

## 10. Memory Compatibility Gate

Before model promotion, Novi should test:

- retrieval behavior;
- entity resolution;
- temporal interpretation;
- spatial interpretation;
- causal reasoning;
- skill evidence;
- privacy behavior;
- deletion behavior;
- provenance preservation;
- downstream task performance.

## 11. Model-Induced Semantic Drift

A new model may reinterpret the same memory:

```text
MEMORY X
 ↓
MODEL M1 → interpretation A
MODEL M2 → interpretation B
```

This is **model semantic drift**, not necessarily memory change.

The system should preserve both interpretations where historically relevant.

## 12. Reinterpretation Must Be Explicit

A new interpretation should be represented as:

```text
MEMORY
 ↓
NEW INFERENCE
 ↓
MODEL VERSION M2
```

rather than overwriting the original memory.

## 13. Continual Learning

Continual learning aims to acquire new information over time while retaining prior capability. Catastrophic forgetting is a major failure mode. citeturn0academia0turn0academia2

Novi therefore treats continual learning as a governed lifecycle rather than unrestricted parameter mutation.

## 14. Stability / Plasticity

Every learning update balances:

```text
PLASTICITY
→ learn new information

STABILITY
→ preserve validated prior capability
```

Neither extreme is acceptable.

## 15. Learning From Memory

Memory used for model adaptation must retain:

- selection criteria;
- sampling policy;
- authorization;
- privacy classification;
- provenance;
- schema version;
- model target;
- training run;
- exclusions.

## 16. Memory Is Not Automatically Training Data

A memory may be retained for recall while being prohibited from training.

```text
MEMORY
 ├── recall: ALLOWED
 └── training: DENIED
```

Training eligibility is an independent policy decision.

## 17. Training Data Lineage

For every model update, Novi should be able to determine, where policy permits:

```text
MODEL UPDATE
 ↓
TRAINING RUN
 ↓
DATA SELECTION
 ↓
MEMORIES / SOURCES
```

This extends the provenance requirements of documents 74 and 92.

## 18. Privacy-Preserving Learning Boundary

Personal or sensitive memory must not enter training merely because it is accessible to retrieval.

```text
ACCESS
 ≠
TRAINING PERMISSION
```

## 19. Forgetting Has Multiple Meanings

Novi distinguishes:

```text
MEMORY DELETION
MODEL UNLEARNING
MODEL PERFORMANCE FORGETTING
RETRIEVAL FORGETTING
REPRESENTATION INVALIDATION
```

These are different operations.

## 20. Deletion vs Model Unlearning

Deleting a memory from the memory store does not prove that a model has forgotten information learned from it.

If policy requires model-level removal, a separate unlearning or retraining process is required.

## 21. Model Forgetting vs User Forgetting

A model can forget a capability because of continual learning while the memory system still retains the relevant information.

Conversely, memory can be deleted while a model still encodes traces of it.

The two lifecycles must be independently evaluated.

## 22. Representation Invalidation

If an embedding model changes:

```text
EMBEDDING MODEL M1
 ↓
INDEX R1
```

then a new model M2 may require:

```text
RE-EMBED
 ↓
INDEX R2
 ↓
VALIDATE RETRIEVAL
```

Old representations must not be silently mixed with incompatible representations.

## 23. Mixed-Version Operation

During migration, Novi may temporarily operate with:

```text
MODEL M1 + REPRESENTATION R1
MODEL M2 + REPRESENTATION R2
```

Compatibility rules must explicitly define which combinations are valid.

## 24. Shadow Evaluation

A candidate model may process live or replayed inputs without controlling decisions:

```text
PRODUCTION MODEL
        ↓
REAL DECISION

CANDIDATE MODEL
        ↓
SHADOW RESULT
```

Differences are measured before promotion.

## 25. Canary Deployment

Candidate models may receive limited traffic under strict rollback criteria.

Canary scope should be risk-aware rather than purely percentage-based.

## 26. Rollback

Rollback must restore a known-good model and compatible derived representations.

```text
M2
 ↓
FAILURE
 ↓
M1
```

Rollback must not silently discard memories created while M2 was active.

## 27. Post-Rollback Memory Handling

Memories created during a failed model version should be marked with the producing model/version and evaluated for validity.

```text
MEMORY Mx
producer = MODEL M2
status = REQUIRES_REVIEW
```

where consequences warrant it.

## 28. Model-Generated Memory

If a model creates a summary, fact, relationship, causal claim, or other derived memory, the system must record:

- producing model;
- prompt/context or generation activity where policy permits;
- source evidence;
- transformation;
- confidence/status;
- timestamp;
- schema version.

## 29. Model Output Is Not Ground Truth

```text
MODEL OUTPUT
 ≠
OBSERVED FACT
```

Model-generated memories require evidence and appropriate admission policy.

## 30. Self-Generated Training Loops

Novi must prevent uncontrolled feedback loops:

```text
MODEL
 ↓
GENERATED MEMORY
 ↓
TRAINING DATA
 ↓
MODEL
```

Without source separation and quality controls, errors can amplify across generations.

## 31. Synthetic Data Provenance

Synthetic memories or examples must be marked as synthetic and retain generator/model provenance.

They must not be indistinguishable from real observations.

## 32. Model Bias Feedback

If a model systematically misinterprets a population, entity, modality, or environment, writing those interpretations back into memory can reinforce the error.

Therefore model-generated knowledge should be monitored for systematic feedback loops.

## 33. Knowledge Promotion

A model-derived claim should pass through explicit states:

```text
MODEL OUTPUT
 ↓
CANDIDATE CLAIM
 ↓
EVIDENCE CHECK
 ↓
VALIDATION
 ↓
PROMOTED KNOWLEDGE
```

## 34. Knowledge Demotion

Contradictory evidence or model regression may require:

```text
PROMOTED
 ↓
QUESTIONED
 ↓
DEMOTED
 ↓
RETIRED
```

## 35. Model Evaluation Against Historical Memory

Candidate models should be evaluated on temporally separated historical datasets where possible, including old and new distributions.

This tests whether improvements on recent data came at the cost of older capabilities.

## 36. Temporal Leakage

Evaluation must prevent future information from leaking into historical tests.

A model should not appear to know a fact at T1 because it was trained on evidence that only became available at T2.

## 37. Counterfactual Model Evaluation

For causal or planning systems, evaluation should include appropriate counterfactual and intervention tests where reliable ground truth or simulation exists.

## 38. Identity Regression

Every model update should be tested for regressions in identity resolution from document 97.

False merges and false splits can contaminate the entire memory graph.

## 39. Temporal Regression

Test whether model updates change:

- interval interpretation;
- temporal ordering;
- current-vs-historical state;
- validity windows;
- temporal uncertainty.

## 40. Spatial Regression

Test whether model updates change:

- location resolution;
- spatial relations;
- map interpretation;
- trajectory understanding;
- spatial uncertainty.

## 41. Causal Regression

Test whether model updates:

- invent causal relationships;
- lose validated causal relationships;
- change regime assumptions;
- confuse prediction with causation;
- degrade counterfactual reasoning.

## 42. Cross-Modal Regression

Test modality-specific and cross-modal behavior after model changes.

A new model may improve language while degrading vision, audio, or sensor grounding.

## 43. Skill Regression

Model updates must be evaluated against document 102's competence claims.

A model replacement can invalidate skill evidence even if the underlying skill memory remains unchanged.

## 44. Evaluation Versioning

Every evaluation should record:

```text
MODEL VERSION
MEMORY VERSION / SNAPSHOT
DATASET VERSION
EVALUATION CODE VERSION
POLICY VERSION
ENVIRONMENT
RESULTS
```

## 45. Model / Memory Compatibility Matrix

Novi should maintain an explicit compatibility matrix:

```text
             MEMORY V1   MEMORY V2
MODEL M1       ✓           ?
MODEL M2       ?           ✓
MODEL M3       ✗           ?
```

Unknown combinations must not silently enter production.

## 46. Schema Migration Integration

Document 103 governs memory schema migration.

Model compatibility must be checked across schema transitions:

```text
M1 + Schema S1
 ↓
M2 + Schema S2
```

The combination requires validation of both model and memory migration semantics.

## 47. Memory Migration Integration

Migration should preserve model-independent memory semantics wherever possible.

If it cannot, the migration must declare the semantic loss and affected model dependencies.

## 48. Model Training Snapshot

A training run should identify the memory snapshot or data version used.

```text
TRAIN RUN T42
DATA SNAPSHOT D17
MODEL M3
```

This enables reproducibility and forensic analysis.

## 49. Reproducibility

Where practical, retain:

- code commit;
- model artifact digest;
- configuration;
- dataset/memory snapshot;
- random seeds where relevant;
- evaluation suite;
- environment/dependency versions.

## 50. Model Lineage

Model lineage should form:

```text
M1
 ↓ fine-tune
M2
 ↓ continual update
M3
 ↓ adapter
M4
```

Lineage is distinct from simple version numbering.

## 51. Adapter / Fine-Tune Semantics

An adapter or fine-tuned model may have different memory compatibility from its base model.

Do not infer compatibility solely from shared ancestry.

## 52. Model Retirement

Retiring a model requires identifying:

- memories produced by it;
- representations produced by it;
- policies referencing it;
- evaluations depending on it;
- active skills depending on it.

## 53. Memory Outliving Models

Memory should normally outlive individual model versions where its retention policy permits.

```text
MODEL M1 → retired
MEMORY   → retained
```

This is a fundamental reason for separating memory from parameters.

## 54. Model-Specific Interpretations

When interpretations are model-specific, store them as derived assertions:

```text
CLAIM C
 ├── derived_by M1
 └── derived_by M2
```

This allows disagreement without corrupting the underlying evidence.

## 55. Model Disagreement

Different models may produce:

```text
M1 → A
M2 → B
```

The arbitration layer should preserve the conflict rather than silently selecting the latest model output.

## 56. Model Promotion Criteria

Promotion should consider:

- aggregate performance;
- regression risk;
- calibration;
- safety;
- privacy;
- security;
- memory compatibility;
- latency/resource cost;
- operational stability.

## 57. No Single Benchmark Gate

A model should not be promoted solely because it improves one benchmark.

Evaluation must reflect Novi's actual memory and downstream workloads.

## 58. Longitudinal Monitoring

After deployment, monitor:

```text
PERFORMANCE
DRIFT
CALIBRATION
RETRIEVAL
ERROR TYPES
MEMORY QUALITY
SKILL RELIABILITY
SAFETY INCIDENTS
```

## 59. Drift Detection

Detect potential changes in:

- input distribution;
- entity population;
- modality quality;
- environment;
- task mix;
- memory distribution.

Task-free continual-learning research explicitly considers distribution shift without relying on predefined task boundaries. citeturn0search4turn0search6

## 60. Model Aging

A model may become less appropriate even without explicit updates because the world changes.

```text
MODEL M1
 ↓
WORLD CHANGES
 ↓
PERFORMANCE DRIFT
```

Model age should therefore be an operational signal, not merely a timestamp.

## 61. Memory Aging

Memory can also become stale independently of the model.

```text
MEMORY STALENESS
 ≠
MODEL STALENESS
```

Both must be assessed separately.

## 62. Model-Induced Memory Re-ranking

A new retrieval model can change what memories are surfaced without changing the memory store.

Such changes must be measurable because retrieval behavior is part of system behavior.

## 63. Retrieval Regression

Candidate models should be evaluated for:

- recall;
- ranking quality;
- freshness;
- provenance visibility;
- conflict preservation;
- authorization filtering.

## 64. Embedding Migration

Embedding model changes require an explicit migration plan under document 103.

Mixed embedding spaces must not be assumed comparable unless validated.

## 65. Model / Memory Transaction Boundary

A consequential operation should record which model version and memory snapshot influenced it.

```text
DECISION
 ├── MODEL M7
 ├── MEMORY SNAPSHOT D22
 └── POLICY P4
```

## 66. Action Traceability

For consequential actions:

```text
ACTION
 ↓
DECISION
 ↓
MODEL
 ↓
MEMORY
 ↓
EVIDENCE
```

This integrates 95's action trace and 92's provenance requirements.

## 67. Model-Dependent Deletion

When memory is deleted, determine whether model artifacts or derived representations depend on it.

```text
MEMORY ERASED
 ↓
REPRESENTATION INVALIDATION
 ↓
TRAINING / UNLEARNING ASSESSMENT
```

## 68. Model-Dependent Privacy

A model can expose information that is no longer directly retrievable from memory.

Privacy review must therefore include model behavior, not only storage access controls.

## 69. Security of Model Updates

Model updates are a privileged change surface.

Threats include:

- poisoned training data;
- malicious model artifacts;
- backdoors;
- unauthorized adapters;
- provenance forgery;
- evaluation manipulation;
- rollback abuse.

## 70. Training Data Poisoning

Memory admission controls and model-training controls must remain separate but coordinated.

A memory that passed admission is not automatically safe for training.

## 71. Model Artifact Integrity

Production models should have integrity identifiers and controlled promotion paths.

Unauthorized artifact replacement must be detectable.

## 72. Evaluation Integrity

Evaluation data and tooling must be protected against contamination by the candidate model or training pipeline.

## 73. Self-Improvement Boundary

Novi must distinguish:

```text
SELF-MONITORING
SELF-EVALUATION
SELF-RECOMMENDED UPDATE
SELF-AUTHORIZED UPDATE
```

A system may recommend its own update without having authority to deploy it.

## 74. Human / Governance Gate

High-impact model changes should require appropriate human or policy approval.

This anticipates documents 105 and 106.

## 75. Safe Learning Sandbox

Experimental model updates should initially operate in:

```text
SANDBOX
 ↓
OFFLINE TEST
 ↓
SHADOW
 ↓
CANARY
 ↓
PRODUCTION
```

## 76. Rollback Safety

Rollback must be tested before production promotion where feasible.

A rollback plan that cannot be executed is not a real rollback capability.

## 77. Knowledge Reconciliation After Model Change

After promotion, Novi should identify materially changed interpretations and decide whether they should:

- remain model-specific;
- become a revised knowledge claim;
- trigger human review;
- be rejected.

## 78. No Automatic Mass Reconsolidation

A new model must not silently rewrite the entire memory graph merely because it can generate new interpretations.

Reconsolidation requires explicit scope, evidence, resource and policy controls.

## 79. Selective Reprocessing

Prefer targeted reprocessing where possible:

```text
AFFECTED MEMORIES
 ↓
REPROCESS
 ↓
VALIDATE
```

rather than indiscriminate full-corpus rewriting.

## 80. Cost Governance

Co-evolution can be computationally expensive.

Track:

- retraining cost;
- re-embedding cost;
- re-indexing cost;
- evaluation cost;
- storage growth;
- inference cost.

## 81. Resource-Aware Evolution

Model and memory updates should be scheduled according to consequence, urgency and resource constraints rather than maximizing update frequency.

## 82. Evolution Events

Important lifecycle events should be represented as durable events:

```text
MODEL_TRAINED
MODEL_EVALUATED
MODEL_PROMOTED
MODEL_ROLLED_BACK
MEMORY_MIGRATED
REPRESENTATION_REBUILT
KNOWLEDGE_RECONCILED
MODEL_RETIRED
```

## 83. Evolution Ledger

Novi should maintain an evolution ledger linking:

```text
MODEL
MEMORY
SCHEMA
POLICY
EVALUATION
DEPLOYMENT
```

This becomes the system's longitudinal audit trail.

## 84. Cross-Version Querying

The system should support queries such as:

> What did Novi believe under model M2?

and:

> What changed after M3 was deployed?

This requires historical model/memory associations.

## 85. Historical Reproducibility

Where retention and privacy permit, Novi should be able to reconstruct the relevant model, memory snapshot and policy context behind a historical decision.

## 86. Decision Replay

Replay should distinguish:

```text
EXACT REPLAY
→ same artifacts/environment where feasible

APPROXIMATE REPLAY
→ reconstructed state with known differences
```

Approximate replay must not be presented as exact historical reproduction.

## 87. Regression Attribution

When behavior changes, Novi should attempt to attribute it to:

```text
MODEL CHANGE
MEMORY CHANGE
SCHEMA CHANGE
POLICY CHANGE
ENVIRONMENT CHANGE
DATA DRIFT
```

Multiple causes may coexist.

## 88. Causal Analysis of Evolution

Evolution events themselves can form a causal lineage:

```text
MODEL UPDATE
 ↓
RETRIEVAL CHANGE
 ↓
DECISION CHANGE
 ↓
OUTCOME CHANGE
```

This integrates with document 100.

## 89. Skill Impact Analysis

A model update should identify competence claims potentially affected by the update and require revalidation where material.

## 90. Cross-Modal Impact Analysis

A model update affecting one modality can change multimodal fusion behavior.

Regression testing must therefore include modality interactions, not only isolated benchmarks.

## 91. Identity Impact Analysis

Model updates that change entity resolution can affect:

```text
MEMORY OWNERSHIP
RELATIONSHIPS
PRIVACY
SKILLS
CAUSAL CLAIMS
```

Therefore identity regression is a high-priority gate.

## 92. Architecture Invariants

1. Model and memory are distinct assets.
2. They must be independently versioned.
3. Model outputs are not automatically authoritative memory.
4. Model-derived representations retain model provenance.
5. A model update must not silently rewrite memory semantics.
6. Memory deletion is not equivalent to model unlearning.
7. Model forgetting is not memory deletion.
8. Training eligibility is distinct from retrieval access.
9. Model-generated memory requires evidence and provenance.
10. Self-generated training loops require explicit controls.
11. New models must be evaluated against historical memory.
12. Temporal leakage is prohibited.
13. Candidate models require compatibility evaluation before promotion.
14. Rollback must account for memories and representations produced by the rolled-back model.
15. Model disagreement must remain observable.
16. Embedding migrations require explicit compatibility handling.
17. Model changes can invalidate skill, identity, temporal, spatial and causal behavior.
18. Privacy and deletion evaluation must include model-derived state.
19. Model updates are privileged security-sensitive operations.
20. Self-recommended changes are not self-authorized changes.
21. High-impact model promotion requires appropriate governance.
22. Mass reconsolidation is never automatic.
23. Evolution events must be traceable.
24. Historical decisions should be reproducible or explicitly marked as approximate replays.
25. Model, memory, schema and policy changes must be jointly considered when behavior changes.

## 93. Integration With Document 95

104 extends the reference pipeline:

```text
EVIDENCE
 ↓
MEMORY
 ↓
KNOWLEDGE
 ↓
MODEL
 ↓
REASONING
 ↓
DECISION
 ↓
ACTION
 ↓
OUTCOME
 ↓
EVALUATION
 ↓
CONTROLLED EVOLUTION
```

Evolution returns to the system only through governed promotion.

## 94. Integration With 97–103

```text
97 Identity
→ model updates can change entity resolution

98 Temporal
→ models must preserve temporal semantics and avoid leakage

99 Spatial
→ spatial representations and models require compatibility

100 Causal
→ causal models require intervention/regime regression testing

101 Cross-Modal
→ multimodal models require modality and fusion regression testing

102 Skill
→ competence claims may require revalidation

103 Migration
→ model compatibility is part of schema/representation evolution
```

## 95. Research Cross-Validation

Continual-learning research consistently identifies catastrophic forgetting as a central problem when models learn sequentially from changing data, and frames the stability–plasticity trade-off as a core design issue. citeturn0academia0turn0academia2

Research on pre-trained models further shows that continual learning introduces distinct challenges and design choices when adapting large pretrained representations to evolving data. citeturn0academia1

Task-free continual-learning research highlights the realistic case where data distributions change without explicit task boundaries and demonstrates the importance of distribution-shift detection and memory selection. citeturn0search4turn0search6

These findings support Novi's separation of model versioning, memory versioning, drift detection, compatibility testing, replay/evaluation, and controlled evolution.

They do not establish one universally correct continual-learning algorithm. Novi therefore specifies lifecycle and governance contracts rather than mandating a single learning method.

## 96. Final Principle

> **Novi must evolve without losing its history. Models may learn, memories may change, schemas may migrate, and interpretations may improve, but every consequential transition must remain traceable, evaluable, reversible where feasible, privacy-aware, and semantically explicit.**

The purpose of co-evolution is not to make the system change constantly. It is to make change **safe, attributable, testable and understandable**.