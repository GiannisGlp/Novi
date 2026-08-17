# Novi — Development Strategy and Implementation Plan

**Status:** Proposed strategic direction  
**Date:** 2026-08-17  
**Scope:** Novi standalone project  
**Authority:** Strategic guidance derived from the current Novi architecture plus the NVIDIA Physical AI research dossier. This document does not replace domain architecture or ADRs; implementation decisions must still be validated and recorded through the project's decision process.

---

## 1. Purpose

This document consolidates the strategic conclusions, architectural recommendations, implementation approach, technology-selection principles, staged roadmap, validation strategy, and research direction established for Novi.

Novi is a **standalone project**. It must not inherit assumptions, requirements, naming, or architecture from other robot projects. Any remaining `Wheely` references in the repository are documentation cleanup items and must not be interpreted as a project dependency.

The central objective is to build Novi as a **persistent autonomous physical-AI system** whose intelligence can be developed and evaluated before committing to physical hardware.

The guiding principle is:

> **Build the mind before the body.**

And the corresponding engineering principle is:

> **Use neural models for capabilities where learning is appropriate, and structured/deterministic systems for state, memory, authorization, safety, provenance, and control.**

---

# 2. Executive Decision

Novi should be built as a **hybrid cognitive architecture**, not as an LLM with motors attached and not as one monolithic neural network.

The target architecture is:

```text
                         NOVI
                          │
                ┌─────────┴─────────┐
                │   Cognitive Core │
                └─────────┬─────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
     MEMORY          WORLD MODEL        AUTONOMY
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                       REASONING
                          │
                    Local LLM/VLM
                          │
                ┌─────────┴─────────┐
                │                   │
           PERCEPTION          PLANNING
                │                   │
       neural + classical      structured + learned
                │                   │
                └─────────┬─────────┘
                          │
                    GOVERNANCE
                          │
                       SKILLS
                          │
                        ROS 2
                          │
                  robotics stack
                          │
                       ROBOT
```

The brain is the **whole cognitive system**, not the LLM alone.

---

# 3. What Novi Should Be

Novi should ultimately be capable of:

- continuously operating rather than only responding to prompts;
- maintaining persistent identity and state;
- perceiving and interpreting its environment;
- maintaining a structured world model;
- remembering experiences and facts;
- distinguishing observations from beliefs, predictions, simulations, and counterfactuals;
- maintaining goals over time;
- allocating attention;
- reasoning about situations;
- planning actions;
- learning from experience where appropriate;
- developing and using skills;
- interacting socially and through multiple modalities;
- acting autonomously within explicit governance and safety boundaries;
- observing the consequences of actions;
- updating memory and world state after actions;
- recovering from interruption or failure;
- operating locally where practical;
- remaining understandable and auditable.

Novi should **not** depend on an LLM to be the authoritative source of system state or physical authority.

---

# 4. What Novi Should Not Be

Avoid these architectures:

```text
Camera
  ↓
LLM
  ↓
Motor Driver
```

or:

```text
Everything
  ↓
One giant neural network
  ↓
Robot
```

or:

```text
LLM
  ↓
Arbitrary code execution
  ↓
Hardware
```

These approaches make safety, determinism, provenance, recovery, testing, and debugging unnecessarily difficult.

The preferred flow is:

```text
Sensor
  ↓
Perception
  ↓
Evidence
  ↓
World Model / Memory
  ↓
Attention / Goals
  ↓
Reasoning
  ↓
Planning
  ↓
Action Proposal
  ↓
Governance / Policy
  ↓
Safety Gateway
  ↓
Skill / Capability
  ↓
ROS 2
  ↓
Controller
  ↓
Actuator
  ↓
Observed Consequence
  ↓
Memory / World Model
```

---

# 5. Neural Networks: Use Them, But Deliberately

## 5.1 Neural networks are a good idea

Novi should use neural networks extensively where they provide the appropriate capability.

Good candidates include:

- object detection;
- segmentation;
- depth estimation;
- visual embeddings;
- image understanding;
- speech recognition;
- speech synthesis;
- voice identification;
- language understanding;
- multimodal reasoning;
- prediction;
- anomaly detection;
- learned perception;
- imitation learning;
- reinforcement learning;
- learned robot policies;
- skill acquisition.

