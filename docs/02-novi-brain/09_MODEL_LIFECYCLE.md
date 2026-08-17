# 09 — Novi Model Lifecycle

**Status:** P0 — critical architecture specification  
**Version:** 0.1  
**Scope:** Lifecycle of every learned model, policy, embedding model, foundation model, world model, speech model and optimized inference artifact used by Novi.

---

# 1. Purpose

A model is not simply a file that Novi loads.

Every learned component has a lifecycle that begins with selection or training and continues through evaluation, packaging, deployment, operation, monitoring, rollback, retirement and archival.

This document defines that lifecycle so that Novi can evolve without losing reproducibility, safety, provenance or behavioral continuity.

The lifecycle must work for:

- perception models;
- speech models;
- embedding/retrieval models;
- VLMs and LLMs;
- world/predictive models;
- VLA/robot policies;
- learned specialist controllers;
- rerankers/classifiers;
- personalization models;
- optimized inference engines.

The lifecycle does **not** assume that every model is trained by Novi. Most early Novi models should be externally developed and integrated through this lifecycle.

---

# 2. Core principle

> **No model becomes part of Novi's trusted runtime merely because it works in a demonstration.**

A candidate must pass explicit gates before promotion.

```text
IDENTIFY
   ↓
PROVENANCE
   ↓
EVALUATE
   ↓
PACKAGE
   ↓
COMPATIBILITY TEST
   ↓
SECURITY / LICENSE REVIEW
   ↓
RESOURCE BENCHMARK
   ↓
SIMULATION / OFFLINE VALIDATION
   ↓
CONTROLLED DEPLOYMENT
   ↓
MONITOR
   ↓
PROMOTE / HOLD / ROLLBACK
   ↓
RETIRE / ARCHIVE
```

The lifecycle is independent of whether the model comes from NVIDIA, an open-source project, a research paper, a commercial provider or Novi-specific training.

---

# 3. Model states

Every model artifact must have an explicit lifecycle state.

```text
DISCOVERED
    ↓
CANDIDATE
    ↓
ASSESSED
    ↓
VALIDATED
    ↓
PACKAGED
    ↓
STAGED
    ↓
SHADOW
    ↓
CANARY
    ↓
PRODUCTION
    ↓
DEPRECATED
    ↓
RETIRED
    ↓
ARCHIVED
```

A model may move backward when evidence invalidates an earlier decision.

For example:

```text
PRODUCTION
    ↓ regression discovered
HOLD / ROLLBACK
```

No lifecycle transition should be implicit.

---

# 4. Model identity

Every model must have an immutable identity independent of its deployment location.

At minimum:

```yaml
model_id:
model_version:
artifact_digest:
model_family:
model_type:
source:
source_revision:
license:
created_at:
validated_at:
owner:
status:
```

`model_id` identifies the logical model lineage.

`model_version` identifies a particular release of that lineage.

`artifact_digest` identifies the exact bytes being deployed.

This distinction is critical: a URL, repository tag or filename is not sufficient to identify the exact executable artifact.

---

# 5. Provenance

Novi must be able to answer:

> Where did this model come from, what happened to it, and exactly what is running right now?

Provenance should capture, where applicable:

- upstream project;
- repository and revision;
- model publisher;
- model card/documentation;
- training or post-training information;
- dataset provenance where available;
- license;
- conversion process;
- quantization process;
- pruning/distillation;
- adapter/LoRA version;
- tokenizer/preprocessor version;
- runtime version;
- optimization engine version;
- build environment;
- hardware target;
- cryptographic digest.

Unknown provenance must be represented as unknown, not inferred.

---

# 6. Candidate intake

A model enters Novi as a **candidate**, not as a trusted dependency.

Candidate intake must record:

1. capability being addressed;
2. reason Novi needs the capability;
3. current baseline;
4. expected improvement;
5. model source;
6. license;
7. supported modalities;
8. input/output contract;
9. known limitations;
10. hardware requirements;
11. runtime requirements;
12. security considerations;
13. evidence supporting adoption.

