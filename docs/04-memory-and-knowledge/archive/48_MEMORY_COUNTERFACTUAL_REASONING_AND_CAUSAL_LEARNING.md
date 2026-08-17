# 48 — Memory Counterfactual Reasoning and Causal Learning

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi can reason about alternative outcomes, interventions and causal hypotheses without confusing imagined, simulated or hypothetical events with real memories or observed facts.

This document extends the causal model in `47_MEMORY_EVENT_CAUSALITY_AND_EPISODE_LINKING.md`.

## Core Principle

> **A counterfactual is a model of what might have happened, not a memory of what happened.**

Novi must preserve a hard boundary between:

```text
REAL OBSERVATION
SIMULATED EXPERIENCE
COUNTERFACTUAL
PREDICTION
HYPOTHESIS
MEMORY
FACT
```

---

## 1. Why Counterfactual Reasoning Matters

Counterfactual reasoning can help Novi understand decisions and improve future behavior.

Example:

```text
Actual:
route A → obstacle → replanning → destination

Counterfactual:
route B → predicted lower obstacle risk
```

This can inform future planning without rewriting history.

---

## 2. Counterfactual Structure

A counterfactual should contain:

```text
base_world_state
intervention
assumptions
model
predicted_outcome
uncertainty
provenance
```

Example:

```text
base = actual state at T0
intervention = choose route B
prediction = arrival likely faster
confidence = moderate
```

---

## 3. Possible Worlds

Novi may represent alternative trajectories from a common state.

```text
             STATE T0
             /      \
        action A    action B
           ↓           ↓
       outcome A    outcome B
```

Only one branch may correspond to reality.

The others remain hypothetical unless subsequently executed.

---

## 4. Actual vs Counterfactual Branches

The event graph must explicitly label branches:

```text
ACTUAL
COUNTERFACTUAL
SIMULATED
PREDICTED
HYPOTHETICAL
```

A counterfactual event must never be inserted into the canonical real-world event stream as if it occurred.

---

## 5. Prediction vs Counterfactual

These are related but different.

```text
Prediction:
What is likely to happen next?

Counterfactual:
What would likely have happened if X had been different?
```

Both require uncertainty.

---

## 6. Retrospective Counterfactual

After an event, Novi may ask:

> What might have happened if the chosen action had not occurred?

This is useful for learning, but the answer remains model-dependent.

---

## 7. Prospective Counterfactual

Before acting, Novi may compare alternatives:

```text
option A → predicted outcome
option B → predicted outcome
option C → predicted outcome
```

The planner can select among them according to goals, safety and policy.

---

## 8. Intervention Model

A causal intervention changes a selected variable or action while holding the appropriate context fixed.

Conceptually:

```text
observed world
      ↓
intervene on X
      ↓
model downstream effects
```

Interventions should be explicit in the representation.

---

## 9. Real-World Intervention

Physical interventions are allowed only when:

- authorized;
- safe;
- reversible where practical;
- within capability;
- useful for the active objective.

Novi must never perform a dangerous physical intervention merely to satisfy curiosity.

---

## 10. Passive Observation vs Intervention

The memory system should distinguish:

```text
observed naturally
vs
observed after intervention
```

This distinction is essential for causal learning.

---

## 11. Controlled Experiments

Where safe and authorized, Novi may conduct bounded experiments.

Example:

```text
hypothesis:
fan activation reduces internal temperature

baseline measurement
      ↓
controlled fan intervention
      ↓
measurement
      ↓
comparison
```

The result becomes evidence with explicit experimental provenance.

---

## 12. Hardware Experiments

Hardware experiments must be governed by the hardware and safety architecture.

Examples may include:

- thermal behavior;
- battery behavior;
- sensor calibration;
- actuator response;
- microphone/speaker characteristics.

Experiments must not bypass protective limits.

---

## 13. Simulation as a Counterfactual Tool

Simulation provides a safe environment for testing alternatives.

NVIDIA Isaac Sim supports physically based simulation, sensor simulation, ROS 2 integration and software-in-the-loop testing; Isaac Lab provides open-source robot-learning workflows including reinforcement and imitation learning. citeturn0search1turn0search3

Simulation is therefore a candidate mechanism for exploring alternative actions before physical execution.

---

## 14. Simulation Evidence Boundary

Simulation results must never silently become real-world facts.

```text
SIMULATED:
route B succeeded in simulation

REAL:
route B has not yet been attempted
```

The distinction remains permanent in provenance.

---

## 15. Sim-to-Real Uncertainty

Simulation cannot perfectly reproduce reality.

Potential gaps include:

- physics parameters;
- friction;
- lighting;
- sensor noise;
- perception errors;
- latency;
- actuator differences;
- unmodeled obstacles;
- human behavior.

Therefore simulated counterfactuals require a transfer-confidence assessment.

---

## 16. Digital Twin Use

Where a sufficiently accurate environment model exists, Novi can evaluate alternatives against it.

A digital twin should identify:

- source data;
- capture date;
- map version;
- sensor model;
- physics model;
- known limitations.

NVIDIA describes Isaac Sim as supporting CAD/URDF/real-world capture inputs, physics, sensors, synthetic data and SIL workflows. citeturn0search1turn0search8

---

## 17. Counterfactual Confidence

Counterfactual confidence should depend on:

- quality of base state;
- model validity;
- intervention definition;
- similarity to observed conditions;
- simulation fidelity;
- historical validation;
- alternative explanations;
- uncertainty in downstream effects.

A model's self-reported confidence is not sufficient evidence.

---

## 18. Counterfactual Comparison

Alternatives can be compared on multiple dimensions:

```text
safety
success probability
energy
travel time
thermal cost
risk
information gain
user preference
reversibility
```

No single scalar should automatically determine every decision.

---

## 19. Safety Dominates Counterfactual Optimization

A hypothetical outcome that appears beneficial cannot override safety policy.

```text
counterfactual utility
        ↓
policy constraints
        ↓
safety constraints
        ↓
permitted options
```

---

## 20. Counterfactual Regret

Novi may compare expected and actual outcomes:

```text
chosen action
expected outcome
actual outcome
alternative predicted outcome
```

This can generate a learning candidate such as:

> "Under these conditions, route B may have been preferable."

It must not become:

> "Route B would definitely have succeeded."

---

## 21. Actual Outcome as New Evidence

After a counterfactual-guided action:

```text
prediction
 ↓
action
 ↓
actual result
 ↓
prediction error
 ↓
model update candidate
```

This closes the learning loop.

---

## 22. Causal Learning Loop

```text
OBSERVE
   ↓
HYPOTHESIZE
   ↓
PREDICT
   ↓
INTERVENE / SIMULATE / WAIT
   ↓
OBSERVE OUTCOME
   ↓
COMPARE
   ↓
UPDATE CAUSAL MODEL
   ↓
VALIDATE
   ↓
PROMOTE OR REJECT
```

This loop is evidence-driven rather than narrative-driven.

---

## 23. Learning From Failure

Failure should produce structured evidence.

```text
expected outcome ≠ actual outcome
        ↓
possible causes
        ↓
new evidence
        ↓
causal hypothesis
```

Failure alone does not prove the suspected cause.

---

## 24. Learning From Success

Success also requires careful interpretation.

```text
action A succeeded
```

does not prove:

```text
A is always sufficient
```

Context must be retained.

---

## 25. Confounding

Novi should consider whether another variable could explain an observed relationship.

Example:

```text
fan turned on
AND
ambient temperature decreased
```

A temperature reduction cannot automatically be attributed entirely to the fan.

---

## 26. Temporal Confounding

Time-correlated events may create false causal beliefs.

Example:

```text
8:00 → user wakes
8:01 → Novi moves
```

This does not prove waking caused movement unless the system has evidence of the triggering relationship.

---

## 27. Selection Bias

Novi's experience may be biased toward situations it encounters.

A route that appears safe from limited observations may simply lack difficult examples.

Learning systems should retain exposure limitations where relevant.

---

## 28. Distribution Shift

A causal relationship learned in one environment may not transfer to another.

Example:

```text
home environment
   ↓
learned obstacle behavior

new environment
   ↓
assumption may not hold
```

Context is therefore part of causal knowledge.

---

## 29. Invariant vs Contextual Causality

Novi should distinguish:

```text
likely invariant mechanism
vs
context-specific relationship
```

For example, a known hardware protection mechanism may generalize broadly, while a learned social pattern may be highly contextual.

---

## 30. Causal Model Updates

Updates should be versioned:

```text
model v1
 ↓
evidence
 ↓
model v2
```

Historical decisions retain the model version used at the time.

---

## 31. No Retroactive Reality Rewrite

A new causal model cannot rewrite what actually happened.

```text
EVENT HISTORY
immutable

CAUSAL INTERPRETATION
revisable
```

This is a fundamental architectural separation.

---

## 32. Counterfactual Memory

Counterfactuals may be retained as a distinct memory type when useful.

Example:

```text
memory_type = COUNTERFACTUAL
status = hypothetical
```

They must never appear in ordinary factual recall without their status.

---

## 33. User Questions About Alternatives

If a user asks:

> "What would have happened if we had taken the other route?"

Novi should answer from the counterfactual model and clearly communicate uncertainty.

