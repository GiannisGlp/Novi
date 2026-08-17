# Novi — World Model Architecture

**Status:** P0 critical architecture specification  
**Version:** 1.0  
**Date:** 2026-08-17  
**Authority:** `02-novi-brain`  
**Depends on:** 02 Cognitive Architecture, 03 Brain State Model, 05 Cognitive Cycle, 11 Perception Architecture, 16 Multimodal Fusion, 17 Spatial & Proprioceptive Fusion

---

## 1. Purpose

The Novi World Model is the persistent computational representation Novi maintains about the external world, Novi's own embodied state, other agents, events, relationships, affordances, uncertainty, and predicted future states.

It is the bridge between raw sensing and cognition.

The World Model must allow Novi to answer, continuously and with explicit uncertainty:

- What is around me?
- Where is it?
- What is it doing?
- What changed?
- Who is present?
- Who is interacting with whom?
- What happened recently?
- What is likely to happen next?
- What can I safely do here?
- What do I know versus merely believe?
- What do I not know?
- What should I observe next?
- How did my own action change the world?

The World Model is **not** a database of raw sensor data, a vector store, an LLM context window, a simulator, or a single neural network.

It is a continuously updated state-estimation and representation layer built from heterogeneous evidence.

---

# 2. Core principle

Novi must never collapse different epistemic categories into one undifferentiated representation.

```text
OBSERVATION
    ≠
MODEL INFERENCE
    ≠
FUSED EVIDENCE
    ≠
BELIEF / ESTIMATE
    ≠
MEMORY
    ≠
PREDICTION
    ≠
SIMULATION
    ≠
COUNTERFACTUAL
    ≠
VERIFIED FACT
```

Every World Model state element must preserve its epistemic status and provenance.

This is essential for safe autonomy and for making Novi capable of saying, in effect, **"I am not sure."**

---

# 3. World Model responsibilities

The World Model owns the representation and evolution of:

1. spatial state;
2. temporal state;
3. entities;
4. entity attributes;
5. relationships;
6. events;
7. activities;
8. environmental conditions;
9. object state;
10. agent state;
11. Novi's embodied state reference;
12. affordances;
13. hazards;
14. interaction state;
15. uncertainty;
16. beliefs;
17. predictions;
18. changes and deltas;
19. provenance;
20. world-state snapshots and versions.

It does **not** own:

- motor control;
- emergency safety;
- raw sensor drivers;
- durable human-memory policy;
- model weights;
- arbitrary LLM context;
- authoritative physical truth.

Those remain owned by their respective subsystems.

---

# 4. Architecture

```text
                    PHYSICAL WORLD
                          │
             ┌────────────┴────────────┐
             │                         │
          SENSORS                   ACTIONS
             │                         │
             ↓                         ↓
      PERCEPTION / FUSION       ACTION OUTCOME
             │                         │
             └────────────┬────────────┘
                          ↓
                 WORLD MODEL INGEST
                          ↓
                TIME / FRAME ALIGNMENT
                          ↓
                 ENTITY ASSOCIATION
                          ↓
                 STATE ESTIMATION
                          ↓
             RELATIONSHIP / EVENT UPDATE
                          ↓
              BELIEF + UNCERTAINTY UPDATE
                          ↓
             ┌────────────┼─────────────┐
             │            │             │
          CURRENT       HISTORY       FUTURE
           STATE        / MEMORY      PREDICTION
             │            │             │
             └────────────┼─────────────┘
                          ↓
                    WORLD MODEL
                          │
          ┌───────────────┼────────────────┐
          ↓               ↓                ↓
      ATTENTION        REASONING        PLANNING
          │               │                │
          └───────────────┼────────────────┘
                          ↓
                       ACTION
                          ↓
                    PHYSICAL WORLD
```

The loop is closed: actions create new observations, and those observations update the World Model.

---

# 5. World Model layers

The canonical World Model consists of several related layers.

## 5.1 Geometric layer

Represents:

- coordinate frames;
- robot pose;
- object poses;
- surfaces;
- obstacles;
- free space;
- maps;
- 3D reconstruction;
- semantic regions;
- navigable space;
- spatial uncertainty.

This layer should consume authoritative spatial outputs from the robotics/perception stack rather than reconstructing geometry from language-model guesses.

## 5.2 Entity layer

Represents persistent or semi-persistent entities such as:

- people;
- animals;
- objects;
- rooms;
- doors;
- furniture;
- vehicles;
- devices;
- locations;
- organizations/services where relevant.

Each entity receives a stable internal identity separate from any external name or recognition hypothesis.

## 5.3 State layer

Represents dynamic properties:

- position;
- velocity;
- orientation;
- visibility;
- activity;
- possession;
- occupancy;
- open/closed;
- powered/unpowered;
- available/unavailable;
- damaged/normal;
- interaction state.

State must have timestamps and confidence/provenance.

## 5.4 Relationship layer

Represents relationships such as:

- person-near-object;
- person-facing-person;
- person-holding-object;
- object-on-surface;
- object-inside-room;
- robot-near-person;
- person-speaking-to-robot;
- obstacle-blocks-path;
- agent-following-agent.

Relationships are time-dependent and should not be treated as permanent facts unless independently verified.

## 5.5 Event layer

Represents changes rather than static state:

- person entered room;
- person left;
- object moved;
- door opened;
- sound detected;
- collision/near-collision;
- command received;
- task started;
- task completed;
- unexpected event;
- sensor degradation.

Events are immutable records with provenance.

## 5.6 Activity layer

Represents higher-level ongoing activities:

- walking;
- talking;
- eating;
- carrying;
- searching;
- approaching;
- manipulating;
- interacting with Novi.

Activity recognition is probabilistic and must retain confidence and temporal evidence.

## 5.7 Affordance layer

Represents actions that may be possible in the current state:

- walk through doorway;
- approach person;
- pick up object;
- place object;
- follow person;
- speak;
- inspect object.

An affordance is **not permission** to act.

```text
AFFORDANCE
   ↓
FEASIBILITY
   ↓
GOAL RELEVANCE
   ↓
AUTHORIZATION
   ↓
SAFETY
   ↓
ACTION
```

## 5.8 Hazard layer

Represents known or inferred hazards:

- obstacle;
- moving object;
- person proximity;
- unsafe surface;
- collision risk;
- heat;
- electrical hazard;
- restricted region;
- uncertain navigation area.

Safety-critical hazard handling must not depend solely on the World Model.

## 5.9 Prediction layer

Represents hypotheses about future state:

- predicted human trajectory;
- object motion;
- likely interaction;
- likely environment change;
- action outcome;
- alternative futures.

Predictions must never overwrite current observed state.

---

# 6. Temporal model

The World Model must be explicitly temporal.

Every meaningful state element should support:

- observed-at time;
- valid-from time;
- valid-until time where known;
- ingested-at time;
- model-produced-at time;
- confidence;
- source;
- version.

Novi must distinguish:

```text
"I see the door is open now"

from

"The door was open five seconds ago"

from

"The door will probably remain open"
```

Temporal reasoning must support:

- ordering;
- duration;
- recurrence;
- simultaneity;
- interruption;
- causally relevant sequences;
- stale-state detection.

---

# 7. Spatial model

The World Model uses a hierarchy of spatial representations rather than a single map.

```text
GLOBAL / MAP FRAME
        ↓
LOCATION / ROOM
        ↓
REGION
        ↓
SURFACE / OBJECT
        ↓
BODY / SENSOR FRAME
        ↓
RELATIVE GEOMETRY
```

Spatial references must carry frame identifiers and timestamps.

No component may silently assume that two poses are expressed in the same frame.

---

# 8. Entity identity

Entity identity is probabilistic unless grounded by a sufficiently authoritative source.

For a person, Novi may maintain:

```text
Entity ID: person-017
Recognition hypothesis: likely Alice
Identity confidence: 0.91
Evidence: face + voice + context
Last observed: timestamp
Location: room-03
Interaction state: speaking-to-Novi
```

