# 100 — Memory Knowledge Causal World Modeling and Causal Memory Architecture

## Status

**NORMATIVE ARCHITECTURE — CRITICAL / V1**

## Purpose

Define how Novi represents, evaluates, learns, retrieves and uses causal knowledge about entities, events, states, actions and outcomes.

This document resolves the fourth P0 architectural gap identified by document 96 only after the prerequisite identity, temporal and spatial layers established by documents 97–99.

It integrates with document 95's reference architecture and preserves the distinction between observation, evidence, temporal order, correlation, causal hypothesis, causal knowledge, prediction, intervention and action.

## 1. Core Principle

> **Temporal order, spatial proximity, correlation and repeated co-occurrence are evidence for causal investigation—not proof of causation.**

Novi must represent causal claims as explicit, evidence-bearing hypotheses or models whose assumptions, interventions, provenance, uncertainty and scope remain inspectable.

Causal representation learning is concerned with discovering meaningful causal variables from lower-level observations and connecting causal structure to generalization and transfer. [1] fileciteturn173file0

## 2. Why Causality Is a Separate Layer

The preceding architecture establishes:

```text
97 IDENTITY
 ↓
98 TIME
 ↓
99 SPACE
```

These provide necessary context for causal reasoning but do not establish causality.

```text
A happened before B
       ≠
A caused B

A is near B
       ≠
A caused B

A correlates with B
       ≠
A caused B
```

## 3. Causal Model vs World Model

A world model represents how a relevant environment evolves.

A causal world model additionally represents dependencies that support reasoning about interventions and counterfactual changes.

```text
STATE
 ↓
DYNAMICS
 ↓
CAUSAL STRUCTURE
 ↓
PREDICTION
 ↓
INTERVENTION / COUNTERFACTUAL
```

## 4. Causal Variables

Causal reasoning requires variables with defined semantics.

Examples:

```text
DOOR_OPEN
TEMPERATURE
BATTERY_LEVEL
LOCATION
MOTION
ACTION_TAKEN
OBSTACLE_PRESENT
```

A raw observation should not automatically become a causal variable.

## 5. Latent Causal Variables

Many relevant causal variables are not directly observed.

```text
RAW OBSERVATIONS
      ↓
REPRESENTATION
      ↓
LATENT VARIABLE
      ↓
CAUSAL MODEL
```

This is a major research challenge in causal representation learning. [1] fileciteturn173file0

## 6. Causal Claims

Novi should represent causal claims explicitly:

```text
CAUSE
  ↓
EFFECT
```

with metadata including:

- evidence;
- context;
- time scope;
- spatial scope;
- population/entity scope;
- assumptions;
- confidence;
- provenance;
- model version;
- validation status.

## 7. Causal Relation Types

The model should distinguish at least:

```text
DIRECT CAUSE
INDIRECT CAUSE
CONTRIBUTING CAUSE
NECESSARY CONDITION
SUFFICIENT CONDITION
ENABLING CONDITION
PREVENTING CONDITION
MODERATOR
MEDIATOR
CONFOUNDING VARIABLE
COMMON CAUSE
COMMON EFFECT
```

These must not be collapsed into a generic `causes` edge when doing so would lose decision-relevant meaning.

## 8. Causal Graph

A causal graph may be represented as:

```text
A ──→ B ──→ C
│           ↑
└───────────┘
```

Graph semantics must distinguish causal edges from descriptive relationships.

## 9. Association vs Causation

Novi must preserve the distinction:

```text
ASSOCIATION
PREDICTION
CAUSATION
```

A predictive relationship can be useful without being causal.

## 10. Confounding

A common cause can produce an apparent relationship:

```text
     C
    ↙ ↘
   A   B
```

Novi should search for plausible confounders before upgrading an association to a causal claim.

## 11. Mediation

A causal pathway can include intermediate variables:

```text
A → M → B
```

The architecture should preserve mediation rather than reducing every relationship to A → B.

## 12. Collider Bias

A common effect can create misleading associations after conditioning:

```text
A → C ← B
```

Causal inference components should therefore distinguish observational relationships from interventionally justified relationships.

## 13. Selection Effects

Observations may arise from non-random selection.

The system must retain relevant sampling/selection context where known.

## 14. Causal Scope

Causal claims are scoped.

```text
CAUSE AFFECTS B
```

is incomplete without considering:

