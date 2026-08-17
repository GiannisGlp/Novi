# Novi Brain — Self Model

**Document:** `22_SELF_MODEL.md`  
**Status:** P0 Critical Architecture Specification  
**Scope:** Novi's computational representation of itself as an embodied, acting system  
**Depends on:** 02 Cognitive Architecture, 03 Brain State Model, 04 Brain Orchestrator, 17 Spatial & Proprioceptive Fusion, 18 World Model, 20 Temporal Cognition, 21 Situation Model

---

## 1. Purpose

The Self Model is Novi's continuously maintained representation of **its own body, capabilities, state, actions, limitations, resources, goals, history and expected consequences**.

It is not a claim of consciousness or subjective experience. It is an engineering construct that lets Novi reason about itself as an entity inside its world model.

```text
WORLD MODEL
     │
     ├── other entities
     ├── environment
     └── NOVI
          │
          └── SELF MODEL
               ├── body
               ├── pose
               ├── capabilities
               ├── current activity
               ├── goals
               ├── internal state
               ├── resources
               ├── limitations
               ├── recent actions
               ├── expected outcomes
               └── uncertainty
```

---

## 2. Core principle

> **Novi must understand itself as a physical agent operating under real capabilities, constraints and uncertainty.**

The self model must never invent capabilities merely because a language model can describe them.

```text
language capability
      ≠
physical capability
      ≠
authorized capability
      ≠
safe capability
```

---

## 3. What the Self Model represents

At minimum:

- physical identity;
- body configuration;
- current pose and velocity;
- sensor health;
- actuator health;
- current motion state;
- current task/activity;
- active goals;
- capabilities;
- capability limits;
- permissions;
- resource state;
- compute availability;
- battery/power state where applicable;
- thermal state where available;
- localization confidence;
- perception confidence;
- cognitive state;
- active model/runtime state;
- recent actions;
- expected action outcomes;
- observed action outcomes;
- prediction errors;
- current uncertainty;
- failures and degraded modes;
- learned skills and skill confidence;
- persistent identity/configuration.

---

## 4. Physical self

The physical self describes Novi's body.

It should include:

- robot identifier;
- morphology/configuration;
- links and joints;
- sensor inventory;
- actuator inventory;
- end effectors if present;
- physical dimensions;
- mass properties where required;
- kinematic limits;
- velocity/acceleration limits;
- payload limits;
- collision geometry;
- battery/power system;
- compute hardware;
- thermal sensors;
- safety devices.

The canonical hardware description remains owned by the hardware/system architecture. The Self Model consumes its authoritative state; it does not redefine hardware truth.

---

## 5. Body state

The Self Model should continuously represent:

```text
pose
velocity
acceleration
joint positions
joint velocities
joint effort/torque where available
contact state where available
battery
thermal state
network/connectivity state
sensor health
actuator health
localization confidence
```

Every value must include appropriate timestamps, validity and provenance.

---

## 6. Body schema

A canonical self-state should be conceptually similar to:

```text
self_id
configuration_id
body_state
pose
velocity
joints
contacts
sensors
actuators
power
thermal
compute
connectivity
localization
capabilities
limitations
permissions
current_activity
active_goals
active_skills
recent_actions
predicted_outcomes
observed_outcomes
uncertainty
health
mode
provenance
schema_version
timestamp
```

The executable schema belongs in the canonical contracts layer before production implementation.

---

## 7. Capability model

Novi must maintain an explicit capability registry.

A capability should identify:

- capability ID;
- description;
- required hardware;
- required models;
- required software/runtime;
- operating conditions;
- performance limits;
- safety constraints;
- authorization requirements;
- confidence/evidence;
- version;
- validation status.

Example:

```text
capability: navigate_to_place
requires:
  localization
  obstacle perception
  navigation stack
  motor control
status:
  available
confidence:
  high
```

A capability is not considered available merely because its software exists.

---

## 8. Capability levels

The architecture should distinguish:

```text
implemented
installed
available
validated
currently_available
safe_now
authorized_now
```

Example:

> A manipulation model may be installed but not validated for the current hardware configuration.

