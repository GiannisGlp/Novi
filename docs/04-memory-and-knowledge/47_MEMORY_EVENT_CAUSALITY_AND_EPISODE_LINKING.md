# 47 — Memory Event Causality and Episode Linking

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi connects events, observations, entities, goals, actions, outcomes and memories into traceable causal and episodic structures.

The purpose is not to claim perfect causal knowledge. Novi must distinguish observed temporal relationships, inferred causal hypotheses and sufficiently validated causal knowledge.

## Core Principle

> **Novi must preserve the difference between what happened before something, what was associated with it, what may have caused it, and what has sufficient evidence to establish a causal relationship.**

---

## 1. Why Causality Matters

A useful autobiographical memory is more than a sequence of observations.

```text
obstacle detected
      ↓
route changed
      ↓
arrival delayed
      ↓
goal completed
```

Novi should be able to reconstruct this chain while preserving uncertainty about the actual cause.

---

## 2. Causal Layers

Represent causal knowledge at different confidence levels:

```text
TEMPORAL
A happened before B

CORRELATIONAL
A and B repeatedly occur together

CAUSAL HYPOTHESIS
A may have contributed to B

SUPPORTED CAUSAL RELATION
Evidence supports A causing/contributing to B

CAUSAL KNOWLEDGE
Repeated/controlled/strong evidence supports the relationship
```

Do not collapse these levels.

---

## 3. Event Graph

Events may be represented as a directed graph:

```text
Event A
  │
  ├── temporal → Event B
  ├── causes?  → Event C
  ├── enables  → Event D
  └── prevents → Event E
```

Edges require provenance and confidence.

---

## 4. Causation ID

Every event that is explicitly triggered by another event should preserve a causation reference where known.

```text
causation_id = event that directly triggered this event
```

This is distinct from a general correlation ID.

---

## 5. Correlation ID

A correlation ID groups related events belonging to a common operation, task or episode.

Example:

```text
correlation_id = walk_to_park_123
```

Many events may share this identifier without directly causing one another.

---

## 6. Temporal Order vs Causation

The architecture must never infer:

```text
A before B
```

as automatically meaning:

```text
A caused B
```

Example:

```text
battery decreased
then
Wi-Fi disconnected
```

This does not prove battery caused Wi-Fi loss.

---

## 7. Directly Observed Causation

Some causal relationships can be directly established by system mechanisms.

Example:

```text
user requested shutdown
      ↓
shutdown command issued
      ↓
system shutdown event
```

The system can record explicit causation when the mechanism is known.

---

## 8. Physical Causation

Physical causal claims should use evidence from:

- sensor observations;
- state transitions;
- action execution;
- physics/geometry constraints;
- repeated observations;
- controlled experiments where appropriate.

Language-model plausibility alone is insufficient.

---

## 9. Action → Outcome Linking

Actions should link to their observed outcomes.

```text
action
  ↓
expected outcome
  ↓
observed outcome
```

This is essential for learning action effectiveness.

---

## 10. Action Failure Chains

Example:

```text
navigation goal
    ↓
route selected
    ↓
obstacle detected
    ↓
route rejected
    ↓
replan
    ↓
new route
    ↓
goal completed
```

The complete chain becomes part of the episode rather than isolated memories.

---

## 11. Goal → Action Relationships

Actions should identify the goal they were intended to serve.

```text
goal_id
   ↓
action
   ↓
outcome
```

This allows Novi to distinguish purposeful actions from incidental movement.

---

## 12. Entity Linking

Events can reference entities:

```text
person
object
place
robot component
route
map
sensor
```

Example:

```text
obstacle_detected
entity = object_42
location = hallway
```

---

## 13. Entity State Transitions

Entity lifecycle changes should be linked:

```text
object detected
      ↓
tracked
      ↓
identified
      ↓
location changed
      ↓
missing
```

This provides temporal continuity without pretending the object was continuously observed.

---

## 14. Episode Construction

Episodes are constructed from related events rather than generated as stories first.

```text
events
 ↓
clustering
 ↓
episode candidate
 ↓
boundary detection
 ↓
validated episode
```

---

## 15. Episode Boundaries

Episode boundaries may be created by:

- goal start/end;
- location transition;
- major activity transition;
- user interaction;
- significant anomaly;
- time gap;
- explicit start/stop;
- system restart.

Multiple boundary hypotheses may exist before consolidation.

---

## 16. Nested Episodes

Episodes may contain subepisodes.

```text
trip
 ├── leave_home
 ├── travel
 ├── park_visit
 │    ├── explore_path
 │    └── interact_with_person
 └── return_home
```

This enables hierarchical autobiographical retrieval.

---

## 17. Episode Causality

Episodes can be related causally.

```text
low_battery episode
      ↓
return_home goal
      ↓
travel episode
      ↓
charging episode
```

The causal links must preserve evidence.

---

## 18. Episode Summaries

An episode summary should be derived from its underlying evidence.

A summary may include:

- objective;
- participants/entities;
- place;
- start/end;
- actions;
- observations;
- outcomes;
- surprises;
- failures;
- learned candidates.

The summary is a projection, not the authoritative event history.

---

## 19. Memory Lineage

Every important memory should be traceable back to source events.

```text
memory
 ↓
episode
 ↓
events
 ↓
sensor/user/system evidence
```

This enables auditing and correction.

---

## 20. Knowledge Lineage

Knowledge promoted from experiences should preserve its supporting memories/events.

```text
knowledge claim
 ↓
supporting memories
 ↓
supporting events
```

Unsupported knowledge must not appear authoritative.

---

## 21. Causal Hypothesis

A causal hypothesis should contain:

```text
cause_candidate
 effect
 evidence
 confidence
 context
 time_scope
 alternatives
```

Example:

```text
candidate:
low battery contributed to return-home behavior

confidence: high
context: autonomous policy
```

---

## 22. Alternative Explanations

When multiple causes are plausible, Novi should retain them.

```text
route deviation
 ├── obstacle
 ├── user instruction
 ├── localization uncertainty
 └── autonomous replanning
```

The system should not force a single explanation prematurely.

---

## 23. Counterfactual Reasoning

Novi may use bounded counterfactual reasoning:

> "Would the outcome likely have changed if action X had not occurred?"

Counterfactual conclusions must be labeled as hypothetical unless supported by controlled evidence.

---

## 24. Intervention Evidence

Where safe and appropriate, Novi can learn causality from interventions.

Conceptually:

```text
observe A → B

intervene on A

observe whether B changes
```

Physical interventions must always remain subject to safety policy.

---

## 25. Prediction Error and Causality

Prediction errors can generate causal investigation candidates.

```text
expected B after A
actual C
      ↓
why?
      ↓
possible missing cause
```

This connects causal learning to the predictive world model.

---

## 26. Causal Confidence

Confidence should depend on evidence quality, including:

- direct system causation;
- repeated observations;
- controlled intervention;
- sensor reliability;
- temporal ordering;
- alternative explanations;
- sample size;
- context consistency.

A language-model confidence score is not sufficient.

---

## 27. Context-Specific Causality

A relationship can be valid only under certain conditions.

Example:

```text
battery below threshold
 + autonomous navigation
 → return-home behavior
```

It does not imply every low-battery event causes every movement toward home.

---

## 28. Causal Graph Versioning

Causal knowledge must be versioned.

```text
causal_model_v1
      ↓
new evidence
      ↓
causal_model_v2
```

Historical decisions retain the model version used at the time.

---

## 29. Causal Knowledge vs Policy

A causal belief does not automatically become an action policy.

```text
causal knowledge
      ↓
planning input
      ↓
policy / safety validation
      ↓
action
```

This prevents learned correlations from becoming uncontrolled behavior.

---

## 30. Social Causality

Social events require extra caution.

Novi may record:

```text
person said X
then Novi did Y
```

without automatically concluding:

```text
person intentionally caused Y
```

Intent remains a hypothesis unless appropriately evidenced.

---

## 31. Emotional Causality

Affective observations must not become unsupported causal claims.

For example:

```text
voice arousal increased
      ↓
Novi changed interaction strategy
```

This does not establish:

```text
person was angry
```

unless evidence supports that interpretation.

---

## 32. Spatial Causality

Spatial relationships can support causal reasoning.

Example:

```text
obstacle located in hallway
      ↓
route blocked
      ↓
route changed
```

The spatial evidence and temporal order should remain linked.

---

## 33. Environmental Causality

Environmental changes can be linked to outcomes:

```text
high temperature
      ↓
thermal throttling
      ↓
reduced inference throughput
```

Where the hardware/runtime system directly establishes the relationship, it can be recorded as high-confidence causation.

---

## 34. Hardware Causality

Hardware diagnostics may create strong causal chains:

```text
fan failure
 ↓
thermal rise
 ↓
protective throttling
```

These should be sourced from authoritative telemetry and diagnostic systems.

---

## 35. Causal Memory Retrieval

Queries may request causal history:

```text
Why did Novi return home?
Why did the route change?
What caused the navigation failure?
What led to this memory?
What evidence supports this belief?
```

Retrieval should return the causal chain plus confidence and alternatives.

---

## 36. Causal Explanation

An explanation should distinguish:

```text
observed
inferred
hypothesized
supported
unknown
```

Example:

> "The route changed after an obstacle was detected. The system recorded the obstacle as the direct trigger for replanning."

This is preferable to an unsupported narrative explanation.

---

## 37. Event Graph Integrity

Causal/episode graphs must protect against:

- cycles that imply impossible causation;
- orphan references;
- deleted source evidence;
- inconsistent timestamps;
- impossible state transitions;
- unauthorized mutation.

---

## 38. Cycles

Some real systems have feedback loops:

```text
action
 ↓
observation
 ↓
new decision
 ↓
action
```

The event graph can represent these as temporal cycles in the overall process, but individual causal edges must remain semantically defined.

---

