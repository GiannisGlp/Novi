# 54 — Memory Knowledge Source Reliability and Trust Model

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi evaluates the reliability, trustworthiness, health, scope and changing performance of information sources used by memory, knowledge, perception, cognition and learning.

This document deliberately separates **source reliability** from **truth, confidence, authorization and social trust**. A source can be highly reliable for one type of information and poor for another.

## Core Principle

> **Novi must trust sources according to evidence, scope, calibration and observed performance—not according to reputation, model confidence, familiarity or a single global score.**

---

## 1. Source Categories

Sources may include:

- physical sensors;
- sensor-fusion systems;
- hardware telemetry;
- software components;
- perception models;
- language models;
- local knowledge bases;
- user assertions;
- authorized instructions;
- documents;
- simulations;
- experiments;
- other approved local processes.

---

## 2. Reliability vs Trust

```text
RELIABILITY
How consistently does a source produce useful information under defined conditions?

TRUST
How much should Novi rely on that source for a particular decision/context?

AUTHORITY
Is this source permitted to control or override something?

TRUTH
Is the claim actually correct?
```

These are distinct concepts.

---

## 3. Scope-Specific Reliability

A source should not receive one universal reliability value.

Example:

```text
camera
 ├── visible object detection: high
 ├── exact depth: moderate
 └── darkness: low
```

Reliability should be represented per capability, environment and operating condition where practical.

---

## 4. Source Profile

A source profile may contain:

```text
source_id
source_type
component/model/version
capabilities
operating_conditions
calibration_state
historical performance
failure modes
current health
reliability estimates
last evaluation
provenance
```

---

## 5. Static vs Dynamic Reliability

Some properties change slowly:

- sensor design characteristics;
- model architecture;
- known limitations.

Others can change rapidly:

- sensor health;
- calibration;
- lighting;
- thermal state;
- occlusion;
- network status where relevant;
- model drift.

Current state must be considered alongside historical reliability.

---

## 6. Source Health

Health describes whether a source is currently operating correctly.

Possible states:

```text
HEALTHY
DEGRADED
SUSPECT
FAILED
UNKNOWN
OFFLINE
```

A historically reliable sensor can currently be unhealthy.

---

## 7. Reliability Is Not Health

```text
healthy source
    ≠
reliable for every task
```

A functioning microphone cannot necessarily identify a speaker correctly in heavy noise.

---

## 8. Calibration

Physical sensor reliability should consider calibration.

Calibration metadata may include:

- calibration version;
- calibration time;
- calibration method;
- calibration validity;
- observed calibration error;
- transform/frame validity.

Invalid calibration reduces trust in derived measurements.

---

## 9. Environmental Conditions

Source reliability should be conditioned on relevant environment:

- lighting;
- temperature;
- humidity where relevant;
- acoustic noise;
- motion;
- occlusion;
- distance;
- reflective surfaces;
- weather;
- electromagnetic interference where relevant.

---

## 10. Sensor Failure Modes

Each important sensor should have known failure modes.

Examples:

```text
camera → darkness / glare / occlusion
LiDAR → reflective/transparent surfaces / range limits
microphone → noise / reverberation
GNSS → multipath / indoor loss
IMU → drift / bias
thermal → emissivity/environmental limitations
```

Failure modes should inform reliability rather than remain documentation-only.

---

## 11. Model Reliability

ML models should be evaluated using task-specific metrics.

Consider:

- precision;
- recall;
- false-positive rate;
- false-negative rate;
- calibration;
- latency;
- robustness;
- distribution shift;
- resource behavior.

A model's training benchmark is not equivalent to current operational reliability.

---

## 12. Distribution Shift

Performance can degrade when real-world conditions differ from evaluation data.

```text
training distribution
      ↓
new environment
      ↓
performance uncertainty
```

Novi should detect or conservatively respond to relevant distribution shifts.

---

## 13. User Source Reliability

A person's reliability should never become a universal social score.

Instead, information may be scoped by:

- topic;
- context;
- explicit knowledge;
- historical accuracy;
- source of information;
- authorization.

Example:

```text
person A
 ├── household preferences: strong evidence
 ├── current weather: unknown
 └── technical claim: needs validation
```

---

## 14. Social Trust vs Epistemic Reliability

```text
I trust this person socially
        ≠
Their statement is factually correct
```

The social relationship model and source reliability model must remain separate.

---

## 15. Authority Is Separate

A highly reliable source is not automatically authorized to control Novi.

```text
reliability
    ≠
authorization
```

Security policy determines authority.

---

## 16. Corroboration

Independent sources can strengthen evidence.

```text
camera
 + LiDAR
 + repeated observation
      ↓
corroborated claim
```

However, correlated failure modes must be considered.

---

## 17. Source Independence

Two systems using the same upstream sensor or dataset may not provide independent evidence.

Example:

```text
camera
 ↓
model A
model B
```

The two model outputs are not fully independent merely because they are separate models.