The identity hypothesis must remain distinct from the stable entity identifier.

This prevents recognition errors from corrupting the entire knowledge/memory system.

---

# 9. Evidence and belief update

A World Model update should follow:

```text
Evidence
   ↓
Association
   ↓
Consistency check
   ↓
State update
   ↓
Uncertainty update
   ↓
Provenance
   ↓
Versioned world state
```

Contradictory evidence must not be silently discarded.

Example:

```text
Vision: object at A, confidence 0.8
LiDAR: object at B, confidence 0.7

        ↓

Conflict detected
        ↓

Temporal/calibration/source check
        ↓

Resolve / maintain uncertainty / request more sensing
```

The correct result may be **uncertain**, not an arbitrary winner.

---

# 10. World state and memory are different

The current World Model answers:

> What is probably true about the world now?

Memory answers:

> What should Novi retain about what happened and what it learned?

The World Model may contain transient state that should never become durable memory.

Conversely, durable memory may contain historical information that is not current World Model state.

```text
WORLD MODEL
   │
   ├── current state
   ├── transient beliefs
   └── active predictions

MEMORY
   │
   ├── episodic
   ├── semantic
   ├── procedural
   └── social
```

Promotion from World Model to memory must use the memory admission policy.

---

# 11. World Model and knowledge are different

Knowledge represents relatively stable or externally sourced information.

The World Model represents current embodied context.

Example:

```text
Knowledge:
"A kettle is a container used to boil water."

World Model:
"There is a kettle on the kitchen counter right now."
```

Knowledge may help interpret World Model observations, but knowledge must not be mistaken for observation.

---

# 12. World Model and simulation are different

Simulation can produce hypothetical worlds.

The World Model represents Novi's current estimated real-world state.

```text
REAL OBSERVATION
    ≠
SIMULATED OBSERVATION
    ≠
PREDICTED FUTURE
    ≠
COUNTERFACTUAL FUTURE
```

Simulation results must carry an explicit provenance class.

A simulated future may inform planning but must never silently enter the current real-world state.

---

# 13. World-model prediction

Novi may maintain predictive models at several levels.

## Deterministic / analytical

- kinematics;
- collision geometry;
- known trajectories;
- navigation constraints.

## Learned specialist models

- human motion;
- object motion;
- activity transitions;
- interaction prediction.

## Foundation/world models

Potential candidates include NVIDIA Cosmos-family world foundation models.

NVIDIA currently describes Cosmos 3 as an omni-model with native reasoning, world generation and action generation, and describes it as capable of generating plausible futures from multimodal inputs. citeturn0search0

NVIDIA's technical material describes the physical-AI problem as requiring both understanding of the current world and generation/prediction of plausible future states; Cosmos 3 combines these capabilities within a unified architecture. citeturn0search24turn0search6

However, **Cosmos is not the Novi World Model by definition**. It is a candidate model capability underneath the World Model abstraction.

---

# 14. Predictive branching

For complex decisions, Novi may maintain multiple candidate futures:

```text
CURRENT STATE
      │
      ├── action A → future A
      ├── action B → future B
      └── action C → future C
```

Each branch must include:

- originating state version;
- proposed action;
- model used;
- assumptions;
- predicted outcome;
- confidence/uncertainty;
- simulation/model provenance;
- expiration.

Branches are hypotheses, not world facts.

---

# 15. Imagination boundary

Novi may internally simulate or imagine possible situations.

The architecture must maintain a strict boundary:

```text
REAL WORLD STATE
       │
       ├── observed
       ├── inferred
       └── predicted

HYPOTHETICAL SPACE
       │
       ├── planned future
       ├── simulated future
       └── counterfactual
```

A hypothetical state must never be committed as current reality without new evidence.

This is a fundamental anti-hallucination invariant for embodied cognition.

---

# 16. Active perception

The World Model must expose uncertainty to attention and perception.

Example:

```text
World Model:
"Unknown sound detected behind Novi."
Confidence: low

        ↓

Attention raises priority
        ↓

Audio localization
        ↓

Novi orients
        ↓

Vision observes region
        ↓

World Model updates
```

