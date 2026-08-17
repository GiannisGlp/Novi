# Novi Brain — Temporal Cognition

**Document:** 20_TEMPORAL_COGNITION.md  
**Status:** P0 Critical Architecture Specification  
**Authority:** `02-novi-brain`  
**Depends on:** 03 Brain State Model, 05 Cognitive Cycle, 09 Model Lifecycle, 10 Model Runtime, 16 Multimodal Fusion, 17 Spatial & Proprioceptive Fusion, 18 World Model, 19 Spatial Cognition  
**Purpose:** Define how Novi represents time, sequence, duration, continuity, change, anticipation, temporal causality and experience across short and long horizons.

---

## 1. Purpose

Temporal cognition gives Novi a persistent relationship with time.

Novi must not perceive the world as disconnected snapshots. It must understand:

- what is happening now;
- what just happened;
- what has been happening;
- what happened before;
- what changed;
- what is expected next;
- what is likely to happen later;
- how long an event has persisted;
- whether two events are related in time;
- whether an action caused an observed change.

```text
PAST
  ↓
CURRENT STATE
  ↓
EXPECTATION
  ↓
FUTURE
  ↓
OBSERVED OUTCOME
  ↓
LEARNED TEMPORAL MODEL
  └──────────────→ future expectations
```

This is foundational to Novi's continuous-existence requirement.

---

# 2. Core principle

> **Novi must experience the world as a continuous process, not as a sequence of unrelated frames.**

Temporal cognition must therefore connect perception, state, memory, action and prediction.

```text
observation(t-2)
      ↓
observation(t-1)
      ↓
observation(t)
      ↓
state estimate
      ↓
change / trend
      ↓
expectation(t+1)
      ↓
action
      ↓
observation(t+2)
```

---

# 3. Time domains

Novi must distinguish at least:

### 3.1 Monotonic runtime time

Used for:

- deadlines;
- durations;
- scheduling;
- latency;
- timeout handling.

It must not be used as a substitute for calendar time.

### 3.2 System/wall time

Used where real-world timestamps are required, such as:

- logs;
- external events;
- persisted records;
- human-facing timestamps.

### 3.3 Robotics/ROS time

ROS 2 systems may operate using a system clock or simulation time. The source and clock domain must be explicit.

NVIDIA's Isaac Sim documentation explicitly distinguishes simulation time from wall/system time and documents `/clock` plus `use_sim_time` for synchronization of ROS 2 nodes. citeturn0search3turn0search2

### 3.4 Event time

The time at which something actually occurred.

### 3.5 Observation time

The time at which Novi observed or received evidence about an event.

### 3.6 Processing time

The time at which a subsystem processed the evidence.

These must not be conflated.

```text
EVENT TIME
    ↓
OBSERVATION TIME
    ↓
PROCESSING TIME
    ↓
DECISION TIME
    ↓
ACTION TIME
```

---

# 4. Temporal provenance

Every significant temporal fact should preserve:

```text
source
clock_domain
event_time
observation_time
processing_time
confidence
latency
sequence_id
causal_context
```

This allows Novi to reason about stale information.

Example:

```text
camera frame captured at t=10.00
received at t=10.08
processed at t=10.15
```

The model must not behave as though the observation occurred at 10.15.

---

# 5. Temporal state

Novi's state model should distinguish:

- instantaneous state;
- short-lived state;
- persistent state;
- historical state;
- predicted state.

Example:

```text
person
 ├── current location
 ├── previous location
 ├── velocity estimate
 ├── current activity
 ├── activity history
 └── predicted trajectory
```

---

# 6. Temporal windows

Different cognitive processes operate at different temporal scales.

```text
microseconds–milliseconds
  control / synchronization

milliseconds–seconds
  perception / reaction

seconds–minutes
  interaction / navigation / task execution

minutes–hours
  episodic activity / task history

days–months
  long-term memory / habits / relationships
```

Exact windows must be determined from measured workload rather than arbitrary constants.

---

# 7. Event representation

An event should be represented as more than a timestamp.

Minimum conceptual representation:

```text
event_id
event_type
start_time
end_time
duration
participants
location
cause_hypothesis
observations
confidence
importance
consequences
related_events
provenance
```

Examples:

- person entered room;
- Novi heard speech;
- object fell;
- door opened;
- Novi started navigation;
- person interrupted Novi;
- obstacle appeared.

