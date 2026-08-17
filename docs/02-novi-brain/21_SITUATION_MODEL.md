# Novi Brain — Situation Model

**Document:** `21_SITUATION_MODEL.md`  
**Status:** P0 Critical Architecture Specification  
**Authority:** `02-novi-brain`  
**Depends on:** 02 Cognitive Architecture, 03 Brain State Model, 04 Brain Orchestrator, 05 Cognitive Cycle, 11 Perception Architecture, 16 Multimodal Fusion, 18 World Model, 19 Spatial Cognition, 20 Temporal Cognition  

---

## 1. Purpose

The Situation Model is Novi's continuously maintained answer to:

> **"What is happening around me right now, what does it mean, how certain am I, and what matters to me?"**

It sits between raw/fused perception and higher-level cognition, planning and behavior.

```text
WORLD
  ↓
SENSORS
  ↓
PERCEPTION
  ↓
MULTIMODAL FUSION
  ↓
WORLD MODEL
  ↓
SPATIAL + TEMPORAL COGNITION
  ↓
SITUATION MODEL
  ↓
ATTENTION / GOALS / REASONING
  ↓
PLANNING / BEHAVIOR
  ↓
ACTION
  ↓
WORLD
```

The Situation Model is **not** a transcript, scene caption, LLM prompt, database dump, or single neural-network output. It is a structured, uncertain, temporal representation of the current situation that can be consumed by multiple cognitive subsystems.

---

# 2. North-star requirement

Novi must maintain an evolving situation representation even when nobody is interacting with it.

It should continuously distinguish:

- what is directly observed;
- what is inferred;
- what is remembered;
- what is predicted;
- what is relevant;
- what is uncertain;
- what is urgent;
- what Novi is currently doing;
- what other agents appear to be doing;
- what changed recently;
- what may happen next.

This is a core requirement for the perception of continuous, embodied life.

---

# 3. Situation is not truth

The Situation Model must preserve epistemic boundaries.

```text
observation
   ≠
perception result
   ≠
fused evidence
   ≠
hypothesis
   ≠
belief
   ≠
intent hypothesis
   ≠
prediction
   ≠
known fact
```

Every derived situation element must carry provenance and uncertainty appropriate to its type.

Example:

```text
Observation:
  person detected at x,y

Evidence:
  person facing Novi
  speech source aligned with person

Hypothesis:
  person may be addressing Novi

Confidence:
  0.86

Action:
  increase attention and listen
```

The system must not silently convert the hypothesis into a fact.

---

# 4. Situation representation

A canonical situation snapshot should contain at least:

```text
situation_id
situation_version
timestamp
world_state_version
spatial_state_version
temporal_state_version
active_entities
active_events
active_activities
relationships
agent_states
Novi_state
current_place
active_goals
active_tasks
attention_targets
hazards
opportunities
social_context
interaction_context
recent_changes
predictions
uncertainties
confidence
provenance
expiration/freshness
```

The exact executable schema belongs in the canonical contract layer.

---

# 5. Situation entities

The Situation Model should represent several classes of entities.

## 5.1 Agents

Examples:

- Novi;
- known person;
- unknown person;
- group;
- animal where relevant;
- autonomous system/robot.

Agent state may include:

- position;
- motion;
- orientation;
- activity;
- interaction state;
- estimated attention target;
- uncertainty.

## 5.2 Objects

Relevant objects may include:

- manipulable objects;
- obstacles;
- tools;
- furniture;
- doors;
- vehicles;
- personal objects;
- hazards.

## 5.3 Places

Examples:

- room;
- corridor;
- workstation;
- home;
- charging area;
- restricted area.

## 5.4 Events

Examples:

- person entering;
- object falling;
- door opening;
- collision risk emerging;
- speech detected;
- task completion;
- unexpected movement.

## 5.5 Activities

Activities are temporally extended patterns rather than instantaneous events:

- someone walking;
- someone working;
- conversation;
- Novi navigating;
- object being manipulated.

---

# 6. Situation state layers

The Situation Model should be layered.

### Layer A — Physical

What physically appears to be happening.

### Layer B — Semantic

What entities/events likely represent.

### Layer C — Social

Who is interacting with whom and what social context may exist.

### Layer D — Goal/task

What tasks and goals appear active.

### Layer E — Predictive

What may happen next.

### Layer F — Cognitive relevance

What matters to Novi right now and why.

This prevents one large undifferentiated representation from becoming the source of every cognitive decision.

---

# 7. Situation formation

Situation formation is an evidence-integration process.