## 5.2 Neural networks should not own authority

Neural models should not be the authoritative owner of:

- authorization;
- safety policy;
- emergency-stop behavior;
- durable provenance;
- canonical identity;
- immutable system invariants;
- deletion policy;
- protected configuration;
- exact actuator limits;
- final physical-action authorization.

The model can **propose**. Structured governance decides. Controllers execute.

## 5.3 Do not train a foundation model from scratch

Novi should initially use existing models and focus original engineering effort on the cognitive architecture around them.

Evaluate existing local models for:

- language/reasoning;
- vision;
- speech;
- embeddings;
- multimodal understanding;
- perception;
- learned robotics skills.

Model training from scratch should only become a later research activity if measured evidence shows that existing models cannot satisfy a specific Novi requirement.

---

# 6. The LLM's Role

The LLM should be treated as a **reasoning/language component of the brain**, not the entire brain.

Conceptually:

```text
                    ┌───────────────┐
                    │   Local LLM   │
                    │               │
                    │ reasoning     │
                    │ language      │
                    │ interpretation│
                    │ hypotheses    │
                    └───────┬───────┘
                            │
                            ↓
                  ┌──────────────────┐
                  │ Cognitive Core    │
                  │                  │
                  │ memory           │
                  │ world model      │
                  │ attention        │
                  │ goals            │
                  │ curiosity        │
                  │ planning         │
                  └────────┬─────────┘
                           │
                           ↓
                       Governance
                           │
                           ↓
                         Action
```

The model should receive carefully constructed context containing:

- current state;
- relevant world-model state;
- relevant memories;
- active goals;
- available capabilities;
- constraints;
- uncertainty;
- recent observations;
- action history where relevant.

The model should produce structured proposals rather than arbitrary privileged commands.

Example:

```json
{
  "intent": "investigate",
  "target": "unknown_object_12",
  "reason": "object is novel and relevant to current context",
  "confidence": 0.82,
  "proposed_action": "inspect_object"
}
```

The governance layer then validates whether that action is allowed and safe.

---

# 7. Memory Is a Core Intelligence Substrate

Memory should be treated as substantially more than a vector database.

Novi should support distinct forms of information such as:

```text
                     MEMORY
                        │
          ┌─────────────┼─────────────┐
          │             │             │
       Episodic      Semantic      Procedural
          │             │             │
      experiences     facts         skills
          │             │             │
          └─────────────┼─────────────┘
                        │
                 Spatial / Temporal
                        │
                   Provenance
```

Potential entities include:

- observations;
- evidence;
- facts;
- beliefs;
- episodes;
- entities;
- relationships;
- goals;
- skills;
- events;
- preferences;
- spatial information;
- temporal information.

Vector embeddings should be considered one retrieval mechanism, not the canonical memory representation.

Example structured knowledge:

```text
Vano
 ├── interacted_with → Novi
 ├── mentioned → project_Novi
 └── associated_with → location_X
```

Example episodic memory:

```text
Episode 1842
  timestamp
  location
  participants
  observations
  actions
  outcomes
  evidence
  confidence
```

---

# 8. Preserve Epistemic Distinctions

A critical Novi invariant is:

```text
REAL OBSERVATION
       ≠
WORLD MODEL STATE
       ≠
BELIEF / INFERENCE
       ≠
PREDICTION
       ≠
SIMULATION
       ≠
COUNTERFACTUAL
```

Every important piece of information should retain enough provenance to determine:

- what it is;
- when it was created;
- where it came from;
- who/what produced it;
- confidence/uncertainty;
- whether it was directly observed;
- whether it was inferred;
- whether it was predicted;
- whether it was simulated;
- whether it was verified;
- what evidence supports it.

This distinction is especially important for future world models, digital twins, synthetic data, learned policies, and autonomous decisions.

---

# 9. World Model

Novi should maintain a structured representation of its current understanding of the world.

Core concepts should include:

```text
People
Objects
Places
Environment
Robot
Time
Events
Relationships
Goals
Actions
Uncertainty
```

A simple conceptual example:

```text
ROOM
 ├── contains → TABLE
 │               ├── contains → CUP
 │               └── contains → LAPTOP
 │
 └── contains → PERSON
```

Neural perception supplies evidence that updates the world model. The world model should not be replaced by raw model outputs.

