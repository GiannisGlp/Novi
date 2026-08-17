# 03 — Novi Brain State Model

**Status:** P0 — critical

Novi's state is layered, not one object or database row.

```text
IMMEDIATE STATE + PERSISTENT STATE + EXTERNAL/PHYSICAL STATE
                         ↓
                 WORLD MODEL
                         ↓
                COGNITIVE STATE
```

## State classes

### Physical

Pose, velocity, actuator state, battery, temperature, sensor health, compute health, connectivity and safety. Physical state must come from telemetry.

### Perceptual

People, objects, speech activity, sound sources, tracked entities, scene geometry and events, with source/timestamp/confidence.

### World

Current structured estimate of entities, locations, relationships, occupancy, activities, environmental conditions and uncertainty.

### Cognitive

Attention target, context, hypotheses, uncertainty, active reasoning, plan and pending decision.

### Goals

Identity, source, priority, constraints, deadline, dependencies, status, progress, confidence, interruption and cancellation policy. Sources include human requests, persistent preferences, system requirements, safety requirements and bounded curiosity/maintenance.

### Interaction

Who is interacting, listening/turn state, topic, social context, expected response and interruption state.

### Self

Capabilities, unavailable capabilities, active skills, limitations, workload, location, task, recent outcomes and uncertainty about itself.

### Affective/expressive

Engineered variables such as engagement, receptivity, confidence, curiosity, urgency and resource pressure. These are control variables, not claims of human subjective emotion.

### Action

`IDLE`, `OBSERVING`, `LISTENING`, `THINKING`, `PLANNING`, `EXECUTING`, `WAITING`, `INTERRUPTED`, `RECOVERING`, `DEGRADED`, `SAFE_STOP`, `SHUTDOWN`.

## Temporal model

Different layers operate at different rates: control/sensors in milliseconds, reactive perception in tens/hundreds of milliseconds, interaction in seconds, deliberation in seconds/minutes, and learning/consolidation over minutes to months.

## State transitions

```text
Evidence / command / timer / outcome
            ↓
       validated transition
            ↓
         new state
            ↓
          event
```

Models may propose changes but cannot silently mutate authoritative state.

## Observation versus belief

```text
observation ≠ interpretation ≠ belief ≠ prediction ≠ simulation ≠ counterfactual
```

Identity, object and world-state estimates must preserve uncertainty and provenance.

## Persistence

Safety state is independent/high priority; active goals and important actions are durable; world state is snapshot/event based; memory is durable; inference context is ephemeral unless explicitly promoted.

## Restart/recovery

Support cold start, process restart, model restart, ROS restart, sensor restart, partial failure and full recovery. Durable identity/goals/memories/recovery state are restored according to policy; ephemeral context is not fabricated.

## Interruptions

An interrupted task retains its state and reason. Safety interrupts bypass ordinary cognition.

## Failure states

Explicitly represent missing/stale/contradictory evidence, invalid model output, unavailable memory, planner/skill failure, sensor failure, resource exhaustion and safety rejection.

## State ownership

Each state field has one authoritative owner: hardware owns telemetry; perception owns tracks; world model owns beliefs; memory owns records; goals own goal lifecycle; planner owns plans; governance owns authorization; personality owns personality configuration; model runtime owns model availability; orchestrator owns scheduling.

## Consistency

Classify state as `SAFETY_CRITICAL`, `STRONG`, `EVENTUAL`, `DERIVED` or `EPHEMERAL`. Safety state cannot depend on eventually consistent cognitive storage.

## Replay

Important transitions must record event ID, timestamp, source, state versions, model/runtime identity, context, configuration and outcome so cognitive decisions can be reconstructed as far as practical.

## Alive behavior

The state model must support continuous awareness, task continuity, bounded initiative, meaningful curiosity, interaction, memory continuity, recovery and intentional idle behavior. Random activity is not required.