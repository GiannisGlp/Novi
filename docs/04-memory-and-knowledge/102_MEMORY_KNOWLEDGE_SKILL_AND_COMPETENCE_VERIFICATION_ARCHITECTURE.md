# 102 — Memory Knowledge Skill and Competence Verification Architecture

## Status

**NORMATIVE ARCHITECTURE — CRITICAL / V1**

## Purpose

Define how Novi represents, acquires, evaluates, validates, deploys, monitors, revises and retires procedural skills and competence claims.

The central problem is not merely learning a procedure. It is determining whether Novi can **reliably perform that procedure, under specified conditions, with acceptable risk, and with evidence strong enough to justify the intended level of autonomy**.

This document resolves the P0 skill/competence gap identified by document 96 and integrates documents 95–101.

## 1. Core Principle

> **Successful execution is evidence of competence in a particular context; it is not automatic proof of general competence.**

Novi must distinguish:

```text
SKILL REPRESENTATION
        ≠
SKILL KNOWLEDGE
        ≠
EXECUTION
        ≠
SUCCESS
        ≠
COMPETENCE
        ≠
GENERALIZATION
        ≠
AUTHORIZATION
```

## 2. Skill vs Competence

A **skill** is a structured capability/procedure that can be represented and potentially executed.

**Competence** is demonstrated ability to perform the skill to defined standards under a defined operating envelope.

```text
SKILL
 ↓
EXECUTION
 ↓
EVIDENCE
 ↓
COMPETENCE ASSESSMENT
```

## 3. Skill Types

Novi should support:

```text
PERCEPTUAL SKILL
COGNITIVE SKILL
MOTOR SKILL
NAVIGATION SKILL
MANIPULATION SKILL
COMMUNICATION SKILL
TOOL-USE SKILL
PLANNING SKILL
SOCIAL SKILL
COMPOSITE / HIERARCHICAL SKILL
```

Skills may combine multiple modalities and subskills.

## 4. Skill Identity

Each durable skill requires a stable identity independent of implementation version.

```text
SKILL_ID
SKILL_VERSION
IMPLEMENTATION_ID
MODEL_VERSION
```

Changing the model or implementation does not silently change the historical identity of a skill.

## 5. Skill Scope

Every competence claim must specify its scope:

```text
TASK
OBJECT / ENTITY TYPE
ENVIRONMENT
HARDWARE
SOFTWARE
TOOLS
USER / POPULATION
TIME / REGIME
SAFETY CONSTRAINTS
```

A skill validated in one scope must not automatically be promoted to another.

## 6. Skill Preconditions

A skill should declare required conditions where known:

- required sensors;
- localization quality;
- object availability;
- environmental constraints;
- permissions;
- prerequisite skills;
- model versions;
- hardware capabilities.

## 7. Skill Dependencies

Skills form a directed dependency graph:

```text
BASIC SKILL A ─┐
               ├→ COMPOSITE SKILL C
BASIC SKILL B ─┘
```

Competence in C must not be assumed merely because A and B were separately validated.

## 8. Skill Representation

A procedural memory should retain, where applicable:

```text
GOAL
PRECONDITIONS
STATE ESTIMATION
ACTION SEQUENCE
DECISION POINTS
FEEDBACK SIGNALS
FAILURE CONDITIONS
RECOVERY STRATEGIES
POSTCONDITIONS
EVIDENCE
SCOPE
VERSION
PROVENANCE
```

## 9. Skill Acquisition Sources

Skills can originate from:

- demonstrations;
- imitation learning;
- reinforcement learning;
- planning;
- human instruction;
- observation;
- simulation;
- transfer from another agent;
- decomposition of validated skills.

Source type must be retained because acquisition method affects evidence quality and expected generalization.

## 10. Demonstration Is Not Competence

A demonstration can provide a training signal or example.

```text
DEMONSTRATION
 ≠
PROVEN COMPETENCE
```

The system must evaluate whether the learned procedure works independently and robustly.

