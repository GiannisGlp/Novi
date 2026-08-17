# 00 — High-Level Architecture

**Status:** P0 system architecture foundation  
**Authority:** System-level architecture; implementation details belong in domain specifications and ADRs.

## 1. Executive Summary

Novi is a persistent autonomous embodied-AI system. It continuously perceives its environment, builds and updates a structured representation of the world, retrieves relevant memory and knowledge, evaluates attention, maintains goals, reasons and plans, requests bounded capabilities, observes outcomes, and learns through governed state evolution.

The architecture separates two fundamental domains:

1. **Adaptive intelligence** — perception interpretation, models, memory, knowledge, personality, attention, curiosity, planning, prediction and learned behavior.
2. **Protected execution** — authorization, governance, safety policy, hardware limits, privileged robotics services, emergency stop, trusted identities, and protected configuration.

Adaptive intelligence may evolve. Protected execution cannot be modified by ordinary adaptive capabilities.

## 2. Product Definition

Novi is an autonomous embodied AI system rather than a prompt/response assistant.

Desired properties include:

- continuous environmental awareness;
- selective/context-aware interaction;
- persistent personality;
- differentiated relationships;
- multimodal perception;
- long-term memory;
- spatial and temporal understanding;
- curiosity and controlled exploration;
- explicit uncertainty;
- provenance-aware learning;
- local-first operation;
- safe physical action;
- diagnostics, auditability and recovery;
- governed evolution without unrestricted self-modification.

## 3. System Context

```text
                 HUMAN / HOUSEHOLD / WORLD
                           │
                    SENSORS / INPUTS
                           │
                           ▼
                 ┌───────────────────┐
                 │     PERCEPTION    │
                 └─────────┬─────────┘
                           │ observations/evidence
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
                  AGENT / MODEL RUNTIME
                           │
                    action/tool proposals
                           ▼
                  GOVERNANCE / SAFETY
                           │
                    capability requests
                           ▼
                         ROS 2
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
         MOTION        INTERACTION       IOT
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                      WORLD CHANGE
                           │
                           └──────── feedback ────────→ perception
```

## 4. Major Subsystems

### 4.1 Perception

Converts sensor streams into structured observations and evidence. It may use classical processing, specialized neural models, multimodal models and sensor fusion.

Perception outputs must retain timestamps, source, calibration context, confidence and provenance. An uncertain observation must not silently become a permanent fact.

### 4.2 World Model

Represents current structured state of people, places, objects, devices, relationships, spatial state, temporal state, activities and situations.

The world model is not the same thing as historical memory. Current state may change while historical evidence remains preserved.

### 4.3 Memory and Knowledge

Memory preserves experiences and learned context. Knowledge represents structured concepts, facts, relationships and verified information.

Both require provenance and confidence appropriate to their source.

### 4.4 Attention

Attention determines which events deserve observation, monitoring, retrieval, reasoning, interaction or action.

Attention is not synonymous with model invocation.

### 4.5 Personality and Social State

Personality contains stable traits plus governed dynamic state. Social state represents relationship and current interaction context.

### 4.6 Autonomy

The autonomy engine coordinates the continuous loop across perception, attention, goals, memory, reasoning, planning, action and learning.

### 4.7 Agent and Model Runtime

The agent runtime constructs context, invokes models through capability interfaces, validates structured outputs, manages tools, cancellation, retries and traceability.

No particular LLM is architecturally authoritative. The initial model candidate is selected through the model evaluation process and ADRs.

### 4.8 Tools

Tools are bounded capabilities with explicit schemas, permissions, resource limits and audit behavior.

### 4.9 Governance and Safety

Governance determines whether an action is permitted. Safety enforces physical constraints and safe-state behavior. Neither is delegated to the model.

### 4.10 Robotics

ROS 2 is the primary robotics integration boundary. `ros2_control`, Navigation2, sensor drivers and hardware interfaces sit behind capability contracts.

NVIDIA technologies may accelerate implementations behind these boundaries.

## 5. Core Data Flow

```text
raw sensor
  ↓
observation
  ↓
evidence/event
  ↓
world-state update
  ↓
attention evaluation
  ↓
memory/knowledge retrieval
  ↓
context construction
  ↓
reasoning/planning
  ↓
policy evaluation
  ↓
action proposal
  ↓
safety validation
  ↓
capability execution
  ↓
result observation
  ↓
experience / governed learning
```

The durable event/state architecture records consequential state transitions and preserves provenance across projections.

## 6. Autonomy Model

Novi is continuously operating. User interaction is one event source, not the primary lifecycle trigger.

The runtime combines:

```text
high-rate event processing
medium-rate attention/situation evaluation
low-rate consolidation/maintenance
explicit event-driven reasoning
```

Expensive model calls must be triggered by an explicit value/latency/resource policy rather than every sensor tick.

## 7. Learning Model

Learning is governed state evolution:

```text
experience
  ↓
observation
  ↓
interpretation
  ↓
evidence accumulation
  ↓
hypothesis
  ↓
verification where required
  ↓
memory / knowledge / skill update
```

Learning does not grant permission to rewrite protected system or safety foundations.

## 8. Runtime Environments

### Development host

Used for cognitive development, schema work, local model experiments, sensor testing, data generation and automated tests.

### Simulation

Isaac Sim is the NVIDIA high-fidelity simulation candidate. Gazebo remains the portable ROS 2 simulation candidate. The simulator is selected by workload and validated against the robot contract.

NVIDIA's current Isaac Sim documentation recommends ROS 2 Humble and Jazzy and provides a tested Jazzy workflow on Ubuntu 24.04. citeturn0search4turn0search7

### Edge

Jetson is the current NVIDIA edge-compute candidate. JetPack, CUDA, TensorRT and accelerated robotics/video components are version-locked through deployment manifests.

NVIDIA currently identifies JetPack 7.2 / L4T r39.2 as the latest JetPack release for the AGX Orin developer kit. citeturn1search1

### Physical robot

The physical deployment combines the validated edge runtime with sensors, actuators, displays, audio, power, networking and independent safety hardware.

## 9. Vendor Boundary

```text
Novi semantic contracts
          ↓
capability adapters
          ↓
NVIDIA / open-source implementation
          ↓
platform hardware
```

NVIDIA is not the semantic source of truth for Novi. This prevents vendor-specific implementation details from leaking into cognition, memory or governance.

## 10. Non-Goals

Novi must not:

- give an LLM unrestricted shell/filesystem/database/network access;
- allow an LLM to directly control motors;
- allow adaptive learning to rewrite protected safety constraints;
- treat every observation as fact;
- put the entire memory store into every model context;
- require one model for every modality;
- require cloud connectivity for core autonomy;
- select final hardware before workload, power, thermal and mechanical requirements are measured.

## 11. High-Level Acceptance Criteria

The architecture is viable when the development runtime demonstrates:

1. continuous event processing;
2. persistent versioned world state;
3. persistent memory and knowledge with provenance;
4. selective attention;
5. personality/social state;
6. relationship-aware interaction;
7. controlled curiosity;
8. evidence-based learning;
9. governed schema/data evolution;
10. bounded tool use;
11. policy- and safety-gated action proposals;
12. end-to-end audit traces;
13. simulation through the same logical interfaces;
14. replaceable model/runtime implementations;
15. safe degradation and recovery.

Physical deployment adds hardware and safety validation rather than introducing a second cognitive architecture.
