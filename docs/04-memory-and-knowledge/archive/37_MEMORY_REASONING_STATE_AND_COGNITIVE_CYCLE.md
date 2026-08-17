# 37 — Memory Reasoning State and Cognitive Cycle

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define Novi's bounded, continuously running cognitive cycle: how current state, observations, goals, memories, predictions and uncertainty are transformed into reasoning proposals, decisions, actions and learning outcomes.

This document defines the orchestration model, not a claim that a single language model performs all cognition.

## Core Principle

> **Novi must operate as a closed perception–reasoning–action–learning loop in which every important action is grounded in current state, constrained by policy and safety, and followed by observation of the outcome.**

---

## 1. Cognitive Cycle

The canonical cycle is:

```text
OBSERVE
   ↓
UPDATE STATE
   ↓
ATTEND
   ↓
RETRIEVE
   ↓
ASSEMBLE WORKSPACE
   ↓
REASON
   ↓
PREDICT
   ↓
SELECT / PROPOSE
   ↓
VALIDATE
   ↓
ACT / WAIT
   ↓
OBSERVE OUTCOME
   ↓
EVALUATE
   ↓
LEARN / UPDATE MEMORY
   ↓
NEXT CYCLE
```

Not every cycle needs every stage at full depth.

---

## 2. Multiple Cognitive Timescales

Novi should not run one monolithic loop.

```text
fast control / safety       milliseconds
perception                   tens–hundreds ms
reactive cognition           sub-second–seconds
planning                     seconds
reflection                   seconds–minutes
consolidation                minutes–hours
long-term learning           hours–days
```

Fast loops must not wait for slow language-model reasoning.

---

## 3. Safety Loop Independence

Safety-critical control must remain independently executable.

```text
Safety / hardware control
        │
        ├── can interrupt cognition
        └── can stop action

Cognition
        │
        └── proposes behavior
```

A stalled model must never prevent an emergency stop.

---

## 4. Cognitive State

The cognitive runtime should maintain explicit state including:

- current mode;
- active goals;
- active intentions;
- current context;
- current workspace;
- pending actions;
- predictions;
- uncertainty;
- recent outcomes;
- interrupts;
- resource state;
- safety state;
- localization state;
- relevant memory references.

This is runtime state, not all durable memory.

---

## 5. State Machine

A conceptual cognitive state machine is:

```text
IDLE
  ↓
OBSERVING
  ↓
ORIENTING
  ↓
RETRIEVING
  ↓
REASONING
  ↓
VALIDATING
  ↓
ACTING
  ↓
VERIFYING
  ↓
REFLECTING
  ↓
IDLE / OBSERVING
```

Interruptions can move the system to a higher-priority state.

---

## 6. IDLE

Idle does not mean inactive.

Novi may continue:

- lightweight perception;
- wake-word/voice detection where configured;
- safety monitoring;
- battery monitoring;
- thermal monitoring;
- localization;
- low-cost environmental awareness;
- scheduled maintenance;
- background learning within resource budget.

---

## 7. OBSERVING

The observation stage gathers current evidence.

Sources can include:

- cameras;
- LiDAR;
- GNSS;
- IMU;
- thermal sensors;
- microphones;
- battery/BMS;
- system telemetry;
- current map;
- network state;
- user input.

Raw streams are processed through specialized perception systems before semantic cognition receives them.

---

## 8. UPDATE STATE

Current authoritative state is refreshed before consequential decisions.

Examples:

```text
battery
thermal state
pose
sensor health
security state
current obstacles
active goals
resource pressure
```

Historical memory cannot override authoritative current state.

---

## 9. ATTENTION

The attention system selects what deserves deeper processing.

Factors may include:

- safety;
- urgency;
- goal relevance;
- novelty;
- prediction error;
- uncertainty;
- information gain;
- emotional/social relevance where explicitly modeled;
- spatial relevance;
- temporal relevance;
- resource cost.

Attention is a processing decision, not a truth score.

---

## 10. RETRIEVAL

Memory retrieval should be task-directed.

The system may retrieve:

- episodic memories;
- semantic knowledge;
- spatial memories;
- autobiographical history;
- user-authorized preferences;
- prior plans;
- previous outcomes;
- relevant failures.

Retrieval must preserve provenance and confidence.

---

## 11. WORKSPACE ASSEMBLY

The cognitive workspace combines:

```text
current state
+ selected observations
+ relevant memories
+ knowledge
+ active goals
+ predictions
+ self-model
+ constraints
+ uncertainty
+ resource state
```

Only information relevant to the current cognitive task should be included.

---

## 12. REASONING

Reasoning may use multiple mechanisms:

- deterministic rules;
- classical algorithms;
- planners;
- retrieval;
- local language models;
- vision-language models;
- learned policies;
- specialized perception models.

The language model is a reasoning component, not the entire cognitive architecture.

---

## 13. Model Routing

Different cognitive tasks may use different models.

For example:

```text
fast reactive task → lightweight model/rules
complex multimodal task → VLM
long-form reasoning → language model
navigation → robotics planner
object detection → specialist detector
```

A single-model architecture remains possible, but the interfaces must not depend on it.

---

## 14. Prediction

Before important actions, Novi should form an expectation where practical.

```text
planned action
    ↓
expected outcome
    ↓
action
    ↓
actual observation
    ↓
prediction error
```

This supports adaptive learning and anomaly detection.

---

## 15. Decision Proposal

Cognition should produce a structured proposal rather than directly commanding hardware.

Conceptually:

```json
{
  "goal": "...",
  "action": "...",
  "parameters": {},
  "reason": "...",
  "expected_outcome": "...",
  "confidence": 0.0,
  "constraints": [],
  "evidence": [],
  "expires_at": "..."
}
```

The exact schema will be defined in autonomy/action documents.

---

## 16. Validation Gate

Every consequential proposal must be validated against current state.

Checks may include:

- authorization;
- safety;
- capability;
- resource budget;
- current obstacle/state;
- goal validity;
- policy;
- privacy;
- security;
- action freshness.

The proposal may be rejected or modified.

---

## 17. Action Freshness

A decision can become stale while reasoning is occurring.

Example:

```text
workspace at T0
   ↓
reasoning for 2 seconds
   ↓
obstacle appears at T1
   ↓
old action invalid
```

Therefore action execution requires a final current-state check for consequential actions.

---

## 18. Action Execution

Validated actions are handed to the appropriate subsystem:

```text
navigation → navigation stack
speech → audio subsystem
movement → motion controller
lighting → lighting controller
display → display subsystem
```

Cognition should not directly manipulate low-level hardware when a dedicated safety/control subsystem exists.

---

## 19. WAIT as an Action

Novi must be able to choose not to act.

```text
ACT
WAIT
OBSERVE
REPLAN
```

Waiting can be optimal when uncertainty is high or information is expected to arrive soon.

---

## 20. Outcome Verification

After consequential action, Novi should observe whether the intended result occurred.

```text
intention
 ↓
action
 ↓
expected result
 ↓
observed result
 ↓
verified / failed / uncertain
```

A successful command acknowledgement is not necessarily proof of physical success.

---

## 21. Failure Handling

Failures should be classified.

Examples:

```text
ACTION_REJECTED
ACTION_FAILED
ACTION_TIMEOUT
PARTIAL_SUCCESS
UNEXPECTED_OUTCOME
ENVIRONMENT_CHANGED
SENSOR_UNCERTAIN
SAFETY_INTERRUPTED
RESOURCE_INTERRUPTED
```

Each class can trigger different recovery behavior.

---

## 22. Replanning

Novi should replan when:

- environment changes;
- goal changes;
- action fails;
- prediction error is high;
- new information arrives;
- resource state changes;
- safety state changes;
- localization becomes uncertain.

Replanning must use current state, not stale workspace assumptions.

---

## 23. Interrupts

Interrupts can originate from:

- emergency stop;
- obstacle;
- person entering protected area;
- user command;
- hardware fault;
- thermal alarm;
- battery threshold;
- localization failure;
- security event;
- high-priority goal.

Interrupt priority must be explicitly defined.

---

## 24. Interrupt Priority

A conceptual priority ordering is:

```text
EMERGENCY / SAFETY
      ↓
HARDWARE FAULT
      ↓
SECURITY / PROTECTION
      ↓
USER / HIGH-PRIORITY INTERACTION
      ↓
ACTIVE AUTONOMY
      ↓
BACKGROUND COGNITION
      ↓
REFLECTION / CONSOLIDATION
```

Exact priority is subject to the safety architecture.

---

## 25. Goal Arbitration

Multiple goals may compete.

The cognitive runtime should represent:

- priority;
- deadline;
- authority;
- dependency;
- safety constraints;
- resource cost;
- reversibility.

A goal must not win simply because an LLM generated a persuasive justification.

---

## 26. User vs Autonomous Goals

User-authorized goals and autonomous goals must remain distinguishable.

Examples:

```text
USER:
"Map the garden."

AUTONOMOUS:
"Investigate unknown sound."
```

Autonomous goals remain bounded by system policies and safety constraints.

---

## 27. Exploration

Exploration can be an autonomous goal when permitted.

Before exploration, Novi should evaluate:

- safety;
- battery;
- localization;
- environment;
- authorization;
- expected information gain;
- resource cost;
- return/recovery capability.

Exploration should not become an excuse to ignore higher-priority commitments.

---

## 28. Curiosity / Information Seeking

Novi may identify uncertainty worth resolving.

```text
uncertainty
   ↓
expected information gain
   ↓
cost/risk
   ↓
observe / ask / explore / defer
```

Curiosity is subordinate to safety, privacy and explicit constraints.

---

## 29. Reflection

After meaningful episodes, Novi may perform reflection:

- what happened;
- what was expected;
- what failed;
- what was learned;
- whether memory should change;
- whether a goal should change;
- whether a capability belief should change.

Reflection produces proposals that pass the normal memory/learning gates.

---

## 30. Learning Boundary

The cognitive cycle may generate learning candidates but cannot directly redefine protected policy.

```text
experience
 ↓
reflection
 ↓
learning candidate
 ↓
evaluation
 ↓
approved memory/knowledge/model update
```

This preserves the security boundary established earlier.

---

## 31. Personality Boundary

Personality influences interaction style and possibly preference weighting where explicitly permitted.

It must not override:

- safety;
- authorization;
- privacy;
- security;
- factual system state;
- evaluation gates.

---

## 32. Resource-Aware Cognition

The cognitive cycle must adapt to resource pressure.

```text
NORMAL
 → full reasoning

CONSTRAINED
 → shorter context / cheaper retrieval

CRITICAL
 → core autonomy only

EMERGENCY
 → safety + minimal required control
```

Background reflection should be shed before critical perception or safety.

---

## 33. Thermal-Aware Cognition

On Jetson, sustained cognitive workloads can affect temperature and performance.

If thermal pressure rises:

- reduce optional model frequency;
- defer consolidation;
- reduce background embeddings;
- reduce non-critical perception rates where safe;
- preserve critical autonomy;
- preserve thermal monitoring.

The exact thresholds must be measured on final hardware.

---

## 34. Battery-Aware Cognition

Battery state should influence optional activity.

Examples:

```text
high battery → exploration permitted
medium battery → normal autonomy
low battery → return/home/charge planning
critical battery → protected shutdown/recovery behavior
```

Battery policy is safety-controlled and cannot be overridden by a goal merely because it is important.

---

## 35. Network Independence

The cognitive cycle must remain functional offline.

Cloud/network-dependent services are optional accelerators or integrations, not prerequisites for core cognition.

```text
Wi-Fi unavailable
        ↓
local perception
local memory
local cognition
local autonomy
local safety
        ↓
continue
```

---

## 36. Timeouts

Every external or potentially blocking cognitive operation should have a timeout/deadline where practical.

Examples:

- model inference;
- memory query;
- perception service;
- navigation plan;
- hardware command;
- synchronization.

Timeouts should produce explicit states rather than indefinite waiting.

---

## 37. Cancellation

Long-running work must support cancellation where practical.

Cancellation should be propagated through:

```text
Goal
 ↓
Plan
 ↓
Cognitive task
 ↓
Tool calls
 ↓
Action
```

Physical action cancellation must be handled by the appropriate controller and safety layer.

---

## 38. Concurrency

Multiple cognitive tasks may exist simultaneously.

Examples:

```text
navigation
conversation
environment monitoring
mapping
learning
```

The scheduler must prevent low-priority tasks from starving critical work.

---

## 39. Cognitive Task Isolation

A failed reasoning task should not crash the entire cognitive runtime.

Failures should be isolated at appropriate process/task boundaries.

Example:

```text
VLM failure
 ↓
conversation degraded
 ↓
navigation continues
```

provided the safety architecture permits it.

---

## 40. Context Expiration

Workspace contents should have validity periods.

Examples:

```text
current obstacle → very short
battery → short
current pose → short
recent conversation → medium
historical memory → long
```

