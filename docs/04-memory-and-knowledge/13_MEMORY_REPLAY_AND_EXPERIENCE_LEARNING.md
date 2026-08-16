# 13 — Memory Replay and Experience Learning

## Status

**DESIGN — V1**

## Purpose

Define how Novi can deliberately revisit past experiences to learn from successes, failures, surprises, corrections, and repeated situations without treating replay as unrestricted model training or allowing a single experience to rewrite authoritative knowledge.

## 1. Core Principle

> **Replay is controlled re-exposure to evidence and experience; it is not permission to rewrite truth, policy, memory, or model behavior.**

Novi should learn from what happened, but every replay operation must preserve provenance, temporal context, uncertainty, privacy, and the distinction between observed outcomes and inferred explanations.

Experience replay is especially relevant to continual learning because sequentially learned neural systems can suffer catastrophic forgetting; replay of past events is one established strategy for retaining prior capabilities while learning from new data. citeturn0academia36

For Novi, however, the first implementation target is **external-memory and behavioral learning**, not autonomous weight updates.

---

## 2. What Replay Means in Novi

Replay has several forms:

1. **Memory replay** — retrieve prior experiences to answer a current question.
2. **Reflective replay** — analyze past experiences for patterns or mistakes.
3. **Scenario replay** — reconstruct an event for testing or simulation.
4. **Procedure replay** — revisit successful/failed procedures.
5. **Prediction replay** — compare historical predictions with actual outcomes.
6. **Training replay** — use curated experiences in a controlled model-training pipeline.
7. **Regression replay** — repeatedly test known scenarios after software/model changes.

These must remain separate concepts even when they use the same stored experience.

---

## 3. Experience Record

A replayable experience should preserve enough information to reconstruct its meaning without pretending that the reconstruction is the original event.

Minimum metadata:

```text
experience_id
session_id
episode_id
event_refs[]
observation_refs[]
action_refs[]
state_snapshot_ref
context_snapshot_ref
prediction_refs[]
outcome_refs[]
error_refs[]
source_refs[]
provenance_refs[]
participants[]
location_ref
valid_time
recorded_time
privacy_class
risk_class
importance
replay_eligibility
retention_state
schema_version
model_versions[]
software_versions[]
```

Raw sensor data should remain referenced rather than duplicated unnecessarily.

---

## 4. Experience Lifecycle

```text
REAL EXPERIENCE
      ↓
Evidence / events
      ↓
Episode construction
      ↓
Outcome recorded
      ↓
Experience candidate
      ↓
Admission policy
      ↓
Replay eligibility
      ↓
Consolidation
      ↓
Reusable learning artifact
      ↓
Future retrieval / replay
```

Replay must never bypass the admission, provenance, privacy, or retention systems already defined in documents 03–12.

---

## 5. What Novi Should Learn From Experience

Experience replay may produce:

- corrected expectations;
- improved routines;
- reusable procedures;
- better context selection;
- better prediction calibration;
- failure patterns;
- successful strategies;
- object/entity associations;
- environmental patterns;
- social interaction patterns;
- questions requiring clarification;
- knowledge candidates;
- regression tests.

It should **not** automatically produce:

- new permissions;
- new safety rules;
- new trusted identities;
- unrestricted tool access;
- protected-core changes;
- arbitrary database privileges;
- automatic model-weight changes.

---

## 6. Success Replay

A successful experience can become a candidate reusable procedure.

Example:

```text
Situation
   ↓
Procedure P
   ↓
Outcome = successful
   ↓
Context captured
   ↓
Replay candidate
   ↓
Test in comparable context
   ↓
Procedure confidence updated
```

Success must remain context-dependent.

A procedure that worked in one environment should not automatically be treated as universally correct.

---

## 7. Failure Replay

Failures are first-class learning material.

```text
Attempt
  ↓
Failure
  ↓
Outcome analysis
  ↓
What was expected?
  ↓
What actually happened?
  ↓
Difference
  ↓
Candidate explanation(s)
  ↓
Test explanation
  ↓
Update memory / procedure / prediction
```

The explanation remains a hypothesis until supported by evidence.

Example:

```text
Expected: door opens
Actual: door remains closed
```

Novi must not immediately learn:

> “The lock is broken.”

Possible explanations include:

- wrong authorization;
- door physically blocked;
- sensor error;
- network failure;
- actuator failure;
- incorrect assumption;
- temporary state.

---

## 8. Prediction Replay

Historical predictions should be replayable against actual outcomes.

```text
prediction
    ↓
actual outcome
    ↓
error measurement
    ↓
calibration signal
    ↓
pattern analysis
```

