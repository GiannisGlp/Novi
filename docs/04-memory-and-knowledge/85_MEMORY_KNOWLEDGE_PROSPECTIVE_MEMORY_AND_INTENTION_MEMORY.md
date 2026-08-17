# 85 — Memory Knowledge Prospective Memory and Intention Memory

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi remembers things that are intended to happen in the future: commitments, reminders, deferred actions, scheduled tasks, conditional intentions, deadlines, dependencies, follow-ups and obligations.

## Core Principle

> **Prospective memory is memory for future-directed commitments and intentions, not proof that the intended action has happened.**

An intention remains pending until its completion is independently established or explicitly cancelled/superseded.

## 1. Position in Architecture

```text
USER / SYSTEM / NOVI INTENTION
        ↓
INTENTION RECORD
        ↓
PROSPECTIVE MEMORY
        ↓
TRIGGER / SCHEDULER / CONDITION
        ↓
REACTIVATION
        ↓
RETRIEVE CONTEXT
        ↓
PLAN / EXECUTE IF AUTHORIZED
        ↓
VERIFY OUTCOME
        ↓
COMPLETE / FAILED / CANCELLED / EXPIRED
```

## 2. Intention Model

An intention can contain:

```text
INTENTION ID
OWNER
CREATED AT
OBJECTIVE
TRIGGER
TIME WINDOW / DEADLINE
LOCATION CONDITION
DEPENDENCIES
PRIORITY
AUTHORIZATION SCOPE
REQUIRED SKILL
STATUS
PROVENANCE
COMPLETION EVIDENCE
```

## 3. Intention vs Plan

```text
INTENTION
"Do X tomorrow."

PLAN
"To do X, perform A → B → C."
```

An intention may generate a plan later. The plan is not itself the commitment.

## 4. Intention vs Action

```text
INTENDED
 ≠
STARTED
 ≠
COMPLETED
```

The system must never mark an intention complete merely because execution began.

## 5. Intention Sources

Intentions may originate from:

- explicit user requests;
- accepted plans;
- system maintenance policies;
- scheduled workflows;
- detected commitments;
- recurring routines;
- Novi-generated suggestions explicitly accepted by an authorized user.

Unaccepted suggestions must not become commitments.

## 6. Explicit User Intent

Explicit instructions should retain their original wording/meaning and provenance where required.

Example:

```text
"Remind me to call Alex tomorrow."
```

becomes a prospective-memory record with a reminder intention, not an assertion that the call will occur.

## 7. Detected Intent

Novi may detect a possible future commitment from conversation, but detection alone should not create an obligation when ambiguity matters.

```text
possible intention
      ↓
clarify / confirm
      ↓
committed intention
```

## 8. Acceptance

An intention can have an explicit acceptance state:

```text
PROPOSED
ACCEPTED
REJECTED
```

Only accepted intentions should normally drive autonomous follow-up.

## 9. Status Lifecycle

```text
PROPOSED
 ↓
ACCEPTED
 ↓
PENDING
 ↓
TRIGGERED
 ↓
IN_PROGRESS
 ↓
VERIFYING
 ↓
COMPLETED
```

Alternative terminal states:

```text
CANCELLED
EXPIRED
FAILED
SUPERSEDED
BLOCKED
```

## 10. Triggers

Triggers may be:

- absolute time;
- time window;
- relative time;
- location arrival/departure;
- sensor condition;
- event occurrence;
- external result;
- dependency completion;
- user interaction.

Trigger semantics must be explicit.

## 11. Time Semantics

Store event/trigger time with timezone context where relevant.

Distinguish:

```text
CREATED_AT
DUE_AT
TRIGGERED_AT
STARTED_AT
COMPLETED_AT
EXPIRED_AT
```

## 12. Time Windows

Some intentions require windows rather than exact times:

```text
VALID FROM
VALID UNTIL
PREFERRED TIME
DEADLINE
```

Novi must not silently convert a window into an arbitrary exact deadline.

## 13. Recurring Intentions

Recurring intentions can define:

- recurrence rule;
- next occurrence;
- exceptions;
- pause state;
- end condition.

Each execution instance should remain distinguishable.

## 14. Location-Triggered Intentions

Examples:

```text
WHEN ARRIVING HOME → perform X
WHEN LEAVING HOME → check Y
```

Location triggers require localization confidence and geofencing policy.

## 15. GPS Uncertainty

A location trigger must account for:

- GNSS accuracy;
- indoor localization;
- map boundary uncertainty;
- signal loss;
- spoofing/anomaly detection where available.

A weak location estimate should not automatically trigger consequential actions.

## 16. Condition-Triggered Intentions

A condition can be:

```text
IF battery < threshold
IF object detected
IF person arrives
IF task remains incomplete
```

Conditions should define evaluation frequency and hysteresis where needed to prevent trigger flapping.

## 17. Event-Triggered Intentions

Intentions can depend on events:

```text
WAIT FOR EVENT
      ↓
TRIGGER
      ↓
REACTIVATE INTENTION
```

