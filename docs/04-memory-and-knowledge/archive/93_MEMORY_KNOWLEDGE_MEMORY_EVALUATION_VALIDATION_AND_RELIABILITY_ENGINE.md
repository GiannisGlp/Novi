# 93 — Memory Knowledge Memory Evaluation Validation and Reliability Engine

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define the continuous evaluation, validation and reliability system for Novi's memory architecture.

This document establishes how Novi determines whether memory is actually useful, accurate, current, safe, traceable, privacy-compliant and operationally reliable across long-running interactions and physical-world operation.

## Core Principle

> **A memory system is not reliable because it can retrieve information. It is reliable when it retrieves the right evidence, uses it correctly, updates it when reality changes, respects forgetting and privacy policy, and remains safe as memory accumulates over time.**

Recent agent-memory research reinforces that evaluation must go beyond simple recall. Long-horizon benchmarks identify failures involving outdated memories, causal/objective information, evidence use and memory-induced safety drift. [1][2][3]

## 1. Evaluation Architecture

```text
MEMORY SYSTEM
      ↓
OBSERVABILITY
      ↓
EVALUATION DATA
      ↓
METRICS
      ↓
VALIDATION
      ↓
REGRESSION DETECTION
      ↓
RELIABILITY ASSESSMENT
      ↓
RELEASE / DEPLOYMENT DECISION
```

Evaluation is a control system, not a one-time benchmark.

## 2. What Must Be Evaluated

Evaluate independently and jointly:

- ingestion;
- provenance;
- storage integrity;
- indexing;
- retrieval;
- ranking;
- evidence fusion;
- conflict resolution;
- consolidation;
- reconsolidation;
- semantic memory;
- procedural memory;
- prospective memory;
- metamemory;
- decay;
- forgetting;
- deletion;
- privacy enforcement;
- distributed synchronization;
- downstream reasoning;
- action safety.

## 3. Memory Evaluation Layers

```text
L0 STORAGE
L1 RETRIEVAL
L2 EVIDENCE
L3 MEMORY SEMANTICS
L4 REASONING
L5 DECISION
L6 ACTION / SAFETY
L7 LONGITUDINAL SYSTEM
```

A high score at one layer cannot compensate for failure at a higher-consequence layer.

## 4. Evaluation Dimensions

At minimum evaluate:

```text
CORRECTNESS
COMPLETENESS
FRESHNESS
RELEVANCE
PROVENANCE
CALIBRATION
ROBUSTNESS
PRIVACY
SECURITY
LATENCY
COST
SAFETY
```

## 5. Retrieval Accuracy

Measure whether relevant memories/evidence are retrieved.

Useful metrics include:

- recall@k;
- precision@k;
- MRR;
- nDCG;
- retrieval sufficiency;
- evidence coverage.

These metrics should not be treated as sufficient measures of memory quality.

## 6. Retrieval Sufficiency

A retrieved context can contain the right memory but still omit information required to answer correctly.

Therefore evaluate:

```text
RETRIEVED
   ↓
SUFFICIENT FOR TASK?
```

This is distinct from raw retrieval recall.

## 7. Evidence Use

Evaluate whether retrieved evidence is actually used correctly.

```text
EVIDENCE AVAILABLE
      ≠
EVIDENCE USED
      ≠
EVIDENCE USED CORRECTLY
```

Recent long-horizon evaluation suggests that evidence use can be a larger bottleneck than simple evidence availability. [4]

## 8. Answer Grounding

Measure whether memory-dependent answers are supported by retrieved evidence and provenance.

A correct answer produced for the wrong reason remains a diagnostic concern.

## 9. Memory Fact Accuracy

Evaluate individual memory claims against ground truth or authoritative evidence where available.

Track:

- true memories;
- false memories;
- outdated memories;
- ambiguous memories;
- unsupported inferences.

## 10. Temporal Accuracy

A memory can be historically correct and currently wrong.

Evaluate:

```text
PAST STATE
CURRENT STATE
STATE TRANSITION
```

The system must distinguish all three.