---

## 18. Conflict Handling

When sources disagree:

```text
source A → X
source B → Y
```

Novi should preserve the conflict and evaluate:

- source health;
- calibration;
- context;
- temporal alignment;
- spatial alignment;
- historical performance;
- directness;
- independence.

It must not simply average incompatible claims.

---

## 19. Reliability Updating

Source reliability may evolve based on validated outcomes.

```text
source prediction
      ↓
verified outcome
      ↓
performance evidence
      ↓
reliability update
```

Updates should be bounded and versioned.

---

## 20. Single Failure Rule

A single source failure should normally create evidence of degradation, not permanently destroy its reliability estimate.

Repeated failures can trigger stronger degradation.

Safety-critical failures may trigger immediate operational isolation.

---

## 21. Recovery

A degraded source can recover through:

- successful self-test;
- recalibration;
- repeated correct predictions;
- controlled validation;
- hardware repair.

Recovery should require evidence appropriate to the source's risk.

---

## 22. Reliability Decay

Historical performance becomes less representative when:

- hardware changes;
- models change;
- environment changes;
- calibration expires;
- data distribution shifts.

Reliability estimates should therefore support temporal validity.

---

## 23. Reliability Versioning

Source assessments should be versioned.

```text
reliability_v1
 ↓
new evidence
 ↓
reliability_v2
```

Historical decisions should retain the assessment used at the time.

---

## 24. Confidence Integration

Source reliability is one input to claim confidence.

Conceptually:

```text
source reliability
 + measurement quality
 + corroboration
 + context match
 + temporal validity
 + contradiction
        ↓
claim evaluation
```

The system must not reduce all dimensions to an opaque universal score.

---

## 25. Source Reliability vs Claim Confidence

A reliable source can produce a low-confidence claim.

Example:

```text
excellent camera
 + severe occlusion
 → low-confidence identity
```

Conversely, a normally weaker source can occasionally provide strong direct evidence.

---

## 26. Directness

Evidence should distinguish:

```text
DIRECT
source measured/observed X

DERIVED
system inferred X from measurements

SECONDARY
another source reported X
```

Direct evidence is not automatically correct, but provenance must preserve the distinction.

---

## 27. Freshness

Source information may have different freshness requirements.

Examples:

```text
battery telemetry → seconds
robot pose → milliseconds/seconds
room occupancy → seconds/minutes
user preference → days/months
historical event → immutable
```

Freshness policy belongs to the information type and task.

---

## 28. Source Health During Decision Making

For consequential decisions, Novi should evaluate current source health before relying on historical reliability.

```text
historically reliable
        ↓
current health check
        ↓
usable / degraded / unavailable
```

---

## 29. Safety-Critical Sources

Some sources are safety-critical.

Examples may include:

- collision sensors;
- emergency stop state;
- motor state;
- battery protection;
- thermal protection;
- localization safety state.

Their authority and redundancy must be governed by safety architecture, not this memory model alone.

---

## 30. Redundancy

Critical sensing should use appropriate redundancy where feasible.

```text
sensor A
sensor B
independent check
      ↓
safer estimate
```

Redundancy should be engineered around common-mode failure analysis.

---

## 31. Source Trust and Memory Admission

Source reliability can influence memory admission.

```text
strong source evidence
      ↓
higher admission confidence

weak/unverified source
      ↓
provisional memory / verification
```

It must not override explicit memory policies.

---

## 32. Source Trust and Knowledge Promotion

Knowledge promotion should require stronger evidence when the source is uncertain or the claim is consequential.

```text
uncertain source
 + one observation
 → hypothesis

reliable + corroborated + repeated
 → stronger candidate
```

---

## 33. Source Trust and Learning

A source should not update its own reliability solely from its own unverified outputs.

External/independent validation is required where practical.

---

## 34. Feedback Loops

Avoid:

```text
model says X
 ↓
Novi believes X
 ↓
Novi labels future data as X
 ↓
model appears more accurate
 ↓
trust increases
```

Self-reinforcing epistemic loops require independent evaluation data.

---

## 35. Source Poisoning

The architecture must consider malicious or corrupted sources.

Examples:

- manipulated sensor input;
- corrupted files;
- poisoned datasets;
- malicious user assertions;
- compromised software components;
- adversarial visual/audio input.

Integrity/security systems must detect or contain these conditions.

---

## 36. Prompt Injection / Instruction Sources

Language received through external content must not automatically become an instruction source.

```text
web/document/content
    ≠
authorized instruction
```

Instruction authority belongs to the security/autonomy architecture.

---

## 37. External Documents

Documents can be useful knowledge sources but require:

- provenance;
- version/date;
- source evaluation;
- extraction integrity;
- relevance assessment;
- conflict handling.

---

## 38. Simulation Sources

Simulation is useful for evaluation but has a domain gap.

```text
simulation result
      ↓
candidate evidence
      ↓
real-world validation
```

