# 02 — Autonomy

## High-Level Description

The Autonomy subsystem defines how Novi continuously perceives its environment, maintains an internal situation model, decides what deserves attention, selects goals, reasons about possible actions, acts through controlled capabilities, observes the consequences, and continues the loop without requiring a user prompt for every cycle.

Autonomy is the core distinction between Novi and a conventional voice assistant. Novi must be able to remain present in its environment, notice meaningful changes, decide when interaction is appropriate, remain silent when it is not, pursue safe internal goals such as learning or returning to charge, and incorporate the results of its experiences into memory and knowledge.

The autonomy layer does **not** directly control motors, unrestricted files, databases, or safety-critical hardware. It produces observations, hypotheses, intentions, plans, and action requests through explicit contracts. Deterministic policy and safety layers remain authoritative over executable actions.

## Detailed Description

The detailed autonomy specification is divided into the following documents:

- `00_HIGH_LEVEL_AUTONOMY.md` — autonomy goals, scope, lifecycle, terminology, and system invariants.
- `01_CONTINUOUS_COGNITIVE_LOOP.md` — the continuously running perceive-understand-update-attend-decide-act-learn cycle.
- `02_PERCEPTION_TO_WORLD_STATE.md` — conversion of multimodal observations into coherent world-state updates.
- `03_ATTENTION_ENGINE.md` — salience, relevance, urgency, interruption, focus, and deciding when not to react.
- `04_GOALS_AND_MOTIVATION.md` — user goals, maintenance goals, curiosity, exploration, priorities, conflicts, and termination.
- `05_CURIOSITY_AND_EXPLORATION.md` — unknown detection, information-seeking behavior, safe exploration, and learning triggers.
- `06_DECISION_AND_PLANNING.md` — reasoning, candidate actions, planning, tool selection, uncertainty, and replanning.
- `07_ACTION_EXECUTION_AND_FEEDBACK.md` — action requests, execution, observation of outcomes, failure handling, and recovery.
- `08_AUTONOMY_STATE_MACHINE.md` — explicit runtime states, transitions, guards, interruptions, and recovery states.
- `09_SOCIAL_AUTONOMY.md` — social awareness, interaction thresholds, relationships, tone, context, and non-interruption behavior.
- `10_INTERNAL_STATE_AND_AFFECT.md` — transient internal state, energy, attention, social context, emotion hypotheses, and behavioral modulation.
- `11_LEARNING_AND_EVOLUTION.md` — how experience becomes memory, knowledge, routines, preferences, and validated learning without uncontrolled self-modification.
- `12_AUTONOMY_SAFETY_BOUNDARIES.md` — immutable constraints, action authorization, risk levels, human confirmation, and safe failure.
- `13_AUTONOMY_DATA_MODEL.md` — schemas for observations, events, situations, goals, intentions, plans, actions, outcomes, and autonomy state.
- `14_AUTONOMY_EVENT_BUS.md` — event contracts, ordering, correlation, deduplication, replay, persistence, and backpressure.
- `15_AUTONOMY_RUNTIME.md` — processes, scheduling, concurrency, cancellation, resource budgets, health, and lifecycle management.
- `16_AUTONOMY_TESTING.md` — deterministic scenarios, simulated environments, adversarial cases, regression testing, and acceptance criteria.
- `17_AUTONOMY_OBSERVABILITY_AND_AUDIT.md` — decision traces, reasons, confidence, metrics, diagnostics, and reproducibility.
- `18_AUTONOMY_NVIDIA_INTEGRATION.md` — Jetson AGX Orin, Isaac ROS, TensorRT, Isaac Sim, GPU/DLA responsibilities, and hardware abstraction boundaries.
- `19_AUTONOMY_IMPLEMENTATION_ROADMAP.md` — implementation phases from Mac runtime through simulation and Jetson deployment.

## Architectural Principles

1. **Continuous, not request-driven:** autonomy remains active even when nobody is speaking to Novi.
2. **Observe before acting:** the system should establish current context before selecting consequential actions.
3. **Attention before interaction:** detecting something does not imply that Novi should speak or act.
4. **Memory is separate from reasoning:** models reason over retrieved state; they do not own the authoritative memory store.
5. **The world model is explicit:** important entities, places, events, relationships, and state changes are represented outside the prompt.
6. **Actions are capabilities:** the reasoning model requests capabilities through typed interfaces rather than touching hardware or storage directly.
7. **Safety is authoritative:** autonomy may propose actions, but a separate policy/safety layer can deny, constrain, delay, or require confirmation.
8. **Learning is controlled evolution:** Novi can acquire knowledge, memories, preferences, routines, and hypotheses without modifying its protected core software or safety rules.
9. **Uncertainty is first-class:** confidence and provenance accompany observations, inferences, memories, and decisions.
10. **Vendor-neutral cognition:** NVIDIA technologies are the reference acceleration/deployment stack, while the autonomy contracts remain portable.
11. **Simulation first:** the majority of autonomy behavior must be testable on the Mac and in simulation before physical hardware exists.
12. **Everything important is observable:** autonomous decisions must be explainable through structured traces without exposing private internal reasoning text.

## Relationship to Other Domains

```text
Perception → Events → World Model → Attention → Goals → Reasoning → Plan
     ↑                                                        ↓
     └──────────── Outcome / Learning / Memory ← Action ← Safety
```

Autonomy consumes perception, memory, knowledge, identity, and world-state services. It invokes models through model contracts and invokes robotics/IoT capabilities through tools. It never bypasses the safety boundary.

## Implementation Status

This directory is a specification baseline. A document may be marked `DESIGN`, `IMPLEMENTATION READY`, `IMPLEMENTED`, `VALIDATED`, or `DEPRECATED`. Design documents must not be interpreted as implemented behavior until corresponding code and tests exist.
