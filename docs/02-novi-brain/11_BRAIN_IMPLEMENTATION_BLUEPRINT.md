# 11 — Brain Implementation Blueprint

**Status:** P0 — implementation gate
**Owner:** `02-novi-brain`
**Primary target:** MacBook Pro, Apple M3 Pro, 38 GB unified memory, 1 TB internal storage, latest macOS
**Purpose:** Convert the existing Novi architecture into an implementation-ready map without creating competing semantic authorities.

---

## 1. Purpose and scope

This document is the bridge between Novi's documentation and the first working Brain implementation.

It does **not** redefine Brain, Cognition, Memory, Autonomy, Safety, or System Architecture. Their existing canonical documents remain authoritative.

Its job is to answer, for every implementation capability:

```text
What is specified?
        ↓
Who owns the semantics?
        ↓
What runtime component implements it?
        ↓
What interface connects it?
        ↓
What runs on the Mac?
        ↓
What model/algorithm is used?
        ↓
How is it tested?
        ↓
How is it benchmarked?
        ↓
How can it later move to robot hardware?
```

No implementation begins until the relevant capability has an identified owner, interface, implementation path and acceptance test.

---

## 2. Architectural law

> **The Brain is an execution system, not a monolithic intelligence model.**

Novi's intelligence is intentionally hybrid:

```text
Neural models
      +
Structured state
      +
Memory
      +
Reasoning
      +
Planning
      +
Rules/constraints
      +
Runtime orchestration
      +
Safety governance
      ↓
Embodied intelligence
```

A neural network is therefore a capability provider inside the Brain ecosystem, not the Brain itself.

---

## 3. Canonical ownership

| Capability | Canonical owner | Brain role |
|---|---|---|
| System contracts | System Architecture | Execute/consume |
| Brain lifecycle | Brain | Own |
| Runtime orchestration | Brain | Own |
| Model execution | Brain | Own runtime |
| Perception execution | Brain | Own runtime |
| World semantics | Cognition | Execute |
| Situation model | Cognition | Execute |
| Reasoning | Cognition | Execute |
| Prediction | Cognition | Execute |
| Identity/personality/affect | Cognition | Execute |
| Long-term memory | Memory & Knowledge | Execute |
| Knowledge | Memory & Knowledge | Execute |
| Goals/behavior | Autonomy | Execute |
| Safety authorization | System Architecture | Consume decision |
| Physical control | Hardware | Interface only |

The existing Brain architecture explicitly establishes this boundary: Brain coordinates and executes, Cognition understands, Memory remembers/knows, Autonomy chooses/pursues, Policy permits/denies, and Hardware executes physical control. fileciteturn72file0

---

## 4. Target runtime topology

The first Mac implementation should use a modular topology that can later be distributed without changing semantic contracts.

```text
                       BRAIN SUPERVISOR
                              │
          ┌───────────────────┼───────────────────┐
          ↓                   ↓                   ↓
     Sensor Runtime      Model Runtime       State Runtime
          │                   │                   │
          ↓                   ↓                   ↓
      Perception        Neural/AI models     Brain State
          │                   │                   │
          └──────────────┬────┴───────────────────┘
                         ↓
                    COGNITION
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
      World Model     Reasoning     Prediction
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                  MEMORY / KNOWLEDGE
                         │
                         ↓
                     AUTONOMY
                         │
                  Goal / Plan / Skill
                         ↓
                   Action Proposal
                         ↓
                 SAFETY / GOVERNANCE
                         ↓
                Controller Interface
                         ↓
               Simulation / Mock Body
                         ↓
                      Outcome
                         ↓
              Memory + Cognition update
```

The loop must remain continuous. A user prompt is only one possible stimulus.

---

## 5. Brain supervisor

The supervisor is the top-level runtime authority for software lifecycle, not semantic decision-making.

Responsibilities:

- startup sequencing;
- dependency readiness;
- lifecycle management;
- process/task supervision;
- configuration loading;
- capability registration;
- health aggregation;
- restart/recovery;
- graceful shutdown;
- resource/degradation coordination;
- observability registration.

It must **not** decide goals or bypass safety.

### Required states

