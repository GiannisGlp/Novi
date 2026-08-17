# 22 — Memory Evaluation and Benchmarking

## Status

**DESIGN — V1 / CRITICAL ARCHITECTURE**

## Purpose

Define how Novi determines whether its memory and knowledge system is correct, useful, reliable, efficient, safe, privacy-preserving, and genuinely improving over time.

This document treats evaluation as a permanent part of the memory architecture rather than a one-time pre-release activity.

NIST's AI evaluation guidance emphasizes testing, evaluation, verification and validation (TEVV), documented metrics and test sets, uncertainty, regular evaluation after deployment, and explicit evidence for validity, reliability, safety and robustness. NIST also cautions that benchmark scores alone do not necessarily predict real-world performance. These principles are adopted here for Novi's memory system. citeturn0search0turn0search3turn0search27

## 1. Core Principle

> **Novi must never be allowed to decide that it is improving solely because its own internal metrics say that it is improving.**

Evaluation criteria, datasets, protected test cases, safety thresholds and release gates must be controlled outside the adaptive learning loop.

```text
Novi learns
   ↓
changes behavior
   ↓
independent evaluation
   ↓
compare against protected baseline
   ↓
pass / fail / investigate
```

Continuous improvement therefore remains bounded by externally defined evaluation criteria.

---

## 2. Evaluation Is Continuous

Evaluation occurs at multiple stages:

```text
component development
       ↓
unit evaluation
       ↓
integration evaluation
       ↓
system evaluation
       ↓
pre-release evaluation
       ↓
field evaluation
       ↓
continuous monitoring
       ↓
periodic re-evaluation
```

NIST explicitly recommends evaluation before deployment and repeatedly during operation because controlled pre-deployment testing cannot represent all real-world variation. citeturn0search24turn0search3

---

## 3. Evaluation Layers

Novi's memory evaluation should be separated into:

1. **Data evaluation** — are test datasets valid and representative?
2. **Component evaluation** — do individual memory components work?
3. **Pipeline evaluation** — does information survive the complete lifecycle?
4. **System evaluation** — does memory improve cognition/autonomy?
5. **Safety evaluation** — does failure remain safe?
6. **Privacy evaluation** — are retention/deletion policies enforced?
7. **Performance evaluation** — can the system meet Jetson resource limits?
8. **Longitudinal evaluation** — does Novi improve without accumulating harmful drift?
9. **Field evaluation** — does behavior remain reliable in real environments?

---

## 4. Memory Quality Model

Memory quality is multidimensional.

At minimum evaluate:

```text
correctness
relevance
retrievability
provenance completeness
freshness
consistency
uncertainty calibration
privacy compliance
retention correctness
forgetting correctness
conflict handling
knowledge usefulness
resource efficiency
```

A single score must not replace the individual metrics.

---

## 5. Retrieval Evaluation

Retrieval must be evaluated independently from generation.

Metrics may include:

- Recall@K;
- Precision@K;
- MRR;
- nDCG;
- hit rate;
- query latency;
- context completeness;
- irrelevant retrieval rate;
- stale retrieval rate;
- provenance coverage.

The exact metric set depends on the retrieval task.

A memory system that retrieves a plausible answer but omits the critical supporting memory has failed even if the language model produces fluent output.

---

## 6. Retrieval Test Cases

Protected retrieval datasets should include:

- exact factual queries;
- paraphrased queries;
- ambiguous queries;
- temporal queries;
- multi-hop queries;
- contradictory memories;
- stale memories;
- forgotten memories;
- privacy-restricted memories;
- sensor-grounded memories;
- episodic memories;
- semantic knowledge;
- negative queries where no memory should be returned.

Negative retrieval cases are essential to detect retrieval hallucination.

---

## 7. Memory Admission Evaluation

Evaluate whether the admission system correctly decides:

```text
retain
reject
provisionally retain
promote
request verification
```

Metrics should include:

- useful-memory precision;
- unnecessary-memory rate;
- missed-important-memory rate;
- duplicate rate;
- unsupported-claim rate;
- provenance completeness;
- privacy-policy violation rate.

---

## 8. Consolidation Evaluation

Consolidation should be evaluated for whether it:

- removes genuine duplication;
- preserves important distinctions;
- retains provenance;
- avoids semantic corruption;
- preserves uncertainty;
- does not merge incompatible people/objects/events;
- does not create unsupported generalizations;
- reduces storage without unacceptable information loss.

A smaller memory database is not automatically a better memory database.

---

## 9. Forgetting Evaluation

Forgetting must be evaluated as a controlled capability.

Measure:

- policy-compliant deletion rate;
- stale-memory removal rate;
- privacy deletion completeness;
- tombstone correctness;
- accidental retention rate;
- accidental deletion rate;
- resurrection rate after synchronization/recovery.

A successful deletion test must verify not only the canonical record but relevant derived representations.

---

## 10. Knowledge Promotion Evaluation

Knowledge promotion should be evaluated against protected ground truth or expert-reviewed datasets where possible.

Measure:

- promotion precision;
- promotion recall;
- unsupported generalization rate;
- contradiction rate;
- provenance completeness;
- confidence calibration;
- retraction correctness;
- update latency.

Repeated observations should not automatically become knowledge merely because they are repeated.

---

## 11. Provenance Evaluation

For important memories and knowledge claims, test whether Novi can answer:

> Why do you believe this?

Evaluation should verify traceability:

```text
knowledge
 ↓
memory
 ↓
observation
 ↓
measurement
 ↓
sensor/event
 ↓
calibration/health
```

Missing or broken provenance should be measurable and treated as a quality defect.

---

## 12. Confidence Calibration

Novi's confidence values must be evaluated against actual correctness.

A system that says:

```text
confidence = 0.95
```

should be correct approximately 95% of the time for the defined population and task, within the limits of the calibration method.

Calibration must be evaluated separately from raw accuracy.

Potential metrics include:

- reliability diagrams;
- expected calibration error;
- Brier score;
- calibration error by scenario;
- calibration under distribution shift.

No universal threshold should be assumed without empirical validation.

---

## 13. Contradiction Evaluation

Construct test cases where memory contains:

```text
A
A
A
B
```

and determine whether Novi:

- detects the contradiction;
- preserves evidence;
- lowers confidence when appropriate;
- identifies the source of disagreement;
- avoids inventing certainty;
- requests verification when required.

The contradiction rate should be tracked longitudinally.

---

## 14. Conflict Resolution Evaluation

The conflict resolver must have protected scenarios covering:

- concurrent updates;
- stale replicas;
- deletion races;
- sensor disagreement;
- user-vs-inference conflicts;
- model-version conflicts;
- schema-version conflicts;
- correlated evidence;
- offline divergence;
- malicious synchronization input.

Evaluate both the resolution and the reason for the resolution.

---

## 15. Longitudinal Learning Evaluation

Novi's defining requirement is continuous evolution.

Therefore evaluate memory across time:

```text
T0 → baseline
T1 → learning
T2 → learning
T3 → learning
...
```

Track whether learning causes:

- improved retrieval;
- improved personalization;
- improved prediction;
- reduced repeated mistakes;
- increased contradiction;
- memory bloat;
- confidence inflation;
- stale knowledge;
- personality drift;
- privacy regressions;
- new failure modes.

Improvement in one metric cannot justify regressions in critical metrics.

---

## 16. Regression Protection

Every significant memory-system change should run protected regression suites.

Examples:

```text
known memory query
→ expected memory remains retrievable

known deletion
→ deleted memory remains inaccessible

known conflict
→ same safe resolution

known provenance chain
→ remains intact
```

Protected tests should not be automatically modified by the adaptive system.

---

## 17. Golden Dataset

Novi should maintain versioned evaluation datasets containing:

- canonical memories;
- canonical queries;
- expected retrieval results;
- known contradictions;
- expected deletion behavior;
- expected provenance chains;
- expected conflict outcomes;
- safety-critical scenarios;
- privacy scenarios.

The dataset must be version controlled and changes must be reviewed.

---

## 18. Hidden Evaluation Set

A protected evaluation set should remain inaccessible to the learning system during development where practical.

This reduces the risk of overfitting the architecture to visible tests.

NIST's AITE work similarly emphasizes blind data and sequestered evaluation environments to reduce train/test contamination. citeturn0search2

---

## 19. Synthetic Evaluation

Synthetic scenarios are useful for systematically generating:

- contradictions;
- temporal conflicts;
- sensor failures;
- missing metadata;
- corrupted events;
- delayed events;
- duplicate events;
- privacy requests;
- storage failures;
- offline periods.

Synthetic evaluation must not replace real-world testing because simulation can omit important environmental behavior.

---

## 20. Real-Robot Evaluation

Physical evaluation must include:

- real sensors;
- real Jetson hardware;
- realistic latency;
- real power constraints;
- real thermal behavior;
- real sensor noise;
- real network loss;
- physical movement;
- human interaction.

Simulation and replay should complement, not replace, physical testing.

---

## 21. Replay Evaluation

Recorded sensor/event streams should be replayable deterministically where practical.