```text
WHO?
WHAT?
WHEN?
WHERE?
UNDER WHAT CONDITIONS?
```

## 15. Context-Specific Causality

A relationship can change under different states:

```text
WORLD STATE S1
A → B

WORLD STATE S2
A ↛ B
```

Recent causal-world-model research explicitly studies changing causal mechanisms across latent world states rather than assuming one invariant causal structure. [2] fileciteturn174file0

## 16. Causal Regime

Every causal model should identify its applicable regime where possible:

```text
ENVIRONMENT
POLICY
HARDWARE
POPULATION
TIME PERIOD
```

A model should not be silently generalized outside its validated regime.

## 17. Structural Causal Model Boundary

Where appropriate, Novi may represent:

```text
EXOGENOUS VARIABLES
      ↓
STRUCTURAL EQUATIONS
      ↓
ENDOGENOUS VARIABLES
```

The architecture does not mandate one mathematical formalism, but production causal components must make assumptions explicit.

## 18. Intervention

Causal reasoning must distinguish observation from intervention:

```text
OBSERVE(A)
```

versus:

```text
DO(A = value)
```

An intervention changes the data-generating process or state rather than merely observing it.

## 19. Intervention Evidence

Interventions generally provide stronger causal evidence than passive correlation when properly designed, but the system must retain the intervention context and limitations.

## 20. Agent Actions as Interventions

Novi's own actions can create intervention evidence:

```text
STATE S
 ↓
ACTION A
 ↓
OUTCOME O
```

However, action success alone does not prove that A was the sole cause of O.

## 21. Action Confounding

An action can coincide with environmental changes:

```text
AGENT ACTION
      +
EXTERNAL EVENT
      ↓
OUTCOME
```

Causal attribution must consider alternative explanations.

## 22. Controlled Experiments

Where safe and appropriate, Novi may compare outcomes under controlled interventions.

```text
CONTROL
vs
INTERVENTION
```

Experiments require explicit authorization and safety constraints.

## 23. No Unsafe Exploration

Causal uncertainty must never justify harmful experimentation.

```text
CAUSAL UNCERTAINTY
 ↓
SAFE OBSERVATION / SIMULATION / PASSIVE EVIDENCE
```

rather than dangerous intervention.

## 24. Counterfactuals

Counterfactual reasoning asks:

```text
"What would have happened if A had not occurred?"
```

Counterfactual conclusions must be explicitly marked as model-derived rather than observed history.

## 25. Counterfactual State

```text
OBSERVED WORLD
      │
      ├── factual trajectory
      │
      └── counterfactual trajectory
```

Counterfactual branches must never overwrite factual memory.

## 26. Prediction vs Counterfactual

```text
PREDICTION
→ what is expected under the model

COUNTERFACTUAL
→ what is expected under a specified alternative intervention/history
```

They are distinct inference tasks.

## 27. Causal Uncertainty

Novi must distinguish:

```text
KNOWN CAUSAL RELATION
SUPPORTED CAUSAL HYPOTHESIS
PLAUSIBLE CAUSAL HYPOTHESIS
UNRESOLVED
CONTRADICTED
UNKNOWN
```

## 28. Confidence Calibration

A causal confidence score should only be interpreted probabilistically when appropriately calibrated.

Otherwise use qualitative status and explicit assumptions.

## 29. Causal Evidence Hierarchy

Evidence should be classified by design and quality rather than using a universal simplistic ranking.

Possible evidence types include:

```text
DIRECT INTERVENTION
CONTROLLED EXPERIMENT
NATURAL EXPERIMENT
QUASI-EXPERIMENT
LONGITUDINAL OBSERVATION
CROSS-SECTIONAL OBSERVATION
MECHANISTIC EVIDENCE
SIMULATION
MODEL-BASED INFERENCE
ANALOGY
```

Each has domain-specific limitations.

## 30. Mechanistic Evidence

A causal model should prefer mechanistic explanations where they can be independently validated.

```text
OBSERVATION
 ↓
MECHANISM
 ↓
PREDICTION
 ↓
TEST
```

## 31. Causal Discovery

Causal discovery attempts to infer causal structure from data under assumptions.

Novi must record the assumptions required by the discovery method rather than treating discovered edges as assumption-free facts.

## 32. Identifiability

A causal effect may not be identifiable from available observations.

In such cases:

```text
NOT IDENTIFIABLE
```

is a valid output.