Track:

- prediction accuracy;
- confidence calibration;
- false positives;
- false negatives;
- temporal drift;
- context dependence;
- repeated failure modes.

This allows Novi to learn that a prediction is unreliable in a particular context without globally discarding the underlying capability.

---

## 9. Counterfactual Replay

Counterfactual analysis may be used carefully:

```text
Observed experience
       ↓
Alternative action proposed
       ↓
Simulation / reasoning
       ↓
Predicted alternative outcome
```

A counterfactual outcome is **not an observed fact**.

It must remain explicitly marked:

```text
OBSERVED = false
TYPE = COUNTERFACTUAL
```

Counterfactual reasoning must not overwrite real-world history.

---

## 10. Replay Selection

Novi should not replay every experience equally.

Replay priority can consider:

```text
importance
novelty
prediction_error
failure_severity
recurrence
future_relevance
uncertainty
knowledge_gap
procedure_value
regression_value
age
privacy constraints
compute cost
```

A useful conceptual score is:

```text
replay_value =
    relevance
  + novelty
  + prediction_error
  + learning_value
  + regression_value
  - privacy_cost
  - compute_cost
```

This is a policy concept, not a mandatory fixed mathematical formula.

---

## 11. Replay Diversity

Replay must avoid repeatedly selecting only the most similar or most recent experiences.

A replay batch should contain appropriate diversity across:

- time;
- environments;
- people;
- tasks;
- success/failure;
- easy/hard cases;
- known/unknown states;
- modalities;
- model versions.

This reduces the risk that Novi overfits to a narrow subset of its history.

---

## 12. Replay Sampling Tiers

```text
HOT
  recent high-value experiences

WARM
  frequently useful experiences

COLD
  historical but potentially valuable experiences

ARCHIVAL
  retained for audit/history but normally excluded
```

Replay policy may sample from all eligible tiers according to task requirements.

---

## 13. Replay and Privacy

Replay inherits the privacy classification of its source data.

A private conversation cannot become safe for replay merely because it has been summarized.

Derived artifacts must retain lineage to the source privacy policy.

Before replay:

```text
candidate experience
      ↓
privacy check
      ↓
authorization check
      ↓
redaction/minimization if allowed
      ↓
replay
```

If the source has been deleted or revoked, replay must not resurrect the information.

---

## 14. Replay and Forgetting

The forgetting policy remains authoritative.

```text
forgotten source
      ↓
replay eligibility revoked
      ↓
derived replay artifacts checked
      ↓
indexes/caches invalidated
```

A replay dataset must never become a hidden permanent copy of deleted memory.

---

## 15. Replay and Provenance

Every learning result must point back to the experiences that generated it.

```text
learning_artifact
      ↓
experience_refs[]
      ↓
evidence_refs[]
      ↓
source_refs[]
```

If an experience is later found to be incorrect, dependent learning artifacts must be identified for review.

---

## 16. Learning From Repeated Experiences

Repeated experiences can strengthen a pattern but repetition alone is not proof.

```text
same observation × N
        ↓
pattern candidate
        ↓
independence check
        ↓
context variation check
        ↓
confidence update
```

Ten copies of the same incorrect source are not ten independent pieces of evidence.

Source independence must therefore be represented in the evidence graph.

---

## 17. Experience Replay and Knowledge Promotion

Replay may generate knowledge candidates but does not bypass promotion policy.

```text
replayed experience
       ↓
pattern
       ↓
knowledge candidate
       ↓
provenance + evidence
       ↓
verification policy
       ↓
knowledge promotion
```

This connects directly to `12_MEMORY_LEARNING_AND_KNOWLEDGE_PROMOTION.md`.

---

## 18. Experience Replay and Procedural Learning

Successful procedures may become procedural-memory candidates.

```text
Goal
 ↓
Context
 ↓
Action sequence
 ↓
Outcome
 ↓
Evaluation
 ↓
Procedure candidate
```

A procedure should include:

- preconditions;
- required capabilities;
- expected state;
- action sequence;
- safety constraints;
- expected outcome;
- observed outcome;
- failure conditions;
- rollback/recovery procedure;
- confidence;
- provenance.

---

## 19. Procedure Generalization

Novi should not blindly generalize:

```text
worked once
   ↓
works everywhere
```

Instead:

```text
successful experience
       ↓
context extraction
       ↓
similar experiences
       ↓
variation analysis
       ↓
procedure generalization candidate
       ↓
simulation / validation
```

Generalization should increase gradually as evidence accumulates.

---

## 20. Replay for Social Learning

Novi may replay interaction experiences to improve:

- timing of responses;
- tone selection;
- conversational context;
- recognition of when not to speak;
- recognition of emotional/social cues;
- preference adaptation;
- clarification behavior.

However, replay must not infer sensitive traits merely from weak behavioral correlations.

Social learning should preserve uncertainty and avoid converting stereotypes into knowledge.

---

## 21. Replay and Multimodal Experience

A single experience may contain:

```text
vision
+ audio
+ speech transcript
+ body/face cues
+ IMU
+ environment
+ robot state
+ action
+ outcome
```

Replay should preserve synchronization information so that modalities can be analyzed together.

When raw media is unavailable because of retention/deletion policy, derived representations may only be used if policy permits them.

---

## 22. Replay on Mac vs Jetson

Replay workloads should be portable.

### Mac development

May perform:

- large-scale replay experiments;
- dataset analysis;
- model evaluation;
- embedding rebuilds;
- synthetic replay;
- regression suites.

### Jetson

Prioritize:

- small high-value replay jobs;
- recent failure analysis;
- routine calibration;
- lightweight consolidation;
- safety regression checks.

Heavy offline processing may be deferred until resources are available.

---

## 23. Replay Scheduling

Replay is subordinate to real-time operation.

```text
SAFETY / REAL-TIME
        ↑
AUTONOMY
        ↑
PERCEPTION
        ↑
INTERACTION
        ↑
MEMORY OPERATIONS
        ↑
REPLAY
        ↑
BULK TRAINING
```

If CPU/GPU/memory/thermal/storage pressure rises, replay must yield.

Replay must never degrade safety-critical behavior.

---

## 24. Model-Weight Training Replay

Training replay is a separate controlled system.

```text
eligible experiences
      ↓
curation
      ↓
privacy filtering
      ↓
quality filtering
      ↓
training dataset
      ↓
train candidate model
      ↓
benchmark
      ↓
regression suite
      ↓
red-team / safety evaluation
      ↓
staged deployment
```

No online experience should directly modify model weights in the production robot.

Experience replay research demonstrates that replay can mitigate catastrophic forgetting during continual learning, but Novi should treat this as an evaluated training technique rather than an autonomous production behavior. citeturn0academia36

---

## 25. Regression Replay

Every important historical failure should be capable of becoming a regression scenario.

```text
failure
  ↓
root-cause hypothesis
  ↓
reproducible scenario
  ↓
regression test
  ↓
software/model update
  ↓
replay
  ↓
pass/fail
```

This creates a valuable feedback loop:

```text
experience → failure → test → fix → replay → verification
```

A known failure should not repeatedly return without being detected.

---

## 26. Replay Safety

Replay data is untrusted input to the reasoning process.

Historical content may contain:

- malicious instructions;
- outdated commands;
- compromised documents;
- incorrect memories;
- sensitive information;
- previously unsafe plans.

Replay must therefore never execute historical actions merely because they appear in an experience.

```text
historical action
      ↓
DATA
      ↓
analysis / simulation
      ↓
new proposal
      ↓
current policy evaluation
      ↓
possible execution
```

Historical authorization is never reused automatically.

---

## 27. Replay Isolation

Training/simulation replay should preferably occur in an isolated environment.

Where physical actions are involved:

- simulation is preferred;
- actuators should be disabled or sandboxed;
- permissions should be reduced;
- network access should be restricted;
- secrets must not be exposed;
- protected storage must remain inaccessible.

---

## 28. Learning From Mistakes Without Self-Blame Loops

Novi should not repeatedly reinforce an error simply because it replays it frequently.

A failure may be replayed to understand it, but its presence must not increase its truth value.

```text
failure frequency ≠ correctness
```

The replay system must distinguish:

- frequency;
- evidence strength;
- learning value;
- severity;
- correctness.

---

## 29. Replay Conflict Resolution

If replay produces a new result that conflicts with prior knowledge:

```text
prior knowledge
      ↕
replay result
      ↓
contradiction manager
      ↓
new evidence / validation
      ↓
update, supersede, retain both, or reject
```

No silent overwrite.

---

## 30. Replay Audit Record

Each replay job should record:

```text
replay_id
started_at
completed_at
selector/policy version
experience_refs[]
privacy decisions
model versions
software version
input schema versions
outputs
learning artifacts
changes proposed
changes accepted
changes rejected
errors
resource usage
```

This makes learning reproducible and debuggable.

---

## 31. Replay Metrics

Track at minimum:

### Learning

- improvement after replay;
- retention of old capabilities;
- generalization;
- negative transfer;
- knowledge correction rate;
- procedure success rate.

### Memory