```text
BOOTING
INITIALIZING
READY
ACTIVE
DEGRADED
RECOVERING
SAFE_STOP
SHUTTING_DOWN
FAILED
```

---

## 6. Core runtime components

### 6.1 Sensor Runtime

Normalizes incoming sensor or simulated-sensor data into canonical observations.

Responsibilities:

- acquisition;
- timestamps;
- sequence numbers;
- calibration metadata;
- frame/coordinate metadata;
- freshness;
- quality flags;
- buffering;
- drop detection.

### 6.2 Perception Runtime

Executes perception models and classical algorithms.

Produces evidence, not commands.

Examples:

- objects;
- people;
- faces where permitted;
- poses;
- speech/audio events;
- scene attributes;
- depth;
- motion;
- localization observations.

### 6.3 Model Runtime

Provides a common execution interface around heterogeneous models.

Responsibilities:

- model loading;
- version/digest validation;
- backend selection;
- batching where appropriate;
- inference;
- cancellation;
- resource accounting;
- fallback;
- health;
- latency measurement.

The existing Brain documents already define neural-network strategy, model taxonomy, routing/selection, lifecycle and model runtime. This blueprint maps those specifications to implementation; it does not replace them. fileciteturn73file0

### 6.4 Brain State Runtime

Maintains short-lived execution state needed to coordinate the embodied loop.

It must not become a duplicate of the canonical World Model or long-term Memory.

### 6.5 Cognition Adapter

Provides typed interfaces into the Cognition domain.

Expected capabilities:

- update evidence;
- query current situation;
- query world state;
- invoke reasoning;
- request prediction;
- update cognitive context;
- expose uncertainty.

### 6.6 Memory Adapter

Provides typed interfaces into Memory & Knowledge.

Expected capabilities:

- store eligible memories;
- retrieve memories;
- query knowledge;
- retrieve provenance;
- update/revise beliefs;
- request consolidation.

The existing Memory domain already specifies taxonomy, lifecycle, provenance, retrieval/consolidation, knowledge graph, identity, temporal/spatial memory and related capabilities. fileciteturn75file0

### 6.7 Autonomy Adapter

Provides:

- goals;
- priorities;
- plan requests;
- behavior state;
- interruptions;
- action proposals;
- replanning requests.

Brain executes the runtime path but does not become the behavioral authority.

### 6.8 Safety Adapter

Accepts ActionProposal records and returns the canonical authorization decision.

No Brain component may bypass this boundary.

### 6.9 Body/Controller Adapter

Initially this may be a simulator/mock.

Later it may connect to robot controllers.

The Brain must see a capability interface rather than assuming a specific motor platform.

---

## 7. Cognitive loop implementation

The first closed loop should implement:

```text
INPUT
 ↓
OBSERVE
 ↓
PERCEIVE
 ↓
UPDATE EVIDENCE
 ↓
UPDATE WORLD/SITUATION
 ↓
ATTEND
 ↓
REACT / THINK / WAIT
 ↓
SELECT GOAL
 ↓
PLAN / SKILL
 ↓
PROPOSE ACTION
 ↓
SAFETY
 ↓
EXECUTE OR SIMULATE
 ↓
OBSERVE OUTCOME
 ↓
UPDATE STATE
 ↓
MEMORY / LEARNING
 ↓
NEXT CYCLE
```

This must support multiple rates rather than one global loop frequency.

---

## 8. First Mac implementation

The Mac is Development Target #1.

The first implementation should run locally wherever practical and avoid depending on unavailable robot hardware.

### Mac backend

```text
Novi interface
      ↓
Mac adapter
      ↓
Apple Silicon CPU/GPU
```

The semantic interfaces must not expose Apple-specific details.

### Future edge backend

```text
Novi interface
      ↓
Edge adapter
      ↓
NVIDIA / other accelerator
```

The future robot target remains an empirical deployment decision.

---

## 9. Neural network placement

Neural networks should initially be evaluated for:

### Perception

- object detection;
- tracking assistance;
- image/scene understanding;
- speech recognition;
- audio classification;
- multimodal interpretation.

### Cognitive assistance

