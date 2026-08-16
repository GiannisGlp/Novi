# 04 — Goals, Curiosity and Learning

## Status

**DESIGN** — detailed specification.

## Purpose

Autonomous behavior requires more than reacting to events. Novi must maintain goals, decide which goals deserve resources, create safe information-seeking goals when it encounters meaningful unknowns, and convert experience into controlled learning.

## Goal Sources

Goals may originate from:

- explicit user requests
- safety/maintenance requirements
- system recovery
- previously authorized routines
- active commitments
- curiosity
- learning opportunities
- navigation requirements

Every goal records its source and authorization level.

## Goal Lifecycle

```text
candidate
  ↓
validated
  ↓
queued
  ↓
active
  ↓
paused / blocked / superseded
  ↓
completed / failed / cancelled / expired
```

Goals must be resumable where useful and must not survive beyond their authorization or validity period without reevaluation.

## Goal Prioritization

Priority considers hard constraints and soft utility. Safety and explicit user commands are not reducible to ordinary utility scores.

A candidate utility model may consider:

```text
priority = urgency + relevance + commitment + expected_benefit
           - risk - resource_cost - interruption_cost
```

This is a planning aid, not a safety authorization mechanism.

## Goal Conflicts

When two goals conflict:

1. apply hard safety constraints;
2. respect explicit user priority;
3. preserve critical system operation;
4. evaluate task dependencies;
5. compare utility/cost;
6. pause or abandon lower-priority goals;
7. record the conflict and resolution.

## Curiosity

Curiosity is a controlled mechanism for identifying valuable unknowns.

Examples:

- unfamiliar object
- unknown person
- unexplained sound
- repeated environmental change
- inconsistent knowledge
- unexplained user behavior
- new IoT device
- unknown place
- repeated failed prediction

Curiosity creates a candidate information goal rather than immediately producing an action.

## Curiosity Pipeline

```text
unknown detected
    ↓
Is it meaningful?
    ↓
Can existing knowledge explain it?
    ↓
Can passive observation resolve it?
    ↓
Can safe local retrieval resolve it?
    ↓
Should Novi ask a person?
    ↓
Create learning candidate
    ↓
Verify
    ↓
Persist
```

## Learning From People

If someone teaches Novi a fact, it should store the source and confidence. For important or ambiguous information, Novi may ask a trusted user to validate it.

Example:

```text
Person A: “That device is a humidifier.”

candidate fact
source = Person A
confidence = 0.68
verification = pending

Later:
Novi asks Vano:
“I was told this is a humidifier. Is that correct?”

Vano: yes

verification = user_confirmed
```

## Learning From Repetition

Repeated observations can support routine hypotheses:

```text
observation × many
    ↓
pattern
    ↓
hypothesis
    ↓
confidence
    ↓
optional human confirmation
    ↓
routine knowledge
```

A repeated pattern must not automatically become a permanent fact.

## Learning From Failure

Failed predictions and actions are valuable experience. Novi should record:

- expectation
- actual result
- likely cause
- confidence
- recovery
- whether a policy/model/tool was involved

The system can use this to improve future planning without silently rewriting protected software.

## Evolution Boundaries

Novi may evolve:

- memories
- semantic knowledge
- preferences
- relationships
- routines
- vocabulary
- curiosity topics
- learned environment structure
- approved adaptive parameters

Novi may not autonomously alter:

- immutable safety rules
- security boundaries
- trust roots
- authorization policies
- protected system binaries
- physical safety limits
- audit integrity controls

## Learning Quality

A learning candidate should have:

- evidence count
- source diversity where appropriate
- confidence
- temporal consistency
- contradiction status
- verification state
- review/expiration policy

## Forgetting and Decay

Not all knowledge deserves permanent retention. The system should support:

- expiration
- confidence decay
- archival
- summarization
- contradiction resolution
- user-directed deletion

Critical safety knowledge and user-designated permanent information follow separate retention rules.

## Acceptance Criteria

Demonstrate that Novi can:

1. create goals from explicit requests;
2. maintain multi-step goals;
3. interrupt lower-priority goals safely;
4. identify meaningful unknowns;
5. investigate without unnecessary interruption;
6. ask users useful learning questions;
7. preserve source/provenance;
8. distinguish hypotheses from verified facts;
9. learn routines from repeated observations;
10. record failures and improve future decisions;
11. evolve managed data without modifying the immutable core.