Novi must not fabricate a unique causal explanation when multiple models fit the evidence.

## 33. Model Equivalence

Different causal structures can be observationally indistinguishable under some conditions.

The architecture should preserve equivalence sets or unresolved alternatives when appropriate.

## 34. Multiple Causal Hypotheses

Novi may retain:

```text
H1: A → B
H2: C → B
H3: A ← C → B
```

until evidence discriminates between them.

## 35. Causal Arbitration

Competing causal hypotheses should be evaluated using:

- evidence quality;
- intervention results;
- temporal consistency;
- spatial consistency;
- mechanistic plausibility;
- model fit;
- independence;
- regime validity;
- counterfactual performance.

This integrates the evidence arbitration model from document 91.

## 36. Causal Provenance

Every causal claim should be traceable:

```text
CAUSAL CLAIM
 ↓
MODEL / INFERENCE ACTIVITY
 ↓
EVIDENCE
 ↓
OBSERVATIONS / INTERVENTIONS
```

This integrates document 92.

## 37. Causal Claim Revision

New evidence can change a causal model:

```text
MODEL V1
 ↓
NEW EVIDENCE
 ↓
MODEL V2
```

The old model must remain historically identifiable where retention permits.

## 38. Causal Memory

Causal memories should store:

```text
CAUSE
EFFECT
CONDITIONS
MECHANISM
EVIDENCE
SCOPE
UNCERTAINTY
PROVENANCE
VALIDITY
```

They should not be stored as unqualified natural-language rules alone.

## 39. Causal Memory vs Procedural Memory

```text
CAUSAL MEMORY
→ why an outcome occurs

PROCEDURAL MEMORY
→ how to perform an operation
```

A procedure may depend on causal knowledge without being identical to it.

## 40. Causal Memory vs Semantic Memory

Semantic memory can store:

```text
"Opening the valve increases flow."
```

Causal memory should additionally preserve the scope, mechanism/evidence and conditions under which the relationship is believed to hold.

## 41. Causal Memory Retrieval

Retrieval should consider:

- causal relevance;
- current regime;
- freshness;
- evidence strength;
- intervention support;
- contradictions;
- provenance;
- consequence.

## 42. Causal Context Assembly

When reasoning about an action, Novi should retrieve not only the target causal edge but relevant:

```text
CAUSES
EFFECTS
CONFOUNDERS
MEDIATORS
CONDITIONS
FAILURE MODES
```

## 43. Planning with Causal Models

A causal model can support planning:

```text
CURRENT STATE
 ↓
CANDIDATE ACTION
 ↓
CAUSAL MODEL
 ↓
PREDICTED OUTCOME
 ↓
RISK / UTILITY
 ↓
PLAN
```

Causally aware planning has been studied as a bridge between causal representation learning and language-agent planning, with reported advantages at longer planning horizons. [3] fileciteturn175file0

## 44. Causal Planning Is Not Authorization

```text
CAUSAL PREDICTION
 ≠
PERMISSION TO ACT
```

Action still requires current authorization and safety validation.

## 45. Model-Based Simulation

Novi may query a causal world model as a simulator:

```text
STATE
 ↓
MODEL
 ↓
SIMULATED INTERVENTION
 ↓
PREDICTED TRAJECTORY
```

Simulation results remain model-derived evidence.

## 46. Simulation-to-Reality Gap

A causal model validated in simulation may fail in the real environment.

Novi must retain environment provenance:

```text
SIMULATION
≠
REAL WORLD
```

## 47. Distribution Shift

Causal models should be monitored when the environment changes.

Robust-agent research links generalization under broad distribution shifts to learning an approximate causal model of the underlying data-generating process. [2] fileciteturn174file0

## 48. Causal Drift

Detect potential changes in:

- causal effect magnitude;
- mechanism;
- intervention response;
- environmental regime;
- policy;
- hardware;
- population.

## 49. Meta-Causal Structure

Where causal rules change by latent context:

```text
META STATE S1
 → GRAPH G1

META STATE S2
 → GRAPH G2
```

Novi may represent conditional causal models rather than forcing one global graph.

## 50. Causal Variables and Identity

Causal variables should reference stable entity IDs from document 97.

```text
DEVICE_X.BATTERY_LEVEL
```

is different from:

```text
DEVICE_Y.BATTERY_LEVEL
```

even if their observations are numerically similar.