## 11. Training vs Evaluation Separation

Production evaluation data must remain distinct from training data where possible.

```text
TRAINING
   ≠
VALIDATION
   ≠
TEST
```

This is necessary to avoid inflated competence estimates from memorization.

## 12. Execution Evidence

Each meaningful skill execution should produce an execution record containing, where available:

```text
SKILL_ID
SKILL_VERSION
START_STATE
GOAL
ENVIRONMENT
ENTITY CONTEXT
ACTIONS
OBSERVATIONS
INTERVENTIONS
ERRORS
RECOVERY
END_STATE
OUTCOME
SAFETY EVENTS
TIMING
RESOURCE USE
PROVENANCE
```

## 13. Outcome Taxonomy

Do not reduce execution to success/failure alone.

Support:

```text
SUCCESS
PARTIAL SUCCESS
RECOVERED SUCCESS
FAILURE
ABORTED
INTERRUPTED
UNSAFE
UNKNOWN OUTCOME
```

## 14. Success Definition

A skill's success criterion must be explicit before evaluation where feasible.

Examples:

```text
TASK COMPLETION
QUALITY THRESHOLD
TIME LIMIT
ERROR BOUND
SAFETY CONSTRAINT
RESOURCE LIMIT
USER ACCEPTANCE
```

## 15. Success Is Multi-Dimensional

A task can be completed while violating other requirements:

```text
TASK SUCCESS
 +
SAFETY FAILURE
```

Therefore competence evaluation must include safety and quality dimensions, not task completion alone.

## 16. Competence Profile

A competence claim should be represented as:

```text
SKILL
+ SCOPE
+ EVIDENCE
+ PERFORMANCE
+ UNCERTAINTY
+ VALIDITY
+ LIMITATIONS
```

## 17. Competence Levels

A practical qualitative scale is:

```text
UNTESTED
EXPERIMENTAL
PROVISIONAL
VALIDATED
HIGH-CONFIDENCE
RESTRICTED / DEGRADED
RETIRED
```

These labels are policy states, not universal statistical probabilities.

## 18. Calibration

Where numerical confidence is used, it must be calibrated against held-out outcomes.

Do not represent an arbitrary model score as a probability of competence.

## 19. Repeated Trials

Repeated successful executions increase evidence only when they provide meaningful independent information.

```text
10 RUNS
FROM SAME TRAJECTORY
```

are not necessarily equivalent to:

```text
10 DIVERSE CONDITIONS
```

## 20. Independence of Evidence

Execution evidence should consider correlation across:

- identical environments;
- repeated trajectories;
- same demonstration source;
- same simulator;
- same model failure mode;
- shared sensor failure;
- copied plans.

Correlated successes must not create artificial confidence.

## 21. Generalization Dimensions

Competence should be tested across relevant axes:

```text
OBJECT VARIATION
ENVIRONMENT VARIATION
GEOMETRY
LIGHTING
WEATHER
DISTRACTIONS
USER VARIATION
TOOL VARIATION
HARDWARE VARIATION
TEMPORAL VARIATION
SPATIAL VARIATION
```

## 22. Distribution Shift

General-purpose robotics research consistently identifies distribution shift and real-world generalization as major barriers to general-purpose skill deployment. citeturn0academia2turn0academia0

Therefore competence is always relative to a validated operating distribution.

## 23. Operating Envelope

Every deployable skill should have an explicit operating envelope:

```text
SUPPORTED CONDITIONS
       ↓
SAFE / VALIDATED OPERATION
```

Outside that envelope:

```text
OUT-OF-DISTRIBUTION
 ↓
RESTRICT / VERIFY / ABORT
```

## 24. Runtime Monitoring

Competence cannot be established once and forgotten.

During execution Novi should monitor:

- state deviation;
- action deviation;
- predicted failure;
- uncertainty;
- out-of-distribution state;
- safety constraints;
- unexpected environment changes.

