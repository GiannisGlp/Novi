# 00 — High-Level Architecture

## 1. Executive Summary

Novi is the implementation platform for Wheely, an autonomous embodied AI system. The intended system continuously perceives the environment, builds and updates an internal representation of the world, retrieves relevant memory and knowledge, evaluates what deserves attention, reasons about goals, decides whether and how to interact, performs actions through controlled capabilities, observes the outcome, and learns from the resulting experience.

The architecture is deliberately split into two broad domains:

1. **Adaptive intelligence** — models, memory, knowledge, personality, attention, curiosity, planning, and learned behavior.
2. **Protected execution** — safety policy, authorization, hardware limits, privileged robotics services, emergency stop, and immutable system configuration.

Adaptive intelligence can evolve. Protected execution cannot be modified by the adaptive system through normal application capabilities.

## 2. Product Definition

Novi/Wheely should behave as an autonomous robotic companion rather than a conventional prompt/response assistant.

Desired properties:

- continuous environmental awareness;
- context-aware and selective interaction;
- persistent personality;
- differentiated relationships with family, known people, and strangers;
- multimodal perception;
- long-term memory;
- spatial and temporal understanding;
- curiosity and controlled exploration;
- ability to recognize uncertainty and ask questions;
- ability to learn from people while tracking provenance;
- ability to create new knowledge and data structures when justified;
- local-first operation;
- safe physical action;
- hardware diagnostics and auditability;
- evolution of knowledge and behavior without uncontrolled self-modification.

## 3. System Context

```text
                 HUMAN / HOUSEHOLD / WORLD
                           │
                ┌──────────▼──────────┐
                │      SENSORS       │
                │ camera/audio/IMU/...│
                └──────────┬──────────┘
                           │ observations
                           ▼
                 ┌───────────────────┐
                 │     PERCEPTION    │
                 └─────────┬─────────┘
                           │ events/evidence
                           ▼
                 ┌───────────────────┐
                 │    WORLD MODEL    │
                 └─────────┬─────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
         MEMORY        KNOWLEDGE       ATTENTION
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                     GOALS / POLICY
                           │
                           ▼
                     AGENT RUNTIME
                           │
                           ▼
                      NEMOTRON
                           │
                     tool/action plan
                           ▼
                    SAFETY GATEWAY
                           │
                           ▼
                         ROS 2
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
          MOTION        INTERACTION       IOT
```

## 4. Major Subsystems

### 4.1 Perception

Converts raw sensor streams into structured observations and evidence. It includes visual detection, visual reasoning, speech recognition, audio event detection, face/voice identity, body/gesture signals, environmental sensors, and multimodal fusion.

Perception should produce evidence with timestamps, source, confidence, and provenance. It must not silently convert an uncertain observation into a permanent fact.

### 4.2 World Model

Represents the current and historical state of people, places, objects, rooms, relationships, routines, spatial state, temporal state, and situations.

The world model is not the same as memory. It represents structured state that can change over time while preserving historical evidence.

### 4.3 Memory and Knowledge

Memory preserves experiences and learned information. Knowledge represents structured facts and concepts. Both must support provenance and confidence.

Novi should support:

- working memory;
- episodic memory;
- semantic memory;
- spatial memory;
- procedural memory;
- owner-verified knowledge;
- external/world knowledge;
- household knowledge;
- personal knowledge;
- multimodal memories.

### 4.4 Attention

Attention decides whether an event should be ignored, monitored, remembered, acted on, or surfaced to a person.

Attention is separate from the LLM. The LLM can help reason about a situation, but the entire environment should not be sent to the model continuously.

### 4.5 Personality and Social State

Personality provides stable behavioral traits such as playfulness, curiosity, warmth, humor, and conversational style. Social state provides dynamic context such as familiarity, relationship, current interaction state, and inferred emotional context.

### 4.6 Autonomy

The autonomy engine maintains the continuous loop. It coordinates perception, attention, goals, memory, reasoning, planning, action requests, and learning.

### 4.7 Agent Runtime

The agent runtime provides model context, tool definitions, structured outputs, reasoning execution, planning, cancellation, retries, and traceability.

### 4.8 Models

The primary general reasoning candidate is NVIDIA Nemotron 3 Nano 30B-A3B. It is not responsible for all AI tasks. Specialized models remain appropriate for speech, object detection, face recognition, embeddings, visual reasoning, and other high-frequency workloads.