## 51. Causal Variables and Time

Causal claims require temporal validity from document 98.

```text
A(t) → B(t+Δ)
```

The relevant lag must be represented when material.

## 52. Causal Variables and Space

Spatial context from document 99 can condition causal relationships:

```text
A → B | LOCATION = L
```

A relationship observed in one environment should not automatically generalize to another.

## 53. Causal Graph Versioning

Every persisted causal model should have:

```text
MODEL_ID
VERSION
VALIDITY_INTERVAL
TRAINING / EVIDENCE SET
ASSUMPTIONS
ENVIRONMENT
```

## 54. Causal Model Lineage

Model updates must preserve:

```text
MODEL V1
 ↓
NEW DATA / INTERVENTION
 ↓
MODEL V2
```

so Novi can explain why a causal belief changed.

## 55. Causal Deletion

If source evidence is erased or invalidated, dependent causal claims must be evaluated.

```text
EVIDENCE DELETED
 ↓
CAUSAL CLAIM DEPENDENCIES
 ↓
REVALIDATE / DEMOTE / REMOVE
```

This integrates documents 87 and 92.

## 56. Causal Security

Threats include:

- poisoned causal evidence;
- fabricated intervention outcomes;
- manipulated simulator state;
- causal provenance forgery;
- adversarial observations;
- malicious model updates;
- reward manipulation;
- unsafe exploratory actions.

## 57. Causal Poisoning

A malicious record such as:

```text
"ACTION X always causes SAFE OUTCOME Y"
```

must not automatically become a causal rule.

It requires provenance, evidence and validation.

## 58. Causal Model Integrity

High-impact causal models should have integrity protection and versioned change records.

Unauthorized model mutation must be detectable.

## 59. Causal Evaluation

Evaluate causal systems using appropriate measures including:

- intervention prediction accuracy;
- effect estimation error;
- structural recovery where ground truth exists;
- counterfactual accuracy;
- calibration;
- robustness under distribution shift;
- planning performance;
- downstream harm.

## 60. No Single Causal Score

A model can predict outcomes accurately while representing the wrong causal structure.

Therefore:

```text
PREDICTIVE ACCURACY
 ≠
CAUSAL VALIDITY
```

## 61. Intervention Testing

Where safe and permitted, evaluation should include interventions rather than only passive prediction.

## 62. Counterfactual Testing

Where ground truth or reliable simulators exist, evaluate counterfactual predictions.

## 63. Longitudinal Causal Evaluation

Causal memory should be evaluated across time:

```text
T1
 ↓
T2
 ↓
T3
 ↓
T100
```

Test whether stale causal models continue influencing decisions after the environment changes.

## 64. Causal Abstention

When causal structure is uncertain or non-identifiable:

```text
UNKNOWN / NOT IDENTIFIABLE
```

is preferred over an invented causal explanation.

## 65. Human Oversight

Human review should be available for:

- safety-critical causal claims;
- disputed causal explanations;
- high-impact interventions;
- model changes affecting autonomous action;
- ambiguous causal evidence.

This prepares for document 106.

## 66. Implementation Components

Logical components should include:

```text
Causal Variable Registry
Causal Evidence Store
Causal Graph Store
Causal Inference Engine
Intervention Manager
Counterfactual Engine
World Model
Causal Model Registry
Causal Evaluation Harness
Causal Policy / Safety Gate
```

## 67. Storage Independence

Causal state may use:

- graph stores;
- relational databases;
- event logs;
- probabilistic models;
- simulation environments;
- vector indexes for retrieval.

Storage technology must not erase causal semantics.

## 68. No Forced Mathematical Formalism

Novi should support multiple causal approaches where justified:

```text
STRUCTURAL CAUSAL MODELS
CAUSAL GRAPHS
POTENTIAL OUTCOMES
CAUSAL DISCOVERY
MECHANISTIC MODELS
SIMULATORS
HYBRID NEURAL / SYMBOLIC MODELS
```

Choice depends on domain and evidence.

## 69. Causal Reasoning with LLMs

LLMs may provide linguistic interfaces to causal models, but their pretrained causal knowledge should not automatically override environment-specific causal evidence.

Research explicitly notes that LLM causal knowledge can be incomplete, incorrect or inapplicable to a specific environment, motivating integration with environment-specific causal world models. [3] fileciteturn175file0

## 70. Natural-Language Causal Claims