```text
new evidence
   ↓
associate with existing entities/events
   ↓
update spatial state
   ↓
update temporal state
   ↓
update world state
   ↓
form/modify situation hypotheses
   ↓
score relevance and urgency
   ↓
publish situation update
```

Situation formation should be incremental rather than requiring a complete scene re-analysis on every sensor cycle.

---

# 8. Situation continuity

Novi must maintain continuity across time.

If a person is observed over ten seconds, the system should represent one evolving agent/activity rather than ten unrelated snapshots.

```text
person detected
  ↓
track
  ↓
approaching
  ↓
near Novi
  ↓
speaking
  ↓
interaction
  ↓
departing
```

This temporal continuity is required for natural behavior.

---

# 9. Situation changes

The system should classify changes by significance.

### Routine

Expected changes with little cognitive consequence.

### Relevant

Changes related to active goals, people, tasks or environment.

### Novel

Unexpected or unfamiliar changes.

### Urgent

Changes requiring immediate reaction.

### Safety-critical

Changes that must bypass deliberative latency and enter the safety/reactive pathway.

This classification feeds the Brain Orchestrator and attention system.

---

# 10. Attention integration

Situation awareness and attention are mutually reinforcing.

```text
situation
   ↓
relevance estimate
   ↓
attention allocation
   ↓
more sensing/reasoning
   ↓
better situation estimate
   ↓
updated relevance
```

Attention should consider:

- safety;
- urgency;
- active goals;
- social relevance;
- novelty;
- uncertainty;
- proximity;
- movement;
- predicted consequence;
- information value.

---

# 11. Situation priority

A situation priority should not be a single opaque neural score.

A structured priority can combine:

```text
priority = f(
  urgency,
  safety,
  goal_relevance,
  social_relevance,
  novelty,
  uncertainty,
  proximity,
  predicted_impact,
  time_sensitivity,
  resource_cost
)
```

The factors and weighting policy must be inspectable, versioned and testable.

---

# 12. Social situation

Novi should maintain a social situation representation separate from raw person detection.

Example:

```text
Person A
  ↓
near Novi
  ↓
facing Novi
  ↓
speaking
  ↓
conversation hypothesis
  ↓
Novi attention
```

The social layer may consider:

- presence;
- proximity;
- orientation;
- gaze where available;
- speech source;
- turn-taking;
- known relationship;
- interaction history;
- group context;
- social boundaries.

Social inference must remain probabilistic and must not infer private mental states as facts.

---

# 13. Intent hypotheses

The Situation Model may maintain hypotheses about what another agent is trying to do.

Examples:

- approaching Novi;
- requesting assistance;
- looking for an object;
- moving through the room;
- manipulating an object.

Intent must be represented as a hypothesis:

```text
intent_hypothesis
confidence
supporting_evidence
contradicting_evidence
created_at
expires_at
```

It must not become an authorization to act.

---

# 14. Activities and events

The model should distinguish:

```text
event       = occurrence at/around a point in time
activity    = process extending over time
state       = condition that persists
```

Example:

```text
event: person entered room
activity: person walking
state: person is in room
```

This distinction is essential for temporal reasoning and memory.

---

# 15. Active tasks

The Situation Model should expose active tasks from the task/goal architecture.

Example:

```text
Goal:
  bring object to person

Task:
  navigate to object

Current situation:
  object visible
  route blocked

Situation update:
  route unavailable

Required cognitive response:
  replan
```

The situation model describes the context; it does not own the task planner.

---

# 16. Hazards and opportunities

The model should represent both negative and positive action-relevant conditions.

### Hazards

- collision risk;
- unstable object;
- person entering path;
- unsafe surface;
- actuator limitation;
- uncertain localization.

### Opportunities

- clear route;
- available charging station;
- visible target;
- human assistance opportunity;
- newly discovered route;
- useful information source.

Safety-critical hazards must also be represented in independent safety systems; the Situation Model cannot be the sole safety authority.

---

# 17. Prediction integration

The Situation Model should expose relevant predictions from the temporal/world-model layers.

```text
current situation
      ↓
prediction candidates
      ↓
expected outcomes
      ↓
planning / attention
```

Each prediction should include:

- horizon;
- confidence;
- assumptions;
- source/model;
- version;
- timestamp.

Prediction failures become situation-change evidence.

---

# 18. Counterfactual context

For higher-level reasoning, Novi may maintain limited counterfactual situations.

Example:

```text
Current:
  doorway blocked

Counterfactual A:
  wait → likely doorway clears

Counterfactual B:
  alternate route → longer travel

Counterfactual C:
  ask person to move → interaction cost
```