Research on model-based runtime monitoring demonstrates the value of detecting anomalies and anticipating failures during deployment rather than relying only on post-hoc failure detection. citeturn0search4

## 25. Preemptive Failure Detection

Where possible:

```text
CURRENT STATE
 ↓
RISK MODEL
 ↓
PREDICTED FAILURE
 ↓
RECOVER / ASK / ABORT
```

A system should not wait for irreversible failure if credible warning signals exist.

## 26. Human Intervention

Human intervention must be recorded as part of execution evidence.

```text
AUTONOMOUS EXECUTION
 ↓
HUMAN INTERVENTION
 ↓
SUCCESS
```

should not be counted as equivalent to:

```text
AUTONOMOUS EXECUTION
 ↓
SUCCESS
```

## 27. Recovery Skills

Recovery itself is a skill and should be evaluated separately.

```text
PRIMARY SKILL
 ↓
FAILURE
 ↓
RECOVERY SKILL
 ↓
SAFE TERMINATION / SUCCESS
```

## 28. Abort Competence

A competent autonomous system must know when not to continue.

Abort decisions should be evaluated as part of competence where safety matters.

```text
UNCERTAINTY / RISK
 ↓
SAFE ABORT
```

can be a successful safety outcome even when the original task is incomplete.

## 29. Skill Verification Modes

Use multiple verification modes where applicable:

```text
SIMULATION
REPLAY
OFFLINE TEST
CONTROLLED LAB TEST
REAL-WORLD TEST
SHADOW MODE
SUPERVISED DEPLOYMENT
AUTONOMOUS DEPLOYMENT
```

Higher-risk skills require stronger evidence before autonomous deployment.

## 30. Simulation Evidence

Simulation is useful for scalable testing but does not establish real-world competence by itself.

```text
SIM SUCCESS
 ≠
REAL-WORLD COMPETENCE
```

Simulation-to-reality differences must be tracked.

## 31. Hardware-Specific Competence

A skill can depend on:

- actuator dynamics;
- sensor placement;
- compute capability;
- tool geometry;
- calibration;
- wear;
- battery state.

Competence must therefore be tied to validated hardware scope.

## 32. Environment-Specific Competence

A skill validated in one environment should not automatically generalize to another.

This is especially important for navigation and manipulation.

## 33. Hierarchical Skills

Composite skills should expose subskill dependencies:

```text
MAKE_COFFEE
 ├── FIND_CUP
 ├── GRASP_CUP
 ├── FILL_CUP
 ├── OPERATE_MACHINE
 └── PLACE_CUP
```

Failure analysis should identify which subskill failed.

## 34. Skill Transfer

Transfer requires explicit validation:

```text
SOURCE SKILL
 ↓
TRANSFER HYPOTHESIS
 ↓
TARGET VALIDATION
 ↓
TARGET COMPETENCE
```

Transfer should not inherit full confidence automatically.

## 35. Skill Composition

Two validated skills do not automatically form a validated composite skill.

Composition must be tested because interaction effects can create new failure modes.

## 36. Skill Memory Consolidation

Successful execution can produce a procedural-memory candidate:

```text
EXECUTION
 ↓
EVALUATION
 ↓
SKILL CANDIDATE
 ↓
VALIDATION
 ↓
PROCEDURAL MEMORY
```

This integrates documents 84 and 89.

## 37. Skill Promotion

Promotion should require:

- defined scope;
- sufficient evidence;
- acceptable failure rate;
- safety validation;
- generalization evidence;
- provenance;
- version identity.

## 38. Skill Demotion

A skill may be demoted because of:

- repeated failures;
- distribution shift;
- hardware change;
- environment change;
- newly discovered unsafe behavior;
- invalidated evidence;
- model update.

## 39. Skill Retirement

Retirement does not mean historical deletion.

The system should preserve the reason for retirement where retention permits:

```text
ACTIVE
 ↓
RETIRED
REASON
EVIDENCE
```

## 40. Skill Versioning