It should not claim the alternative outcome as historical fact.

---

## 34. Counterfactuals in Conversation

Conversational hypotheticals should be marked as hypothetical.

```text
User:
"Imagine the door was locked."

Novi:
scenario = hypothetical
```

The scenario must not enter canonical world state.

---

## 35. Fiction and Roleplay

Roleplay can generate internally consistent hypothetical worlds.

These must remain isolated from real-world memory.

```text
fiction context
      ≠
real-world context
```

---

## 36. Model-Generated Worlds

An LLM may generate possible explanations or outcomes.

Those outputs are:

```text
MODEL_PROPOSAL
```

until supported by external evidence or controlled evaluation.

---

## 37. Action Authorization

Counterfactual reasoning cannot authorize an action.

```text
counterfactual result
      ↓
planning proposal
      ↓
current-state validation
      ↓
policy
      ↓
safety
      ↓
action
```

---

## 38. Current-State Revalidation

A counterfactual may become stale.

Before execution, Novi must recompute or revalidate against current state.

```text
simulation at T0
      ↓
world changes
      ↓
T1 action request
      ↓
revalidate
```

---

## 39. Counterfactual Branch Expiration

Hypothetical branches should have validity metadata.

They can expire when:

- world state changes;
- map changes;
- model changes;
- assumptions become invalid;
- required evidence becomes stale.

---

## 40. Resource Budgets

Counterfactual search can become computationally expensive.

Budgets should constrain:

- branch count;
- simulation duration;
- model calls;
- search depth;
- memory retrieval;
- energy;
- thermal load.

The system should stop when additional analysis is unlikely to justify its cost.

---

## 41. Background Counterfactual Learning

When idle, Novi may analyze past decisions:

```text
important episode
      ↓
alternative actions
      ↓
simulation/model analysis
      ↓
learning candidates
```

This work must yield to active tasks and thermal/battery constraints.

---

## 42. Safe Exploration

Novi may use low-risk exploration to improve causal knowledge.

Examples:

- testing harmless sensor hypotheses;
- measuring environmental effects;
- comparing routes in safe conditions.

It must not intentionally create dangerous conditions.

---

## 43. Simulation Framework Selection

NVIDIA Isaac Sim/Isaac Lab are strong candidates for Novi's robotics counterfactual and policy-evaluation infrastructure because they support physics simulation, sensor simulation, ROS 2/SIL workflows and scalable robot learning. citeturn0search1turn0search3

However, Novi remains vendor-neutral. Other local open-source simulation/causal tools should be benchmarked when they offer a better fit, including lightweight simulators for focused experiments.

---

## 44. Research Status

Counterfactual causal reasoning in robotics is an active research area rather than a solved engineering problem. Research has explored causal representations, interventions and counterfactual reasoning for reinforcement learning, including work evaluating robustness improvements in simulated robotic environments. citeturn0academia24

Therefore Novi should treat advanced causal learning as an experimental capability with explicit evaluation gates, not as an assumption that a generic LLM can perform reliable causal inference.

---

## 45. Testing

Test:

- historical counterfactual queries;
- prospective planning alternatives;
- intervention recording;
- simulated interventions;
- real interventions;
- real/simulated separation;
- stale counterfactuals;
- counterfactual contamination of memory;
- confounding;
- alternative explanations;
- model updates;
- branch expiration;
- uncertainty propagation;
- safety gating;
- resource limits;
- restart recovery;
- offline operation.

---

## 46. Architectural Invariants

1. Counterfactuals are never real memories.
2. Simulated events are never silently promoted to real events.
3. Predictions are not observations.
4. Temporal order is not causation.
5. Correlation is not causation.
6. LLM-generated causal claims are hypotheses until supported.
7. Physical interventions require authorization and safety validation.
8. Counterfactual reasoning cannot grant action authority.
9. Current state must be revalidated before consequential action.
10. Counterfactual branches retain assumptions and provenance.
11. Simulation evidence remains labeled as simulation.
12. Causal models are versioned and revisable.
13. Historical event reality is immutable.
14. Uncertainty propagates through counterfactual conclusions.
15. Context and distribution shift limit causal generalization.
16. Resource and thermal budgets constrain background analysis.
17. Counterfactual learning remains locally executable without network connectivity.
18. Safety dominates information-seeking and causal experimentation.

---

## 47. Final Principle

> **Novi should be able to imagine alternatives without confusing imagination with history, and learn from alternatives without pretending that an unobserved outcome is known.**

Counterfactual reasoning becomes valuable when it creates better hypotheses, safer plans and better causal models while preserving an uncompromising boundary between reality, simulation, prediction and imagination.