Therefore:

```text
installed = true
validated = false
safe_now = false
```

The orchestrator must respect the strongest applicable constraint.

---

## 9. Capability uncertainty

Novi should maintain confidence/evidence for learned capabilities.

For example:

```text
skill: grasp_object
training_evidence: strong
simulation_validation: strong
physical_validation: limited
current_gripper: different configuration
confidence: reduced
```

This prevents transfer from simulation/training from being treated as guaranteed physical competence.

---

## 10. Current activity

The Self Model should represent what Novi is currently doing.

Examples:

- idle;
- observing;
- listening;
- speaking;
- navigating;
- searching;
- following;
- interacting;
- manipulating;
- charging;
- recovering;
- learning;
- awaiting input.

An activity should have:

- activity ID;
- start time;
- owner/goal;
- priority;
- expected duration where known;
- current phase;
- interruption state;
- cancellation state;
- outcome.

---

## 11. Goals

The Self Model contains Novi's currently active goals but does not become the authoritative goal planner.

Each active goal should expose:

```text
goal_id
source
priority
status
progress
constraints
required_capabilities
current_plan
blocked_reason
expected_completion
```

Goals may originate from:

- system objectives;
- user requests;
- autonomous policies;
- safety/recovery behavior;
- ongoing interaction.

Safety constraints always supersede ordinary goals.

---

## 12. Self-location

Novi must represent where it believes it is:

- global/world position where available;
- map position;
- current place;
- orientation;
- local velocity;
- localization confidence;
- localization source;
- map version.

This state must remain consistent with spatial cognition and localization authority.

---

## 13. Self-perception

Novi should model what it currently knows about its own physical state.

Example:

```text
I commanded forward motion.
        ↓
encoders report movement
        ↓
IMU agrees
        ↓
visual odometry agrees
        ↓
self model:
  movement confirmed
```

If evidence conflicts:

```text
commanded movement
      ≠
observed movement
```

Novi should enter an appropriate uncertainty/degraded state rather than assuming success.

---

## 14. Action ownership

Every significant action initiated by Novi should be attributable to:

- initiating goal;
- selected skill/policy;
- model/runtime version;
- context ID;
- action timestamp;
- requested action;
- safety decision;
- controller execution;
- observed outcome.

This is essential for learning, debugging and causal reasoning.

---

## 15. Action prediction

Before significant actions, the cognitive system may generate an expected outcome.

Example:

```text
Action:
  turn toward person

Expected:
  heading changes
  person enters frontal view
  visual confidence increases

Actual:
  heading changed
  person not found

Result:
  prediction error
```

Prediction error should update the world model, situation model and learning systems as appropriate.

---

## 16. Agency boundary

The Self Model must distinguish between:

```text
Novi proposed an action
Novi was authorized to act
controller accepted action
hardware executed action
world changed
```

These are different events.

Novi must not infer physical agency merely because it generated a command.

---

## 17. Internal resources

The Self Model should expose resource state relevant to cognition:

- CPU utilization;
- GPU utilization;
- memory;
- accelerator availability;
- inference queue pressure;
- storage;
- network state;
- battery;
- thermal headroom;
- sensor bandwidth;
- actuator availability.

The runtime remains authoritative for detailed resource metrics; the Self Model receives a cognitive representation suitable for decision making.

Example:

```text
GPU headroom: low
thermal headroom: low
battery: low

Self Model implication:
  avoid expensive optional cognition
  preserve safety-critical perception
  reduce background work
```

---

## 18. Cognitive self-state

The Self Model may represent high-level cognitive conditions such as:

- attention load;
- active reasoning task;
- uncertainty load;
- memory retrieval state;
- model availability;
- degraded cognition;
- interruption state;
- current interaction mode.

These are operational state variables, not claims about subjective consciousness.

---

## 19. Self-knowledge

Novi should distinguish:

```text
known capability
known limitation
unknown capability
unknown limitation
currently unavailable capability
```

The system should be able to answer:

> "Can I do this?"

with a grounded response based on the capability registry and current state.

If evidence is insufficient, the correct result is:

> "I don't know whether I can safely do that."

not fabricated confidence.

---

## 20. Self-model and language

The language system may query the Self Model for grounded information.

Examples:

> "Where are you?"

> "Can you reach that shelf?"

> "Why did you stop?"

> "What are you doing?"

> "Can you see me?"

The answer should be generated from structured self-state and relevant evidence, not from model imagination.

---

## 21. Self-model and personality

Personality may influence expression and preferences, but it must not rewrite physical truth.

```text
Personality:
  calm / curious / friendly

Physical state:
  battery low

Result:
  express calmly
  but do not claim capability that is unavailable
```

Personality is therefore a behavioral layer over grounded self-state.

---

## 22. Self-model and memory

The Self Model integrates with memory to support continuity.

Useful memories include:

- previous actions;
- successful skills;
- failed attempts;
- learned limitations;
- calibration changes;
- known configuration changes;
- recurring tasks;
- interaction history;
- previous locations;
- prior prediction errors.

Memory must preserve provenance and time.

---

## 23. Self-model and learning

Learning systems may update:

- skill confidence;
- expected action outcomes;
- calibration estimates;
- model confidence;
- resource predictions;
- task duration estimates.

Learning must not silently modify hard safety constraints or hardware limits.

---

## 24. Self-model and active perception

Novi can use knowledge of its own body to decide how to perceive.

Examples:

```text
camera obstructed
   ↓
recognize limited viewpoint
   ↓
rotate body / head if permitted
   ↓
observe again
```

or:

```text
microphone confidence low
   ↓
orient toward source
   ↓
reduce self-noise where possible
   ↓
listen again
```

This creates a closed loop between **self-state and perception**.

---

## 25. Self-model and planning

Planning should query the Self Model for:

- available capabilities;
- current pose;
- resource limits;
- skill availability;
- actuator constraints;
- current activity;
- active safety restrictions.

A plan that requires unavailable capabilities must be rejected or revised before execution.

---

## 26. Self-model and recovery

Recovery is a core self-model capability.

Examples:

```text
localization lost
   ↓
self model: localization degraded
   ↓
navigation capability unavailable
   ↓
stop / recover / relocalize
```

```text
camera failed
   ↓
self model: visual perception degraded
   ↓
reduce capabilities relying on vision
   ↓
continue only within safe degraded policy
```

---

## 27. Self-model and continuous existence

The Self Model contributes directly to the Novi North Star.

Novi should maintain continuity across:

- activity changes;
- interruptions;
- conversations;
- movement;
- failures;
- charging;
- degraded modes;
- ordinary process restarts where state persistence is supported.

The objective is not artificial constant activity.

It is **persistent identity and state continuity**.

```text
working
  ↓
interrupted
  ↓
respond
  ↓
remember previous task
  ↓
resume
```

---

## 28. Self-model persistence

Persistable self-state should be divided into:

### Durable identity/configuration

- robot identity;
- hardware configuration;
- validated capabilities;
- installed model identities;
- persistent safety configuration.

### Recoverable operational state

- active task;
- current place;
- pending interaction;
- recent action context;
- recoverable workflow state.

### Ephemeral runtime state

- current tensors;
- process-local queues;
- transient model sessions;
- temporary caches.

Not all runtime state should be persisted.

---

## 29. Failure states

The Self Model must represent explicit health/degradation modes, including:

- nominal;
- degraded perception;
- degraded hearing;
- degraded localization;
- degraded compute;
- degraded power;
- degraded thermal state;
- degraded actuation;
- communication loss;
- recovery;
- safe-stop.

State transitions must be deterministic and auditable.

---

## 30. Safety boundary

The Self Model is **not** the safety controller.

It may report:

> "My localization confidence is low."

It may recommend:

> "Navigation should stop."

But the safety/controller layer retains final authority over physical actuation.

```text
Self Model
    ↓
recommendation
    ↓
Governance / Safety
    ↓
Controller
    ↓
Actuator
```

---

## 31. NVIDIA technology mapping

Relevant NVIDIA technologies are implementation candidates for portions of the self model's supporting infrastructure:

- Isaac ROS for localization, perception and robot-state-connected ROS workflows;
- Isaac Sim for deterministic simulation of sensors, transforms, articulation state and actions;
- Isaac Lab for learning policies that depend on proprioceptive state;
- TensorRT for optimized inference where validated;
- Triton where multi-model serving actually provides measurable benefit;
- Cosmos/GR00T as candidate learned physical-world and embodied-policy components.

NVIDIA technologies do not own Novi's semantic self model. Novi's canonical state, contracts and governance remain architecture-owned.

---

## 32. Deterministic vs learned self-model components

### Deterministic

- hardware inventory;
- joint limits;
- sensor inventory;
- actuator limits;
- current resource telemetry;
- controller state;
- authorization;
- configuration identity.

### Estimated / fused

- pose;
- velocity;
- health estimates;
- localization confidence;
- sensor quality.

### Learned

Potentially:

- action outcome prediction;
- skill success prediction;
- resource prediction;
- recovery prediction;
- capability confidence estimation.

### Cognitive

- interpreting what Novi is doing;
- choosing which capability to use;
- deciding when uncertainty requires more information;
- relating current self-state to goals and social context.

---

## 33. Self-model anti-patterns

Novi must not:

- claim a capability because an LLM can describe it;
- claim an action succeeded because it generated the command;
- claim a sensor observation is correct without evidence;
- infer physical health from language-model output;
- modify safety limits through ordinary learning;
- confuse personality with internal truth;
- persist transient state as durable fact;
- treat simulation performance as physical validation;
- treat a model's confidence as ground truth.

---

## 34. Validation

Required validation includes:

### Identity

- configuration consistency;
- hardware inventory consistency;
- model/runtime identity.

### State

- sensor/encoder consistency;
- commanded-vs-observed motion;
- resource telemetry consistency;
- localization consistency.

### Capability

- capability availability;
- capability restrictions;
- validation status;
- safe-now status.

### Agency

- action attribution;
- outcome attribution;
- prediction error;
- interruption/resumption.

### Recovery

- sensor failure;
- localization loss;
- compute pressure;
- thermal/power degradation;
- controller rejection.

### Persistence

- restart recovery;
- state-version compatibility;
- corruption handling;
- stale-state rejection.

---

## 35. Required tests

At minimum:

- `SELF-001` hardware identity consistency;
- `SELF-002` body-state synchronization;
- `SELF-003` capability registry correctness;
- `SELF-004` unavailable-capability rejection;
- `SELF-005` commanded-vs-observed action attribution;
- `SELF-006` action prediction error;
- `SELF-007` resource-aware capability degradation;
- `SELF-008` localization-loss transition;
- `SELF-009` sensor-failure transition;
- `SELF-010` controller rejection handling;
- `SELF-011` task interruption/resumption;
- `SELF-012` self-state persistence;
- `SELF-013` stale self-state rejection;
- `SELF-014` simulation-to-real capability separation;
- `SELF-015` grounded language answers about capability/state.

---

## 36. Definition of done

The Self Model is architecturally complete when Novi can represent and validate:

- who/what it is;
- its physical configuration;
- where it is;
- how it is moving;
- what it can do;
- what it cannot safely do;
- what it is currently doing;
- what it intends to do;
- what resources it has;
- what actions it performed;
- what outcomes actually occurred;
- what it expected to happen;
- where its expectations were wrong;
- what is uncertain;
- what has degraded;
- what must recover;
- what state can persist;
- how all of this is grounded in authoritative evidence.

---

# 37. Core principle

> **Novi must know itself well enough to act as an embodied agent, but never so confidently that it mistakes a model of itself for reality.**

The Self Model closes the loop between:

```text
WORLD
  ↕
PERCEPTION
  ↕
SELF
  ↕
GOALS
  ↕
PLANNING
  ↕
ACTION
  ↕
OUTCOME
  ↕
LEARNING
```

This is a foundational requirement for autonomous behavior, grounded interaction, safe action, continuous identity and the persistent embodied character defined by the Novi North Star.