---

# 10. Attention, Goals, and Curiosity

Novi should not reason equally about every observation.

The autonomy layer should eventually consider:

- relevance;
- novelty;
- urgency;
- uncertainty;
- expected information gain;
- current goals;
- user priorities;
- safety;
- resource cost.

A possible curiosity mechanism is:

```text
unknown object
    ↓
high uncertainty
    +
high novelty
    +
contextual relevance
    ↓
investigation candidate
```

Curiosity must remain governed by policy and resource constraints. It should not become uncontrolled behavior.

---

# 11. Build the Brain Before the Body

The first implementation should not require a physical robot.

Start with:

```text
Mac / development machine
        ↓
Novi Brain
        ↓
Software Sensors
        ↓
Simulated Environment
        ↓
Robot Simulation
```

The first sensor inputs can be synthetic events.

Example:

```json
{
  "type": "person_observed",
  "person_id": "unknown",
  "location": "living_room",
  "timestamp": "...",
  "confidence": 0.87
}
```

The system should process this through:

```text
Observation
  ↓
Evidence
  ↓
World Model
  ↓
Memory
  ↓
Attention
  ↓
Goal Evaluation
  ↓
Reasoning
  ↓
Action Proposal
```

This allows the cognitive architecture to be tested independently of hardware.

---

# 12. First Definition of a "Brain"

Novi should not be considered successful merely because it can answer questions.

The first meaningful brain milestone is a system that can run continuously:

```text
start
 ↓
load identity/state
 ↓
observe
 ↓
update world model
 ↓
retrieve memory
 ↓
evaluate attention
 ↓
maintain goals
 ↓
decide whether cognition is needed
 ↓
reason
 ↓
plan
 ↓
propose action
 ↓
execute approved capability
 ↓
observe consequence
 ↓
update memory
 ↓
continue
```

This should run as a persistent process rather than a request/response script.

---

# 13. Implementation Stages

## Stage 0 — Architecture Cleanup

Before substantial implementation:

- remove stale `Wheely` terminology;
- establish Novi as a standalone project everywhere;
- identify canonical terminology;
- reconcile conflicting documentation;
- freeze core interface boundaries;
- identify missing contracts;
- identify MVP cognitive capabilities;
- establish architecture decision records for important selections.

**Exit condition:** the architecture clearly describes Novi and no longer mixes it with another project.

---

## Stage 1 — Novi Kernel

Build the smallest persistent runtime.

Initial components:

```text
Novi Runtime
├── Lifecycle
├── Clock
├── Event Bus
├── State Store
├── Identity
├── Configuration
└── Persistence
```

No advanced AI is required yet.

The kernel must be able to:

- start;
- stop;
- recover;
- persist state;
- consume events;
- publish events;
- expose stable contracts;
- operate continuously.

**Exit condition:** Novi can run continuously and recover its state after restart.

---

## Stage 2 — Memory and Evidence

Implement the initial durable cognitive substrate.

Core concepts:

```text
Observation
Evidence
Entity
Relationship
Fact
Belief
Episode
Goal
Skill
Event
```

Add provenance and uncertainty from the beginning.

**Exit condition:** Novi can remember events and retrieve structured and semantic information across restarts.

---

## Stage 3 — World Model

Implement:

- people;
- places;
- objects;
- relationships;
- robot state;
- spatial state;
- temporal state;
- events;
- uncertainty;
- source/provenance.

The world model must distinguish observation from inference.

**Exit condition:** synthetic observations can create and update a coherent persistent world representation.

---

## Stage 4 — Continuous Cognitive Loop

Implement:

```text
observe
 → update
 → retrieve
 → attention
 → goals
 → reason
 → plan
 → act
 → observe outcome
 → learn/update state
 → repeat
```

This stage should introduce:

- attention;
- goal manager;
- prioritization;
- decision cycle;
- action proposals;
- feedback;
- autonomy state machine.

**Exit condition:** Novi operates autonomously in a synthetic environment without requiring a user prompt for every cycle.

---

## Stage 5 — LLM / VLM Integration

Integrate a local model behind a stable reasoning interface.

The model receives:

- current cognitive state;
- relevant memory;
- world model;
- active goals;
- available capabilities;
- constraints;
- recent evidence.