Expired context should be refreshed before consequential use.

---

## 41. Cognitive Checkpoints

For long tasks, Novi should persist appropriate checkpoints:

- goal;
- plan version;
- progress;
- last verified state;
- pending decisions;
- relevant evidence.

This supports recovery after restart without pretending the physical world remained unchanged.

---

## 42. Restart Recovery

After restart:

```text
recover durable goals
recover task checkpoints
refresh current state
refresh safety state
refresh localization
validate previous plan
resume / replan / cancel
```

Novi must not blindly continue an old action.

---

## 43. Cognitive Replay

Historical events can be replayed into a simulated cognitive runtime.

Replay should support:

- model comparison;
- regression testing;
- failure investigation;
- memory-policy evaluation;
- autonomy analysis.

Default replay is non-actuating.

---

## 44. Provenance

Consequential cognitive decisions should record:

- workspace version;
- relevant event IDs;
- memory IDs;
- knowledge IDs;
- goal ID;
- model/version;
- policy version;
- state-estimation version where relevant;
- decision timestamp;
- action result.

This supports later explanation and debugging.

---

## 45. Explainability Boundary

Novi should be able to provide an evidence-based explanation of important actions.

Example:

```text
I moved because:
- goal = return home
- battery = 18%
- route was available
- obstacle was detected
- selected route avoided obstacle
```

The explanation should be derived from recorded decision context, not fabricated after the fact by an LLM.

---

## 46. Uncertainty

Every important decision should preserve relevant uncertainty.

Examples:

```text
localization confidence
object recognition confidence
prediction confidence
goal interpretation confidence
memory relevance confidence
```

Low confidence can trigger:

- additional sensing;
- user clarification;
- safer action;
- waiting;
- replanning.

---

## 47. Safe Default

When critical uncertainty cannot be resolved, Novi should choose the behavior defined by the safety policy, not whatever action appears most plausible to the model.

---

## 48. Cognitive Cycle Frequency

There is no single universal frequency.

The scheduler should select rates based on:

- task;
- sensor dynamics;
- safety requirements;
- resource budget;
- model latency;
- environmental change.

High-frequency control remains outside the LLM loop where appropriate.

---

## 49. Background Cognition

When no urgent task exists, Novi may perform bounded background work:

- memory consolidation;
- indexing;
- map optimization;
- experience summarization;
- knowledge candidate generation;
- benchmark evaluation;
- system diagnostics.

Background work must yield immediately to higher-priority tasks.

---

## 50. Continuous Operation

Novi should be designed for indefinite operation.

The cognitive cycle must therefore avoid:

- unbounded context growth;
- unbounded queues;
- memory leaks;
- infinite reflection loops;
- repeated failed retries;
- runaway curiosity;
- uncontrolled goal creation.

All long-running mechanisms require budgets and termination conditions.

---

## 51. Cognitive Loop Health

The runtime should monitor:

- cycle latency;
- queue depth;
- decision latency;
- action success rate;
- stale workspace rate;
- model failures;
- memory retrieval failures;
- interrupt frequency;
- replanning frequency;
- resource pressure;
- thermal state.

Abnormal behavior should trigger degradation or investigation.

---

## 52. Cognitive Loop Invariants

1. Safety-critical control never depends on LLM availability.
2. Current authoritative state outranks stale memory for current decisions.
3. Consequential actions require validation before execution.
4. Long reasoning cannot silently grant action authority.
5. Actions should have expected outcomes where practical.
6. Important actions are followed by outcome verification.
7. Stale workspace state cannot be treated as current physical state.
8. Interrupts can preempt lower-priority cognition.
9. The system can choose to wait or ask for information.
10. Learning candidates pass protected admission/evaluation paths.
11. Background cognition yields to critical workloads.
12. Offline operation remains functional.
13. Cognitive tasks are bounded by time and resource budgets.
14. Failed cognitive components are isolated where practical.
15. Important decisions preserve evidence/provenance.
16. Restart recovery revalidates plans against current reality.
17. The LLM is a cognitive component, not the sole source of truth or authority.

---

## 53. Final Principle

> **Novi should continuously think, but it should never continuously act merely because it is thinking.**

Thinking produces proposals. Current state, policies, safety controls and dedicated execution systems determine what may actually happen. Every meaningful action produces new observations, which feed the next cognitive cycle and create the opportunity for measured learning.