Every implementation change should produce a version transition:

```text
SKILL V1
 ↓
MODEL / CODE CHANGE
 ↓
SKILL V2
```

V2 must not inherit V1 competence without validation of equivalence or revalidation.

## 41. Model Updates

A foundation-model update can change behavior even when the procedural description is unchanged.

Therefore skill competence is linked to implementation/model version.

## 42. Memory Update Safety

A successful execution should not immediately overwrite a validated skill.

Instead:

```text
NEW EXECUTION
 ↓
EVIDENCE
 ↓
UPDATE CANDIDATE
 ↓
VALIDATION
 ↓
NEW SKILL VERSION
```

## 43. Skill Drift

Monitor for gradual degradation:

```text
SUCCESS RATE
QUALITY
LATENCY
RECOVERY RATE
SAFETY EVENTS
```

Trend changes can trigger revalidation before catastrophic failure.

## 44. Competence Decay

Competence may become stale because:

- environment changes;
- hardware ages;
- tools change;
- software changes;
- task distribution changes;
- evidence becomes old.

Competence should therefore have validity conditions and revalidation triggers.

## 45. No Automatic Forgetting of Skills

Skill decay should affect deployment confidence and retrieval priority according to policy; it should not silently destroy historical evidence.

## 46. Skill and Identity

Execution evidence must attach to the correct agent/entity from document 97.

```text
SKILL EXECUTED BY AGENT X
```

is not equivalent to:

```text
SKILL OBSERVED NEAR AGENT X
```

## 47. Skill and Time

Competence claims require temporal validity:

```text
VALIDATED_AT
VALID_UNTIL / REVALIDATION_TRIGGER
```

Historical competence cannot be assumed current indefinitely.

## 48. Skill and Space

Spatially dependent skills must retain spatial scope from document 99.

A navigation skill can be valid in one map/version and invalid after structural changes.

## 49. Skill and Causality

Skill execution can generate causal evidence, but one successful action does not prove a complete causal model.

```text
ACTION
 ↓
OUTCOME
```

is evidence requiring alternative-explanation analysis before causal promotion.

## 50. Skill and Cross-Modal Evidence

Execution evaluation may combine:

```text
VIDEO
FORCE SENSORS
PROPRIOCEPTION
AUDIO
TEXT FEEDBACK
TASK STATE
```

Evidence must preserve shared provenance and avoid double counting correlated modalities, integrating document 101.

## 51. Skill Safety Classification

Skills should be classified by consequence:

```text
LOW
MODERATE
HIGH
CRITICAL
```

The classification determines required evidence, supervision and runtime safeguards.

## 52. Autonomy Levels

Competence and autonomy are separate.

Possible policy levels:

```text
OBSERVE ONLY
SUGGEST
SUPERVISED EXECUTION
CONSTRAINED AUTONOMY
FULL AUTONOMY
```

A high competence score does not itself grant a higher autonomy level.

## 53. Authorization Boundary

```text
COMPETENCE
 ≠
AUTHORIZATION
```

Authorization depends on current policy, principal identity, environment, task and consequence.

## 54. Safety Boundary

```text
COMPETENCE
 ≠
CURRENT SAFETY
```

A highly competent skill can still be unsafe under changed circumstances.

## 55. Competence Under Uncertainty

When uncertainty is high:

```text
VERIFY
ASK
REDUCE SCOPE
SUPERVISE
ABORT
```

may be preferable to autonomous execution.

## 56. Benchmark Design

Skill benchmarks should measure more than average success rate.

Include:

- success;
- partial completion;
- failure severity;
- safety violations;
- recovery;
- intervention rate;
- latency;
- resource use;
- robustness;
- generalization;
- calibration.

## 57. Holdout Evaluation

Holdout conditions should test meaningful variation rather than only random splits.

Examples:

```text
UNSEEN OBJECTS
UNSEEN ENVIRONMENTS
UNSEEN USERS
UNSEEN COMBINATIONS
UNSEEN HARDWARE
```

