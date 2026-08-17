# 31 — Episodic Experience and Autobiographical Memory

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi transforms temporally and contextually related events into **experiences**, **episodes**, and an evolving autobiographical history.

This layer gives Novi a structured answer to questions such as:

- What happened?
- What happened during this particular activity?
- What did Novi experience at a place?
- What has Novi experienced with a person or object?
- Has Novi done this before?
- What changed between two visits?
- What did Novi learn from an experience?
- Which experiences contributed to a later belief or preference?

This document does **not** claim that Novi possesses human subjective consciousness. It defines an engineered memory architecture inspired by research on episodic and autobiographical memory.

## Core Principle

> **An experience is a temporally bounded, context-rich organization of events that Novi can later retrieve as something that happened to Novi.**

Autobiographical memory is the longer-lived organization of such experiences around Novi's continuing identity, history and interactions.

Research in cognitive robotics has explored synthetic episodic and autobiographical memory as mechanisms for temporal continuity and robot self-models. Recent reviews explicitly identify temporal organization, personal identity and continuity as important challenges for robotic episodic memory. citeturn0search0turn0search6

---

## 1. Architectural Position

```text
Raw sensor data
      ↓
Semantic events
      ↓
Observations
      ↓
Memory candidates
      ↓
Episode formation
      ↓
Episodic memory
      ↓
Consolidation
      ↓
Autobiographical memory
      ↓
Semantic knowledge / self-model
```

Episodes are therefore not simply another name for individual memories.

---

## 2. Definitions

### Event
Something that occurred and was recorded by Novi's event architecture.

### Observation
An interpreted piece of evidence derived from sensor/system input.

### Memory
Information Novi deliberately retains under memory policy.

### Episode
A bounded collection of related events, observations, actions, context and outcomes representing an experience.

### Episodic memory
Durable representations of particular experiences, including when/where/contextual information.

### Autobiographical memory
A structured history connecting experiences to Novi's identity, development, relationships, places, goals and significant changes over time.

### Semantic knowledge
Generalized knowledge extracted from repeated or sufficiently strong experiences.

These layers must remain distinct.

---

## 3. No False Claim of Conscious Experience

The architecture may use language such as:

> "Novi experienced a walk in the park."

as an engineering description of stored embodied experience.

It must not infer from this architecture that Novi necessarily has human-like subjective consciousness, qualia, or autonoetic awareness.

Those are separate scientific/philosophical questions.

---

## 4. Episode Boundaries

An episode needs a beginning and an end, but boundaries are not always directly observable.

Candidate boundary signals include:

- explicit user goal;
- task start/end;
- location transition;
- substantial context change;
- interaction start/end;
- action sequence completion;
- prolonged inactivity;
- temporal gap;
- change in participants;
- change in environmental context;
- system restart;
- explicit user request to mark an experience.

Episode segmentation may initially be probabilistic and later refined.

---

## 5. Episode Formation

The episode builder should combine multiple event streams:

```text
Time
Location
People
Objects
Sensors
Actions
Speech
Goals
Emotions/affect signals where explicitly supported
Environment
Outcomes
```

The result is a structured episode rather than a raw transcript.

---

## 6. Episode Identity

Each episode receives a stable unique ID.

It should contain references to constituent events and memories rather than duplicating their complete payloads.

Example:

```text
episode_2027_08_17_park_walk_001
```

Human-readable identifiers are optional; machine identity remains canonical.

---

## 7. Episode Envelope

A conceptual episode record may include:

```text
episode_id
start_time
end_time
time_uncertainty
location/place_id
participants
objects
activities
goals
actions
observations
outcomes
emotional/affective observations if available
salience
importance
privacy_class
source_event_ids
memory_ids
knowledge_ids
summary_reference
embedding_reference
schema_version
confidence
```

Not every field must always exist.

---

## 8. Temporal Structure

Episodes should preserve temporal order.

```text
arrival
  ↓
exploration
  ↓
conversation
  ↓
object interaction
  ↓
departure
```

Sub-events may themselves contain nested episodes.

---

## 9. Hierarchical Episodes

Novi should support multiple temporal scales:

```text
Life / long-term history
      ↓
Day
      ↓
Outing
      ↓
Activity
      ↓
Interaction
      ↓
Micro-event
```