The model produces structured reasoning outputs and action proposals.

The governance layer remains authoritative.

**Exit condition:** Novi can use language/multimodal reasoning to interpret situations, formulate goals, retrieve knowledge, and propose actions while remaining constrained by the architecture.

---

## Stage 6 — Real Perception

Introduce actual sensor inputs, initially without physical actuation.

Candidate capabilities:

- camera input;
- object detection;
- tracking;
- depth;
- speech recognition;
- voice identification;
- audio events;
- multimodal perception.

Use existing mature models rather than building new neural networks initially.

**Exit condition:** Novi can convert real sensory inputs into provenance-aware evidence and update its world model reliably.

---

## Stage 7 — Simulation

Connect the cognitive architecture to a simulated robot.

Candidate stack:

```text
Novi
 ↓
Vendor-neutral interfaces
 ↓
ROS 2
 ↓
Nav2 / robotics infrastructure
 ↓
Gazebo or Isaac Sim
```

Use simulation for:

- navigation;
- perception;
- action execution;
- failure scenarios;
- sensor simulation;
- safety testing;
- long-duration autonomy tests.

**Exit condition:** Novi can complete defined autonomous tasks in simulation repeatedly and recover from faults.

---

## Stage 8 — Learned Skills

Only after the cognitive architecture and simulation are stable should learned robot policies become a major focus.

Investigate:

- imitation learning;
- reinforcement learning;
- offline RL;
- learned manipulation/navigation skills;
- skill libraries;
- NVIDIA Isaac Lab;
- NVIDIA GR00T or equivalent models.

A learned policy must pass:

```text
training
 ↓
simulation
 ↓
evaluation
 ↓
safety gate
 ↓
real-robot canary
 ↓
verification
 ↓
promotion
```

**Exit condition:** at least one learned skill is demonstrably useful and safely integrated through Novi governance.

---

## Stage 9 — Physical Prototype

Only after the software brain and simulated embodiment meet defined gates should physical hardware become the priority.

The physical stack should remain:

```text
Novi cognition
 ↓
Novi interfaces
 ↓
ROS 2
 ↓
robotics/navigation
 ↓
controllers
 ↓
hardware
```

Hardware should be selected based on measured workload rather than the architecture document.

**Exit condition:** the physical robot can perform a controlled autonomous mission while maintaining the same semantic architecture used in simulation.

---

# 14. Hardware Strategy

Do not commit to Jetson now.

The hardware decision should follow measurement.

Define an edge capability contract containing:

- CPU requirements;
- GPU requirements;
- RAM;
- accelerator availability;
- camera bandwidth;
- sensor interfaces;
- storage;
- power budget;
- thermal budget;
- real-time requirements;
- operating system;
- CUDA requirements where applicable;
- TensorRT requirements where applicable;
- ROS 2 compatibility.

Then benchmark candidate systems.

Potential progression:

```text
Software prototype
      ↓
Simulation
      ↓
Measured workload
      ↓
Candidate edge computer
      ↓
Benchmark
      ↓
Hardware decision
```

Jetson Orin, Jetson Thor, x86 GPU systems, or another platform should be evaluated against the actual Novi workload.

The goal is not to build an "NVIDIA robot". The goal is to build Novi and use NVIDIA where it provides measurable value.

---

# 15. NVIDIA Strategy

NVIDIA should be treated as a major implementation ecosystem, not as Novi's architectural owner.

Potentially valuable components include:

- Jetson;
- CUDA;
- TensorRT;
- TensorRT-LLM;
- Isaac ROS;
- Isaac Sim;
- Isaac Lab;
- GR00T;
- Cosmos;
- OpenUSD;
- Holoscan;
- DeepStream;
- Metropolis;
- NeMo/Nemotron.

Use them when they solve a Novi requirement better than alternatives.

The semantic Novi interfaces should remain vendor-neutral.

Conceptually:

```text
Novi Interface
      ↓
implementation adapter
      ↓
NVIDIA / open-source / other runtime
```

Not:

```text
Novi architecture
      ↓
NVIDIA-specific API everywhere
```

---

# 16. Technology Selection Rules

The existing Novi technology-selection philosophy should remain the default:

1. mature existing solution;
2. open-source or compatible licensing;
3. local/offline execution;
4. hardware compatibility;
5. accuracy and robustness;
6. latency;
7. memory/compute requirements;
8. power requirements;
9. security/privacy;
10. maintenance/community health;
11. integration complexity;
12. cloud only when no practical local solution exists.

Every major external dependency should eventually have an evaluation record containing:

- capability solved;
- candidates;
- version;
- license;
- local/offline support;
- platforms;
- model/runtime size;
- quality metrics;
- latency;
- memory;
- power/thermal implications;
- maintenance status;
- security;
- privacy;
- integration requirements;
- fallback;
- reason for selection;
- date tested.

---

# 17. Suggested Initial Technology Stack

These are **starting candidates**, not permanent commitments.

## Runtime

- Python for research/prototyping and AI orchestration where appropriate;
- a strongly typed systems language/runtime component where real-time or performance requirements justify it;
- asynchronous event-driven architecture;
- durable local state.

## Robotics

- ROS 2;
- Navigation2 where navigation is required;
- established drivers and controllers instead of custom replacements.

## AI

- PyTorch as a primary research/training ecosystem;
- ONNX where portability is useful;
- TensorRT where NVIDIA deployment benchmarking demonstrates a benefit;
- existing local models for language, vision, audio and embeddings.

## Classical perception

- OpenCV and other deterministic tools where they are sufficient.

## Memory

Use a combination of:

- structured relational/state storage;
- event log;
- graph-like relationships where justified;
- vector/embedding retrieval;
- durable provenance.

Do not make the vector database the canonical source of truth.

## Simulation

Start with the simulator that gives the fastest path to useful development and testing. Evaluate Gazebo and Isaac Sim against Novi requirements. Isaac Sim/Isaac Lab should become particularly attractive once realistic sensor simulation and robot-learning workflows become important.

---

# 18. What Should Be Built vs Reused

## Build Novi-specific

Novi should own:

- cognitive runtime;
- cognitive state model;
- world-model semantics;
- memory semantics;
- provenance model;
- attention;
- goals;
- curiosity;
- autonomy orchestration;
- reasoning interface;
- governance;
- authorization;
- action semantics;
- audit semantics;
- model/skill lifecycle;
- Novi-specific evaluation framework;
- cross-layer contracts.

## Reuse mature infrastructure

Prefer existing solutions for:

- ROS 2 middleware;
- navigation;
- hardware drivers;
- camera drivers;
- standard message formats;
- object detection models;
- speech recognition;
- speech synthesis;
- embeddings;
- model runtimes;
- physics simulation;
- visualization;
- low-level controllers.

Novi should not reinvent mature infrastructure without a demonstrated requirement.

---

# 19. Cognitive Benchmark — What Does "Really a Brain" Mean?

Novi should have an explicit cognitive benchmark instead of relying on subjective impressions.

## Persistence

Can Novi remember information from previous sessions?

## Identity

Can Novi maintain stable entities and identities while representing uncertainty?

## Spatial understanding

Can Novi maintain a coherent representation of where entities are?

## Temporal reasoning

Can Novi understand sequences and relationships between events?

## Goal persistence

Can Novi maintain goals over extended periods?

## Attention

Can Novi decide what deserves processing and what can be ignored?

## Self-monitoring

Can Novi represent uncertainty and recognize what it does not know?

## Curiosity

Can Novi decide when obtaining information is worth the cost?

## Planning

Can Novi break objectives into executable actions?

## Learning

Does experience affect future behavior in a persistent way?

## Consequence learning

Can Novi remember failed actions and adapt?

## Self-state

Does Novi understand its own location, capabilities, limits, resources and status?

## Autonomous initiative

Can Novi initiate an appropriate investigation or action without a direct user command?

## Embodied consequence

Can Novi connect actions to observed physical outcomes?

A strong Novi milestone is reached when the system demonstrates:

```text
continuity
+
memory
+
world model
+
attention
+
goals
+
reasoning
+
planning
+
learning
+
agency
+
embodiment
```

rather than merely strong language generation.

---

# 20. Simulation and Validation Gates

Physical deployment must not be the first serious test.

Use progressively stronger gates:

```text
Unit Tests
    ↓
Contract Tests
    ↓
Cognitive Scenario Tests
    ↓
Long-Duration Runtime Tests
    ↓
Simulation
    ↓
Fault Injection
    ↓
Safety Tests
    ↓
Hardware-in-the-loop
    ↓
Controlled Physical Tests
    ↓
Limited Autonomous Operation
```

Important scenario categories include:

- sensor loss;
- stale observations;
- conflicting observations;
- model failure;
- memory corruption;
- network loss;
- process crash;
- unexpected object;
- unexpected person;
- navigation failure;
- low battery;
- actuator fault;
- invalid action proposal;
- policy denial;
- recovery after restart.

---

# 21. Learned Skill Governance

A learned policy must never automatically gain physical authority merely because it performs well in training.

Maintain the distinction:

```text
competence ≠ authorization
```

Skill lifecycle:

```text
Skill Idea
   ↓
Dataset
   ↓
Training
   ↓
Simulation
   ↓
Evaluation
   ↓
Safety Gate
   ↓
Real-Robot Canary
   ↓
Verification
   ↓
Skill Promotion
```

Every learned skill should be traceable to:

- dataset version;
- source data;
- robot embodiment;
- simulator version;
- physics version;
- training code;
- model version;
- hyperparameters;
- evaluation set;
- safety results;
- deployment target.

---

# 22. World Model and Digital Twin Strategy

OpenUSD and digital-twin technology should be evaluated as representations for simulation and physical environments, not as Novi's universal semantic data model.

Novi should retain its own semantic concepts for:

- entities;
- observations;
- provenance;
- beliefs;
- permissions;
- memory;
- causal claims.

A useful distinction is:

```text
Novi semantic world model
          ↕
OpenUSD / simulator representation
          ↓
Simulation / digital twin
```

This allows vendor-specific simulation technology to evolve without changing the cognitive architecture.

---

# 23. First Practical MVP

The first meaningful MVP should not be a physical robot.

It should be a **persistent autonomous software entity** that lives inside a synthetic environment.

Example:

```text
Synthetic world
 ├── rooms
 ├── people
 ├── objects
 ├── events
 └── time

             ↓

Novi
 ├── perception input
 ├── world model
 ├── memory
 ├── attention
 ├── goals
 ├── curiosity
 ├── reasoning
 ├── planning
 ├── action proposals
 └── learning/update
```

Example behavior:

1. Novi observes an unknown object.
2. It records evidence.
3. It adds the object to the world model.
4. It recognizes that the object is novel.
5. It decides whether investigation is worthwhile.
6. It creates an investigation goal.
7. It plans an investigation.
8. It executes a simulated capability.
9. It receives a new observation.
10. It updates its knowledge.
11. It remembers the episode.
12. Later, it behaves differently because of the experience.

That is a far more meaningful first demonstration than a chatbot connected to a motor.

---

# 24. Is Novi Achievable?

## What is achievable now

A sophisticated system with:

- persistent memory;
- structured world model;
- multimodal perception;
- local language reasoning;
- autonomous goals;
- planning;
- tool use;
- simulation;
- learning components;
- ROS 2 integration;
- physical robot control;

is achievable with current technology.

## What is significantly harder

A highly general autonomous physical intelligence that can robustly operate across arbitrary environments and tasks is a major research and engineering challenge.

## What cannot currently be promised

Human-level general physical intelligence, consciousness, or subjective experience should not be treated as guaranteed engineering outcomes.

The project should instead target **observable cognitive capabilities** and measurable improvements over time.

---

# 25. Recommended Development Philosophy

### 1. Mind before body

Build the cognitive runtime before buying expensive robotics hardware.

### 2. Hybrid intelligence

Combine neural, symbolic/structured, deterministic, and optimization-based components.

### 3. Existing technology first

Reuse mature infrastructure instead of recreating it.

### 4. Vendor neutrality

NVIDIA is a major candidate ecosystem, not Novi's architecture.

### 5. Local-first

Prefer local execution, especially for core cognition, memory, safety, and control.

### 6. Safety is structural

Safety must be enforced outside the model.

### 7. Provenance everywhere

Novi must know where important information came from.

### 8. Simulation before physical autonomy

Use simulation to expose failures before they become physical failures.

### 9. Benchmark instead of guessing

Hardware and model decisions should be based on measurements.

### 10. Small working increments

Every stage should produce an executable and testable capability.

