# 01 — Continuous Cognitive Loop

## Status

**DESIGN** — detailed runtime specification.

## Objective

Novi must behave as a continuously operating embodied system rather than a request/response application. The cognitive loop runs whenever the runtime is healthy, including periods where no person is speaking to Novi.

## Canonical Loop

```text
SENSE
  ↓
INGEST
  ↓
NORMALIZE
  ↓
CORRELATE
  ↓
INTERPRET
  ↓
UPDATE WORLD MODEL
  ↓
RETRIEVE CONTEXT
  ↓
ATTEND
  ↓
MAINTAIN GOALS
  ↓
DECIDE WHETHER TO ACT
  ↓
REASON / PLAN
  ↓
POLICY CHECK
  ↓
SAFETY CHECK
  ↓
EXECUTE
  ↓
OBSERVE OUTCOME
  ↓
STORE EXPERIENCE
  ↓
LEARN / UPDATE
  ↓
RETURN TO SENSE
```

The stages are logical rather than necessarily separate processes. Implementations may combine stages where latency or reliability benefits, but the contracts and observability boundaries must remain identifiable.

## Sensing

Inputs can include:

- RGB cameras
- depth cameras
- LiDAR
- microphones
- IMU
- wheel odometry
- battery telemetry
- thermal sensors
- touch/contact sensors
- screen interactions
- IoT state
- navigation state
- system diagnostics

Sensor adapters produce timestamped observations. They do not directly update high-level memory.

## Ingestion and Normalization

Each observation receives:

- unique observation ID
- source ID
- sensor/modality
- capture timestamp
- ingestion timestamp
- coordinate frame if spatial
- confidence where applicable
- payload reference
- privacy classification

The system normalizes different modalities into a common event representation while preserving modality-specific evidence.

## Correlation

The event correlator groups observations that may describe the same real-world occurrence.

Example:

```text
camera: person enters room
microphone: door opens
IMU: robot stationary
IoT: front door contact → open

             ↓

correlated event: PERSON_ENTERED_HOME
```

Correlation must support temporal windows, spatial constraints, identity confidence, duplicate suppression, and late-arriving observations.

## Interpretation

Interpretation produces semantic observations such as:

- `person.entered_room`
- `person.left_home`
- `door.opened`
- `object.moved`
- `speech.detected`
- `music.started`
- `possible_emotion.change`
- `unknown_object.detected`

Interpretations are not automatically facts. They carry evidence and confidence.

## World Update

The World Model receives validated observation updates and derives current state:

```text
Where is each known person?
Where is Novi?
What rooms are occupied?
Which doors are open?
What objects have changed location?
What activity is probably occurring?
What events are currently active?
```

World state is time-aware. A stale observation must not overwrite newer state without an explicit conflict-resolution rule.

## Context Retrieval

Before reasoning, the autonomy engine retrieves only relevant context from:

- current world state
- recent events
- episodic memory
- semantic knowledge
- relationship state
- active goals
- pending questions
- known routines
- relevant tool state

The complete database is never blindly injected into a model context.

## Attention

Attention evaluates whether an event warrants internal processing or external interaction. Attention must consider:

- urgency
- safety relevance
- novelty
- user relevance
- relationship
- confidence
- persistence
- emotional/social cues
- current conversation
- active goals
- whether Novi has already reacted
- interruption cost

## Decision

The autonomy engine chooses one of:

```text
IGNORE
OBSERVE
REMEMBER
UPDATE_STATE
ASK
RESPOND
SIGNAL
PLAN
ACT
DEFER
ESCALATE
```

A decision can be internal only. Most events should not result in speech.

## Planning

For non-trivial actions, the system creates a plan consisting of typed steps and expected outcomes.

Example:

```text
Goal: go to kitchen

1. determine current location
2. obtain map/localization confidence
3. request navigation route
4. execute navigation
5. monitor obstacles
6. verify arrival
7. mark goal complete
```

The planner must support cancellation and replanning when observations invalidate assumptions.

## Policy and Safety

All external actions pass through policy and safety checks. Examples:

- movement near a person
- opening/closing a connected device
- changing IoT state
- accessing protected information
- sending an external message
- manipulating physical objects

The safety layer may transform an action into a constrained version, require confirmation, or reject it.

## Execution

Actions are sent to capability services using typed requests. Execution returns:

- accepted/rejected
- execution ID
- start time
- completion state
- result data
- failure code
- safety intervention if any

The LLM does not receive direct motor commands or arbitrary shell execution privileges.

## Outcome Observation

Novi must verify outcomes rather than assuming success.

Example:

```text
request: turn kitchen light on
       ↓
IoT command accepted
       ↓
state observation: light=ON
       ↓
verified success
```

If the expected outcome does not occur, the system records the discrepancy and may retry, replan, ask the user, or abandon the goal according to policy.

## Learning

Experiences can create:

- episodic memories
- semantic knowledge candidates
- relationship updates
- routine hypotheses
- preferences
- curiosity questions
- model-evaluation data

Learning is asynchronous where possible so expensive processing does not block immediate safety or interaction loops.

## Scheduling Model

The implementation should support multiple cadence classes rather than one fixed loop frequency:

- **high-frequency:** safety, odometry, obstacle monitoring
- **real-time-ish:** perception/event detection
- **interactive:** conversation and active task planning
- **background:** memory consolidation, indexing, learning
- **maintenance:** diagnostics, cleanup, model health

A scheduler coordinates resource budgets and priorities.

## Failure Handling

If one component fails:

1. isolate the failed capability;
2. preserve safe operation;
3. degrade gracefully;
4. record the failure;
5. attempt recovery according to policy;
6. notify the user only when useful or required;
7. continue other independent functions.

Examples:

- camera unavailable → audio/social operation may continue;
- speech recognition unavailable → text/UI interaction may continue;
- VLM unavailable → basic detector may continue;
- network unavailable → local operation continues where possible;
- primary LLM unavailable → deterministic tools and safety remain operational.

## Loop Timing

The implementation must not assume that every stage completes in one synchronous tick. Long-running actions and model inference execute asynchronously. The world model can change while a plan is running.

Every state transition must therefore validate that its assumptions are still current before executing consequential actions.

## Deterministic Replay

Autonomy events should be persisted sufficiently to replay a scenario in simulation without retaining unnecessary private raw media. A replay should be able to reproduce:

- event ordering
- world-state transitions
- attention decisions
- goal changes
- tool requests
- policy outcomes
- action results

This is essential for debugging autonomous behavior.

## Acceptance Tests

A minimal continuous-loop test suite must demonstrate:

- autonomous operation with no user input;
- event ingestion from multiple modalities;
- event correlation;
- stale-event protection;
- attention/no-attention decisions;
- interruption of low-priority work by high-priority events;
- multi-step planning;
- action authorization;
- outcome verification;
- failure and recovery;
- memory/knowledge update;
- deterministic replay;
- graceful degradation when individual services disappear.