## 11. Forgetting-Aware Accuracy

Accuracy should penalize reliance on obsolete or explicitly invalidated information.

This is especially important for personalized agents whose users and environments change over time. Recent work proposes Forgetting-Aware Memory Accuracy for this purpose. [1]

## 12. Change Tracking

Evaluate whether Novi correctly detects:

```text
OLD VALUE
   ↓
NEW VALUE
```

rather than storing both indefinitely and choosing arbitrarily at retrieval time.

## 13. False Memory Rate

Track false or unsupported memories separately from ordinary answer errors.

```text
FALSE MEMORY
→ incorrect retained claim
```

A system that confidently invents persistent memories can be more dangerous than one that simply fails to remember.

## 14. Contradiction Handling

Create controlled tests containing:

- contradictory observations;
- corrected user facts;
- stale state;
- unreliable sources;
- correlated duplicate evidence;
- conflicting agents.

Measure whether Novi preserves, resolves or escalates the conflict appropriately.

## 15. Evidence Independence

Evaluate whether correlated evidence is incorrectly counted as independent confirmation.

Example:

```text
SOURCE
 ↓
SUMMARY
 ↓
EMBEDDING
```

must not score as three independent observations.

## 16. Provenance Completeness

For important memory claims measure:

```text
source known?
origin known?
transformation known?
derivation known?
version known?
```

Missing provenance should be measurable rather than silently ignored.

## 17. Provenance Integrity

Test whether lineage can be altered, lost, forged or incorrectly attached.

A provenance graph that is complete but corrupt is not reliable.

## 18. Confidence Calibration

Evaluate whether confidence corresponds to empirical correctness.

```text
PREDICTED CONFIDENCE
       ↓
OBSERVED CORRECTNESS
       ↓
CALIBRATION
```

Track calibration separately for important task classes.

## 19. Overconfidence

Measure cases where Novi is highly confident while evidence is weak, stale, conflicted or absent.

Overconfidence should be treated as a distinct reliability failure.

## 20. Underconfidence

Excessive abstention also matters.

Measure whether Novi unnecessarily refuses when sufficient evidence exists.

The goal is calibrated uncertainty, not maximal refusal.

## 21. Abstention Quality

Evaluate:

```text
SHOULD ANSWER → ANSWERS
SHOULD ABSTAIN → ABSTAINS
```

A good memory system must know when evidence is insufficient.

## 22. Safety-Critical Evaluation

Safety-related memory should use stricter evaluation thresholds.

Test:

- stale safety information;
- conflicting sensors;
- missing observations;
- uncertain localization;
- memory poisoning;
- unsafe procedural memory;
- incorrect authorization memory.

## 23. Memory-Induced Safety Risk

Evaluate safety against a **NullMemory baseline** where appropriate.

```text
MEMORY-ENABLED SYSTEM
        vs
NO-MEMORY SYSTEM
```

The difference can reveal risks caused specifically by accumulated memory. Recent longitudinal research identifies temporal memory contamination as a measurable safety phenomenon. [3]

## 24. Longitudinal Evaluation

Memory must be evaluated over time.

```text
DAY 1
 ↓
DAY 10
 ↓
DAY 100
 ↓
DAY 1000
```

A system that performs well at day 1 may degrade as memory accumulates.

## 25. Memory Accumulation Stress

Stress-test:

- large memory volume;
- repeated entities;
- contradictory updates;
- stale memories;
- irrelevant memories;
- sensitive memories;
- long task sequences;
- many simultaneous intentions.

## 26. Temporal Memory Contamination

Test whether earlier unrelated memories influence later tasks incorrectly.

Use fixed probe tasks across different memory-prefix lengths where practical.

This isolates memory-induced effects from ordinary task variation. [3]

## 27. Counterfactual Memory Testing

Compare:

```text
FULL MEMORY
MINIMAL MEMORY
NULL MEMORY
CORRECT MEMORY
CORRUPTED MEMORY
```

This helps identify whether performance changes are genuinely attributable to memory.

## 28. Retrieval Contamination Testing