- language understanding;
- multimodal reasoning;
- learned prediction;
- semantic representation.

### Future learned behavior

Learned policies may be evaluated only behind action/safety contracts.

The default design is **not** end-to-end neural control.

```text
Neural model
    ↓
Evidence / prediction / proposal
    ↓
Structured state + reasoning
    ↓
Autonomy
    ↓
Safety
    ↓
Control
```

---

## 10. Personality and continuity

Personality is not a prompt template.

Novi's persistent identity should emerge from coordinated state across:

```text
Identity
 +
Personality
 +
Values
 +
Preferences
 +
Affect
 +
Goals
 +
Relationships
 +
Autobiographical memory
 +
Experience
 →
Behavioral continuity
```

The canonical personality/identity material belongs to Cognition; Brain provides the runtime pathways that allow those state changes to influence behavior.

---

## 11. The “soul” concept

For Novi design purposes, **soul is a conceptual term, not a software component**.

It describes the desired continuity of:

- identity;
- memories;
- personality;
- values;
- relationships;
- preferences;
- experiences;
- learned tendencies;
- current internal state;
- behavioral history.

We must not create a `SoulService`, `SoulModel`, or other artificial subsystem solely to satisfy the metaphor.

The engineering objective is to make the resulting system exhibit coherent continuity over time.

---

## 12. Minimum interfaces

The initial Brain implementation should define typed interfaces for at least:

```text
Observation
Evidence
WorldState
Situation
MemoryQuery
MemoryRecord
KnowledgeQuery
Goal
Plan
Skill
ActionProposal
SafetyDecision
ActionExecution
ActionOutcome
InternalState
PersonState
ModelInvocation
ModelResult
HealthState
DiagnosticEvent
```

These interfaces must use the canonical system contracts rather than creating local incompatible versions.

---

## 13. Initial process boundaries

The first Mac version does not need a distributed microservice architecture.

Prefer a modular monolith/process architecture where practical:

```text
novi-brain
├── supervisor
├── sensor-runtime
├── perception-runtime
├── model-runtime
├── state-runtime
├── cognition-adapter
├── memory-adapter
├── autonomy-adapter
├── safety-adapter
├── body-adapter
└── observability
```

Components should communicate through explicit interfaces/events even when they initially execute in one process.

This preserves a path to later process separation without prematurely paying distributed-system complexity.

---

## 14. Data flow rules

### Rule 1 — Evidence is not truth

Perception produces observations/evidence with uncertainty and provenance.

### Rule 2 — State is not memory

Current working state must not be treated as historical memory.

### Rule 3 — Memory is not world state

Historical records can inform current beliefs but do not automatically overwrite current observations.

### Rule 4 — Thought is not action

Reasoning and planning may propose actions; they do not authorize them.

### Rule 5 — Model output is untrusted input

Neural/LLM/VLM output must pass through typed contracts and appropriate governance.

### Rule 6 — Failure is explicit

Missing, stale, contradictory or low-confidence information must remain representable.

---

## 15. Implementation order

The first implementation should not begin with a humanoid robot, Jetson, or a large collection of neural networks.

### Stage 0 — Contract foundation

Implement:

- canonical data types;
- timestamps;
- IDs/correlation;
- health;
- errors;
- configuration;
- observability.

### Stage 1 — Brain runtime skeleton

Implement:

- supervisor;
- lifecycle;
- scheduler;
- event/state loop;
- resource monitoring;
- adapters;
- simulated body.

### Stage 2 — Minimal perception

Implement a small local perception capability using prerecorded or generated inputs.

### Stage 3 — World + memory

Implement:

- current world state;
- working memory;
- durable memory interface;
- retrieval;
- provenance.

### Stage 4 — Cognition

Implement a closed cognitive loop with reasoning and situation updates.

### Stage 5 — Personality/continuity

Introduce persistent identity, preferences, affect and autobiographical continuity.

### Stage 6 — Autonomy

Introduce proactive goals, planning and interruption.

### Stage 7 — Action simulation

Let Novi propose and execute abstract/simulated actions through safety.

### Stage 8 — Multimodal interaction

Add speech/audio/vision interaction and cross-modal fusion.