## 58. Long-Horizon Evaluation

Composite skills should be tested over long sequences because small errors can compound.

Research on general-purpose robot learning highlights long-horizon generalization as a central deployment challenge. citeturn0academia2

## 59. Continual Learning Evaluation

When new experiences update skill memory, test for:

```text
NEW SKILL PERFORMANCE
OLD SKILL RETENTION
CATASTROPHIC FORGETTING
REGRESSION
INTERFERENCE
```

## 60. Negative Transfer

A learned skill should not be reused merely because it is semantically similar.

Transfer can reduce performance when source and target conditions differ.

## 61. Skill Retrieval

Retrieval should rank skills by:

- task relevance;
- competence status;
- scope compatibility;
- freshness;
- hardware compatibility;
- environment compatibility;
- safety classification;
- provenance.

## 62. Skill Retrieval Is Not Skill Validation

```text
RETRIEVED SKILL
 ≠
CURRENTLY VALID SKILL
```

A final deployment check is required.

## 63. Runtime Skill Gate

```text
RETRIEVE
 ↓
SCOPE CHECK
 ↓
VERSION CHECK
 ↓
CURRENT STATE CHECK
 ↓
SAFETY CHECK
 ↓
COMPETENCE CHECK
 ↓
EXECUTE / SUPERVISE / ABORT
```

## 64. Runtime Monitoring Feedback

During execution:

```text
EXECUTION
 ↓
MONITOR
 ↓
DEVIATION
 ├─ recover
 ├─ replan
 ├─ ask
 └─ abort
```

This integrates with 100's causal world model and 95's action boundary.

## 65. Human Feedback

Human feedback should be typed:

```text
CORRECT
INCORRECT
UNSAFE
QUALITY ISSUE
PREFERENCE
UNKNOWN
```

A preference is not necessarily evidence of objective task correctness.

## 66. User Acceptance

User approval can establish acceptance for user-specific tasks but should not automatically establish general technical competence.

## 67. Skill Evidence Provenance

Every competence assessment should answer:

```text
WHAT WAS TESTED?
WHERE?
WHEN?
WITH WHAT HARDWARE?
WITH WHAT MODEL?
WHO SUPERVISED?
WHAT HAPPENED?
WHAT EVIDENCE SUPPORTS THE CLAIM?
```

## 68. Skill Evidence Lineage

```text
COMPETENCE CLAIM
 ↓
EVALUATION
 ↓
EXECUTIONS
 ↓
OBSERVATIONS
 ↓
RAW MULTIMODAL EVIDENCE
```

This integrates document 92.

## 69. Security Threats

Skill memory can be attacked through:

- poisoned demonstrations;
- fake success records;
- malicious skill injection;
- unsafe procedure modification;
- provenance forgery;
- replayed competence evidence;
- compromised evaluation environments;
- reward hacking;
- hidden unsafe behaviors.

## 70. Skill Poisoning

A malicious success record must not directly promote a skill:

```text
FAKE SUCCESS
 ↓
NO AUTOMATIC PROMOTION
```

Evidence must pass provenance, integrity and evaluation controls.

## 71. Evaluation Integrity

Production evaluation must be protected from contamination by training data and manipulated test environments.

## 72. Skill Quarantine

Suspicious skills should enter:

```text
ACTIVE
 ↓
QUARANTINED
 ↓
REVIEW / REVALIDATE
 ↓
RESTORE / RETIRE
```

Quarantined skills must not be used for unrestricted autonomous action.

## 73. Skill Rollback

When a skill update causes regression:

```text
V2
 ↓
REGRESSION
 ↓
ROLLBACK TO TRUSTED V1
```

The rollback must preserve the evidence explaining the regression.

## 74. Skill Dependency Impact

When a prerequisite skill changes:

```text
SKILL A UPDATED
 ↓
SKILL C DEPENDS ON A
 ↓
C REVALIDATION REQUIRED
```