The candidate must have a clearly defined Novi task.

"This is a powerful model" is not an adoption reason.

---

# 7. Functional validation

The first technical gate asks whether the model actually performs the required task.

Validation must use a Novi-owned benchmark where possible.

Metrics depend on capability.

Examples:

### Vision

- precision/recall;
- mAP where appropriate;
- segmentation quality;
- depth error;
- tracking stability;
- false positive/negative rates.

### Speech

- word error rate;
- streaming latency;
- endpointing behavior;
- noisy-environment performance.

### Reasoning

- task success;
- groundedness;
- structured-output validity;
- contradiction handling;
- tool-use correctness;
- uncertainty behavior.

### Robot policy

- task success rate;
- collision rate;
- intervention rate;
- recovery rate;
- trajectory quality;
- generalization.

A model must not be promoted based solely on a vendor benchmark unrelated to Novi's operating distribution.

---

# 8. Safety validation

Safety validation is separate from functional quality.

A model can be highly accurate and still be unsuitable for physical autonomy.

Safety evaluation must consider:

- unsafe outputs;
- worst-case behavior;
- confidence calibration;
- out-of-distribution behavior;
- stale input handling;
- malformed output;
- adversarial input;
- prompt injection where applicable;
- sensor spoofing assumptions;
- physical consequences;
- failure and timeout behavior.

A learned component must never be granted safety authority merely because its confidence is high.

---

# 9. Compatibility validation

A model must be compatible with the exact Novi runtime in which it will operate.

Compatibility includes:

- operating system;
- CPU architecture;
- GPU architecture;
- CUDA version where applicable;
- driver requirements;
- framework version;
- TensorRT/runtime version;
- ROS 2 integration where applicable;
- tokenizer/preprocessor;
- input tensor schema;
- output schema;
- precision;
- memory requirements.

NVIDIA's TensorRT documentation explicitly treats serialized engines as version-sensitive artifacts; plan/engine reuse can require compatible TensorRT versions, and compatibility should therefore be validated rather than assumed. citeturn0search0turn0search4

For this reason, a TensorRT engine is a **deployment artifact**, not the canonical source model.

The canonical model and the exact optimized artifact must both be tracked.

---

# 10. Optimization lifecycle

Optimization is itself a transformation and must be reproducible.

A typical NVIDIA deployment path is:

```text
trained model
    ↓
export
    ↓
ONNX / supported representation
    ↓
precision selection
    ↓
TensorRT build
    ↓
optimized engine
    ↓
benchmark
    ↓
deployment
```

NVIDIA documents this export → precision → conversion → deployment workflow for TensorRT. citeturn0search6turn0search8

Every transformation must record:

- source artifact digest;
- transformation tool/version;
- configuration;
- precision;
- calibration data/version where applicable;
- target hardware;
- resulting artifact digest;
- benchmark results.

The transformation must be reproducible from controlled inputs.

---

# 11. Resource validation

Before deployment, measure the model on representative hardware.

At minimum:

- cold-start latency;
- warm latency;
- throughput;
- p50/p95/p99 latency where meaningful;
- CPU usage;
- GPU usage;
- RAM;
- VRAM;
- power;
- thermal impact;
- concurrency;
- startup time;
- storage footprint.

NVIDIA explicitly recommends measuring latency and throughput on the target model and hardware rather than assuming performance from generic results. citeturn0search1

For Novi, resource cost is part of model quality because an apparently excellent model that starves perception or interaction is not an acceptable production model.

---

# 12. Simulation validation

Physical-action models must first be validated in simulation whenever practical.

The sequence should be:

```text
offline dataset
      ↓
unit / functional tests
      ↓
simulation
      ↓
scenario evaluation
      ↓
stress / adversarial evaluation
      ↓
hardware-in-the-loop where appropriate
      ↓
controlled physical test
```

The simulation environment must use the same or explicitly versioned interfaces as the target runtime.