Natural language should be parsed into structured causal hypotheses when persisted:

```text
"Opening the valve increases flow"
          ↓
CAUSE: valve_open
EFFECT: flow
CONDITION: applicable regime
```

The original statement remains provenance evidence, not unquestioned causal truth.

## 71. Causal Contradiction

Conflicting causal claims should form explicit conflict sets:

```text
H1: A → B
H2: A ↛ B
```

Novi should preserve unresolved disagreement where evidence cannot decide.

## 72. Causal Explanation

When explaining a decision, Novi should distinguish:

```text
OBSERVED FACT
MODEL ASSUMPTION
CAUSAL INFERENCE
PREDICTION
DECISION
```

This prevents a model inference from being presented as an observation.

## 73. Causal Traceability

A consequential causal decision should be traceable:

```text
ACTION
 ↓
DECISION
 ↓
PREDICTION
 ↓
CAUSAL MODEL
 ↓
CAUSAL CLAIMS
 ↓
EVIDENCE
 ↓
OBSERVATIONS / INTERVENTIONS
```

## 74. Causal Memory and Provenance

Causal knowledge must inherit provenance and evidence quality requirements from documents 74, 75, 91 and 92.

## 75. Causal Memory and Security

Causal knowledge inherits the memory security model from document 94.

Persistent causal rules are high-value poisoning targets because they can influence many future decisions.

## 76. Causal Memory and Privacy

Causal models can reveal sensitive relationships even when raw observations are removed.

Therefore derived causal knowledge may remain sensitive and must follow privacy policy.

## 77. Causal Memory and Erasure

Deletion of an observation does not automatically imply that every derivative causal claim can remain unchanged.

Dependency analysis must determine whether the causal claim still has sufficient independent support.

## 78. Causal Model Promotion

A causal hypothesis should progress through states:

```text
OBSERVATION
 ↓
ASSOCIATION
 ↓
CAUSAL HYPOTHESIS
 ↓
SUPPORTED CAUSAL MODEL
 ↓
VALIDATED IN REGIME
```

Promotion requires evidence.

## 79. Causal Model Demotion

Contradictory evidence may cause:

```text
SUPPORTED
 ↓
QUESTIONED
 ↓
DEMOTED
 ↓
RETIRED
```

Historical provenance remains intact.

## 80. Causal Model Reuse

Reuse should check:

```text
SAME ENTITY TYPE?
SAME ENVIRONMENT?
SAME REGIME?
SAME TIME RANGE?
SAME INTERVENTION?
SAME ASSUMPTIONS?
```

Otherwise the model may require revalidation.

## 81. Causal Generalization

Generalization should be treated as a hypothesis requiring evidence, not as an automatic consequence of successful prediction in one environment.

## 82. Causal Transfer

When transferring a model across environments:

```text
SOURCE REGIME
 ↓
TRANSFER HYPOTHESIS
 ↓
VALIDATION
 ↓
TARGET REGIME
```

## 83. Causal World Model and Planning Horizon

Long-horizon planning increases the cost of small causal-model errors because errors compound across predicted state transitions.

Causally aware planning research reports benefits particularly at longer horizons, supporting explicit causal state modeling for extended planning. [3] fileciteturn175file0

## 84. Causal State Transition

A world model should support:

```text
STATE(t)
 +
ACTION(t)
 +
EXTERNAL INPUT(t)
        ↓
STATE(t+1)
```

The model should preserve uncertainty where transitions are not deterministic.

## 85. Stochastic Causality

Many environments contain stochastic outcomes:

```text
A
 ↓
B with probability distribution
```

A probabilistic effect must not be represented as deterministic merely because it occurred repeatedly.

## 86. Causal Uncertainty Propagation

Uncertainty should propagate through multi-step predictions:

```text
STATE UNCERTAINTY
 ↓
MODEL UNCERTAINTY
 ↓
ACTION UNCERTAINTY
 ↓
OUTCOME UNCERTAINTY
```

## 87. Causal Safety Margin

For consequential decisions, planning should account for uncertainty and worst-case or risk-sensitive outcomes where appropriate.

## 88. Causal Model Failure States

Support explicit states:

```text
VALIDATED
PROVISIONAL
STALE
OUT_OF_REGIME
CONFLICTED
UNIDENTIFIABLE
QUARANTINED
RETIRED
```

## 89. Causal Model Quarantine