```text
recorded experience
       ↓
replay
       ↓
new memory system
       ↓
compare against baseline
```

This is especially useful for regression testing because the same physical experience can be evaluated across software/model versions.

---

## 22. Resource Evaluation on Jetson

Novi must measure memory performance under the actual target compute platform.

NVIDIA documents `tegrastats` for monitoring Jetson memory, CPU, GPU, temperature and related resource usage, and `nvpmodel` for power-mode control. These should be incorporated into performance evaluation rather than relying only on desktop development metrics. citeturn0search5

Track:

- RAM usage;
- GPU memory usage;
- CPU utilization;
- GPU utilization;
- inference latency;
- retrieval latency;
- indexing latency;
- embedding throughput;
- storage I/O;
- temperature;
- power consumption;
- thermal throttling;
- background workload impact.

---

## 23. Latency Budgets

Memory operations should have explicit latency classes.

Example categories:

```text
critical safety path
interactive response
normal retrieval
background consolidation
embedding/index maintenance
backup
long-term evaluation
```

Background evaluation must not starve real-time autonomy.

Exact budgets will be determined through prototype measurements.

---

## 24. Resource-Aware Evaluation

A memory algorithm that improves quality while making Novi unusable is not considered an unconditional improvement.

Evaluation therefore considers:

```text
quality gain
vs
CPU/GPU/RAM/storage/power/latency cost
```

Tradeoffs must be recorded explicitly.

---

## 25. Safety Evaluation

Memory failures can affect cognition and autonomy.

Test cases must verify that memory errors cannot directly bypass safety mechanisms.

Examples:

- incorrect object memory;
- stale obstacle memory;
- incorrect person identity;
- stale environmental state;
- corrupted knowledge;
- false confidence;
- unavailable memory service.

The system must fail safely when memory is unavailable or unreliable.

NIST's AI RMF recommends evaluating safety, robustness, response times and safe failure, with residual risk kept within defined tolerance. citeturn0search3

---

## 26. Privacy Evaluation

Test:

- retention periods;
- deletion requests;
- derived-memory deletion;
- embedding deletion;
- graph deletion;
- backup deletion policy;
- synchronized deletion;
- access control;
- unauthorized retrieval;
- privacy-mode behavior.

A memory test passes only if prohibited information cannot be recovered through an alternate representation covered by the applicable deletion policy.

---

## 27. Security Evaluation

Test:

- unauthorized memory writes;
- unauthorized reads;
- replayed synchronization commands;
- malicious memory records;
- corrupted backups;
- poisoned knowledge;
- malicious model outputs;
- provenance forgery;
- index poisoning;
- privilege escalation.

Security evaluation is separate from ordinary accuracy evaluation.

---

## 28. Benchmark Categories

Novi should maintain benchmarks for:

| Category | Primary objective |
|---|---|
| Retrieval | Find the right evidence |
| Admission | Keep useful information |
| Consolidation | Reduce redundancy safely |
| Forgetting | Remove what policy requires |
| Knowledge | Form valid abstractions |
| Provenance | Preserve evidence chains |
| Conflict | Resolve disagreement safely |
| Synchronization | Reconcile replicas |
| Recovery | Restore valid state |
| Privacy | Prevent prohibited retention/access |
| Performance | Meet resource/latency constraints |
| Longitudinal | Improve without harmful drift |

---

## 29. Benchmark Interpretation

Benchmark results must include:

- test version;
- software version;
- model versions;
- dataset version;
- hardware;
- configuration;
- random seeds where applicable;
- environment;
- sample size;
- uncertainty/confidence intervals where appropriate;
- known limitations;
- excluded cases.

NIST's recent benchmarking guidance warns against interpreting benchmark scores as universal measures of real-world performance; Novi therefore requires contextual interpretation and complementary field testing. citeturn0search27

---

## 30. Statistical Rigor

Where sample sizes support it, evaluations should report uncertainty rather than only point estimates.

Examples:

```text
Recall@10 = 0.94 ± interval

Latency p50 = ...
Latency p95 = ...
Latency p99 = ...
```

The exact statistical method depends on the metric and evaluation design.

Small datasets must not be presented as highly precise measurements.

---

## 31. Human Evaluation

Some memory qualities require human assessment.

Examples:

- usefulness;
- naturalness of personalization;
- appropriateness of retrieved context;
- whether a consolidated memory preserves meaning;
- whether an explanation accurately represents evidence.

Human evaluation protocols should define:

- evaluator instructions;
- sampling;
- rating scales;
- disagreement handling;
- evaluator qualifications where required;
- blinded comparisons where practical.