Inject irrelevant but semantically similar memories and evaluate whether Novi retrieves or relies on them.

## 29. Memory Poisoning Tests

Introduce malicious or incorrect memory content and measure:

- retrieval probability;
- propagation;
- belief influence;
- action influence;
- recovery after correction.

## 30. Correction Recovery

After a memory is corrected, test whether the obsolete memory continues influencing retrieval or decisions.

```text
OLD
 ↓
CORRECTION
 ↓
NEW
```

The old claim should remain historically traceable when required, but should not remain falsely authoritative.

## 31. Forgetting Tests

Verify that requested forgetting produces the intended state:

```text
SUPPRESSED
DELETED
SANITIZED
```

according to scope.

## 32. Deletion Verification

Test source and derivative removal across:

- primary storage;
- indexes;
- caches;
- summaries;
- embeddings;
- replicas;
- materialized views;
- backups according to policy.

## 33. Reappearance Testing

Attempt to recover erased information through:

- stale caches;
- old replicas;
- summaries;
- embeddings;
- synchronization;
- generated reconstruction.

A memory that reappears unexpectedly is a critical failure.

## 34. Privacy Evaluation

Test whether users can retrieve information outside their authorization scope.

Measure:

```text
unauthorized retrieval
unauthorized inference
metadata leakage
cross-user contamination
```

## 35. Multi-User Isolation

Use adversarial tests where one person's memory resembles another person's memory.

Verify that semantic similarity never bypasses identity and authorization boundaries.

## 36. Data Minimization Evaluation

Measure whether the system stores or retrieves more sensitive information than necessary for the task.

## 37. Skill-Memory Evaluation

For procedural memory evaluate:

- applicability;
- precondition accuracy;
- postcondition verification;
- success rate;
- recovery rate;
- failure rate;
- environmental generalization;
- hardware compatibility;
- safety abort rate.

## 38. Prospective-Memory Evaluation

For intentions evaluate:

- trigger accuracy;
- missed-trigger rate;
- false-trigger rate;
- completion verification;
- duplicate execution rate;
- interruption recovery;
- dependency handling;
- deadline behavior.

## 39. Semantic World-Model Evaluation

Evaluate:

- object identity;
- location accuracy;
- temporal state accuracy;
- relationship accuracy;
- uncertainty representation;
- update latency;
- stale-state rate.

## 40. Episodic Memory Evaluation

Evaluate whether episodes preserve:

- who;
- what;
- when;
- where;
- observed evidence;
- action;
- outcome;
- uncertainty;
- provenance.

## 41. Metamemory Evaluation

Evaluate whether Novi correctly knows:

```text
WHAT IS STORED
WHAT IS RETRIEVABLE
WHAT IS STALE
WHAT IS CONFLICTED
WHAT IS UNKNOWN
WHAT WAS DELETED
```

Metamemory errors are distinct from ordinary memory errors.

## 42. Consolidation Evaluation

Measure whether repeated episodes correctly produce abstractions without creating false certainty.

Test:

```text
episode diversity
episode conflict
source independence
abstraction correctness
provenance retention
```

## 43. Reconsolidation Evaluation

Test whether updates correctly revise eligible memories while preserving historical lineage.

Avoid assuming that every retrieval should modify memory.

## 44. Retrieval Ranking Evaluation

Evaluate ranking across:

- semantic similarity;
- temporal relevance;
- spatial relevance;
- task relevance;
- source quality;
- confidence;
- freshness;
- user scope;
- safety consequence.

## 45. Context Assembly Evaluation

Measure whether the final reasoning context is:

- sufficient;
- minimal;
- non-duplicative;
- provenance-aware;
- uncertainty-aware;
- privacy-compliant.

## 46. Cost and Latency

Track:

- storage cost;
- indexing cost;
- retrieval latency;
- consolidation latency;
- synchronization cost;
- compute cost;
- network cost;
- memory maintenance overhead.

Recent surveys emphasize that latency, throughput and maintenance cost are frequently overlooked in agent-memory evaluation. [4]