### Stage 9 — Physical hardware

Only after the Brain demonstrates meaningful closed-loop behavior should hardware-specific integration begin.

---

## 16. First “brain is alive” milestone

Before committing to Jetson, Novi should demonstrate locally on the Mac that it can:

1. continuously perceive simulated/local inputs;
2. maintain a persistent world state;
3. remember relevant experiences;
4. retrieve those experiences later;
5. recognize familiar people/entities where permitted;
6. maintain a coherent identity;
7. exhibit consistent personality;
8. maintain changing internal/affective state;
9. form goals without requiring a new user prompt every cycle;
10. react to environmental changes;
11. reason about situations;
12. choose between actions;
13. explain structured decision evidence;
14. pass every action through safety/governance;
15. observe outcomes;
16. update memory/state from outcomes;
17. continue operating when no user is actively interacting.

This is the first meaningful definition of **“the brain is really a brain”** for the project.

---

## 17. Evaluation framework

Every capability must have:

```text
Specification
 ↓
Unit test
 ↓
Integration test
 ↓
Scenario test
 ↓
Performance benchmark
 ↓
Failure test
 ↓
Regression test
```

Important metrics include:

- perception latency;
- cognitive-cycle latency;
- memory retrieval latency;
- planning latency;
- action proposal latency;
- end-to-end reaction latency;
- sustained runtime stability;
- resource consumption;
- model failure/fallback rate;
- memory consistency;
- identity continuity;
- behavioral consistency;
- safety intervention rate.

---

## 18. Mac acceptance criteria

The initial Brain is considered Mac-ready when:

- it starts from a clean environment;
- all required dependencies are version-pinned/recorded;
- the Brain supervisor reaches READY;
- simulated/local inputs can enter the loop;
- perception produces canonical evidence;
- Cognition can update/query state;
- Memory can persist/retrieve records;
- Autonomy can produce an ActionProposal;
- Safety can authorize/deny it;
- a simulated body can execute it;
- outcomes return to the Brain;
- observability can reconstruct the cycle;
- failure/degradation paths are exercised;
- resource usage is measured;
- tests are reproducible.

---

## 19. Hardware migration criteria

Do not choose Jetson merely because the Brain works.

Collect measured workload requirements first:

```text
CPU
GPU
accelerator
RAM
VRAM/unified memory
storage
power
thermal
latency
sensor bandwidth
model set
concurrency
```

Then compare candidate deployment hardware against those requirements.

The hardware decision must be recorded as an ADR supported by measurements.

---

## 20. Required implementation artifacts

Before coding the full Brain, the repository should contain or identify:

- canonical contract schemas;
- interface definitions;
- Brain state definitions;
- lifecycle state machine;
- runtime configuration schema;
- model registry schema;
- model metadata format;
- memory interface schema;
- observation/evidence schema;
- goal/plan/action schemas;
- safety decision schema;
- diagnostic event schema;
- test fixtures;
- simulation/mock interfaces;
- benchmark harness;
- Mac environment snapshot;
- dependency/version lock information.

---

## 21. What this document does NOT authorize

This blueprint does not authorize:

- physical actuator control;
- autonomous operation without safety validation;
- adoption of Jetson;
- adoption of a specific neural architecture without benchmark evidence;
- treating LLM output as ground truth;
- treating personality as a prompt-only feature;
- creating duplicate semantic authorities;
- bypassing canonical system contracts.

---

## 22. Definition of implementation readiness

Novi Brain is implementation-ready when every P0 capability can be traced:

```text
North Star / requirement
        ↓
Canonical owner
        ↓
Contract
        ↓
Brain runtime component
        ↓
Implementation
        ↓
Mac execution path
        ↓
Test
        ↓
Benchmark
        ↓
Observed result
```

If any P0 capability cannot complete this chain, the implementation gate remains closed.

---

## 23. Guiding principle

> **Build Novi's brain as a continuously running embodied intelligence system whose identity, cognition, memory, personality, perception, autonomy and learned models work together — while keeping every consequential physical action behind explicit contracts, governance and safety.**

The Mac is where this architecture must first prove itself.

The robot is the next embodiment, not the definition of the Brain.
