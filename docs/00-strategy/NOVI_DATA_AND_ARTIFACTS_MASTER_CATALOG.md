# Novi — Data & Artifact Master Catalog

**Date:** 2026-08-17  
**Status:** P0 pre-implementation baseline  
**Purpose:** Define the data, datasets, models, simulation assets, schemas, artifacts and evidence that must exist before Novi can be considered implementation-ready.

---

# 1. Principle

Novi cannot be built correctly from source code alone.

The project requires controlled artifacts for:

```text
Requirements
 ↓
Schemas
 ↓
Knowledge
 ↓
Models
 ↓
Datasets
 ↓
Simulation worlds
 ↓
Robot descriptions
 ↓
Calibration
 ↓
Benchmarks
 ↓
Validation evidence
 ↓
Deployment artifacts
```

Every important artifact must have provenance and a version.

---

# 2. Canonical artifact classes

## A. Architecture artifacts

- North Star;
- system architecture;
- domain specifications;
- interface contracts;
- ADRs;
- threat model;
- safety case;
- validation plans.

## B. Semantic schemas

Required canonical schemas include:

- EventEnvelope;
- Observation;
- Measurement;
- Evidence;
- Entity;
- Relationship;
- Fact;
- Belief;
- Prediction;
- SimulationResult;
- Counterfactual;
- Episode;
- Goal;
- Intention;
- Plan;
- ActionProposal;
- Authorization;
- ActionExecution;
- ActionOutcome;
- Skill;
- SkillVersion;
- Model;
- ModelInvocation;
- Dataset;
- DatasetVersion;
- Sensor;
- Calibration;
- HardwareHealth;
- DeploymentManifest.

## C. Model artifacts

For every model:

- model ID;
- model family;
- exact version;
- source repository;
- license;
- weights digest;
- tokenizer/preprocessor version;
- input schema;
- output schema;
- parameter count;
- quantization;
- runtime;
- hardware target;
- benchmark results;
- known limitations;
- safety limitations;
- provenance.

## D. Dataset artifacts

Every dataset version should contain:

- dataset ID/version;
- source;
- acquisition method;
- acquisition date;
- license;
- privacy classification;
- synthetic/real/augmented/reconstructed label;
- schema version;
- transformations;
- deduplication status;
- quality metrics;
- labels/annotations;
- train/validation/test split;
- evaluation results;
- checksum.

The NVIDIA research explicitly recommends this type of lineage and immutable dataset versioning. fileciteturn22file0L493-L505

---

# 3. Initial Novi datasets

Novi does not need a massive training corpus to start the cognitive architecture.

The initial dataset program should instead create **evaluation-first datasets**.

## 3.1 Cognitive scenarios

Create deterministic scenarios for:

- identity;
- memory recall;
- temporal reasoning;
- spatial reasoning;
- uncertainty;
- contradiction handling;
- goal persistence;
- attention selection;
- planning;
- action/outcome learning;
- curiosity;
- personality continuity;
- recovery after restart.

## 3.2 Synthetic perception scenarios

Generate controlled data for:

- people;
- objects;
- rooms;
- occlusion;
- lighting variation;
- motion;
- distance;
- depth;
- multiple objects;
- sensor failure;
- ambiguous identity;
- environmental changes.

## 3.3 Navigation scenarios

Create repeatable environments covering:

- open rooms;
- corridors;
- doorways;
- narrow passages;
- dynamic people;
- temporary obstacles;
- localization loss;
- sensor degradation;
- goal changes;
- recovery behavior.

## 3.4 Safety scenarios

Create deterministic test cases for:

- emergency stop;
- controller failure;
- perception failure;
- stale sensor data;
- invalid action proposal;
- policy rejection;
- communication loss;
- thermal limit;
- battery low;
- storage failure;
- model timeout;
- malformed model output.

---

# 4. Simulation assets

The simulation package must contain:

```text
robot model
  ├── URDF/Xacro
  ├── meshes
  ├── joints
  ├── transmissions
  ├── ros2_control config
  ├── sensor definitions
  └── materials

USD representation
  ├── robot
  ├── environment
  ├── sensors
  └── physics metadata

scenarios
  ├── worlds
  ├── task definitions
  ├── seeds
  ├── fault injections
  └── expected outcomes
```

Every simulation run must record:

- simulator version;
- physics engine;
- world/asset version;
- robot version;
- sensor configuration;
- seed;
- scenario;
- policy/model version;
- configuration digest.

This follows the provenance requirements in the NVIDIA research. fileciteturn22file0L102-L116

---

# 5. Real sensor data

When physical hardware is eventually introduced, raw sensor data should be retained selectively according to privacy/retention rules.

Data categories:

- camera frames/keyframes;
- depth;
- LiDAR scans;
- IMU;
- audio;
- actuator telemetry;
- power;
- thermal;
- environmental sensors.

The runtime should generally promote **meaningful observations/events** into semantic memory rather than storing every raw frame forever.

---

# 6. Perception annotations

Where supervised evaluation is required, datasets should include:

- bounding boxes;
- masks;
- classes;
- tracking IDs;
- poses;
- depth ground truth where available;
- identity labels only where permitted;
- scene labels;
- temporal links;
- sensor calibration metadata.

Ground-truth provenance must be explicit.

---

# 7. Model evaluation datasets

Each candidate model class needs a Novi-specific benchmark.