This creates a closed loop between:

```text
WORLD MODEL
     ↕
ATTENTION
     ↕
PERCEPTION
```

Novi therefore does not merely consume perception; it can **actively decide what additional evidence it needs**.

---

# 17. Action grounding

Before an action is executed, the planner should query the World Model for:

- current pose;
- relevant entities;
- obstacles;
- hazards;
- affordances;
- expected consequences;
- uncertainty;
- freshness;
- environmental constraints.

After execution, the result must be fed back:

```text
ACTION
 ↓
EXECUTION
 ↓
OBSERVED RESULT
 ↓
WORLD MODEL UPDATE
 ↓
PREDICTION ERROR
 ↓
LEARNING / MEMORY / PLAN REVISION
```

This enables Novi to learn from the difference between expectation and reality.

---

# 18. Prediction error

Prediction error is a first-class signal.

Example:

```text
Prediction:
"Person will continue walking forward."

Observation:
"Person stopped and turned."

        ↓

Prediction error
        ↓

World Model correction
        ↓

Attention increase
        ↓

Potential plan revision
```

Prediction error may trigger:

- increased perception;
- model escalation;
- replanning;
- curiosity;
- memory admission;
- skill/model evaluation.

It must not automatically trigger learning from every anomaly.

---

# 19. Continuous world-state lifecycle

The World Model operates continuously while Novi is running.

```text
INGEST
  ↓
VALIDATE
  ↓
ASSOCIATE
  ↓
ESTIMATE
  ↓
UPDATE
  ↓
PREDICT
  ↓
EXPOSE TO COGNITION
  ↓
OBSERVE CONSEQUENCES
  ↓
CORRECT
  ↓
CONTINUE
```

There is no requirement for a user request to initiate a World Model update.

This supports Novi's always-alive behavior.

---

# 20. Update frequencies

Different state classes operate at different rates.

### High frequency

- robot pose;
- obstacle state;
- velocity;
- sensor health;
- local hazards.

### Medium frequency

- object tracks;
- people state;
- activity;
- room occupancy;
- interaction state.

### Low frequency

- semantic scene summaries;
- long-term environmental changes;
- relationship hypotheses;
- background predictions.

### Event-driven

- person arrival;
- speech;
- unexpected movement;
- collision risk;
- object disappearance;
- task completion/failure.

The orchestrator and model runtime must schedule these according to freshness and importance rather than forcing a single global loop rate.

---

# 21. Staleness

Every World Model state element must have freshness semantics.

A consumer must be able to determine:

```text
Is this state current enough for this decision?
```

For example:

- navigation may require sub-second spatial state;
- dialogue may tolerate slower room context;
- long-term reasoning may tolerate historical information.

Stale state must be marked explicitly and must not silently appear current.

---

# 22. Conflict handling

World Model conflicts must be explicit.

Sources may disagree because of:

- sensor noise;
- occlusion;
- calibration errors;
- timing errors;
- model errors;
- identity ambiguity;
- dynamic objects;
- communication delay.

Resolution strategies include:

1. source-quality weighting;
2. temporal alignment;
3. spatial alignment;
4. cross-modal corroboration;
5. uncertainty expansion;
6. additional sensing;
7. human confirmation where appropriate;
8. safe degradation.

The World Model must record unresolved conflicts when they matter.

---

# 23. Privacy

World-state representations involving people require privacy controls.

The architecture must distinguish:

- transient perception;
- identity hypotheses;
- interaction context;
- durable social memory;
- sensitive attributes.

Not every detected person becomes a persistent identity.

Not every conversation becomes durable memory.

Retention and access are governed by the privacy and memory architectures.

---

# 24. Security and integrity

World Model inputs are security-sensitive because corrupted state can produce unsafe behavior.

Threats include:

- spoofed sensors;
- replayed observations;
- corrupted timestamps;
- malicious environment signals;
- compromised perception components;
- unauthorized state injection;
- poisoned learned outputs.

Controls should include:

- source authentication where supported;
- integrity checks;
- timestamps;
- provenance;
- anomaly detection;
- access control;
- audit logs;
- bounded trust.

Safety-critical decisions must retain independent validation outside the World Model.

---

# 25. Storage architecture boundary

The World Model is a logical subsystem, not a mandated database technology.

Potential implementation layers may include:

- in-memory state store;
- time-series/event store;
- spatial store;
- graph store;
- object storage;
- vector retrieval;
- durable relational metadata.

The actual technology selection requires benchmark and ADR evidence.

No database technology is architecturally mandated by this document.

---

# 26. Model integration boundary

Foundation models may consume World Model context, but they must not directly mutate authoritative world state.

Correct:

```text
WORLD MODEL
   ↓
CONTEXT BUILDER
   ↓
MODEL
   ↓
STRUCTURED HYPOTHESIS / PREDICTION
   ↓
VALIDATION
   ↓
WORLD MODEL UPDATE
```

Incorrect:

```text
LLM
 ↓
write arbitrary world state
```

This protects the semantic integrity of the system.

---

# 27. NVIDIA technology mapping

NVIDIA technologies are candidates for specific World Model capabilities, not substitutes for the Novi abstraction.

| Capability | NVIDIA candidate | Role |
|---|---|---|
| visual/spatial perception | Isaac ROS | evidence generation |
| dense 3D reconstruction | nvblox | geometric world representation |
| simulation | Isaac Sim | synthetic evidence / validation |
| world prediction | Cosmos | learned future-state hypothesis |
| physical reasoning | Cosmos | multimodal reasoning candidate |
| action/world modeling | Cosmos 3 | research/learning candidate |
| robot policy | GR00T family | embodied policy candidate |
| inference | TensorRT / Triton | model execution |

NVIDIA describes Cosmos as a platform for physical-AI world foundation models and explicitly positions it for world reasoning, future generation, policy development and closed-loop simulation. citeturn0search0turn0search5

NVIDIA's Cosmos research also distinguishes world models from the broader physical-AI system and emphasizes a digital twin/world simulation approach for training and validation. citeturn0search5

Therefore Novi should treat Cosmos as a **learned predictive capability** that can augment the World Model, not as the sole authoritative state store.

---

# 28. Performance architecture

The World Model must not become a latency bottleneck for fast control.

Fast safety/control loops must operate independently.

```text
FAST CONTROL
   │
   ├── independent of LLM/WFM latency
   └── receives bounded state/constraints

WORLD MODEL
   │
   ├── continuous state estimation
   ├── semantic reasoning
   └── prediction

DELIBERATIVE COGNITION
   │
   └── consumes selected World Model context
```

World-model updates must support incremental/delta updates rather than requiring full-world reconstruction for every event.

---

# 29. Observability

Every important World Model update should be traceable to:

- source observation(s);
- source component;
- model version if learned;
- timestamp(s);
- frame(s);
- previous state;
- update operation;
- resulting state;
- confidence;
- provenance;
- validation status.

A debugger must be able to reconstruct:

> **Why did Novi believe this was happening?**

---

# 30. Replay

A recorded World Model session must be replayable for debugging and evaluation.

Replay must preserve:

- event ordering;
- timestamps;
- source identity;
- model versions;
- configuration;
- random seeds where relevant;
- world-state versions.

Replay should support deterministic reproduction where the underlying components permit it.

---

# 31. Failure modes

The World Model must explicitly handle:

- no perception;
- partial perception;
- contradictory sensors;
- localization loss;
- stale data;
- identity ambiguity;
- model timeout;
- model hallucination;
- storage failure;
- memory pressure;
- clock problems;
- corrupted state;
- unexpected world changes.

The correct response may be:

```text
DEGRADE
↓
INCREASE UNCERTAINTY
↓
REQUEST MORE EVIDENCE
↓
REPLAN
↓
ASK HUMAN
↓
SAFE STATE
```

rather than inventing certainty.

---

# 32. Human interaction

The World Model should represent interaction context, for example:

```text
person-017
  location: room-03
  orientation: facing Novi
  speech: active
  speech-source-match: high
  interaction-hypothesis: addressing Novi
  confidence: 0.91
```

This allows the cognitive layer to decide whether to:

- listen;
- respond;
- approach;
- wait;
- ask clarification;
- continue current task.

The World Model should provide evidence, not decide personality or social intent by itself.

---

# 33. Self/world boundary

Novi must maintain a clear distinction between:

```text
SELF
  ├── body
  ├── pose
  ├── sensors
  ├── actuators
  ├── current actions
  └── internal state

WORLD
  ├── people
  ├── objects
  ├── environment
  ├── other agents
  └── external events
```

The boundary must support relationships such as:

- "I am holding this object";
- "this person is approaching me";
- "I moved the object";
- "the object moved independently".

This is foundational for agency and self-modeling.

---

# 34. World Model acceptance criteria

The implementation is not considered compliant until it can demonstrate:

- [ ] continuous world-state updates;
- [ ] explicit timestamps;
- [ ] explicit coordinate frames;
- [ ] uncertainty;
- [ ] provenance;
- [ ] entity identity separate from recognition;
- [ ] temporal relationships;
- [ ] spatial relationships;
- [ ] event representation;
- [ ] activity hypotheses;
- [ ] affordances separate from permissions;
- [ ] prediction separate from current state;
- [ ] simulation separate from reality;
- [ ] contradiction handling;
- [ ] stale-state detection;
- [ ] active perception;
- [ ] action-result feedback;
- [ ] replay;
- [ ] observability;
- [ ] privacy controls;
- [ ] security controls;
- [ ] safe degraded operation.

---

# 35. Required validation program

Before physical autonomy, test the World Model in:

1. deterministic unit scenarios;
2. synthetic perception scenarios;
3. Isaac Sim scenarios;
4. sensor replay;
5. HIL;
6. controlled physical experiments;
7. long-duration runs.

Required scenarios include:

- person entering/exiting;
- object moved;
- object occluded;
- conflicting sensors;
- localization drift;
- sudden environmental change;
- speech + vision interaction;
- unexpected obstacle;
- action outcome mismatch;
- prediction error;
- model timeout;
- stale data;
- restart/recovery.

---

# 36. Key invariants

### WM-001 — No silent certainty

Uncertain evidence must remain uncertain until adequately resolved.

### WM-002 — No time travel

Future predictions cannot overwrite current state.

### WM-003 — No simulation leakage

Simulated state cannot silently become real state.

### WM-004 — No model authority

A foundation model cannot directly mutate authoritative World Model state.

### WM-005 — Provenance preservation

Every meaningful state update must be traceable.

### WM-006 — Freshness awareness

Consumers must be able to determine whether state is stale.

### WM-007 — Spatial correctness

Spatial state must identify its coordinate frame and timestamp.

### WM-008 — Action closure

Important actions must have observable outcomes fed back into the World Model.

### WM-009 — Self/world separation

Novi must distinguish its own body/state from external entities.

### WM-010 — Safety independence

Safety-critical control must remain independently enforceable.

---

# 37. Decision status

## Adopt now

- explicit world-state abstraction;
- spatial/temporal representation;
- entity/relationship/event model;
- uncertainty;
- provenance;
- prediction separation;
- simulation separation;
- active perception interface;
- action-result feedback;
- replayability.

## Candidate technology

- NVIDIA Isaac ROS;
- nvblox;
- Isaac Sim;
- Cosmos family;
- graph/spatial/time-series storage;
- learned trajectory/activity models.

## Requires benchmark/ADR

- exact world-model database;
- exact graph technology;
- exact vector store;
- exact WFM;
- exact learned prediction models;
- edge inference configuration;
- update rates and compute budgets.

---

# 38. Final architectural principle

> **Novi does not live in the world because a model describes the world. Novi lives in the world because it continuously maintains, questions, updates, predicts and acts against an embodied, time-aware, spatially grounded and uncertainty-aware model of reality.**

The World Model is therefore one of the central foundations of Novi's identity as a persistent autonomous agent.