Counterfactuals must remain explicitly hypothetical and must never be written into factual world state.

---

# 19. Active perception

The Situation Model should identify when the current situation is too uncertain to support a good decision.

```text
uncertain situation
      ↓
what evidence would reduce uncertainty?
      ↓
choose sensing action
      ↓
orient / move / listen / inspect
      ↓
new evidence
      ↓
update situation
```

This is one of the mechanisms that can make Novi appear naturally attentive without requiring random autonomous behavior.

---

# 20. Human interaction example

### Initial state

```text
Novi navigating
Person enters room
```

### Situation updates

```text
vision → person detected
spatial → person near doorway
temporal → person approaching
identity → likely known person
speech → person speaks
ASR → partial speech
orientation → facing Novi
```

### Situation interpretation

```text
active situation:
  known person approaching Novi
  likely addressing Novi
  Novi currently navigating
  interaction relevance: high
```

### Cognitive response

The orchestrator may decide to:

1. reduce navigation speed or pause where appropriate;
2. orient toward the person;
3. listen;
4. understand the request;
5. respond;
6. resume or modify the task.

The exact physical behavior remains governed by navigation and safety systems.

---

# 21. Unexpected event example

```text
sound event
   ↓
behind Novi
   ↓
uncertain visual explanation
   ↓
attention increases
   ↓
active perception
   ↓
turn/orient
   ↓
vision detects object falling
   ↓
spatial/temporal update
   ↓
hazard assessment
   ↓
appropriate reaction
```

No conversational model is required for the initial reaction.

This is a key design principle:

> **Novi must be able to react before it has time to formulate a sentence about what happened.**

---

# 22. Quiet periods

A quiet environment is itself a valid situation.

Novi should not generate artificial activity simply to appear alive.

During low-change periods, the system may:

- continue perception;
- maintain tracks;
- monitor goals;
- maintain spatial/temporal state;
- perform low-priority memory work;
- monitor health;
- remain available for interruption.

The system may also initiate bounded, goal-relevant behavior when appropriate, but spontaneous behavior must be governed by the autonomy policy.

---

# 23. Situation decay and freshness

Not every situation fact remains valid indefinitely.

Examples:

```text
"person is here"
```

becomes stale if the person has not been observed and tracking confidence falls.

The model should support:

- freshness windows;
- decay policies;
- revalidation requirements;
- explicit unknown states.

A stale fact must not silently remain a current fact.

---

# 24. Situation uncertainty

Situation uncertainty can arise from:

- sensor ambiguity;
- model disagreement;
- missing modalities;
- occlusion;
- stale data;
- identity ambiguity;
- intent ambiguity;
- localization uncertainty;
- temporal uncertainty.

When uncertainty is operationally important, Novi should:

1. gather information;
2. choose a safer action;
3. ask a person;
4. defer.

---

# 25. Deterministic vs learned components

The Situation Model is hybrid.

## Deterministic

- entity/state schemas;
- timestamps;
- freshness;
- provenance;
- relationship storage;
- event lifecycle;
- safety boundaries;
- state transitions;
- conflict handling.

## Learned

Potentially:

- activity recognition;
- scene interpretation;
- intent hypotheses;
- social-context classification;
- event prediction;
- multimodal relevance scoring;
- situation embeddings.

## Cognitive

- determining what matters;
- choosing evidence-gathering actions;
- relating situation to goals;
- resolving ambiguity;
- deciding whether to react, think or wait.

---

# 26. Model routing

The Situation Model must not require a large model on every update.

Typical flow:

```text
fast perception
   ↓
state/event update
   ↓
cheap relevance assessment
   ↓
escalate only when necessary
   ↓
VLM/LLM/world-model reasoning
```

Examples:

- obstacle detected → fast local response;
- familiar person detected → lightweight social update;
- ambiguous interaction → multimodal reasoning;
- complex future consequence → deliberative/world-model reasoning.

This preserves latency and compute for the cases that actually need it.

---

# 27. NVIDIA technology mapping

NVIDIA technologies are candidates for specific capabilities rather than replacements for the Situation Model.

Relevant technologies include:

- Isaac ROS for accelerated perception and robotics pipelines;
- Isaac Sim for reproducible multimodal simulation and replay;
- Cosmos 3 for multimodal physical reasoning, world-state prediction and action-conditioned modeling;
- Cosmos 3 Edge for future/available edge deployment scenarios where its measured capability and hardware fit Novi's requirements.

NVIDIA describes Cosmos 3 as combining physical reasoning, world generation and action generation in an omnimodal architecture, with a reasoner capable of interpreting multimodal observations before generation/prediction. citeturn0search0turn0search1