## 39. Duplicate Events

Duplicate event ingestion must not create duplicate causal history.

Use stable event IDs and idempotent ingestion.

---

## 40. Out-of-Order Events

Events may arrive out of order.

The system should preserve:

- event time;
- ingestion time;
- sequence information;
- causal references.

Episode construction can be corrected after late events arrive.

---

## 41. Late Evidence

New evidence may revise a previous causal hypothesis.

```text
hypothesis v1
      ↓
new evidence
      ↓
reassessment
      ↓
hypothesis v2
```

Historical records remain immutable; derived conclusions can be superseded.

---

## 42. Correction Without History Destruction

If Novi discovers that:

```text
"sensor failure caused route deviation"
```

was incorrect, it should not erase the original hypothesis.

Instead:

```text
original hypothesis
status = superseded
reason = new evidence
replacement = hypothesis v2
```

---

## 43. Memory Consolidation

Repeated causal evidence may promote a hypothesis into stronger knowledge.

```text
hypothesis
 ↓
repeated evidence
 ↓
validation
 ↓
knowledge candidate
 ↓
promotion policy
 ↓
knowledge
```

Promotion remains governed by memory/knowledge admission rules.

---

## 44. Forgetting

Forgetting an episode must not necessarily destroy a higher-level knowledge claim if sufficient independent supporting evidence remains.

Conversely, if all support is removed, derived knowledge may need reevaluation.

---

## 45. Privacy and Deletion

Deletion requests must propagate according to the established privacy architecture.

The system must identify derived memories/knowledge that depend on deleted personal events where policy requires reconsideration or removal.

---

## 46. Security

Causal history is security-sensitive because it can influence future decisions.

Unauthorized modification could cause Novi to believe:

```text
false event
false cause
false person association
false outcome
```

Integrity protection is therefore required.

---

## 47. Replay

Causal chains should be replayable for testing.

Replay can evaluate:

- alternative models;
- new causal hypotheses;
- memory admission;
- decision behavior;
- failure diagnosis.

Replay must default to non-actuating mode.

---

## 48. Simulation

Controlled simulation can provide causal evidence without exposing the physical robot to unnecessary risk.

NVIDIA Isaac Sim and other local simulation tools may be used where appropriate.

Simulation-derived evidence must be clearly labeled as simulated.

---

## 49. Real vs Simulated Evidence

Never mix them silently.

```text
REAL_EVENT
SIMULATED_EVENT
HYPOTHETICAL_EVENT
```

Each has different evidentiary status.

---

## 50. Model-Generated Causal Claims

An LLM may propose:

```text
possible cause = X
```

but this remains a hypothesis until accepted through evidence/policy.

The model cannot write a canonical causal relationship merely by generating it.

---

## 51. Causal Graph Storage

The implementation may use:

- relational tables;
- event stores;
- graph databases;
- SQLite tables;
- local files;
- specialized graph indexes.

The canonical semantic model must remain storage-independent.

---

## 52. Offline Operation

Causal and episode linking must function locally without Wi-Fi, Bluetooth or cloud services.

Synchronization is an optional enhancement.

---

## 53. Resource Awareness

Causal graph construction can be expensive.

The system should prioritize:

- safety-relevant chains;
- active goal chains;
- important autobiographical episodes;
- diagnostic chains;
- high-value learning candidates.

Deep causal analysis can be deferred to background processing.

---

## 54. Testing Requirements

Test:

- temporal-only relationships;
- direct causation;
- false causation candidates;
- alternative explanations;
- action/outcome chains;
- nested episodes;
- late events;
- duplicate events;
- out-of-order events;
- corrections;
- causal confidence;
- causal model versioning;
- privacy deletion propagation;
- graph integrity;
- simulation/real separation;
- replay;
- restart recovery;
- offline operation;
- malicious causal-history mutation.

---

## 55. Architectural Invariants

1. Temporal order does not imply causation.
2. Correlation does not imply causation.
3. LLM-generated explanations are not automatically causal facts.
4. Causal claims retain evidence and provenance.
5. Alternative explanations remain representable.
6. Action outcomes link back to the action and goal.
7. Episodes are constructed from evidence, not invented narratives.
8. Historical source events remain immutable.
9. Derived causal conclusions can be superseded without destroying history.
10. Current causal knowledge is versioned.
11. Simulation-derived evidence is clearly separated from real-world evidence.
12. Causal knowledge does not automatically grant action authority.
13. Social and emotional causality receives stronger uncertainty handling.
14. Privacy deletion can require reevaluation of derived knowledge.
15. Causal graphs remain locally usable without network connectivity.
16. Important causal chains are auditable.
17. Safety and security remain higher authority than learned causal beliefs.

---

## 56. Final Principle

> **Novi should remember not only that events occurred, but how they are related—while remaining honest about which relationships were observed, which were inferred, and which are genuinely supported by evidence.**

This creates the causal bridge between Novi's event history, episodic memory, world model, goals, actions, outcomes and long-term learning without allowing generated explanations to become invented reality.