### 4.9 Tools

Tools provide controlled access to capabilities such as navigation, IoT, time, calculations, files, knowledge, diagnostics, and external services. Tools have explicit schemas and permissions.

### 4.10 Safety Gateway

The safety gateway validates physical action requests and enforces immutable constraints before commands reach robotics middleware or hardware.

### 4.11 Robotics Layer

ROS 2 is the principal robotics integration boundary. Isaac ROS and NVIDIA accelerated components may provide implementations behind this boundary.

## 5. Core Data Flow

The preferred data flow is:

```text
raw sensor
  ↓
observation
  ↓
event / evidence
  ↓
world-model update
  ↓
attention evaluation
  ↓
memory / knowledge retrieval
  ↓
context construction
  ↓
reasoning / planning
  ↓
policy evaluation
  ↓
action request
  ↓
safety validation
  ↓
execution
  ↓
result observation
  ↓
experience / learning
```

## 6. Autonomy Model

Novi must not be implemented as a request-response loop only.

A continuously running autonomy loop should operate on event streams and periodic evaluation cycles. The system should be able to remain silent while observing, become attentive when something relevant happens, and initiate appropriate interaction when policy permits it.

Example:

```text
Person enters room
  ↓
Face recognized
  ↓
Relationship = family
  ↓
No active interaction
  ↓
Attention = observe
  ↓
Person speaks directly to Novi
  ↓
Attention = engage
  ↓
Retrieve recent relationship/context
  ↓
Reason
  ↓
Respond using personality + social context
```

## 7. Learning Model

Learning occurs primarily through state and knowledge evolution rather than uncontrolled source-code modification.

```text
experience
  ↓
observation
  ↓
candidate interpretation
  ↓
evidence accumulation
  ↓
hypothesis
  ↓
verification when appropriate
  ↓
knowledge/memory update
```

A new observation must not automatically become a permanent truth.

## 8. Data Generation

Novi may generate data as part of normal operation. This includes:

- new entities;
- relationships;
- observations;
- memories;
- embeddings;
- documents;
- structured records;
- learned schemas;
- simulation scenarios;
- diagnostic reports.

Generated data must pass through governed APIs and storage policies. The adaptive system must not directly modify immutable safety or system foundations.

## 9. Runtime Environments

### Mac

Primary software-development environment. Supports cognitive development, local models where practical, camera/microphone testing, data generation, UI, memory, knowledge, simulated hardware, and most automated tests.

### Simulation

Isaac Sim + ROS 2 is the reference robotics simulation environment. It supplies virtual sensors, robot state, environments, people, objects, navigation scenarios, and fault injection.

### Jetson

Jetson AGX Orin 64GB is the reference edge target. NVIDIA-specific implementations include JetPack, CUDA, TensorRT, Isaac ROS, and other validated components.

### Physical robot

The final deployment combines the Jetson runtime with physical sensors, motors, head mechanism, display, audio, battery, networking, and safety hardware.

## 10. Vendor Boundary

NVIDIA is the reference platform because the target robot is Jetson-based and the system benefits from NVIDIA's robotics and accelerated-AI ecosystem.

However:

```text
NVIDIA platform implementation
             ↓
       Wheely interfaces
             ↓
       Cognitive core
```

not:

```text
Cognitive core
      ↓
NVIDIA-specific APIs everywhere
```

This allows future hardware/runtime changes without rewriting the cognitive architecture.

## 11. Non-Goals

The system is not intended to:

- give an LLM unrestricted shell access;
- let an LLM directly control motors;
- let learned behavior rewrite safety constraints;
- treat all observations as facts;
- make the entire knowledge base part of every model prompt;
- require one model to perform every modality;
- hard-code every possible future entity into the initial schema;
- depend on cloud services for core autonomy.

## 12. High-Level Acceptance Criteria

The architecture is considered viable when the Mac runtime can demonstrate:

1. continuous perception/event processing;
2. persistent world state;
3. persistent memory and knowledge;
4. selective attention;
5. personality-aware responses;
6. relationship-aware interaction;
7. controlled curiosity;
8. evidence-based learning;
9. controlled data/schema generation;
10. tool use;
11. safety-gated action planning;
12. complete audit traces;
13. simulated robot operation;
14. hardware-independent interfaces.

The Jetson implementation must then demonstrate the same behavior under real edge constraints, with NVIDIA-specific performance and hardware validation.