### 11. Research without architectural drift

Research documents inform decisions. They do not automatically become dependencies.

### 12. Build what makes Novi unique

Novi's value is in its cognitive architecture and persistent autonomous behavior, not in reinventing ROS 2, object detection, or motor control.

---

# 26. Immediate Next Steps

The next work should proceed in this order.

## A. Documentation

- remove remaining Wheely terminology;
- audit all architecture documents for contradictions;
- identify missing contracts;
- define canonical terminology;
- create/maintain ADRs for technology decisions;
- define the initial Novi cognitive benchmark.

## B. Architecture

Freeze the first contracts for:

- events;
- observations;
- evidence;
- entities;
- world state;
- memory;
- goals;
- action proposals;
- capabilities;
- policy decisions;
- safety decisions.

## C. Implementation

Start with:

```text
Stage 1 — Novi Kernel
        ↓
Stage 2 — Memory / Evidence
        ↓
Stage 3 — World Model
        ↓
Stage 4 — Cognitive Loop
```

Do not start with robot hardware.

## D. AI integration

After the cognitive contracts work:

```text
Local LLM
   ↓
Structured reasoning interface
   ↓
Cognitive Core
```

## E. Perception

Then add real models and real sensor inputs.

## F. Simulation

Then integrate ROS 2 and a simulator.

## G. Robotics

Only after simulation demonstrates robust autonomous behavior should physical hardware become a primary implementation target.

---

# 27. Immediate Research Targets

Before making major NVIDIA-specific decisions, investigate:

1. Isaac ROS package-by-package capabilities and ROS 2 compatibility.
2. Jetson Thor vs AGX Orin vs Orin NX for measured Novi workloads.
3. Isaac Sim sensor fidelity and robot/sensor support.
4. Isaac Lab training and evaluation architecture.
5. GR00T model inputs, outputs, licensing, and deployment constraints.
6. Cosmos model families and practical robotics use cases.
7. TensorRT/TensorRT-LLM deployment constraints.
8. Holoscan vs Isaac ROS vs DeepStream boundaries.
9. OpenUSD representation for world-model/digital-twin integration.
10. NVIDIA security and OTA/update architecture.
11. Simulation-to-real benchmark design.
12. NVIDIA and open-source reference architectures for small autonomous mobile robots.

These should produce **decision inputs**, not uncontrolled additions to the architecture.

---

# 28. Long-Term Target Architecture

The intended mature architecture can be represented as:

```text
                         NOVI
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
  FOUNDATION          COGNITION          MEMORY
   MODELS                │                  │
       │             WORLD MODEL           │
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                       AUTONOMY
                          │
              ┌───────────┼───────────┐
              │           │           │
          Attention     Goals     Curiosity
              │           │           │
              └───────────┼───────────┘
                          │
                       Reasoning
                          │
                       Planning
                          │
                    Governance
                          │
                 Skills / Policies
                          │
                      Controllers
                          │
                       ROS 2
                          │
                       Robot
                          │
                       Sensors
                          │
                    World Evidence
                          │
                          └──────────────→ Memory
```

Surrounding the entire system:

```text
Safety
Security
Provenance
Observability
Recovery
Privacy
Resource Governance
Evaluation
Simulation
Model/Skill Lifecycle
```

---

# 29. Final Strategic Position

Novi should not be designed as an "NVIDIA robot" or an "LLM robot".

It should be designed as:

> **A hardware- and vendor-independent autonomous intelligence architecture whose physical-AI implementation can exploit the best available neural models, robotics middleware, simulation systems, and edge-compute platforms.**

The most important architectural separation is:

```text
Model
  ≠
Cognition
  ≠
Memory
  ≠
World Model
  ≠
Planning
  ≠
Governance
  ≠
Authorization
  ≠
Controller
```

And the most important development sequence is:

```text
Architecture
    ↓
Novi Kernel
    ↓
Memory / Evidence
    ↓
World Model
    ↓
Continuous Cognitive Loop
    ↓
Local Reasoning Model
    ↓
Real Perception
    ↓
Simulation
    ↓
Learned Skills
    ↓
Physical Robot
    ↓
Hardware Optimization
```

The project should reach a point where the **brain is demonstrably useful before the body becomes expensive**.

That is the central strategy for Novi.