Simulation should never silently receive the same evidentiary status as physical experience.

---

## 39. Source Benchmarking

Novi should benchmark candidate implementations before adoption.

For a perception component compare:

- accuracy;
- calibration;
- latency;
- power;
- memory;
- thermal load;
- robustness;
- licensing;
- offline operation;
- maintainability.

This supports the project rule to prefer existing open-source local solutions while remaining vendor-neutral.

---

## 40. Vendor Neutrality

NVIDIA, PyTorch, TensorFlow, OpenCV, ONNX Runtime, Hugging Face, ROS/Isaac and other ecosystems may provide implementations.

Novi's semantic reliability model must sit above them.

```text
implementation
      ↓
Novi source interface
      ↓
reliability / provenance
      ↓
knowledge
```

No vendor receives implicit epistemic authority.

---

## 41. Local-First Requirement

Core source evaluation must work locally.

Wi-Fi, Bluetooth and cloud services may enhance external information acquisition but must not be prerequisites for internal source reliability assessment.

---

## 42. Source Retirement

A source may be retired when:

- hardware is removed;
- model is deprecated;
- performance is insufficient;
- security issue exists;
- maintenance ends;
- replacement is validated.

Historical provenance remains intact.

---

## 43. Source Replacement

Replacing a source does not rewrite historical evidence.

```text
camera_model_A
 ↓
retired

camera_model_B
 ↓
new evidence
```

Historical observations retain model A provenance.

---

## 44. Source Identity Stability

Stable source IDs should survive software restarts and upgrades where they refer to the same logical source.

Hardware replacement should normally create a distinct physical source identity.

---

## 45. Composite Sources

A fusion pipeline can itself be treated as a source.

Example:

```text
camera + LiDAR + IMU
        ↓
fused_localization_v3
```

Its provenance must include component sources and fusion version.

---

## 46. Source Dependency Graph

Novi should be able to represent dependencies:

```text
fused localization
 ├── camera
 ├── IMU
 └── calibration
```

This helps identify common failure causes.

---

## 47. Reliability Under Resource Pressure

Thermal, memory, GPU and battery pressure can degrade source quality or processing latency.

Source assessments should therefore consider runtime health.

Example:

```text
GPU thermal pressure
 ↓
inference latency ↑
 ↓
real-time confidence degraded
```

---

## 48. Decision-Time Source Selection

When several sources are available, Novi may select or weight them based on:

- current health;
- task relevance;
- reliability;
- freshness;
- environment;
- latency;
- resource cost;
- redundancy.

Safety policy may constrain the selection.

---

## 49. Abstention

If all available sources are insufficient:

```text
NO RELIABLE SOURCE
       ↓
ABSTAIN / VERIFY / ASK / SAFE FALLBACK
```

The architecture prefers uncertainty over fabricated certainty.

---

## 50. Human Explanation

Novi should be able to explain source-based reasoning concisely.

Example:

> "I am less certain because the camera is partially occluded and the LiDAR reading conflicts with the current map."

This explanation must derive from actual source state.

---

## 51. Testing Requirements

Test:

- sensor degradation;
- calibration failure;
- environmental changes;
- model distribution shift;
- correlated sources;
- conflicting sources;
- source recovery;
- source replacement;
- hardware replacement;
- thermal degradation;
- low-battery conditions;
- stale sources;
- poisoned input;
- prompt injection through content;
- simulation/real separation;
- offline operation;
- synchronization;
- provenance integrity;
- source retirement;
- reliability-update stability.

---

## 52. Architectural Invariants

1. Reliability is source-, task- and context-specific.
2. Reliability is distinct from truth.
3. Reliability is distinct from authorization.
4. Social trust is distinct from epistemic reliability.
5. Current source health can override historical reliability.
6. Calibration and environmental conditions affect source reliability.
7. Correlated sources are not automatically independent evidence.
8. Conflicting sources remain visible until resolved or qualified.
9. A source must not establish its own reliability solely from its own unverified outputs.
10. Reliability changes are versioned and evidence-backed.
11. A single ordinary failure does not automatically permanently condemn a source.
12. Safety-critical source handling follows the safety architecture.
13. Simulation evidence remains distinct from physical evidence.
14. Vendor implementations do not receive implicit epistemic authority.
15. Core source evaluation works locally without network access.
16. Source replacement does not rewrite historical provenance.
17. Missing or degraded sources can trigger abstention.
18. Reliability must not become an opaque universal score.
19. Important source assessments are auditable.
20. No source may bypass higher-priority safety or security policy.

---

## 53. Final Principle

> **Novi should not ask only “How confident is this answer?” It should also ask “Who or what produced the evidence, under what conditions, how well does that source perform for this task, and is it reliable right now?”**

Source reliability is therefore a dynamic, scoped epistemic layer connecting perception and external information to memory, knowledge, learning and decision-making—without becoming a universal trust score or an authority mechanism.