---

# 8. Duration

Novi should represent how long relevant conditions persist.

Examples:

- person has been waiting;
- door has remained open;
- obstacle has persisted;
- conversation has been active;
- task has been running;
- sensor has been unavailable.

Duration must be measured from explicit timestamps rather than inferred from processing cycles.

---

# 9. Temporal ordering

The system should support relationships such as:

- before;
- after;
- simultaneous/overlapping;
- during;
- starts;
- finishes;
- immediately before;
- recently after.

These relationships should carry uncertainty when timestamps are imprecise.

---

# 10. Temporal continuity

Novi should maintain continuity across sensor observations.

```text
frame 1 → person detected
frame 2 → person tracked
frame 3 → person moved
frame 4 → person speaking
frame 5 → person approached
```

These should form one evolving entity/event history where justified.

The system must avoid repeatedly treating the same persistent event as novel.

---

# 11. Change detection

Temporal cognition should detect meaningful changes:

```text
previous state
     ↓
new observation
     ↓
difference
     ↓
change hypothesis
     ↓
verification
     ↓
state transition
```

Examples:

- person entered;
- person stopped;
- person began speaking;
- object moved;
- door closed;
- route became blocked.

---

# 12. State transitions

Temporal cognition should model important state transitions explicitly.

Example:

```text
person:
UNKNOWN
  ↓ detected
PRESENT
  ↓ interaction begins
ENGAGED
  ↓ leaves
DEPARTING
  ↓ no longer observed
ABSENT
```

Transitions require evidence and should not be generated solely by elapsed time unless timeout semantics are explicitly defined.

---

# 13. Temporal attention

Temporal change can drive attention.

Novi should prioritize events based on:

- suddenness;
- persistence;
- acceleration;
- novelty;
- goal relevance;
- social relevance;
- threat;
- prediction error;
- expected future consequence.

This is a major component of continuous autonomous behavior.

Example:

```text
room is quiet
     ↓
unexpected sound
     ↓
rapid attention increase
     ↓
hearing + spatial localization
     ↓
visual inspection
```

---

# 14. Prediction

Novi should continuously generate predictions where they materially improve behavior.

Predictions may concern:

- object motion;
- human motion;
- speech turn completion;
- task completion;
- navigation state;
- environmental changes;
- likely next interaction;
- expected sensor observations.

Predictions must include:

```text
prediction
horizon
confidence
model
assumptions
generated_at
```

A prediction must never overwrite observed reality.

---

# 15. Prediction error

Prediction error is a first-class signal.

```text
prediction
   ↓
world evolves
   ↓
observation
   ↓
compare
   ↓
prediction error
   ↓
update beliefs / model / attention
```

Large unexpected changes can trigger:

- attention escalation;
- replanning;
- additional perception;
- safety behavior;
- learning data capture.

---

# 16. Anticipation

Novi should use temporal knowledge proactively.

Example:

```text
person approaches doorway
       ↓
trajectory suggests crossing Novi's path
       ↓
anticipated interaction
       ↓
slow / yield / reposition
```

Anticipation is preferable to waiting for a collision or explicit instruction.

---

# 17. Causality

Temporal order alone does not prove causality.

```text
A happened before B
        ≠
A caused B
```

Novi may maintain:

- causal hypotheses;
- confidence;
- supporting observations;
- competing explanations.

Example:

```text
Novi moved
  ↓
object moved
```

This does not automatically establish that Novi's movement caused the object movement.

---

# 18. Action–outcome attribution

When Novi acts, temporal cognition should correlate the action with subsequent observations.

```text
ACTION
  ↓
expected outcome
  ↓
observation window
  ↓
actual outcome
  ↓
comparison
  ↓
causal/effect hypothesis
```

This enables learning from experience.

---

# 19. Interruptions

An interruption must be represented temporally rather than simply deleting the current task.

```text
Task A
  ↓
interrupted by Event B
  ↓
handle B
  ↓
resume / revise / abandon A
```

The system must retain:

- task progress;
- interruption cause;
- elapsed time;
- changed world state;
- whether the previous plan is still valid.

---

# 20. Waiting

Waiting is an intentional temporal state.

Novi may wait because:

- an event is expected;
- a person is speaking;
- a route is blocked temporarily;
- more evidence is required;
- a timer is active;
- a task has a temporal dependency.