## 75. Skill Migration

When schema or runtime representations change, preserve:

- skill identity;
- version history;
- competence evidence;
- provenance;
- scope;
- retirement status.

## 76. Cross-Agent Skill Exchange

An agent receiving a skill from another agent must treat it as an imported skill claim, not proven competence.

```text
REMOTE SKILL
 ↓
VERIFY PROVENANCE
 ↓
LOCAL VALIDATION
 ↓
LOCAL COMPETENCE
```

## 77. Competence Claims Across Agents

Competence is agent-specific unless explicitly demonstrated to transfer.

```text
AGENT A: competent
        ≠
AGENT B: competent
```

Different hardware, embodiment, sensors and policies can change performance.

## 78. Skill Marketplace / External Skills

External skills must enter through quarantine and validation boundaries.

No external skill should receive autonomous execution authority merely because it has high reputation.

## 79. Model Selection and Skill Competence

Foundation-model selection should consider deployment-specific evaluation rather than generic leaderboard performance. Recent work on robot foundation-model evaluation argues for layered evaluation from general metrics through simulation to robot-specific tests because real embodied requirements are poorly captured by generic benchmarks. citeturn0academia1

## 80. Evaluation Funnel

A recommended funnel is:

```text
GENERAL TESTS
      ↓
SIMULATION
      ↓
CONTROLLED HARDWARE
      ↓
SUPERVISED REAL-WORLD
      ↓
LIMITED AUTONOMY
      ↓
FULL DEPLOYMENT
```

Promotion requires passing the applicable gates.

## 81. Risk-Based Evidence

Evidence requirements scale with consequence:

```text
LOW CONSEQUENCE
→ lightweight validation

HIGH CONSEQUENCE
→ diverse validation + runtime monitoring

CRITICAL CONSEQUENCE
→ controlled validation + independent checks + human oversight where required
```

## 82. Competence and Causal World Models

Skill evaluation can use causal world models to test expected outcomes before execution, but simulated causal predictions remain model-derived evidence and cannot replace real-world validation for high-consequence deployment.

## 83. Competence and Spatial Memory

Spatial skills must be revalidated after relevant map/environment changes.

## 84. Competence and Temporal Memory

Historical performance should remain linked to the time and version under which it was measured.

## 85. Competence and Identity

Competence evidence must be attributed to the correct agent/entity and must not leak across principals.

## 86. Competence and Cross-Modal Memory

Multimodal execution evidence must preserve source lineage and independence assumptions from 101.

## 87. Competence Evaluation Under Missing Data

Missing telemetry should reduce evidence completeness rather than being silently interpreted as normal behavior.

## 88. Unknown Outcome

If the system cannot establish whether a skill succeeded:

```text
UNKNOWN OUTCOME
```

must remain a valid state.

Unknown is not success.

## 89. Competence Under Partial Observability

When important parts of execution cannot be observed, competence confidence must be limited accordingly.

## 90. Final Architectural State Machine

```text
SKILL CANDIDATE
 ↓
UNTESTED
 ↓
EVALUATION
 ├─ FAIL → REVISE / RETIRE
 └─ PASS
      ↓
PROVISIONAL
      ↓
DIVERSE VALIDATION
      ├─ FAIL → DEMOTE
      └─ PASS
           ↓
VALIDATED
           ↓
DEPLOYMENT MONITORING
 ├─ STABLE → ACTIVE
 ├─ DRIFT → REVALIDATE
 ├─ RISK → RESTRICT
 └─ FAILURE → QUARANTINE / ROLLBACK
```

## 91. Normative Invariants