NIST ARIA demonstrates the value of combining model testing, human testing, red-teaming and field evaluation for AI-system assessment. citeturn0search12turn0search26

---

## 32. Field Evaluation

Field evaluation should observe Novi under realistic conditions.

Measure:

- real retrieval usefulness;
- memory errors;
- user corrections;
- repeated failures;
- latency;
- sensor degradation;
- environmental variation;
- offline periods;
- recovery events;
- resource pressure.

Field data must not automatically become evaluation ground truth.

It must be curated and governed.

---

## 33. Distribution Shift

Novi's environment will change.

Evaluate across:

- new rooms;
- new lighting;
- different acoustics;
- new people;
- sensor aging;
- hardware replacements;
- software updates;
- model updates;
- seasonal/environmental changes.

A system that performs well in the development environment but degrades elsewhere must be recognized as such.

---

## 34. Catastrophic Memory Failure Tests

Explicitly test:

```text
empty database
corrupt index
corrupt embedding store
partial database
missing provenance
stale backup
conflicting backup
power loss during write
power loss during consolidation
storage full
sensor metadata loss
schema migration interruption
```

The expected recovery behavior must be defined before implementation.

---

## 35. Memory Poisoning Tests

Test whether repeated false information can manipulate long-term knowledge.

Example:

```text
false claim
 ↓ repeated
false claim
 ↓ repeated
false claim
 ↓
knowledge promotion
```

Novi should resist frequency-only poisoning.

Evidence diversity, provenance quality and verification should matter.

---

## 36. Personality and Memory Evaluation

Because Novi is intended to have personality, evaluation should distinguish:

```text
personality consistency
vs
memory correctness
```

Personality adaptation must not be allowed to justify factual memory corruption.

Changes to personality-related state should be evaluated for:

- consistency;
- user alignment;
- unwanted drift;
- manipulation resistance;
- privacy;
- stability.

---

## 37. Self-Evaluation Boundaries

Novi may:

- collect telemetry;
- propose evaluation cases;
- identify suspicious regressions;
- recommend tests;
- compare current behavior to approved baselines;
- flag uncertainty.

Novi may not unilaterally:

- redefine acceptance thresholds;
- delete failing tests;
- rewrite golden datasets;
- declare safety tests obsolete;
- certify its own unsafe behavior;
- suppress negative evaluation results.

This is essential for safe continuous evolution.

---

## 38. Release Gates

A memory-system change should not ship solely because aggregate quality improved.

A release gate should evaluate at least:

```text
functional correctness
safety
privacy
security
provenance
regression
performance
resource usage
longitudinal impact
```

Critical threshold failures block release regardless of gains elsewhere.

---

## 39. Baselines

Every meaningful experiment should compare against a baseline.

Baseline examples:

- previous production version;
- deterministic retrieval baseline;
- simple ranking baseline;
- previous memory policy;
- known-good hardware configuration.

Without a baseline, claims of improvement are weak.

---

## 40. A/B and Controlled Experiments

Where safe and practical, compare:

```text
baseline
vs
candidate
```

using the same evaluation set and controlled conditions.

Candidate changes should not be promoted based on anecdotal success alone.

---

## 41. Benchmark Contamination

Evaluation data must be protected from accidental training or memory ingestion.

Novi must not permanently learn the answers to its protected evaluation suite.

If an evaluation case enters the operational memory, it must be marked and excluded from future independent evaluation datasets.

---

## 42. Evaluation Artifacts

Each evaluation run should produce a durable artifact containing:

- run ID;
- timestamp;
- software commit;
- model versions;
- configuration;
- hardware;
- dataset versions;
- metrics;
- failures;
- logs;
- resource measurements;
- evaluator information where applicable;
- conclusion;
- approval status.

Artifacts must be immutable after finalization except through explicit correction procedures.

---

## 43. Evaluation Dashboard

A future dashboard should show trends for:

```text
Memory Quality
Retrieval Quality
Knowledge Quality
Conflict Rate
Deletion Correctness
Provenance Coverage
Latency
RAM/GPU
Power
Thermal State
Safety Failures
Privacy Failures
Longitudinal Drift
```

Trend visualization must distinguish statistical noise from meaningful regression.

---

## 44. Evaluation Frequency

Different evaluation classes have different cadences.

```text
unit tests                 → every change
regression suite           → every relevant change
resource benchmark         → relevant performance changes
full memory benchmark     → release candidates
security/privacy suite     → every relevant release
field evaluation           → continuous/periodic
longitudinal evaluation    → scheduled
recovery drill             → scheduled
```

Exact frequencies should be defined after operational experience exists.

---

## 45. Acceptance Thresholds