## 47. Benchmark Design

A serious benchmark should contain:

```text
STATIC FACTS
CHANGING FACTS
CONTRADICTIONS
LONG-HORIZON TRAJECTORIES
DISTRACTORS
MISSING EVIDENCE
FALSE PREMISES
DELETIONS
PRIVACY BOUNDARIES
SAFETY-CRITICAL CASES
```

## 48. Benchmark Units

Do not evaluate only question/answer pairs.

Use multiple units:

- memory item;
- knowledge point;
- episode;
- task;
- trajectory;
- user;
- time window;
- system lifetime.

Recent work argues that per-question averages can hide important behavior across changing knowledge points. [4]

## 49. Ground Truth

Ground truth should be typed:

```text
OBSERVED
AUTHORITATIVE
HUMAN-VERIFIED
SIMULATED
SYNTHETIC
UNKNOWN
```

Synthetic truth should not be presented as real-world validation.

## 50. Human Evaluation

Use human evaluation where automated metrics cannot establish:

- semantic usefulness;
- factual grounding;
- appropriateness of uncertainty;
- privacy handling;
- safety reasoning.

Human evaluation protocols must specify raters, criteria and inter-rater agreement where applicable.

## 51. Automated Evaluation

Automated evaluation can provide scale for:

- retrieval metrics;
- provenance checks;
- deletion checks;
- state consistency;
- schema validation;
- latency;
- deterministic safety invariants.

Automated judges should themselves be validated against human judgments when used for semantic quality.

## 52. Judge Sensitivity

If an LLM judge is used, evaluate sensitivity to:

- prompt wording;
- model choice;
- answer ordering;
- verbosity;
- citation formatting.

Recent agent-memory evaluation research identifies judge sensitivity as a significant measurement concern. [4]

## 53. Benchmark Leakage

Do not allow evaluation answers, gold facts or hidden test information to enter persistent memory before evaluation.

## 54. Reproducibility

Each evaluation run should record:

- memory snapshot/version;
- model version;
- retrieval configuration;
- prompts/policies;
- tools;
- dataset version;
- random seeds where applicable;
- hardware/software environment;
- evaluator version.

## 55. Frozen Evaluation Artifacts

For important benchmarks, preserve immutable evaluation artifacts sufficient to reproduce the result.

## 56. Regression Testing

Every significant memory-system change should run regression suites covering:

- retrieval;
- evidence use;
- belief arbitration;
- provenance;
- forgetting;
- privacy;
- safety;
- longitudinal behavior.

## 57. Canary Evaluation

New memory algorithms can be evaluated against a controlled subset before broad deployment.

Compare against the previous production system.

## 58. Shadow Evaluation

Where safe, run a new memory system in parallel without allowing it to affect decisions.

Compare outputs before promotion.

## 59. Release Gates

A memory-system release should not ship solely because aggregate accuracy improved.

Example gates:

```text
NO CRITICAL SAFETY REGRESSION
NO CRITICAL PRIVACY REGRESSION
NO ERASURE REGRESSION
PROVENANCE ≥ THRESHOLD
CALIBRATION ≥ THRESHOLD
RETRIEVAL ≥ THRESHOLD
LATENCY ≤ BUDGET
COST ≤ BUDGET
```

Thresholds should be task-specific and documented.

## 60. Reliability Scorecard

Maintain a multidimensional scorecard:

```text
MEMORY
├── Retrieval
├── Evidence
├── Correctness
├── Freshness
├── Provenance
├── Calibration
├── Forgetting
├── Privacy
├── Security
├── Safety
├── Latency
└── Cost
```

Avoid collapsing all dimensions into one opaque score.

## 61. Severity Classification

Failures should be classified:

```text
INFO
LOW
MODERATE
HIGH
CRITICAL
```

Examples of critical failures:

- unauthorized disclosure;
- unsafe action caused by stale memory;
- deleted memory reappearing contrary to policy;
- forged provenance accepted as authoritative;
- persistent false memory driving consequential behavior.

## 62. Error Budgets