NVIDIA also describes Cosmos as supporting world simulation, prediction and closed-loop evaluation. citeturn0search3

Isaac ROS remains the robotics/perception infrastructure layer and is designed to integrate with ROS 2 and NVIDIA acceleration. citeturn0search5

Novi must benchmark these capabilities against its own latency, reliability, resource, privacy and safety requirements before adopting them.

---

# 28. Data contract

A situation record should contain at least:

```text
situation_id
version
timestamp
entities
events
activities
relationships
Novi_state
place
active_goals
active_tasks
attention_targets
hazards
opportunities
social_context
intent_hypotheses
predictions
recent_changes
uncertainties
confidence
provenance
freshness
source_versions
```

The canonical machine-readable schema must be versioned and validated before production implementation.

---

# 29. Conflict resolution

Different subsystems may disagree.

Example:

```text
vision: person at doorway
LiDAR: obstacle at doorway
tracking: person hypothesis uncertain
memory: doorway normally clear
```

The Situation Model must not simply choose the most recent output.

Conflict resolution should consider:

- timestamp;
- sensor quality;
- calibration state;
- model confidence;
- modality reliability;
- spatial consistency;
- temporal consistency;
- source provenance.

Safety-critical conflicts must escalate to the safety architecture.

---

# 30. Failure modes

Required handling includes:

- contradictory sensor evidence;
- stale situation state;
- entity identity switches;
- event duplication;
- missed events;
- temporal ordering errors;
- multimodal desynchronization;
- incorrect intent hypothesis;
- hallucinated context;
- world-model prediction mismatch;
- lost localization;
- model/runtime failure;
- resource exhaustion.

The system must fail toward **explicit uncertainty**, not fabricated certainty.

---

# 31. Observability

Every meaningful situation transition should be inspectable.

The system should be able to answer:

> Why did Novi believe this was happening?

The trace should connect:

```text
sensor evidence
 ↓
perception result
 ↓
fusion
 ↓
world/spatial/temporal state
 ↓
situation hypothesis
 ↓
attention
 ↓
model invocation
 ↓
decision
```

Sensitive data must be subject to privacy and retention controls.

---

# 32. Validation

### Unit tests

- state transitions;
- freshness;
- provenance;
- event/activity semantics;
- confidence propagation.

### Scenario tests

- person enters;
- person leaves;
- person approaches;
- conversation starts;
- obstacle appears;
- object falls;
- door changes state;
- task becomes blocked;
- conflicting sensors;
- localization loss.

### Simulation

Use Isaac Sim to generate repeatable multimodal scenarios and controlled edge cases where practical.

### Physical

Validate:

- latency;
- continuity;
- false-positive rate;
- false-negative rate;
- situation stability;
- recovery;
- long-duration behavior;
- human interaction.

---

# 33. Required acceptance tests

At minimum:

- `SITUATION-001` continuous situation maintenance;
- `SITUATION-002` entity continuity;
- `SITUATION-003` event/activity/state distinction;
- `SITUATION-004` multimodal correlation;
- `SITUATION-005` social situation formation;
- `SITUATION-006` intent hypothesis uncertainty;
- `SITUATION-007` hazard escalation;
- `SITUATION-008` active-perception trigger;
- `SITUATION-009` prediction integration;
- `SITUATION-010` stale-state decay;
- `SITUATION-011` sensor conflict handling;
- `SITUATION-012` explanation/provenance trace;
- `SITUATION-013` quiet-period stability;
- `SITUATION-014` interruption/recovery;
- `SITUATION-015` long-duration continuity.

---

# 34. Definition of done

The Situation Model is complete when Novi can continuously maintain a structured representation of:

- who/what is present;
- where they are;
- what they are doing;
- what has changed;
- what Novi is doing;
- what Novi is trying to accomplish;
- what appears socially relevant;
- what may happen next;
- what is dangerous;
- what is uncertain;
- what requires attention;
- why the system believes these things;
- when each belief becomes stale.

It must work without requiring a user prompt to refresh the situation.

---

# 35. Core principle

> **Novi should not experience the world as a sequence of disconnected sensor readings. It should maintain an evolving situation.**

The desired computational behavior is:

```text
sense
 ↓
understand
 ↓
remember
 ↓
contextualize
 ↓
anticipate
 ↓
attend
 ↓
act
 ↓
observe consequence
 ↓
update situation
 ↓
continue existing
```

That continuous situation loop is a foundational mechanism for Novi's intended behavior: **responsive, embodied, socially aware, autonomous, and persistently present in its environment.**