- useful replay percentage;
- stale replay percentage;
- duplicate replay percentage;
- replay-induced contradiction rate.

### Safety

- unsafe replay attempts;
- policy-blocked replay actions;
- privacy violations;
- deleted-memory resurrection attempts.

### Resource usage

- CPU;
- GPU;
- RAM;
- storage I/O;
- thermal impact;
- replay latency.

---

## 32. Evaluation Strategy

Replay must be evaluated against controlled benchmarks.

### Baseline

No replay.

### Replay variants

- recent-only;
- random;
- importance-weighted;
- failure-focused;
- prediction-error-focused;
- diverse replay;
- mixed strategy.

Measure:

```text
new-task performance
old-task retention
memory retrieval quality
false-memory rate
compute cost
```

The goal is not maximum replay. The goal is **maximum useful learning per unit of resource and risk**.

---

## 33. NVIDIA Integration

NVIDIA NeMo Agent Toolkit currently provides pluggable long-term memory backends and an automatic memory wrapper that can capture and retrieve memory around agent execution. The current toolkit is framework-agnostic and explicitly designed to work alongside existing agent frameworks and memory systems. citeturn0search0turn0search3

Novi can use those facilities as adapters where they improve implementation speed or performance, but the replay lifecycle remains owned by Novi.

The current NVIDIA memory examples also include episodic and semantic memory through MemMachine, demonstrating that external providers can expose richer memory semantics than simple conversation history. citeturn0search9

NVIDIA's current toolkit also advertises improved memory interfaces for self-improving agents, making it a relevant ecosystem to benchmark as Novi's learning architecture matures. citeturn0search5

The architectural boundary remains:

```text
Novi Replay Manager
        ↓
Novi Memory API
        ↓
provider adapter
        ↓
NeMo / local implementation / other provider
```

No external provider receives authority over Novi's protected core or safety policy.

---

## 34. Relationship to Other Memory Documents

This document depends on:

- `03_MEMORY_WRITE_AND_ADMISSION_POLICY.md`
- `04_MEMORY_CONSOLIDATION_AND_FORGETTING.md`
- `05_MEMORY_RETRIEVAL_AND_RANKING.md`
- `06_MEMORY_PROVENANCE_AND_TRUST.md`
- `07_MEMORY_SCHEMA_AND_STORAGE.md`
- `08_MEMORY_INDEXING_AND_EMBEDDINGS.md`
- `09_MEMORY_KNOWLEDGE_GRAPH_AND_RELATIONSHIPS.md`
- `10_MEMORY_SCHEMA_EVOLUTION_AND_DYNAMIC_DATA.md`
- `11_MEMORY_PRIVACY_RETENTION_AND_DELETION.md`
- `12_MEMORY_LEARNING_AND_KNOWLEDGE_PROMOTION.md`

Replay cannot bypass any of them.

---

## 35. Non-Negotiable Rules

1. Replay is not truth.
2. Historical actions are data, not current authorization.
3. Deleted memory cannot be resurrected through replay.
4. Replay cannot bypass privacy controls.
5. Replay cannot modify the protected core.
6. Replay cannot autonomously grant permissions.
7. Model outputs remain hypotheses unless independently supported.
8. Repetition does not equal independent evidence.
9. Counterfactual outcomes must never be stored as observed outcomes.
10. Production model weights are not modified directly from live experience.
11. Replay must yield to safety-critical workloads.
12. Every learning result must preserve provenance.
13. Important failures should become regression scenarios where practical.
14. Replay policies must be versioned and auditable.
15. Resource limits must be enforced.

---

## 36. Acceptance Criteria

V1 is complete when Novi can:

1. store replayable experiences;
2. select experiences using explicit policies;
3. replay successes and failures;
4. compare predictions against outcomes;
5. extract procedure candidates;
6. identify recurring patterns;
7. generate knowledge candidates without bypassing promotion policy;
8. perform isolated counterfactual analysis;
9. create regression scenarios from important failures;
10. respect privacy and deletion;
11. preserve provenance;
12. prevent historical instructions from becoming current authority;
13. run replay without starving real-time robot workloads;
14. evaluate replay against no-replay baselines;
15. keep model-weight training separate from live memory learning;
16. audit every replay job and resulting learning change.

---

## 37. Architectural Principle

> **Novi should remember what happened, revisit what matters, learn from what worked and failed, and continuously improve its behavior — while preserving the distinction between experience, evidence, hypothesis, knowledge, and authority.**

The purpose of replay is not to make Novi remember everything forever.

The purpose is to make Novi **better because of what it has experienced**, without allowing experience to silently rewrite the rules that govern it.