Define explicit error budgets for important dimensions.

A system may tolerate occasional low-impact retrieval misses while allowing essentially zero tolerance for certain privacy or safety violations.

## 63. Reliability Over Time

Track metrics longitudinally rather than only per release.

```text
VERSION 1
 ↓
VERSION 2
 ↓
VERSION 3
```

Detect gradual degradation and distribution shift.

## 64. Distribution Shift

Re-evaluate when:

- users change;
- environments change;
- hardware changes;
- models change;
- task distributions change;
- memory volume changes.

A benchmark score from yesterday may not represent today's reliability.

## 65. Memory Health Monitoring

Runtime monitoring should detect:

- unusual false-memory growth;
- stale-memory growth;
- conflict spikes;
- retrieval drift;
- provenance gaps;
- privacy violations;
- deletion lag;
- synchronization failures;
- safety-memory anomalies.

## 66. Online vs Offline Evaluation

Separate:

```text
OFFLINE BENCHMARK
→ controlled measurement

ONLINE MONITORING
→ real deployment behavior
```

Neither is sufficient alone.

## 67. Safe Online Evaluation

Production evaluation must not intentionally expose users or physical systems to unsafe experimental memory behavior.

Use shadowing, simulation, replay and controlled canaries where appropriate.

## 68. Replay Evaluation

Recorded trajectories can be replayed against new memory versions.

Replay should preserve the original observation/action sequence while preventing unintended real-world actions.

## 69. Simulation

Simulation can test:

- memory accumulation;
- world changes;
- contradictory observations;
- long horizons;
- safety edge cases.

Simulation results must remain separate from physical-world validation.

## 70. Physical Validation

Physical-world memory behaviors should be validated under controlled conditions before relying on them operationally.

## 71. Causal Evaluation

Where possible, evaluate whether memory actually caused an outcome.

Compare:

```text
WITH MEMORY
WITHOUT MEMORY
ALTERNATIVE MEMORY
```

Causal attribution should not be inferred merely because a memory was present in context.

## 72. Error Attribution

Every failure should be assigned, where possible, to one or more layers:

```text
INGESTION
STORAGE
RETRIEVAL
EVIDENCE
ARBITRATION
MEMORY UPDATE
REASONING
ACTION
```

This prevents improving the wrong subsystem.

## 73. Failure Taxonomy

Maintain standardized failure classes:

- missed memory;
- wrong memory;
- stale memory;
- false memory;
- insufficient context;
- provenance loss;
- conflict mishandling;
- privacy leak;
- deletion failure;
- safety contamination;
- unauthorized action;
- evaluation artifact failure.

## 74. Root-Cause Analysis

Critical failures require investigation through the provenance graph from outcome backward to memory source and system configuration.

```text
OUTCOME
 ↓
DECISION
 ↓
BELIEF
 ↓
EVIDENCE
 ↓
MEMORY
 ↓
SOURCE
```

## 75. Reliability Claims

Novi should only make reliability claims supported by evaluation evidence.

Avoid statements such as:

```text
"The memory system is always accurate."
```

Prefer measurable claims:

```text
"On benchmark X under configuration Y, metric Z was ..."
```

## 76. Confidence in Evaluation Results

Evaluation results themselves have uncertainty.

Report sample sizes, confidence intervals or other uncertainty estimates when statistically appropriate.

Avoid overinterpreting small benchmark differences.

## 77. Statistical Testing

When comparing systems, choose tests appropriate to paired data, repeated measures, clustering and the evaluation unit.

Do not treat correlated questions as independent samples without justification.

## 78. Benchmark Saturation

A benchmark can become too easy or too familiar.

Periodically refresh test distributions and include adversarial and longitudinal cases.

Recent surveys identify benchmark saturation as a concern in agent-memory evaluation. [4]

## 79. Memory Evaluation Dataset Governance

Datasets should have:

- provenance;
- versioning;
- privacy classification;
- licensing/usage rights;
- contamination controls;
- gold-label policy;
- deletion/update policy.

## 80. Adversarial Evaluation

Test attacks including:

- memory poisoning;
- prompt injection in memory;
- retrieval manipulation;
- identity confusion;
- stale-state exploitation;
- unauthorized cross-user retrieval;
- deletion bypass;
- provenance forgery.

## 81. Robustness to Corrupted Memory

Introduce controlled corruption and measure:

```text
DETECTION
 ↓
CONTAINMENT
 ↓
RECOVERY
```

The objective is not merely resilience; it is graceful, diagnosable failure.

## 82. Recovery Evaluation

After a memory subsystem failure, evaluate:

- recovery time;
- state integrity;
- loss of provenance;
- duplicate creation;
- stale replicas;
- safety behavior;
- user-visible consequences.

## 83. Backup and Restore Evaluation

Restore tests must verify that:

- valid memory returns correctly;
- deleted memory does not improperly return;
- provenance remains consistent;
- tombstones remain effective;
- replicas reconcile safely.

## 84. Cross-Version Compatibility

Test whether newer memory schemas can safely read older records and whether migration preserves semantics and provenance.

## 85. Migration Validation

Memory migrations should be evaluated before and after:

```text
SCHEMA v1
 ↓ migration
SCHEMA v2
```

Check semantic equivalence where intended and intentional differences where not.

## 86. Reliability SLOs

Define service-level objectives for memory infrastructure where appropriate:

- retrieval availability;
- maximum retrieval latency;
- synchronization lag;
- deletion completion time;
- provenance completeness;
- backup recovery objectives.

## 87. Evaluation Dashboard

A production dashboard should expose trends, not just current values:

```text
accuracy
freshness
false-memory rate
conflicts
privacy events
erasure lag
safety incidents
latency
cost
```

## 88. Alerting

Alerts should trigger on meaningful deviations, such as:

- sudden false-memory increase;
- retrieval recall collapse;
- stale-memory spike;
- privacy breach;
- erasure backlog;
- safety-memory regression;
- provenance completeness drop.

## 89. Human Review Queue

Critical or ambiguous memory events can enter human review where required.

Review should expose provenance and relevant evidence without unnecessarily exposing unrelated private data.

## 90. Evaluation and Self-Improvement

Evaluation results may inform improvements to retrieval, consolidation and memory policies.

However:

```text
EVALUATION RESULT
      ≠
AUTOMATIC PERMISSION TO CHANGE MEMORY
```

Changes require controlled validation.

## 91. Preventing Evaluation Feedback Loops

Do not let evaluation-generated judgments automatically become training/memory evidence for the same evaluation without isolation.

Otherwise:

```text
SYSTEM
 ↓
EVALUATE
 ↓
STORE JUDGMENT
 ↓
RETRIEVE JUDGMENT
 ↓
SCORE SYSTEM
```

can create circular validation.

## 92. Benchmark Isolation

Keep evaluation memory separate from production memory unless deliberate contamination testing is being performed.

## 93. Canary Rollback

If a new memory release violates a critical gate:

```text
DETECT
 ↓
FREEZE
 ↓
ROLL BACK / ISOLATE
 ↓
INVESTIGATE
 ↓
REVALIDATE
```

## 94. Reliability Certification

A memory subsystem can receive a scoped reliability status such as:

```text
EXPERIMENTAL
VALIDATED
PRODUCTION
RESTRICTED
DEGRADED
SUSPENDED
```

Certification is scoped to the tested configuration and task domain.

## 95. No Universal Memory Score

A single number cannot adequately represent Novi's memory reliability.

```text
HIGH RETRIEVAL
 + LOW PRIVACY
 = NOT RELIABLE

HIGH ACCURACY
 + BROKEN ERASURE
 = NOT RELIABLE

HIGH ACCURACY
 + UNSAFE STALE MEMORY
 = NOT RELIABLE
```

## 96. Architectural Invariants