Event provenance remains attached to the trigger.

## 18. Dependencies

An intention can depend on another state:

```text
Intention B
 ↓ requires
Intention A completed
```

Dependencies should be explicit and cycle-checked.

## 19. Dependency Failure

If a prerequisite fails:

```text
BLOCKED
```

The dependent intention must not silently proceed as though the prerequisite succeeded.

## 20. Deadlines

Deadlines should be treated as constraints, not commands to violate safety.

```text
DEADLINE
   ↓
priority signal
   ≠
safety override
```

## 21. Priority

Priorities can consider:

- user importance;
- urgency;
- deadline proximity;
- safety relevance;
- dependencies;
- resource constraints.

Priority must not bypass authorization or safety.

## 22. Reminder vs Autonomous Action

These are distinct:

```text
REMINDER
 → notify / surface intention

AUTONOMOUS ACTION
 → execute if authorized and safe
```

A reminder should not silently become an autonomous physical action.

## 23. Notification Policy

Notifications can be:

- immediate;
- scheduled;
- batched;
- suppressed during quiet periods;
- escalated after repeated failure.

Notification policy is separate from intention truth state.

## 24. Commitment Tracking

Novi may track commitments such as:

```text
"I will do X."
"Novi will do Y."
"We agreed to Z."
```

The source and responsible party must be explicit.

## 25. Responsibility

An intention should identify who is responsible:

```text
USER
NOVI
OTHER AGENT
EXTERNAL SYSTEM
SHARED
```

Novi must not mark another party's responsibility as its own.

## 26. User Commitments

If a user says they will do something, Novi can remember the commitment when permitted, but should distinguish:

```text
USER COMMITTED
 ≠
USER COMPLETED
```

Completion requires evidence or explicit confirmation.

## 27. Novi Commitments

If Novi commits to an action, the commitment should be persisted sufficiently to survive context switching and interruption according to retention policy.

## 28. External Commitments

Commitments involving external systems should include external identifiers and synchronization status where available.

## 29. Completion Verification

Completion should be established through:

- direct observation;
- authoritative tool result;
- explicit user confirmation;
- verified external state;
- successful postcondition.

A command returning successfully is not always equivalent to the real-world outcome being achieved.

## 30. Failed Completion

If an action fails:

```text
PENDING
 ↓
ATTEMPT
 ↓
FAILURE
 ↓
FAILED / RETRY / BLOCKED / ESCALATE
```

Retry behavior must be bounded and policy-driven.

## 31. Partial Completion

Some intentions may be partially completed.

Represent:

```text
0%
25%
50%
75%
100%
```

or structured subtask state where percentage would be misleading.

## 32. Cancellation

Cancellation should identify:

- who cancelled;
- when;
- reason where appropriate;
- whether future recurring instances are also cancelled.

## 33. Supersession

A new intention can replace an older one:

```text
Intention A
   ↓ superseded by
Intention B
```

Historical intention records remain traceable where policy requires.

## 34. Expiration

An intention can expire naturally after its validity window.

Expiration is distinct from completion and cancellation.

## 35. Missed Trigger

If Novi was offline or unavailable when a trigger occurred, policy should define:

```text
RUN IMMEDIATELY
RUN IF STILL RELEVANT
SKIP
ASK USER
MARK MISSED
```

No default should be assumed for consequential actions.

## 36. Offline Operation

Prospective memory must remain locally available for essential intentions.

Offline behavior should preserve due times and conditions and reconcile missed triggers after recovery.

## 37. Clock Integrity

Time-based intentions depend on trustworthy time.

The system should detect significant clock changes and avoid incorrectly firing or completing time-sensitive intentions.

## 38. Calendar Integration

If calendars are integrated, imported events remain external data with provenance.

A calendar event does not automatically become a Novi commitment unless policy/authorization establishes that relationship.

## 39. External State Synchronization

For external systems:

```text
LOCAL INTENTION
      ↕
EXTERNAL STATE
```

Conflicts require explicit reconciliation.

## 40. Duplicate Execution Prevention

The system should use idempotency keys or equivalent execution identity where supported.

This prevents retries from accidentally performing a consequential action twice.

## 41. Exactly-Once Limitations

Physical actions may not support true exactly-once semantics.

Therefore, execution should record:

```text
ATTEMPTED
ACKNOWLEDGED
OBSERVED OUTCOME
```

rather than assuming a perfect transaction boundary.

## 42. Interruptions

If Novi is interrupted during execution:

```text
INTENTION
 ↓
EXECUTION CHECKPOINT
 ↓
INTERRUPTION
 ↓
RECOVER / VERIFY / ABORT
```

It must verify actual state before resuming.

## 43. Context Recovery

After task switching or restart, Novi should reconstruct only the active intention context needed to continue safely.

## 44. Long-Running Intentions

Long-running intentions should checkpoint:

- current state;
- completed subtasks;
- pending subtasks;
- assumptions;
- dependencies;
- evidence;
- next trigger.