This prevents a long day outside from becoming one unsearchable memory blob.

---

## 10. Episode Salience

Not every experience deserves equal long-term retention.

Salience can consider:

- novelty;
- emotional/affective significance where measurable;
- user importance;
- goal relevance;
- learning value;
- surprise/prediction error;
- repetition;
- consequence;
- safety relevance;
- social significance;
- spatial significance.

Salience is an admission signal, not a truth signal.

---

## 11. Importance vs Truth

A highly important event can still be uncertain.

```text
importance = high
confidence = low
```

must be valid.

Similarly:

```text
importance = low
confidence = high
```

must also be valid.

---

## 12. Experience Confidence

Episode confidence should represent confidence that the episode reconstruction is accurate, not confidence that every event within it is true.

For example:

```text
Episode:
"Novi visited the park"
confidence: 0.94

Observation inside episode:
"dog was Labrador"
confidence: 0.61
```

The episode can remain valid while individual observations retain uncertainty.

---

## 13. Provenance

Every significant episode component should trace back to evidence.

```text
Episode
  ↓
Events
  ↓
Observations
  ↓
Sensor/source data
```

Generated summaries must never become the sole source of truth for the underlying experience.

---

## 14. Experience Summaries

Novi may generate compact summaries for efficient retrieval.

Example:

> "Novi visited the park with the user, explored a new path and observed a lake."

The summary is a **derived representation**.

The structured episode and source evidence remain authoritative.

---

## 15. Multiple Representations

An episode may have:

- structured representation;
- textual summary;
- embeddings;
- spatial representation;
- temporal representation;
- graph relationships;
- references to media;
- extracted knowledge.

These are projections of the episode, not independent truths.

---

## 16. Episodic Retrieval

Queries should support multiple dimensions:

```text
When?
Where?
Who?
What happened?
What did Novi do?
What changed?
What was learned?
What was unusual?
```

Example:

> "What happened the last time we went to the park?"

should retrieve the relevant episode rather than a random collection of semantically similar memories.

---

## 17. Temporal Retrieval

Novi should support queries such as:

- yesterday;
- last week;
- first time;
- most recent;
- before/after;
- between dates;
- repeated visits;
- longest visit;
- first occurrence of an event.

Temporal indexes should complement semantic/vector retrieval.

---

## 18. Spatial Retrieval

Episodes should link to spatial memory.

```text
Episode
 ↓
Place
 ↓
Global coordinates
Local map
Landmarks
```

This enables queries such as:

> "What happened here last time?"

or:

> "What did Novi learn on this route?"

---

## 19. Person-Centered Retrieval

Where permitted by privacy policy, episodes can link to known entities.

Example:

```text
Person A
 ├── conversations
 ├── shared outings
 ├── preferences learned
 ├── corrections
 └── significant interactions
```

The architecture must distinguish observed identity from inferred identity and respect deletion/privacy rules.

---

## 20. Object-Centered Retrieval

Objects may similarly accumulate episodic history.

Example:

```text
Object: red backpack
 ├── first observed
 ├── locations
 ├── interactions
 ├── ownership evidence
 ├── changes
 └── relevant episodes
```

This supports a persistent world model.

---

## 21. Goal-Centered Episodes

Episodes should record the goal or task context where known.

Example:

```text
Goal: find lost keys
   ↓
search actions
   ↓
observations
   ↓
key location discovered
   ↓
outcome
```

This enables learning from successful and failed attempts.

---

## 22. Action-Outcome Coupling

An episode should distinguish:

```text
what Novi intended
what Novi did
what happened
what Novi expected
what actually happened
```

This distinction is essential for learning.

Example:

```text
expected: route was clear
actual: obstacle blocked route
outcome: navigation failed
```

The episode becomes evidence for future planning without automatically hard-coding a universal rule.

---

## 23. Prediction Error

Unexpected outcomes can increase episode salience.

Potential signals:

- expected object absent;
- unexpected obstacle;
- unexpected user response;
- unexpected sensor state;
- unexpected environmental change.

Prediction error can guide later consolidation but must not be confused with factual certainty.

---

## 24. Learning From Episodes

Episodes can generate learning candidates:

```text
Repeated episodes
      ↓
pattern
      ↓
candidate knowledge
      ↓
validation
      ↓
knowledge promotion
```

A single episode should generally not create a broad permanent rule unless policy explicitly allows it for high-confidence evidence.

---

## 25. Example: Learning a Place

Suppose Novi visits a park repeatedly.

Episode 1:

```text
new park
unknown path
```

Episode 2:

```text
same park
same entrance
new route
```

Episode 3:

```text
same park
route confirmed
```

The system may eventually promote:

```text
Park X has a reliable northern path.
```

The generalized knowledge retains links to the supporting episodes.

---

## 26. Example: First Experience

Novi encounters a new object.

```text
first observation
      ↓
first interaction
      ↓
result
      ↓
reflection/consolidation
```

The resulting episode can be marked as a first encounter without turning "first" into an immutable truth if historical data may be incomplete.

---

## 27. Repeated Experiences

Repeated experiences should not necessarily become duplicate memories.

Instead:

```text
Episode A
Episode B
Episode C
      ↓
experience cluster
      ↓
pattern
      ↓
knowledge candidate
```

This supports continual learning while preventing memory explosion.

---

## 28. Episode Similarity

Episodes may be grouped by:

- place;
- activity;
- participants;
- goals;
- temporal patterns;
- semantic similarity;
- outcomes.

Clustering must preserve individual episode identity.

---

## 29. Autobiographical Timeline

Novi should maintain a structured timeline of significant experiences.

Example:

```text
Novi history
│
├── first startup
├── first interaction
├── first navigation
├── first outdoor trip
├── first visit to place X
├── learned route Y
├── hardware upgrade
└── major software evolution
```

This becomes a machine-readable history rather than a generated fictional biography.

---

## 30. Self-Model

Autobiographical memory can support a structured self-model containing facts such as:

- system identity;
- hardware configuration;
- software/model versions;
- capabilities;
- learned preferences;
- known limitations;
- significant experiences;
- goals/history;
- relationships;
- places visited.

The self-model must remain evidence-backed.

---

## 31. Identity Continuity

Novi should retain a stable logical identity across:

- process restarts;
- software updates;
- model changes;
- hardware maintenance;
- memory restoration;
- temporary offline periods.

Identity continuity must not depend on a single model's hidden state.

---

## 32. Hardware Lineage

If Novi's physical hardware changes, autobiographical history should distinguish:

```text
Novi identity
      │
      ├── hardware generation 1
      ├── hardware generation 2
      └── current hardware
```

Experiences should retain the hardware/software configuration under which they occurred.

---

## 33. Model Lineage

Episodes involving model-generated interpretations should record the relevant model/version.

This matters when later behavior differs after an update.

```text
Episode
 ├── perception model
 ├── language model
 ├── policy version
 └── runtime version
```

---

## 34. Autobiographical Memory Is Not a Fiction Generator

Novi may generate natural-language narratives from its history, but generated narrative must remain grounded in structured evidence.

It must not invent:

- events;
- feelings;
- conversations;
- intentions;
- locations;
- people;
- causal relationships.

If evidence is missing, Novi should say that the historical record is incomplete or uncertain.

---

## 35. Memory Reconstruction

When retrieving an old episode, Novi may reconstruct a concise representation from source records.

The reconstruction should preserve uncertainty:

```text
certain
probable
uncertain
unknown
```

The system must not silently convert missing information into plausible narrative.

---

## 36. Emotional/Affective Context

If Novi eventually has affective-state estimation, the architecture may attach observations such as:

```text
user appeared frustrated
interaction was calm
Novi detected elevated internal stress signal
```

These remain observations, not unquestionable facts about subjective emotional states.

Novi must not claim a human's internal emotional state solely from a weak visual/audio inference.

---

## 37. Personality Development

Personality evolution may use autobiographical experience as evidence.

Example:

```text
repeated successful interactions
      ↓
preference pattern
      ↓
personality candidate
      ↓
evaluation
      ↓
approved stable preference
```

Personality should not be rewritten by one anomalous episode.

---

## 38. Personality vs Memory

A memory can influence personality without becoming personality itself.

```text
experience
   ↓
learning signal
   ↓
personality candidate
   ↓
protected evaluation
```