1. Memory evaluation is continuous, not one-time.
2. Retrieval accuracy is necessary but insufficient.
3. Evidence availability is distinct from evidence use.
4. Correct answers do not prove correct memory reasoning.
5. Historical accuracy is distinct from current validity.
6. Obsolete memories must be penalized when they affect current tasks.
7. False-memory rate is a first-class metric.
8. Provenance completeness and integrity are independently evaluated.
9. Confidence must be calibrated against observed correctness.
10. Abstention quality matters alongside answer accuracy.
11. Longitudinal memory safety must be evaluated across accumulating memory.
12. NullMemory/counterfactual baselines should be used where causal attribution matters.
13. Privacy and erasure are release-critical reliability properties.
14. Multi-user isolation must be tested adversarially.
15. Skill, semantic, episodic and prospective memory require specialized evaluation.
16. Benchmark units must include knowledge points, trajectories and time, not only questions.
17. Automated judges require validation and sensitivity analysis.
18. Evaluation artifacts must be reproducible and versioned.
19. Evaluation data must remain isolated from production memory when contamination would invalidate results.
20. Evaluation results do not automatically authorize memory or policy changes.
21. Critical failures require provenance-based root-cause analysis.
22. Simulation cannot substitute for required physical validation.
23. Reliability claims must be scoped to tested configurations and domains.
24. A multidimensional scorecard is preferred to one opaque memory score.
25. Safety, privacy and erasure failures can invalidate an otherwise strong aggregate score.

## 97. Research Cross-Validation

The architecture is informed and stress-tested against recent peer-reviewed/academic agent-memory evaluation work:

### [1] From Recall to Forgetting: Benchmarking Long-Term Memory for Personalized Agents

**Md Nayem Uddin, Kumar Shubham, Eduardo Blanco, Chitta Baral, Ge Wang — 2026 — arXiv — 15 citations.**

Supports evaluating remembering, reasoning and recommending over weeks/months and explicitly penalizing obsolete-memory use through forgetting-aware evaluation. The study reports frequent reuse of invalid memories and difficulty reconciling changing information. fileciteturn146file0

### [2] AMA-Bench: Evaluating Long-Horizon Memory for Agentic Applications

**Yujie Zhao, Boqin Yuan, Junbo Huang, Haochen Yuan, Zhongming Yu, Haozhou Xu, Lanxiang Hu, Abhilash Shankarampeta, Zimeng Huang, Wentao Ni, Yuandong Tian, Jishen Zhao — 2026 — arXiv — 37 citations.**

Supports trajectory-based evaluation using states, actions, observations and tool outputs rather than dialogue-only memory tests. It reports weaknesses in capturing causal/objective information and losses from similarity-only retrieval. fileciteturn147file0

### [3] Remembering More, Risking More: Longitudinal Safety Risks in Memory-Equipped LLM Agents

**Ahmad S. Al-Tawaha, Shangding Gu, Peizhi Niu, Ruoxi Jia, Ming Jin — 2026 — arXiv — 3 citations.**

Supports longitudinal safety evaluation, fixed trigger-probe sets across memory-prefix lengths, and NullMemory counterfactual comparison. It identifies temporal memory contamination as a deployment-relevant risk. fileciteturn148file0

### [4] Anatomy of Agentic Memory: Taxonomy and Empirical Analysis of Evaluation and System Limitations

**Dongming Jiang, Yi Li, Songtao Wei, Jinxin Yang, Ayushi Kishore, Alysa Zhao, Dingyi Kang, Xue Hu, Bingzhe Li, Qiannan Li, Feng Chen — 2026 — arXiv — 20 citations.**

Supports the need to evaluate semantic utility, benchmark saturation, judge sensitivity, backbone dependence, latency, throughput and memory-maintenance cost rather than relying on a single accuracy metric. fileciteturn149file0

## 98. Final Principle

> **Novi's memory is trustworthy only when its behavior remains measurable, reproducible, calibrated, privacy-preserving, provenance-aware and safe as memories accumulate, change, conflict, decay and disappear over long periods.**

The memory system therefore requires continuous validation at every layer—from stored evidence to retrieval, belief formation, action influence and eventual forgetting—because a memory architecture that cannot measure its own failures cannot reliably govern its own evolution.