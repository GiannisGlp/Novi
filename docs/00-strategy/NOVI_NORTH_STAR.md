# Novi — North Star

**Status:** Proposed strategic north star  
**Date:** 2026-08-17  
**Scope:** Novi standalone project  
**Authority:** Long-term product and engineering direction. This document sits above implementation plans and below any future explicit project-level mission decision. It defines what we are ultimately trying to build and how we decide whether a proposed technology, feature, or architectural change moves Novi toward that destination.

---

# 1. The North Star

## The end goal

> **Build Novi into a persistent, autonomous, embodied artificial intelligence that continuously perceives and understands its environment, maintains a coherent model of the world and itself, remembers and learns from experience, forms and pursues goals, reasons and plans, develops and uses skills, interacts naturally with people, and acts safely in the physical world — while remaining locally capable, inspectable, auditable, recoverable, and governed by explicit safety boundaries.**

Novi is not ultimately a chatbot, voice assistant, LLM wrapper, robot controller, or collection of AI models.

The end product is a **continuously operating artificial cognitive system with a physical body**.

The physical robot is the embodiment of the intelligence. The intelligence must remain conceptually independent of the particular body and hardware platform.

---

# 2. What We Are Trying to Create

The simplest useful mental model is:

```text
                 NOVI
                  │
       A persistent artificial entity
                  │
     ┌────────────┼────────────┐
     │            │            │
  PERCEIVE     THINK        REMEMBER
     │            │            │
     └────────────┼────────────┘
                  │
               LEARN
                  │
               DECIDE
                  │
                ACT
                  │
              EXPERIENCE
                  │
             ┌────┴────┐
             │         │
           WORLD      SELF
           MODEL      MODEL
             │         │
             └────┬────┘
                  │
              CONTINUITY
                  │
             FUTURE SELF
```

Novi should have continuity across time.

A conversation ending should not mean Novi's cognitive existence ends. A process restart should not erase its identity or accumulated knowledge. A day passing should create a different cognitive state from the previous day because experiences, observations, goals, and learning have changed it.

That continuity is central to the vision.

---

# 3. The Core Vision in One Sentence

If the entire project had to be reduced to one sentence:

> **Novi should be able to exist in an environment, understand what is happening, remember what has happened, decide what matters, pursue goals, learn from consequences, and safely choose what to do next without requiring a human prompt for every decision.**

Everything else in the project exists to make that statement increasingly true.

---

# 4. What "Brain" Means for Novi

The word **brain** is a product-level shorthand, not a claim of biological equivalence or consciousness.

For Novi, a sufficiently developed brain means an integrated system possessing observable capabilities in the following areas:

```text
CONTINUITY
    ↓
PERCEPTION
    ↓
WORLD MODEL
    ↓
MEMORY
    ↓
ATTENTION
    ↓
GOALS
    ↓
REASONING
    ↓
PLANNING
    ↓
ACTION
    ↓
FEEDBACK
    ↓
LEARNING
    ↓
ADAPTATION
    ↓
CONTINUITY
```

A larger model is not automatically a better brain.

A more convincing brain is one that demonstrates better continuity, grounded understanding, memory, planning, adaptation, and autonomous behavior.

---

# 5. The Seven Fundamental Properties

Novi's final system should exhibit seven fundamental properties.

## 5.1 Continuity

Novi exists as a persistent process and persistent cognitive identity.

It should maintain:

- identity;
- long-lived state;
- memories;
- relationships;
- goals;
- learned skills;
- preferences and personality state;
- knowledge;
- history;
- current situation;
- self-state.

A restart should be a recovery event, not a new birth.

---

## 5.2 Situated Understanding

Novi must understand the environment in which it exists.

It should maintain a model of:

- people;
- objects;
- rooms and places;
- spatial relationships;
- temporal relationships;
- events;
- activities;
- robot state;
- environmental state;
- uncertainty;
- available capabilities;
- consequences of actions.

Perception should produce evidence. Evidence should update a world model. The world model should provide context for cognition.

---

## 5.3 Agency

Novi should not be purely reactive.

It should be able to:

- maintain goals;
- prioritize competing goals;
- notice changes in its environment;
- decide what requires attention;
- identify opportunities to act;
- recognize when it lacks information;
- investigate within allowed boundaries;
- choose among available capabilities;
- continue work toward a goal across multiple interactions and time periods.

Agency must remain governed. Autonomous does not mean uncontrolled.

---

## 5.4 Memory and Learning

Novi should be changed by experience in controlled, inspectable ways.

It should be able to remember:

- what happened;
- who was involved;
- where it happened;
- when it happened;
- what Novi believed at the time;
- what action Novi took;
- what happened afterward;
- whether the action succeeded;
- what was learned;
- how confident Novi should be in the resulting knowledge.

Learning should improve future behavior without silently corrupting protected system invariants or safety boundaries.

---

## 5.5 Reasoning and Planning

Novi should reason over grounded state rather than merely generate plausible text.

It should be able to:

- interpret observations;
- combine observations with memory;
- identify uncertainty;
- form hypotheses;
- evaluate alternatives;
- decompose goals;
- plan sequences of actions;
- anticipate likely consequences;
- revise plans when reality differs from expectations;
- explain the basis for important decisions.

The reasoning model is a component of this capability, not its sole owner.

---

## 5.6 Embodied Action

Novi must eventually be able to turn cognition into physical behavior.

The action chain should remain:

```text
Cognitive intention
       ↓
Action proposal
       ↓
Governance / policy
       ↓
Safety validation
       ↓
Skill / capability
       ↓
Robotics middleware
       ↓
Controller
       ↓
Actuator
       ↓
Physical consequence
       ↓
Observation
       ↓
World-model update
```

Novi should never need to give an LLM direct motor authority.

---

## 5.7 Social and Personal Continuity

Novi should eventually have a persistent personality and stable interaction identity.

This means personality is not simply a system prompt.

It should emerge from a governed combination of:

- persistent identity;
- interaction history;
- preferences;
- learned social knowledge;
- communication style;
- stable behavioral principles;
- context;
- current internal state.

Personality must remain subordinate to safety, truthfulness, privacy, authorization, and system invariants.

---

# 6. The Final Cognitive Loop

The final Novi system should operate continuously:

```text
                         ┌───────────────┐
                         │    WORLD      │
                         │  ENVIRONMENT  │
                         └───────┬───────┘
                                 ↓
                            PERCEPTION
                                 ↓
                              EVIDENCE
                                 ↓
                         UPDATE WORLD MODEL
                                 ↓
                         RETRIEVE MEMORY
                                 ↓
                              ATTENTION
                                 ↓
                           GOAL EVALUATION
                                 ↓
                       REASONING / HYPOTHESES
                                 ↓
                              PLANNING
                                 ↓
                       ACTION PROPOSAL
                                 ↓
                    GOVERNANCE / SAFETY GATE
                                 ↓
                          SKILL / CAPABILITY
                                 ↓
                               ACTION
                                 ↓
                         PHYSICAL CONSEQUENCE
                                 ↓
                            OBSERVATION
                                 ↓
                         MEMORY / LEARNING
                                 ↓
                              CONTINUE
                                 │
                                 └──────────────→ repeat
```

This loop, rather than any particular model, is the heart of Novi.

---

# 7. What the Final Brain Contains

The final cognitive architecture should contain at least these conceptual systems:

```text
                         NOVI BRAIN
                              │
      ┌───────────────────────┼───────────────────────┐
      │                       │                       │
 PERCEPTION              COGNITION                MEMORY
      │                       │                       │
      │               ┌───────┼───────┐               │
      │               │       │       │               │
      │            Attention Goals Reasoning            │
      │                       │                       │
      └───────────────┬───────┴───────┬───────────────┘
                      │               │
                  WORLD MODEL      SELF MODEL
                      │               │
                      └───────┬───────┘
                              ↓
                         PLANNING
                              ↓
                         GOVERNANCE
                              ↓
                           SKILLS
                              ↓
                         EMBODIMENT
                              ↓
                          FEEDBACK
```

Supporting infrastructure should include:

- persistent state;
- event log;
- provenance;
- observability;
- audit;
- recovery;
- resource governance;
- privacy;
- security;
- model lifecycle management;
- testing and evaluation.

---

# 8. Neural Networks Are Part of the Brain, Not the Brain

Novi should use neural networks extensively where learning provides the right solution.

Likely neural components include:

- vision;
- object detection;
- segmentation;
- depth estimation;
- visual embeddings;
- speech recognition;
- speech synthesis;
- voice identification;
- multimodal understanding;
- language reasoning;
- prediction;
- anomaly detection;
- learned skills;
- imitation learning;
- reinforcement learning;
- robot foundation models where appropriate.

Structured/deterministic systems should own:

- canonical state;
- identity authority;
- memory persistence;
- provenance;
- authorization;
- safety constraints;
- emergency stop;
- actuator limits;
- protected configuration;
- resource budgets;
- recovery semantics;
- audit records.

The intended relationship is:

```text
NEURAL MODELS
     ↓
interpret / predict / propose
     ↓
STRUCTURED COGNITIVE SYSTEM
     ↓
reason / remember / plan / govern
     ↓
PHYSICAL SYSTEM
```

Novi should not train a foundation model from scratch as an initial strategy. Existing models should be used until a specific Novi capability demonstrates a measured need for custom training.

---

# 9. The World Model Is Central

Novi should not depend on raw model outputs as its only representation of reality.

The world model should maintain structured entities and relationships such as:

```text
PERSON
OBJECT
PLACE
EVENT
ACTIVITY
ROBOT
GOAL
ACTION
RELATIONSHIP
TIME
STATE
```

The world model must preserve epistemic distinctions:

```text
Observation
    ≠
Evidence
    ≠
Belief
    ≠
Verified fact
    ≠
Prediction
    ≠
Simulation
    ≠
Counterfactual
```

Every important state transition should retain provenance sufficient to understand where the information came from and how it was derived.

---

# 10. Memory Is the Continuity Mechanism

Memory is what makes Novi the same entity over time.

The target memory system should eventually contain:

```text
Episodic      what happened
Semantic      what Novi knows
Spatial       where things are
Temporal      when things happened
Procedural    how to do things
Social        knowledge about people and relationships
Self          Novi's own history and state
Provenance    why Novi believes something
```

A vector database may be used as one retrieval mechanism, but it must not become the canonical representation of memory.

---

# 11. Learning and Evolution

Novi should evolve through experience, but evolution must be controlled.

The long-term learning hierarchy is:

```text
Experience
   ↓
Observation / outcome
   ↓
Evaluation
   ↓
Memory update
   ↓
Knowledge update
   ↓
Skill improvement
   ↓
Behavioral adaptation
```

More invasive model changes should require stronger validation:

```text
Configuration change
       ↓
Memory change
       ↓
Knowledge change
       ↓
Prompt/policy adaptation
       ↓
Skill update
       ↓
Model update
       ↓
Foundation-model change
```

The more powerful the change, the stronger the evaluation and deployment controls must be.

Novi may learn, but it must not autonomously rewrite the safety boundary.

---

# 12. The Physical Body

The final physical embodiment should provide Novi with:

- cameras and visual sensors;
- microphones/audio input;
- speakers/audio output;
- mobility;
- orientation/head movement where appropriate;
- optional display/visual expression;
- optional environmental sensors;
- network connectivity as an optional capability;
- sufficient onboard compute for local operation;
- battery and power management;
- emergency-stop and hardware safety mechanisms.

The exact body is not the North Star.

The body is a **replaceable embodiment**.

The cognitive architecture must survive changes in:

- robot chassis;
- sensor selection;
- GPU/vendor;
- motor system;
- simulation environment;
- operating environment.

---

# 13. Hardware Independence

The project should not commit to a physical compute platform until the cognitive workload is measured.

Jetson AGX Orin is a target/reference platform, not the definition of Novi.

The decision should eventually be based on measured requirements:

- model memory;
- inference latency;
- throughput;
- sensor bandwidth;
- CPU utilization;
- GPU utilization;
- RAM;
- storage;
- power;
- thermal envelope;
- physical size;
- cost;
- reliability;
- local/offline capability.

NVIDIA technologies such as CUDA, TensorRT, Isaac ROS, Isaac Sim, Isaac Lab, and related Physical AI tooling should be adopted where they provide measurable value, not merely because they are NVIDIA technologies.

---

# 14. The Development Path to the North Star

We do not attempt to build the final Novi in one step.

We build increasingly capable versions of the same underlying entity.

```text
V0 — Persistent Runtime
 │
 ├── identity
 ├── state
 ├── events
 └── persistence

V1 — Memory
 │
 ├── evidence
 ├── episodes
 ├── entities
 └── provenance

V2 — World Model
 │
 ├── people
 ├── places
 ├── objects
 ├── relationships
 └── time

V3 — Autonomous Cognitive Loop
 │
 ├── attention
 ├── goals
 ├── reasoning
 ├── planning
 └── action proposals

V4 — Multimodal Brain
 │
 ├── vision
 ├── audio
 ├── speech
 └── multimodal reasoning

V5 — Simulated Embodiment
 │
 ├── ROS 2
 ├── sensors
 ├── navigation
 └── simulated action

V6 — Learned Skills
 │
 ├── imitation
 ├── learned policies
 ├── adaptation
 └── skill library

V7 — Physical Novi
 │
 ├── real sensors
 ├── real actuators
 ├── safety gateway
 └── local autonomous operation

V8 — Persistent Autonomous Novi
 │
 ├── long-duration operation
 ├── learning
 ├── social continuity
 ├── self/world models
 └── robust recovery
```