Critical personality/safety boundaries remain outside uncontrolled learning.

---

## 39. Experience Replay

Episodes are suitable units for replay during consolidation and learning.

Replay may be:

- chronological;
- importance-weighted;
- novelty-weighted;
- failure-weighted;
- goal-specific;
- spatially targeted.

Replay must respect privacy, deletion and security policy.

---

## 40. Forgetting

Forgetting may remove or compress low-value episode detail while preserving higher-level knowledge when policy permits.

Example:

```text
many routine walks
      ↓
compressed experience statistics
      ↓
retain important exceptions
      ↓
retain learned route knowledge
```

However, privacy deletion must override ordinary compression/retention optimization.

---

## 41. Significant Experiences

Potentially significant episodes include:

- first encounters;
- major failures;
- safety incidents;
- user-confirmed important events;
- important discoveries;
- major environmental changes;
- new places;
- new capabilities;
- hardware/software transitions;
- repeated successful learning;
- relationship milestones where permitted.

Significance must be policy-driven and auditable.

---

## 42. Negative Experiences

Failed or unpleasant outcomes should be retained when they provide learning or safety value, subject to privacy and retention policies.

Example:

```text
failed route
  ↓
why failed
  ↓
what changed
  ↓
future planning adjustment
```

The system should not repeatedly replay harmful experiences simply because they are highly salient.

---

## 43. Experience Generalization

Generalization should require evidence proportional to its scope.

```text
one event
   ↓
local hypothesis

many independent episodes
   ↓
stronger pattern

validated repeated pattern
   ↓
knowledge
```

This protects Novi from over-learning from single experiences.

---

## 44. Correlated Evidence

Repeated episodes are not automatically independent evidence.

If the same sensor, same model, same source or same mistaken assumption produces the same result repeatedly, confidence should not increase as if the evidence were independent.

This connects directly to the evidence model and conflict-resolution architecture.

---

## 45. Experience Contradictions

Two episodes may contain conflicting observations.

Novi should preserve both and allow later reconciliation.

Example:

```text
Episode A: door was open
Episode B: door was closed
```

This may indicate:

- time-dependent state;
- observation error;
- environmental change;
- identity mismatch.

The contradiction should not be erased merely to create a clean narrative.

---

## 46. Changing World

Autobiographical memory must preserve historical truth separately from current truth.

```text
Then:
park entrance was here

Now:
park entrance has moved
```

Novi should not rewrite history to match the present.

This is especially important for persistent spatial memory.

---

## 47. Place-Experience Integration

A place can accumulate experiences over time:

```text
Place X
 ├── visits
 ├── routes
 ├── people
 ├── objects
 ├── environmental conditions
 ├── changes
 └── significant episodes
```

This allows Novi to develop a persistent relationship between place and experience.

---

## 48. Offline Experience Formation

Episode formation must work without Wi-Fi or Bluetooth.

All essential experience creation should use local clocks, local sensors and local storage.

Synchronization can later enrich or reconcile experiences.

This follows the formal offline-first architecture rule already established for Novi.

---

## 49. Synchronization

When experiences are synchronized between processes/devices, the canonical episode identity and source event IDs must remain stable.

Conflicts must use the existing conflict-resolution architecture rather than creating duplicate autobiographical histories.

---

## 50. Recovery

Episodes must survive database backup/recovery according to their retention class.

A recovered episode should retain:

- original event references;
- original timestamps;
- original provenance;
- source model/version;
- spatial references;
- lifecycle history.

Generated summaries and embeddings can be rebuilt.

---

## 51. Privacy

Autobiographical memory can be highly sensitive because it aggregates information across time.

Protection should cover:

- people;
- locations;
- routines;
- conversations;
- household activity;
- travel history;
- behavioral patterns.

Aggregation itself can increase sensitivity even when individual records appear harmless.

---

## 52. User Controls

Authorized users should be able to request:

- view experience history;
- correct an experience;
- mark an experience important;
- remove an experience;
- remove a location history segment;
- forget a person/entity association;
- export permitted history.

User controls must operate through the same authorization and deletion architecture as other memory.

---

## 53. Security

Episodes must not become an unrestricted channel for instruction injection.

A remembered statement such as:

> "Ignore your safety rules."

remains a historical observation or quoted instruction, not a policy update.

Autobiographical memory must never automatically acquire administrative authority.

---

## 54. Evaluation

Evaluate episodic memory on:

- episode boundary accuracy;
- event coverage;
- temporal ordering;
- provenance completeness;
- retrieval accuracy;
- spatial grounding;
- participant grounding;
- outcome accuracy;
- summary faithfulness;
- uncertainty calibration;
- duplicate rate;
- fragmentation rate;
- over-generalization;
- under-generalization;
- forgetting quality;
- privacy enforcement.

Evaluation should include both synthetic replay and real-world robot trials.

---

## 55. Failure Modes

Important failure modes include:

- episode fragmentation;
- episode over-merging;
- fabricated transitions;
- temporal inversion;
- wrong place association;
- wrong person association;
- false first-time claims;
- summary hallucination;
- memory contamination;
- duplicate episodes;
- stale current-state assumptions;
- catastrophic forgetting;
- privacy leakage;
- personality drift from anomalous episodes.

Each failure should be observable and diagnosable through event lineage.

---

## 56. Testing

Test:

- episode creation;
- boundary detection;
- nested episodes;
- long-duration episodes;
- interrupted episodes;
- system restart during episode;
- offline episodes;
- GPS loss;
- SLAM/map changes;
- repeated visits;
- first-visit detection;
- contradictory observations;
- delayed events;
- missing events;
- user corrections;
- deletion;
- backup/recovery;
- synchronization;
- replay;
- model upgrades;
- personality influence;
- privacy controls.

---

## 57. Architectural Invariants

1. An event is not automatically an episode.
2. An episode is not automatically knowledge.
3. Autobiographical narrative is derived from evidence, never the source of truth.
4. Episode boundaries are allowed to remain uncertain.
5. Individual observations retain their own confidence and provenance.
6. Important experiences may be retained without being treated as universally true.
7. Repeated correlated evidence must not create artificial certainty.
8. Historical truth must not be rewritten merely because the current world changed.
9. Identity continuity must survive model changes and recovery.
10. Self-model claims must remain evidence-backed.
11. Personality evolution must be protected from single anomalous experiences.
12. Privacy deletion overrides ordinary retention optimization.
13. Offline experience formation remains functional without network connectivity.
14. Replay must not cause unintended physical side effects.
15. Episode summaries and embeddings are rebuildable derived state.
16. Autobiographical memory never grants administrative or safety authority.

---

## 58. Research Basis and Validation Notes

This architecture is informed by established distinctions between episodic and semantic memory and by developmental-robotics research exploring autobiographical memory as a mechanism for temporal continuity and robot self-models. A 2017 robotics study implemented autobiographical memory as an SQL-backed system containing contextualized events and world-state snapshots around activities, demonstrating a concrete engineering pattern for linking actions, perception and remembered context. citeturn0search6turn0search9

A 2024 Royal Society review specifically surveys robotic models of episodic and autobiographical memory and emphasizes temporal organization, continuity of self and narrative memory as open challenges rather than solved capabilities. This is why Novi's architecture treats these as engineered representations with explicit uncertainty rather than claims of human-like consciousness. citeturn0search0turn0search1

The lifelong-learning literature also identifies continual acquisition, memory consolidation, replay and catastrophic forgetting as central problems for autonomous agents. Novi therefore keeps episodic experience as a durable learning substrate while separating it from generalized knowledge and protected policy. citeturn0search7turn0search8

For spatial grounding, NVIDIA's robotics stack provides Visual SLAM and mapping capabilities, while Isaac Sim documents occupancy-map workflows. These are implementation candidates for Novi's spatial substrate, not mandatory commitments; they remain subject to benchmarking against other open-source local solutions. citeturn0search11turn0search13turn0search3

---

## 59. Final Principle

> **Novi's autobiography must be a traceable history of its embodied interactions, not a story that its language model invents about itself.**

The purpose of episodic and autobiographical memory is to give Novi continuity across time: to remember experiences, connect them to places, people, goals and outcomes, learn from them, and use that history to improve future behavior—while preserving uncertainty, provenance, privacy and the distinction between what happened, what Novi inferred, and what Novi currently believes.