Simulation success does not prove real-world safety.

---

# 13. Shadow deployment

A new model may first run in **shadow mode**.

In shadow mode:

```text
production model → authoritative result
candidate model  → observes same input
                 → produces comparison only
```

The candidate must not control the robot.

This enables comparison of:

- accuracy;
- latency;
- disagreement;
- confidence;
- resource consumption;
- failure behavior.

Shadow results become part of the promotion evidence.

---

# 14. Canary deployment

After shadow validation, a model may enter canary operation.

Canary deployment must be constrained by:

- scenario;
- capability;
- duration;
- workload;
- physical operating area;
- maximum autonomy level;
- rollback trigger.

For physical policies, the canary must use bounded environments and explicit intervention capability.

---

# 15. Production promotion gate

A model becomes `PRODUCTION` only when all required gates pass.

Recommended gate record:

```yaml
functional_validation: PASS
safety_validation: PASS
compatibility_validation: PASS
resource_validation: PASS
security_review: PASS
license_review: PASS
simulation_validation: PASS
shadow_validation: PASS
canary_validation: PASS
rollback_verified: PASS
observability_ready: PASS
owner_approved: true
adr_reference:
```

Not every model requires every gate, but every skipped gate must have an explicit reason.

---

# 16. Deployment manifest

The deployment manifest must bind the logical model to its executable artifact.

Example:

```yaml
model_id: novi.person_detector
model_version: 1.4.0
artifact_digest: sha256:...
source_model:
  format: onnx
  digest: sha256:...
engine:
  runtime: tensorrt
  version: "11.x"
  precision: fp16
hardware:
  architecture: "validated-target"
contract:
  input_schema: person_detector.v2
  output_schema: detections.v3
limits:
  max_latency_ms: 40
  max_vram_mb: 1200
status: production
rollback_to: 1.3.2
```

Exact schema will be defined by the model runtime/deployment documents later in this directory.

---

# 17. Runtime monitoring

Production models must be continuously observable.

Monitor:

### Availability

- startup failures;
- crashes;
- timeouts;
- queue saturation;
- unavailable dependencies.

### Performance

- latency;
- throughput;
- resource consumption;
- thermal effects.

### Quality

Where measurable:

- confidence distributions;
- error rates;
- drift indicators;
- disagreement with other sensors/models;
- task success.

### Behavioral safety

- rejected actions;
- abnormal outputs;
- intervention events;
- safety-triggered fallback;
- repeated failures.

The monitoring system must not depend exclusively on the model being monitored.

---

# 18. Drift

Novi must distinguish several forms of drift:

```text
DATA DRIFT
    input distribution changes

CONCEPT DRIFT
    relationship between input and desired output changes

ENVIRONMENT DRIFT
    physical environment changes

MODEL DRIFT
    deployed model/runtime behavior changes

SYSTEM DRIFT
    surrounding software/hardware changes
```

A model may be unchanged while its effective behavior changes because the environment or surrounding system changed.

Drift indicators should trigger evaluation, not automatic retraining or automatic promotion.

---

# 19. Rollback

Rollback must be designed before promotion.

A rollback must identify:

- previous known-good version;
- compatible runtime;
- compatible preprocessing;
- compatible output schema;
- state migration requirements;
- rollback trigger;
- operator/automation authority.

For physical-action models, rollback must leave the robot in a safe executable state.

A rollback that requires a network connection when the system is designed to operate offline is not an acceptable core recovery mechanism.

---

# 20. Model replacement and identity continuity

Replacing a model must not replace Novi's identity.

```text
Model A
   ↓ replacement
Model B

Novi identity ─────────────── remains
Memories ──────────────────── remain
Goals ─────────────────────── remain
Relationships ─────────────── remain
Protected policies ────────── remain
```

Historical records must retain the model version that produced them.

This is essential for debugging and scientific reproducibility.

---

# 21. Learning lifecycle

If Novi eventually creates its own model update:

```text
experience/data
      ↓
dataset admission
      ↓
data validation
      ↓
training / fine-tuning / post-training
      ↓
held-out evaluation
      ↓
safety evaluation
      ↓
resource benchmark
      ↓
simulation / shadow / canary
      ↓
promotion
```

Production runtime should not silently update model weights from individual experiences.

---

# 22. Dataset lineage

Any model trained by Novi must link back to the data used to train it.

Track:

- dataset ID;
- dataset version;
- source;
- collection period;
- consent/authorization where applicable;
- filtering;
- preprocessing;
- labeling version;
- train/validation/test split;
- synthetic-data provenance;
- augmentation configuration.

A model without sufficient training-data lineage should be treated as lower-confidence research infrastructure.

---

# 23. Security and supply chain

Model artifacts are executable trust dependencies.

The lifecycle must therefore include:

- cryptographic digests;
- trusted source records;
- artifact integrity checks;
- dependency scanning;
- container/image provenance where applicable;
- signed release metadata where supported;
- controlled artifact storage;
- least-privilege runtime access.

Downloaded model files must never be trusted solely because their filename or publisher name looks correct.

---

# 24. Version compatibility

Novi must version the complete inference contract, not only the neural weights.

At minimum:

```text
model
+ tokenizer
+ preprocessing
+ postprocessing
+ schema
+ runtime
+ optimization engine
+ configuration
```

A model update that changes output semantics is a contract change even if the model name remains the same.

NVIDIA's TensorRT documentation explicitly documents semantic versioning for public APIs while warning that serialized engine compatibility is more constrained. citeturn0search0turn0search10

Therefore Novi should never infer deployment compatibility from semantic version numbers alone.

---

# 25. Retirement

A model should be retired when:

- a better validated replacement exists;
- the model becomes unsupported;
- security concerns emerge;
- runtime compatibility is lost;
- performance becomes unacceptable;
- data/licensing conditions change;
- its capability is no longer required.

Retirement must preserve enough metadata to reproduce historical decisions.

The executable artifact may be removed from active deployment while its immutable metadata and required archival evidence remain retained according to Novi's data lifecycle policy.

---

# 26. NVIDIA-specific lifecycle considerations

NVIDIA's current documentation demonstrates why Novi needs explicit lifecycle control around optimized artifacts and platform versions.

TensorRT supports multiple deployment paths and hardware targets, while serialized engines can be tied to the TensorRT version and build environment that created them. citeturn0search0turn0search6

NVIDIA also publishes lifecycle and compatibility information for its broader software stack, reinforcing the need to validate the complete platform rather than pinning a component in isolation. citeturn0search7turn0search9

Novi therefore adopts this rule:

> **Every production model is a versioned software supply-chain artifact with explicit runtime compatibility, benchmark evidence and rollback information.**

---

# 27. Required records

For every production model, Novi should retain:

```text
MODEL_CARD
MODEL_MANIFEST
PROVENANCE_RECORD
BENCHMARK_REPORT
SAFETY_REPORT
COMPATIBILITY_MATRIX
RESOURCE_PROFILE
DEPLOYMENT_RECORD
OBSERVABILITY_DEFINITION
ROLLBACK_RECORD
ADR
```

The exact document/file locations will be standardized by the later model-runtime and deployment specifications.

---

# 28. Acceptance criteria

This document is complete only when Novi can answer, for every deployed learned component:

1. What exact model is running?
2. What exact artifact is running?
3. Where did it come from?
4. What license governs it?
5. What data or upstream model produced it?
6. Which runtime and hardware does it require?
7. Which preprocessing/postprocessing contract does it use?
8. What benchmark evidence justified adoption?
9. What safety evidence exists?
10. What are its resource costs?
11. How is it monitored?
12. How is drift detected?
13. What version replaces it?
14. How is it rolled back?
15. Can historical outputs be attributed to the exact model version?
16. Can the deployment be reproduced?

If those questions cannot be answered, the model is not fully production-governed.
