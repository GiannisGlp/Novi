# 02 — Autonomy

## High-Level Description

The Autonomy subsystem defines how Novi continuously perceives its environment, maintains an internal situation model, decides what deserves attention, selects goals, reasons about possible actions, acts through controlled capabilities, observes the consequences, and continues the loop without requiring a user prompt for every cycle.

Autonomy is the core distinction between Novi and a conventional voice assistant. Novi must remain present in its environment, notice meaningful changes, decide when interaction is appropriate, remain silent when it is not, pursue safe internal goals such as learning or returning to charge, and incorporate the results of experiences into memory and knowledge.

The autonomy layer does **not** directly control motors, unrestricted files, databases, or safety-critical hardware. It produces observations, hypotheses, intentions, plans, and action requests through explicit contracts. Deterministic policy and safety layers remain authoritative over executable actions.

## Detailed Description

The detailed autonomy specification is organized as follows:

### Foundation

- `00_HIGH_LEVEL_AUTONOMY.md` — scope, invariants, autonomy levels, priorities, silence, resource awareness, and cross-platform requirements.
- `01_CONTINUOUS_COGNITIVE_LOOP.md` — the continuous sense → understand → attend → decide → act → observe → learn cycle.
- `02_AUTONOMY_DATA_AND_EVENTS.md` — canonical data vocabulary for observations, events, situations, goals, intentions, plans, actions, outcomes, and learning candidates.
- `03_ATTENTION_AND_SOCIAL_BEHAVIOR.md` — salience, interaction thresholds, social context, non-interruption, personality integration, and multimodal social cues.
- `04_GOALS_CURIOSITY_AND_LEARNING.md` — goals, prioritization, curiosity, unknown discovery, verification, routine learning, failure learning, and controlled evolution.

### Decision and Execution

- `05_DECISION_AND_PLANNING.md` — context construction, deterministic prechecks, Nemotron reasoning, candidate plans, tool selection, validation, replanning, uncertainty, and human confirmation.
- `06_ACTION_EXECUTION_AND_FEEDBACK.md` — capability gateway, execution lifecycle, physical-action boundary, outcome verification, cancellation, retries, and recovery.
- `07_AUTONOMY_STATE_MACHINE.md` — deterministic runtime states, guards, interruptions, emergency states, and recovery.
- `08_INTERNAL_STATE_AND_AFFECT.md` — transient internal state, energy/resource state, attention, social context, affect, and probabilistic emotion hypotheses.
- `09_AUTONOMY_SAFETY_BOUNDARIES.md` — immutable constraints, risk classes, authorization, confirmation, safety overrides, and safe failure.

### Runtime Infrastructure

- `10_AUTONOMY_EVENT_BUS.md` — event envelopes, delivery, ordering, correlation, persistence, replay, deduplication, priority, and backpressure.
- `11_AUTONOMY_RUNTIME.md` — processes, concurrency, cancellation, resource budgets, model runtime, health, startup/shutdown, and Mac/simulation/Jetson profiles.
- `12_AUTONOMY_TESTING.md` — unit, contract, scenario, adversarial, simulation, hardware-in-loop, and endurance testing.
- `13_AUTONOMY_OBSERVABILITY_AND_AUDIT.md` — structured decision traces, metrics, privacy-aware audit, reproducibility, and user-visible diagnostics.

### NVIDIA / Robotics Integration

- `14_AUTONOMY_NVIDIA_INTEGRATION.md` — how NVIDIA technologies fit into autonomy, including JetPack, CUDA, TensorRT, Isaac ROS, Isaac Sim, DeepStream, Nemotron, and Nav2 boundaries.
- `15_AUTONOMY_IMPLEMENTATION_ROADMAP.md` — contracts → Mac runtime → reasoning → learning → simulation → Jetson → hardware → continuous evolution.

## NVIDIA-First, Not NVIDIA-Locked

Novi will actively use NVIDIA technology when NVIDIA provides an existing, mature solution that is appropriate for the requirement. We should **not reimplement equivalent NVIDIA capabilities merely for architectural purity**.

At the same time, vendor-neutral interfaces remain mandatory for the cognitive core. NVIDIA components belong behind those interfaces.

The selection rule is:

```text
Does NVIDIA provide a suitable component?
        ↓ yes
Does it materially improve the workload?
        ↓ yes
Is it supported and maintainable?
        ↓ yes
Use NVIDIA implementation behind a Novi contract.
```

If a non-NVIDIA component is objectively better for a specific workload, it may be used behind the same contract.

## Architectural Principles

1. **Continuous, not request-driven:** autonomy remains active when nobody is speaking to Novi.
2. **Observe before acting:** establish current context before consequential actions.
3. **Attention before interaction:** detecting something does not imply speaking or acting.
4. **Memory is separate from reasoning:** models reason over retrieved state; they do not own authoritative memory.
5. **The world model is explicit:** entities, places, events, relationships, and state changes exist outside the prompt.
6. **Actions are capabilities:** reasoning requests typed capabilities rather than touching hardware/storage directly.
7. **Safety is authoritative:** autonomy may propose, while policy/safety can deny, constrain, delay, or require confirmation.
8. **Learning is controlled evolution:** Novi can evolve managed knowledge, memories, preferences, routines, and hypotheses without modifying protected software or safety rules.
9. **Uncertainty is first-class:** confidence and provenance accompany observations, inferences, memories, and decisions.
10. **NVIDIA is the reference platform:** Jetson/Isaac/TensorRT/CUDA are preferred where they are the appropriate existing solution, while cognition remains portable.
11. **Simulation first:** most autonomy behavior must be testable on Mac and simulation before physical hardware.
12. **Everything important is observable:** consequential behavior has structured traces without storing private chain-of-thought.

## Relationship to Other Domains

```text
Perception → Events → World Model → Attention → Goals → Reasoning → Plan
     ↑                                                        ↓
     └──────────── Outcome / Learning / Memory ← Action ← Safety
```

Autonomy consumes perception, memory, knowledge, identity, personality, and world-state services. It invokes models through model contracts and robotics/IoT capabilities through tools. It never bypasses the safety boundary.

## Implementation Status

This directory is a specification baseline. A document may be marked:

- `DESIGN`
- `IMPLEMENTATION READY`
- `IMPLEMENTED`
- `VALIDATED`
- `DEPRECATED`

A design document must not be interpreted as implemented behavior until corresponding code and tests exist.