1. Skill representation is not competence.
2. One successful execution does not prove general competence.
3. Demonstration is not proof of independent competence.
4. Simulation success is not real-world competence.
5. Competence is scope-dependent.
6. Competence is version-dependent.
7. Competence is time-dependent.
8. Competence is environment-dependent where applicable.
9. Hardware-specific skills require hardware-specific validation.
10. Composite skills require composite validation.
11. Skill transfer requires target validation.
12. Skill retrieval does not validate current competence.
13. Competence does not authorize action.
14. Competence does not guarantee current safety.
15. Human intervention must be recorded and distinguished from autonomous success.
16. Recovery and abort behavior are part of safety-relevant competence.
17. Correlated execution evidence must not be double-counted.
18. Evaluation and training must remain separated where possible.
19. Unknown outcome is not success.
20. Missing telemetry is not evidence of normality.
21. Competence claims require provenance.
22. Competence claims must retain scope and limitations.
23. Skill updates require validation.
24. Model updates can invalidate previous competence evidence.
25. Dependency changes can invalidate composite skills.
26. Skill poisoning must not automatically promote competence.
27. Imported skills require local validation.
28. Competence claims are agent-specific unless transfer is demonstrated.
29. Runtime monitoring is required for applicable autonomous skills.
30. Out-of-distribution execution requires restriction, verification, supervision or abort according to risk.
31. Safety outcomes must be evaluated separately from task completion.
32. Historical competence cannot override current authorization or safety state.
33. Retired skills retain historical provenance where policy permits.
34. Quarantined skills cannot receive unrestricted autonomous execution.
35. High-consequence skills require stronger and more diverse evidence.

## 92. Integration With Document 95

The competence layer follows the reference pipeline:

```text
OBSERVATION
 ↓
EVIDENCE
 ↓
IDENTITY / TIME / SPACE
 ↓
CAUSAL / PROCEDURAL MODEL
 ↓
SKILL EXECUTION
 ↓
OUTCOME
 ↓
COMPETENCE EVALUATION
 ↓
RETRIEVAL / PLANNING
 ↓
AUTHORIZATION + SAFETY
 ↓
ACTION
 ↓
NEW EVIDENCE
```

## 93. Integration With Documents 97–101

```text
97 IDENTITY
→ who executed the skill?

98 TIME
→ when and under which version/state?

99 SPACE
→ where and under which spatial conditions?

100 CAUSAL
→ what outcomes and mechanisms were expected?

101 CROSS-MODAL
→ what evidence supports the execution and outcome?

102 COMPETENCE
→ is the skill sufficiently validated for this scope?
```

## 94. Integration With Document 96

102 resolves the P0 gap:

**Procedural Skill / Competence Verification.**

It establishes prerequisites for future work on:

- memory/schema migration;
- model/memory co-evolution;
- governance;
- human oversight;
- distributed skill exchange.

## 95. Research Cross-Validation

The architecture was cross-validated against current robotics research emphasizing:

- generalization and distribution shift in general-purpose robotics;
- sample-efficient skill learning and real-world benchmarking;
- runtime failure prediction and monitoring;
- deployment-specific foundation-model evaluation;
- continual skill memory and reuse.

Recent work demonstrates that skill systems can show strong performance in selected settings while still requiring explicit evaluation of generalization, sample efficiency and real-world deployment conditions. citeturn0academia0turn0academia2

Runtime-monitoring research further supports treating error prediction and intervention as part of trustworthy deployment rather than relying only on final task success. citeturn0search4

Recent foundation-model evaluation work emphasizes layered evaluation from generic metrics through simulation and finally robot-specific testing, reinforcing the risk-based funnel defined here. citeturn0academia1

These sources support the architectural principles but do not establish one universally optimal skill-learning or competence-verification algorithm.

## 96. Final Principle

> **Novi must never confuse knowing how to perform a skill with being competent to perform it autonomously. Competence is an evidence-backed, scope-specific, versioned and time-bounded claim that must survive diverse evaluation, runtime monitoring and safety checks. Successful execution can update the evidence base, but it cannot by itself grant generalized competence or authorization.**

Skill memory therefore becomes a controlled bridge between learning and action: it stores reusable procedures, preserves their evidence and limitations, continuously tests their validity, and degrades autonomy conservatively when the evidence no longer supports the claim.