## 45. Human Confirmation Gates

High-impact actions may require confirmation immediately before execution even when the intention was previously accepted.

Acceptance does not automatically eliminate future confirmation requirements.

## 46. Authorization at Execution Time

Permissions can change after an intention is created.

```text
CREATED WITH PERMISSION
        ≠
CURRENTLY AUTHORIZED
```

Authorization must be re-evaluated when execution becomes imminent.

## 47. Safety at Execution Time

Environmental conditions can change after an intention is created.

Safety must be evaluated against current state, not historical conditions.

## 48. Intention Privacy

Future plans and commitments can reveal sensitive information.

Examples:

- appointments;
- travel plans;
- household routines;
- reminders;
- health-related scheduling;
- private communications.

Access and telemetry must respect privacy classifications.

## 49. Multi-User Intentions

Shared intentions should identify:

- participants;
- owner;
- responsible party;
- visibility;
- authorization scope.

Household membership alone does not grant access to all intentions.

## 50. Distributed Intentions

When multiple Novi instances share intentions, records must retain:

- origin agent;
- owner;
- version;
- synchronization state;
- causal metadata;
- conflict status.

## 51. Conflict Resolution

Conflicts can occur when two systems modify the same intention.

Use explicit version/causal rules rather than last-write-wins for high-consequence commitments where possible.

## 52. Trigger Security

External events used as triggers can be spoofed or malformed.

Important triggers should require source validation and integrity checks.

## 53. Prompt Injection Boundary

Text stored in an intention, reminder or external calendar entry is data.

It must not silently become a higher-priority instruction to the reasoning system.

## 54. Retrieval

Prospective memories should be retrieved when relevant to:

- current task;
- conversation;
- scheduling;
- planning;
- commitments;
- location context;
- pending follow-up.

Retrieval does not execute an intention.

## 55. Working-Memory Integration

When an intention becomes active:

```text
PROSPECTIVE MEMORY
      ↓
RETRIEVAL
      ↓
WORKING MEMORY
      ↓
PLAN
```

Only the relevant intention context should enter active memory.

## 56. Episodic Integration

Execution creates an episode:

```text
INTENTION
 ↓
ACTION
 ↓
EPISODE
 ↓
OUTCOME
```

This provides evidence for completion and future learning.

## 57. Procedural Integration

Intentions can select procedural skills:

```text
INTENTION
 ↓
SKILL RETRIEVAL
 ↓
PLAN
 ↓
EXECUTE
```

The skill remains subject to current capability, authorization and safety checks.

## 58. Semantic Integration

Intention triggers can use world-model conditions:

```text
WHEN OBJECT X IS AT LOCATION Y
 → perform task Z
```

World-model uncertainty must be respected before triggering consequential actions.

## 59. Observability

Track:

- intentions created;
- trigger latency;
- missed triggers;
- completion rate;
- failure rate;
- cancellation;
- expiration;
- blocked dependencies;
- retries;
- duplicate-prevention events;
- human confirmations;
- synchronization conflicts.

Telemetry is subject to privacy and retention policy.

## 60. Testing

Test:

- exact-time triggers;
- time windows;
- recurring intentions;
- location triggers;
- condition triggers;
- event triggers;
- missed triggers;
- offline recovery;
- clock changes;
- duplicate execution;
- interruption/resume;
- partial completion;
- cancellation;
- supersession;
- expiration;
- dependency cycles;
- authorization revocation;
- safety-state changes;
- human confirmation gates;
- distributed conflicts;
- trigger spoofing;
- prompt injection in stored content;
- privacy isolation;
- calendar synchronization.

## 61. Architectural Invariants

1. An intention is not an action.
2. An intended action is not a completed action.
3. Suggestions do not become commitments without appropriate acceptance.
4. Completion requires evidence or explicit confirmation according to policy.
5. Deadlines never override safety.
6. Authorization is checked at execution time.
7. Safety is checked against current state.
8. Reminder and autonomous execution are distinct capabilities.
9. Missed triggers follow explicit recovery policy.
10. Recurring instances remain individually traceable.
11. Duplicate execution is actively controlled.
12. Physical actions do not assume exactly-once semantics.
13. Interrupted execution requires state verification before resume.
14. External trigger data remains untrusted until validated.
15. Stored intention text is data, not instruction authority.
16. User and multi-party privacy boundaries remain enforced.
17. Distributed intentions retain provenance and causal/version metadata.
18. Intention state survives context switching according to lifecycle policy.
19. Historical commitments remain distinct from current commitments.
20. Completion, cancellation, expiration, failure and supersession are distinct states.

## 62. Final Principle

> **Novi should remember what it intends to do, why, when, under which conditions, and for whom—but should act only after rechecking the current world, authorization and safety state, and should never confuse intention with completion.**

Prospective memory gives Novi continuity into the future: it connects commitments and deferred goals with its working memory, procedural skills, semantic world model and episodic history while preserving explicit verification and control boundaries.