A causal rule showing signs of poisoning, corruption or unexplained behavior change may be quarantined from autonomous decision-making while remaining available for forensic analysis.

## 90. Causal Model Recovery

Recovery should identify:

- last trusted model version;
- affected decisions;
- affected actions;
- supporting evidence;
- model changes;
- downstream dependencies.

This uses document 92 lineage.

## 91. Causal Evaluation Dataset

Benchmarks should include:

- confounding;
- mediation;
- selection bias;
- temporal shifts;
- spatial shifts;
- intervention data;
- counterfactual queries;
- hidden variables;
- regime changes;
- adversarial causal claims.

## 92. Causal Architecture Invariants

1. Temporal precedence does not prove causation.
2. Spatial proximity does not prove causation.
3. Correlation does not prove causation.
4. Prediction does not prove causal validity.
5. Causal claims must have scope and provenance.
6. Causal uncertainty must remain explicit.
7. Non-identifiability is a valid result.
8. Multiple causal hypotheses may coexist.
9. Observations and interventions are distinct.
10. Counterfactuals must not overwrite factual history.
11. Agent actions are not automatically isolated causal experiments.
12. Causal claims are regime-dependent unless validated otherwise.
13. Causal model versions must be traceable.
14. Causal model updates require evidence.
15. Causal model deletion/invalidity propagates through dependent claims.
16. Causal knowledge can remain sensitive after source deletion.
17. Causal models cannot authorize actions.
18. LLM-generated causal knowledge is not authoritative environment-specific truth.
19. Predictive accuracy is not sufficient evidence of causal validity.
20. Unsafe experimentation is prohibited.
21. Current state overrides stale causal memory for consequential decisions.
22. Causal simulation is not equivalent to real-world observation.
23. Distribution shift can invalidate causal models.
24. Causal explanations must distinguish observation, assumption, inference and prediction.
25. High-impact causal claims require stronger validation.

## 93. Integration With Document 95

100 follows the reference pipeline:

```text
OBSERVATION
 ↓
EVIDENCE
 ↓
IDENTITY / TIME / SPACE
 ↓
CAUSAL HYPOTHESIS
 ↓
ARBITRATION
 ↓
CAUSAL MODEL
 ↓
REASONING / SIMULATION
 ↓
AUTHORIZATION + SAFETY
 ↓
ACTION
 ↓
OUTCOME
 ↓
MODEL EVALUATION / REVISION
```

## 94. Integration With 97–99

```text
97 IDENTITY
→ WHAT entity/state is involved?

98 TEMPORAL
→ WHEN did the relevant state/event occur?

99 SPATIAL
→ WHERE did it occur and under what spatial conditions?

100 CAUSAL
→ WHY / THROUGH WHAT MECHANISM did the state change?
```

The layers are complementary.

## 95. Integration With Document 96

100 resolves the P0 gap:

**Causal World Modeling / Causal Memory.**

It also establishes prerequisites for future:

- cross-modal memory;
- skill verification;
- model/memory co-evolution;
- governance;
- human oversight.

## 96. Research Cross-Validation

The architecture is informed by three complementary research directions:

### Causal representation learning
Schölkopf et al. identify causal representation learning as a central problem for discovering meaningful causal variables from low-level observations and connecting causality to generalization and transfer. [1] fileciteturn173file0

### Robust causal world models
Richens and Everitt provide a theoretical argument connecting robust performance under broad distribution shifts with learning approximate causal models of the data-generating process. [2] fileciteturn174file0

### Language agents + causal world models
Gkountouras et al. study an interface between causal representation learning and language-agent reasoning, treating the causal world model as a simulator and reporting benefits for longer-horizon planning. [3] fileciteturn175file0

These results support the architecture's emphasis on causal variables, environment-specific models, intervention-aware evaluation, distribution-shift monitoring and explicit interfaces between language reasoning and structured causal models.

They do **not** establish that any single causal architecture is universally optimal.

## 97. Final Principle

> **Novi must treat causality as a governed model of how states change, not as a story inferred from temporal order or correlation. Causal knowledge must be scoped, evidence-backed, intervention-aware where possible, uncertainty-bearing, versioned, traceable and continuously tested against changing environments.**

Causal world modeling therefore becomes the layer connecting Novi's identity, temporal and spatial understanding to robust prediction, planning and learning—without allowing causal hypotheses to masquerade as facts or authorize actions by themselves.