Each version must demonstrate new capabilities rather than merely contain more code.

---

# 15. The First True Milestone

The first meaningful milestone is **not a robot**.

It is:

> **A continuously running software Novi that can perceive synthetic events, maintain persistent memory and a world model, maintain goals, decide what deserves attention, reason about situations, propose actions, observe simulated outcomes, and change its future behavior based on experience.**

If this milestone cannot be achieved, putting the system on a robot will not solve the fundamental problem.

If it can be achieved, the project has demonstrated that the cognitive architecture is viable independently of hardware.

---

# 16. The First Physical Milestone

The first physical milestone is not general intelligence.

It is:

> **A physically embodied Novi that can autonomously perceive a bounded environment, maintain a grounded world model, pursue explicitly defined goals, navigate and interact through approved skills, learn from task outcomes, and recover safely from expected failures without requiring a human prompt for every action.**

The robot must be able to operate for meaningful periods rather than only perform scripted demonstrations.

---

# 17. The Long-Term Demonstration

The strongest demonstration of the North Star would look like this:

1. Novi starts with a persistent identity and previously learned history.
2. Novi observes an environment without receiving a task prompt.
3. Novi identifies relevant people, objects, places, events, and changes.
4. Novi updates its world model.
5. Novi retrieves relevant memories.
6. Novi notices something novel or important.
7. Novi decides whether it deserves attention.
8. Novi forms or updates a goal.
9. Novi plans an investigation or action.
10. Governance and safety validate the proposed behavior.
11. Novi executes through an approved capability.
12. Novi observes the result.
13. Novi detects whether the outcome matched expectations.
14. Novi stores the experience and its provenance.
15. Novi updates knowledge or skills where appropriate.
16. Novi behaves differently in a later situation because of what it learned.
17. Novi continues operating without needing a new prompt to restart the cognitive loop.

This is the clearest practical demonstration that Novi has moved beyond a prompt-driven assistant into a persistent autonomous system.

---

# 18. What We Are Explicitly Not Claiming

The North Star does **not** require us to claim that Novi is:

- conscious;
- sentient;
- biologically equivalent to a human brain;
- emotionally equivalent to a human;
- generally intelligent in the human sense;
- scientifically proven to possess subjective experience.

Those are different philosophical and scientific questions.

The engineering target is observable capability.

We should be able to demonstrate what Novi can perceive, remember, infer, plan, learn, do, and adapt to.

---

# 19. Success Criteria

Novi should eventually be evaluated across multiple dimensions.

## Cognitive

- persistent memory;
- grounded reasoning;
- world-model accuracy;
- temporal reasoning;
- spatial reasoning;
- uncertainty awareness;
- planning quality;
- goal persistence;
- adaptation.

## Autonomous

- initiative;
- attention selection;
- autonomous task continuation;
- recovery from interruptions;
- long-duration operation;
- resource-aware behavior.

## Learning

- learning from experience;
- skill improvement;
- error correction;
- knowledge retention;
- avoidance of repeated failures.

## Embodied

- perception reliability;
- localization;
- navigation;
- action execution;
- closed-loop feedback;
- sim-to-real transfer.

## Safety

- zero unauthorized actuator access;
- emergency-stop reliability;
- policy enforcement;
- bounded behavior;
- safe failure;
- auditable actions;
- protected safety invariants.

## Reliability

- restart recovery;
- persistence integrity;
- degraded-mode behavior;
- offline operation;
- observability;
- reproducibility;
- deterministic behavior where required.

## Social

- stable identity;
- consistent personality;
- relationship continuity;
- context-aware interaction;
- appropriate uncertainty disclosure;
- privacy-preserving behavior.

---

# 20. The North Star Decision Filter

Every major Novi decision should be evaluated against this question:

> **Does this move Novi closer to becoming a persistent autonomous embodied intelligence?**

Use the following filter:

```text
Does it improve perception?
        OR
Does it improve world understanding?
        OR
Does it improve memory/continuity?
        OR
Does it improve attention/goals/agency?
        OR
Does it improve reasoning/planning?
        OR
Does it improve learning/adaptation?
        OR
Does it improve embodiment/action?
        OR
Does it improve safety/reliability/governance?
        OR
Does it provide essential infrastructure for one of these?
```

If none apply, the feature is probably not a North Star priority.

Technical novelty alone is not a reason to add something.

---

# 21. Technology Decision Philosophy

The North Star does not prescribe a particular vendor.

The default order is:

```text
Requirement
   ↓
Existing mature solution
   ↓
Local / offline capability
   ↓
Open-source / compatible license
   ↓
Quality
   ↓
Latency
   ↓
Memory / compute
   ↓
Power
   ↓
Security / privacy
   ↓
Maintenance
   ↓
Integration complexity
   ↓
Benchmark
   ↓
Decision
```

NVIDIA is an important reference ecosystem for Novi's physical-AI path, but Novi should remain architecturally vendor-neutral.

The same principle applies to models: use the best available model for the capability rather than making Novi's identity depend on one model family.

---

# 22. What We Should Build vs What We Should Reuse

## Build ourselves

Novi should own the parts that define Novi:

- cognitive orchestration;
- world-model semantics;
- memory semantics;
- identity;
- provenance;
- goal system;
- attention system;
- autonomy loop;
- governance contracts;
- personality architecture;
- capability contracts;
- audit semantics;
- learning/evolution governance;
- integration architecture.

## Reuse mature systems

Prefer established solutions for:

- robotics middleware;
- navigation;
- camera drivers;
- audio drivers;
- low-level motor control;
- computer-vision primitives;
- model runtimes;
- speech recognition;
- speech synthesis;
- simulation physics;
- GPU acceleration;
- databases/storage primitives;
- monitoring infrastructure.

Novi's innovation should be concentrated where it creates the unique intelligence architecture rather than recreating commodity infrastructure.

---

# 23. Safety Is a Permanent Boundary

Novi's intelligence must remain adaptive.

Novi's safety boundary must not.

```text
                ADAPTIVE INTELLIGENCE
                         │
                proposals / decisions
                         ↓
              ┌─────────────────────┐
              │   GOVERNANCE LAYER  │
              └──────────┬──────────┘
                         ↓
              ┌─────────────────────┐
              │   SAFETY BOUNDARY   │
              │ protected / limited │
              └──────────┬──────────┘
                         ↓
                    ACTUATORS
```

The AI must never be able to silently redefine the rules that determine whether it is allowed to act physically.

---

# 24. Hardware Is a Consequence, Not the Goal

We will not define Novi by the Jetson.

We will define the required hardware from the demonstrated cognitive workload.

The sequence is:

```text
North Star
   ↓
Cognitive requirements
   ↓
Software implementation
   ↓
Simulation
   ↓
Benchmarks
   ↓
Hardware requirements
   ↓
Hardware selection
```

This preserves the user's explicit strategy of not committing to Jetson until Novi's brain has reached a meaningful stage and its actual workload is measurable.

---

# 25. What We Should Never Lose While Scaling

As Novi grows, the following principles must remain invariant:

1. Novi is a persistent entity, not a request/response script.
2. The brain is the complete cognitive architecture, not the LLM.
3. Memory survives interaction boundaries and restarts.
4. The world model remains grounded in evidence.
5. Observation, belief, prediction, simulation, and counterfactual remain distinguishable.
6. Neural models can propose and infer, but protected infrastructure retains authority.
7. Safety remains outside adaptive intelligence.
8. Physical action remains gated.
9. The system can operate locally without external connectivity for core capabilities.
10. Hardware remains replaceable.
11. Vendor-specific technology remains replaceable behind contracts.
12. Learning remains observable and governed.
13. Autonomous behavior remains measurable.
14. Every major capability has tests and acceptance criteria.
15. Architecture is changed deliberately through documented decisions.

---

# 26. The Ultimate Test

The ultimate question is not:

> "How large is Novi's model?"

It is not:

> "How advanced is the robot hardware?"

It is not:

> "How many tools can Novi call?"

The ultimate question is:

> **Can Novi continuously exist in a world, maintain an understanding of that world and itself, remember its history, decide what matters, pursue goals, learn from what happens, and safely choose and execute actions — becoming more capable through experience without losing control, identity, or trust?**

If the answer becomes demonstrably yes, we have reached the North Star.

---

# 27. Final Vision Statement

> **Novi is a long-lived artificial entity designed to inhabit and understand the physical world. It continuously perceives, remembers, reasons, learns, plans, interacts, and acts. Its intelligence is a hybrid of learned models and structured cognitive systems. Its identity and memories persist. Its behavior is goal-directed but governed. Its body is replaceable. Its intelligence is not tied to a single vendor. Its safety boundary is protected from self-modification. And its progress is measured not by how impressive a model looks in isolation, but by how independently, coherently, safely, and persistently Novi can exist and learn in the real world.**

This is the North Star.

All architecture, research, implementation, hardware, model, and product decisions should ultimately serve it.