## LLM

- grounded reasoning;
- memory use;
- structured output;
- tool use;
- planning;
- uncertainty handling;
- hallucination resistance;
- long-context behavior.

## VLM

- scene understanding;
- object relationships;
- spatial reasoning;
- temporal reasoning from sequences;
- uncertainty;
- grounding.

## Speech

- word error rate;
- noise robustness;
- far-field performance;
- speaker separation;
- latency.

## Embeddings/reranking

- retrieval recall;
- precision;
- semantic similarity;
- temporal relevance;
- entity disambiguation.

## Perception

- detection;
- segmentation;
- depth;
- tracking;
- localization;
- calibration sensitivity;
- latency;
- failure behavior.

---

# 8. Skill/policy datasets

Later learned skills require:

```text
demonstration
 ↓
trajectory
 ↓
simulation
 ↓
training
 ↓
evaluation
 ↓
controlled physical validation
 ↓
skill verification
```

Each skill dataset must record:

- embodiment;
- sensor configuration;
- action representation;
- environment;
- task;
- demonstrator/source;
- policy version;
- success criteria;
- safety limitations.

The NVIDIA research recommends exactly this type of skill provenance. fileciteturn22file0L501-L510

---

# 9. Hardware artifacts

Required before final physical build:

- electrical schematics;
- power tree;
- BOM;
- CAD;
- mechanical drawings;
- sensor placement map;
- FOV coverage model;
- wiring harness;
- connector map;
- firmware versions;
- calibration files;
- time-sync configuration;
- safety circuit design;
- BMS configuration;
- thermal model;
- hardware validation report.

---

# 10. Deployment artifacts

Every release must produce:

- source commit;
- build artifact;
- container digest;
- deployment manifest;
- model artifact digests;
- configuration digest;
- schema version;
- database migration version;
- ROS distribution;
- OS version;
- hardware target;
- runtime versions;
- test report;
- security report;
- rollback target.

---

# 11. Evidence and validation artifacts

Every major capability must generate evidence:

```text
requirement
 ↓
test
 ↓
run
 ↓
measurement
 ↓
result
 ↓
artifact/log/trace
 ↓
pass/fail
 ↓
approval
```

A model card or README is not sufficient evidence for a safety-critical claim.

---

# 12. Data provenance rule

All meaningful data should answer:

```text
WHAT?
WHEN?
WHERE?
SOURCE?
WHICH SENSOR/MODEL?
WHICH VERSION?
HOW WAS IT TRANSFORMED?
REAL / SYNTHETIC / SIMULATED?
WHAT CONFIDENCE?
WHO/WHAT VERIFIED IT?
```

This supports the central Novi invariant:

```text
OBSERVED ≠ INFERRED ≠ PREDICTED ≠ SIMULATED ≠ COUNTERFACTUAL
```

---

# 13. Data that must NOT be silently mixed

Never silently mix:

- real and synthetic training data;
- simulated and observed world state;
- raw memory and training data;
- model outputs and verified knowledge;
- KV cache and durable memory;
- embeddings and semantic truth;
- simulation outcomes and historical events.

The NVIDIA research explicitly calls out these distinctions. fileciteturn22file0L341-L367

---

# 14. Initial data package required before Stage 1

Before implementing the Novi Kernel, the repository should contain at least:

- canonical schemas;
- event examples;
- world-model examples;
- memory examples;
- cognitive scenario catalog;
- benchmark definitions;
- sample model manifests;
- sample dataset manifests;
- deployment manifest schema;
- initial simulation scenario schema;
- hardware capability schema.

The initial package does **not** require training Novi's own foundation model.

---

# 15. Initial data package required before simulation

Before serious simulation:

- robot URDF/Xacro;
- ros2_control configuration;
- sensor models;
- calibration assumptions;
- world assets;
- navigation maps/scenarios;
- fault scenarios;
- deterministic seeds;
- expected outcomes;
- simulator provenance schema.

---

# 16. Initial data package required before physical hardware

Before physical actuation:

- final BOM;
- electrical design;
- mechanical design;
- safety case;
- calibration procedures;
- sensor synchronization;
- hardware test plan;
- motor/controller limits;
- battery/BMS design;
- emergency-stop validation;
- HIL results;
- simulation regression results.

---

# 17. Artifact ownership

Novi should explicitly own the semantics of:

- schemas;
- event types;
- memory records;
- knowledge records;
- world state;
- action proposals;
- skills;
- deployment manifests;
- evaluation records.

External tools own their native artifacts, but Novi stores references, versions, provenance and validation results.

---

# 18. Data readiness gate

Before implementation is considered ready:

- [ ] canonical semantic schemas exist;
- [ ] event examples exist;
- [ ] cognitive scenario catalog exists;
- [ ] model benchmark definitions exist;
- [ ] dataset manifest exists;
- [ ] simulation asset manifest exists;
- [ ] deployment manifest exists;
- [ ] provenance requirements are testable;
- [ ] privacy classification exists;
- [ ] retention rules exist;
- [ ] evaluation evidence format exists.

---

# 19. Final principle

The goal is not to create a giant pile of datasets before writing Novi.

The goal is to ensure that **every important claim Novi makes and every important capability Novi acquires can be represented, tested, versioned, reproduced and traced**.

That is the data foundation required for a persistent autonomous system.