```text
WAIT
 ↓
monitor relevant evidence
 ↓
condition changes
 ↓
resume / react
```

Waiting must not disable relevant perception or safety monitoring.

---

# 21. Temporal memory

Temporal cognition provides the timeline foundation for memory.

Memory should distinguish:

- event time;
- sequence;
- duration;
- context;
- recurrence;
- importance.

This allows Novi to remember:

> "We spoke earlier."

rather than merely storing:

> "Speech occurred."

---

# 22. Episodic sequence

Episodes should be represented as connected sequences.

Example:

```text
person arrived
  ↓
greeted Novi
  ↓
asked a question
  ↓
Novi answered
  ↓
person left
```

This enables later reasoning over the experience as a coherent episode.

---

# 23. Recurrence and habits

Repeated temporal patterns may become candidates for learned routines.

Examples:

- repeated charging behavior;
- recurring interaction times;
- repeated room transitions;
- recurring environmental events.

A repeated pattern must not automatically become an autonomous behavior. It must pass the goal, safety and governance layers.

---

# 24. Temporal language grounding

Novi should resolve temporal expressions when sufficient context exists:

- now;
- just now;
- earlier;
- later;
- yesterday;
- tomorrow;
- recently;
- for five minutes;
- before we entered this room.

Language should query temporal state rather than invent history.

---

# 25. Multi-rate cognition

Temporal cognition must integrate systems operating at different frequencies.

```text
fast
 ├── control
 ├── collision reaction
 ├── perception
 └── tracking

medium
 ├── attention
 ├── interaction
 ├── navigation
 └── task reasoning

slow
 ├── memory consolidation
 ├── model adaptation
 ├── learning
 └── long-horizon planning
```

The orchestrator must prevent slow cognition from blocking fast safety and perception loops.

---

# 26. Temporal freshness

Every world-model fact should have a freshness concept.

Example:

```text
fresh
recent
stale
expired
unknown
```

A stale observation must not silently be treated as current.

Freshness thresholds should be capability-specific.

A map may remain useful for minutes or hours; a person's current pose may become stale within fractions of a second.

---

# 27. Time uncertainty

Timestamps themselves can be uncertain due to:

- sensor clock drift;
- network latency;
- processing queues;
- synchronization error;
- simulation timing;
- dropped frames.

Temporal reasoning must preserve these uncertainties where they affect decisions.

---

# 28. Simulation time

Simulation must reproduce temporal behavior accurately enough for meaningful validation.

NVIDIA Isaac Sim documents `/clock` and `use_sim_time` for synchronizing ROS 2 nodes with simulation time and explicitly distinguishes simulation time from wall time. citeturn0search2turn0search3

Novi simulation tests must therefore record:

- simulation clock;
- wall clock;
- real-time factor;
- sensor timestamps;
- ROS timestamps;
- replay sequence.

---

# 29. World-model temporal representation

The World Model should support:

```text
CURRENT
 ├── current entities
 ├── current relationships
 └── current environment

HISTORY
 ├── previous states
 ├── events
 ├── episodes
 └── changes

PREDICTION
 ├── expected states
 ├── trajectories
 └── future events
```

Current state, history and prediction must remain distinguishable.

---

# 30. Learned temporal models

Potential learned components include:

- trajectory prediction;
- action prediction;
- temporal activity recognition;
- speech-turn prediction;
- world-state prediction;
- video prediction;
- temporal anomaly detection;
- learned dynamics.

NVIDIA Cosmos 3 is directly relevant as a candidate world foundation model: NVIDIA describes it as combining physical reasoning, world generation and action prediction, including understanding motion and spatial-temporal relationships and predicting future world states. citeturn0search0turn0search1

However, Cosmos remains a **candidate model capability**, not the authoritative temporal state of Novi.

---

# 31. Deterministic temporal mechanisms

Deterministic mechanisms should own:

- deadlines;
- timers;
- scheduling;
- timeouts;
- timestamp validation;
- freshness rules;
- event ordering contracts;
- clock synchronization;
- safety timing;
- replay sequence identity.

Learned models should not be responsible for hard timing guarantees.

---

# 32. Temporal cognition and the feeling of being alive

Temporal cognition is essential to Novi's behavioral continuity.

Without it:

```text
see person
→ react
→ forget
→ see person again
→ react again
```

With it:

```text
see person
→ recognize continuity
→ remember previous interaction
→ monitor what changed
→ anticipate next action
→ respond differently based on context
```

This is not a claim of consciousness.

It is a requirement for persistent embodied behavior.

---

# 33. Failure modes

Required failure handling includes:

- clock jumps;
- clock source disagreement;
- stale data;
- out-of-order messages;
- duplicate events;
- missing timestamps;
- sensor latency spikes;
- simulation time mismatch;
- incorrect event ordering;
- prediction divergence;
- temporal-memory corruption;
- action/outcome attribution errors.

Critical timing failures must fail conservatively.

---

# 34. Safety boundary

Temporal cognition must not directly control actuators.

```text
Temporal belief / prediction
        ↓
Behavior / planning
        ↓
Safety / governance
        ↓
Navigation / controller
        ↓
Actuation
```

Fast safety mechanisms must remain independent of slow predictive cognition.

---

# 35. Data contract

A canonical temporal record should include at least:

```text
event_id
sequence_id
clock_domain
event_time
observation_time
processing_time
decision_time
action_time
start_time
end_time
duration
source
confidence
latency
freshness
causal_context
prediction_context
provenance
```

Exact executable schemas belong in the canonical contract layer.

---

# 36. Validation strategy

### Unit

- timestamp arithmetic;
- ordering;
- duration;
- freshness;
- clock conversion;
- timeout behavior.

### Simulation

- deterministic replay;
- clock acceleration;
- clock pause/resume;
- dropped messages;
- delayed messages;
- out-of-order events;
- moving people;
- prediction evaluation.

### HIL

- real sensor timing;
- processing latency;
- network delay;
- controller deadlines;
- synchronization.

### Physical

- long-duration operation;
- human interruptions;
- task resumption;
- changing environments;
- temporal prediction;
- memory continuity.

---

# 37. Required tests

At minimum:

- `TEMPORAL-001` clock-domain consistency;
- `TEMPORAL-002` event-time preservation;
- `TEMPORAL-003` out-of-order event handling;
- `TEMPORAL-004` duplicate-event handling;
- `TEMPORAL-005` freshness enforcement;
- `TEMPORAL-006` duration accuracy;
- `TEMPORAL-007` interruption/resumption;
- `TEMPORAL-008` temporal continuity;
- `TEMPORAL-009` prediction error calculation;
- `TEMPORAL-010` action/outcome attribution;
- `TEMPORAL-011` simulation-time synchronization;
- `TEMPORAL-012` long-duration clock stability;
- `TEMPORAL-013` temporal memory reconstruction;
- `TEMPORAL-014` prediction-vs-observation separation;
- `TEMPORAL-015` degraded timing recovery.

---

# 38. Open ADRs

The following require explicit decisions:

- canonical clock authority;
- timestamp precision;
- temporal-event store;
- event-sourcing strategy;
- retention periods;
- temporal indexing;
- prediction representation;
- causal-graph representation;
- replay format;
- cross-process clock synchronization;
- simulation-time policy;
- long-horizon temporal memory strategy.

---

# 39. Definition of done

Temporal cognition is architecturally complete when Novi has documented and validated:

- clock domains;
- event-time semantics;
- temporal provenance;
- temporal state;
- event representation;
- duration;
- ordering;
- continuity;
- change detection;
- prediction;
- prediction error;
- anticipation;
- causality hypotheses;
- action/outcome attribution;
- interruptions;
- waiting;
- temporal memory;
- recurrence;
- temporal language grounding;
- freshness;
- uncertainty;
- simulation time;
- failure handling;
- safety boundaries;
- executable contracts;
- benchmarks and acceptance criteria.

---

# 40. Core principle

> **Novi must not only know where it is and what is around it. Novi must know what is happening across time.**

The complete embodied loop is:

```text
PERCEIVE
   ↓
UNDERSTAND CURRENT STATE
   ↓
REMEMBER WHAT CAME BEFORE
   ↓
PREDICT WHAT COMES NEXT
   ↓
DECIDE
   ↓
ACT
   ↓
OBSERVE CONSEQUENCE
   ↓
COMPARE EXPECTATION WITH REALITY
   ↓
UPDATE WORLD + MEMORY + MODELS
   ↓
CONTINUE
```

That temporal continuity is a foundational requirement for Novi to remain responsive, context-aware, adaptive and continuously embodied rather than behaving like a collection of disconnected inference calls.