Initial thresholds should be classified as:

```text
BLOCKING
WARNING
INFORMATIONAL
```

Do not invent arbitrary numerical thresholds before baseline measurements exist.

The first prototype phase should establish empirical baselines, followed by reviewed thresholds.

Safety and privacy thresholds may be blocking from the beginning where justified by risk.

---

## 46. Evaluation and Continuous Learning

The learning loop is:

```text
experience
   ↓
memory
   ↓
learning
   ↓
new behavior
   ↓
evaluation
   ↓
approved improvement
   ↓
new baseline
```

Evaluation must occur outside the learning mechanism sufficiently to prevent self-reinforcing measurement bias.

---

## 47. Failure Classification

Failures should be classified as:

- data failure;
- perception failure;
- memory admission failure;
- retrieval failure;
- consolidation failure;
- provenance failure;
- knowledge failure;
- synchronization failure;
- conflict-resolution failure;
- privacy failure;
- security failure;
- resource failure;
- hardware/sensor failure;
- evaluation failure.

This prevents all failures from being incorrectly attributed to the LLM.

---

## 48. Evaluation of the Whole Robot

Memory must ultimately be evaluated by whether it improves the robot's real tasks.

Examples:

```text
Can Novi remember a user's preference?
Can Novi retrieve the right past experience?
Can Novi avoid repeating a known mistake?
Can Novi recognize that a memory is uncertain?
Can Novi forget information when required?
Can Novi recover after power loss?
Can Novi operate offline?
Can Novi avoid acting on stale knowledge?
```

Memory quality is therefore a system property, not merely a database property.

---

## 49. Architecture for Evaluation

```text
                     NOVI
                      │
              operational system
                      │
               telemetry/events
                      │
               Evaluation Layer
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
     Metrics       Test Data      Oracles
        │             │             │
        └─────────────┼─────────────┘
                      ▼
                Evaluation Run
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
     Baseline       Candidate     Risk Review
        │             │             │
        └─────────────┼─────────────┘
                      ▼
               Release Decision
```

---

## 50. Architectural Invariants

1. Evaluation is continuous, not one-time.
2. Benchmark scores are not sufficient evidence of real-world improvement.
3. Protected evaluation data must remain independent from operational learning where practical.
4. Novi cannot redefine its own acceptance criteria.
5. Critical safety/privacy regressions block release even when aggregate quality improves.
6. Retrieval must be evaluated independently from generation.
7. Provenance completeness is measurable.
8. Forgetting and deletion correctness are measurable.
9. Confidence calibration is evaluated separately from accuracy.
10. Resource consumption is part of system quality on Jetson.
11. Synthetic tests complement but do not replace physical evaluation.
12. Field evaluation complements but does not replace controlled regression testing.
13. Evaluation artifacts are versioned and auditable.
14. Longitudinal evaluation is required because Novi continuously evolves.
15. Personality evolution must not corrupt factual memory.
16. Derived indexes cannot hide canonical-memory failures.
17. The evaluation system itself must be tested.
18. Self-evaluation cannot be the sole authority for safety or release decisions.

---

## 51. Cross-Validation Basis

The architecture is grounded in multiple independent evaluation traditions:

- **NIST AI RMF / AIRC:** continuous measurement, documented TEVV, validity, reliability, safety, robustness and contextual evaluation. citeturn0search0turn0search3turn0search11
- **NIST ARIA:** model testing, red-teaming, human testing and field testing as complementary evaluation layers. citeturn0search12turn0search26
- **NIST benchmark guidance:** benchmark results require contextual interpretation and should not automatically be treated as evidence of general real-world performance. citeturn0search27
- **NVIDIA Jetson documentation:** target-hardware resource, thermal and power measurements should use platform-aware telemetry such as `tegrastats` and power-mode information from `nvpmodel`. citeturn0search5
- **Robotics benchmarking literature:** robot evaluation requires attention to safety, human context, task conditions and methodological consistency rather than relying on a single universal metric. citeturn0academia25

These sources support the evaluation principles; they do not dictate a final Novi-specific metric set. Novi's final thresholds must be established through controlled experiments on the actual hardware and workloads.

---

## 52. Final Principle

> **Novi's ability to learn is only as trustworthy as our ability to measure whether learning made it better.**

The evaluation system therefore becomes part of Novi's architecture itself. It protects against memory drift, confidence inflation, benchmark gaming, privacy regression, resource exhaustion and silent degradation while allowing genuine improvements to accumulate.

Continuous evolution without independent measurement is uncontrolled drift. Continuous evolution with protected evaluation, explicit boundaries and repeatable evidence becomes engineering.
