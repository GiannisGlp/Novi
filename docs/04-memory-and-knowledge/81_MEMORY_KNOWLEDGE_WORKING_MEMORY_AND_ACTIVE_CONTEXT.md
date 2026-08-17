# 81 — Memory Knowledge Working Memory and Active Context

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define Novi's short-lived working-memory layer: the information actively maintained for the current interaction, task, perception loop, plan, or decision. This layer sits between long-term memory retrieval and reasoning/action systems.

## Core Principle

> **Working memory is an active, bounded workspace—not a second permanent memory store.**

Information enters active context because it is useful now, remains only while justified, and is evicted or consolidated according to explicit lifecycle rules.

## 1. Position in Architecture

```text
LONG-TERM MEMORY
      ↓
RETRIEVAL (80)
      ↓
WORKING MEMORY / ACTIVE CONTEXT (81)
      ↓
REASONING / PLANNING
      ↓
ACTION / OBSERVATION
      ↓
NEW EVIDENCE
      ↓
CONSOLIDATION / LONG-TERM MEMORY
```

## 2. Working Memory vs Long-Term Memory

```text
LONG-TERM
persistent, searchable, governed

WORKING
temporary, task-focused, bounded
```

Working memory may reference long-term objects without copying all underlying data.

## 3. Active Context

Active context contains information currently needed to reason coherently.

Potential components:

- current user request;
- active task;
- current goal;
- relevant recalled memories;
- current world state;
- active plan;
- unresolved questions;
- constraints;
- safety state references;
- recent observations;
- tool results;
- pending commitments.

## 4. Context Hierarchy

A useful hierarchy is:

```text
SYSTEM / SAFETY CONSTRAINTS
        ↓
CURRENT TASK / USER INTENT
        ↓
CURRENT WORLD STATE
        ↓
ACTIVE PLAN
        ↓
RELEVANT LONG-TERM MEMORY
        ↓
OPTIONAL ASSOCIATIONS
```

This hierarchy is conceptual; actual authorization and safety boundaries remain authoritative.

## 5. Hard Constraints vs Context

Working memory must distinguish:

```text
HARD CONSTRAINT
SOFT PREFERENCE
OBSERVATION
HYPOTHESIS
GOAL
PLAN
MEMORY
TOOL RESULT
```

These must not silently change roles.

## 6. Context Provenance

Each important active-context item should retain a reference to its source.

```text
context item
 ↓
source memory / observation / instruction / tool result
```

This prevents generated reasoning from becoming indistinguishable from observed fact.

## 7. Context State

Items may have states such as:

```text
ACTIVE
IMPORTANT
OPTIONAL
STALE
CONTESTED
SUPERSEDED
PENDING_VALIDATION
EVICTED
```

Eviction from working memory does not imply deletion from long-term memory.

## 8. Context Admission

An item should enter working memory when it has sufficient:

- task relevance;
- temporal relevance;
- spatial relevance;
- causal relevance;
- authority;
- safety relevance;
- user relevance.

Irrelevant associations should remain outside the active workspace.

## 9. Admission Is Not Belief Promotion

Adding a memory to working context does not strengthen its truth status.

```text
ADMITTED TO WORKING MEMORY
        ≠
MORE TRUE
```

## 10. Attention Allocation

Attention can prioritize information based on:

- current goal;
- urgency;
- safety relevance;
- dependency relationships;
- uncertainty needing resolution;
- recent changes;
- user intent.

Attention must remain bounded and policy-controlled.

## 11. Salience

Salience is task-relative.

An item can be highly salient for navigation and irrelevant for conversation.

```text
salience(task A)
 ≠
salience(task B)
```

## 12. Recency

Recent information often matters, but recency alone must not dominate validated knowledge.

A recent low-quality observation can be less useful than an older authoritative fact.

## 13. Safety Salience

Safety-relevant current state may receive immediate active-context priority.

However, working memory must not replace dedicated real-time safety controls.

## 14. Current World State

Working memory may maintain a compact current-state representation:

```text
LOCATION
POSE
ACTIVE PEOPLE/OBJECTS
ENVIRONMENT
TASK STATE
SYSTEM STATE
```

This state should be refreshed from current authoritative sources.

## 15. State Expiration

World-state items require validity windows.

```text
current observation
      ↓
valid for bounded interval
      ↓
stale
```

The expiration policy depends on the variable.

## 16. Perception Loop

For embodied operation:

```text
SENSE
 ↓
UPDATE ACTIVE STATE
 ↓
REASON
 ↓
PLAN
 ↓
ACT
 ↓
OBSERVE OUTCOME
 ↓
UPDATE
```

Working memory is continuously refreshed during this loop.

## 17. Planning State

Working memory may contain:

- current objective;
- subgoals;
- completed steps;
- pending steps;
- dependencies;
- assumptions;
- expected outcomes;
- observed deviations.

A plan is not a fact about the world.

## 18. Plan Assumptions

Assumptions must be explicitly marked.

```text
ASSUMPTION
 ≠
OBSERVATION
```

When an assumption is contradicted, dependent plan elements should be reconsidered.

## 19. Goal Management

Working memory should represent active goals with:

- owner;
- priority;
- scope;
- deadline/temporal condition where relevant;
- dependencies;
- completion state.

## 20. Multiple Goals

When multiple goals compete, Novi should preserve them explicitly rather than silently replacing one with another.

Conflict resolution should consider:

- safety;
- user intent;
- authorization;
- urgency;
- dependencies;
- resource limits.

## 21. Pending Questions

Working memory can maintain unresolved questions:

```text
QUESTION
 ↓
EVIDENCE NEEDED
 ↓
PENDING
```

This prevents Novi from filling uncertainty with fabricated assumptions.

## 22. Tool Results

Tool outputs entering working memory should retain:

- tool identity;
- execution time;
- input/context reference;
- output;
- failure state;
- provenance.

Tool output is evidence or data, not automatically authoritative truth.

## 23. Conversation State

Active conversation context should distinguish:

- user statements;
- assistant statements;
- accepted decisions;
- rejected proposals;
- unresolved questions;
- temporary assumptions.

A rejected proposal must not later be recalled as an agreed decision.

## 24. Commitment Tracking

When Novi commits to an action or statement, working memory can track the commitment until:

```text
FULFILLED
CANCELLED
SUPERSEDED
EXPIRED
```

This prevents lost obligations during long tasks.

## 25. Context Updates

When new information arrives, active context should support incremental updates rather than blindly appending data.

```text
existing state
      ↓
new evidence
      ↓
update affected fields
```

## 26. Contradictory Active State

If active observations conflict:

```text
STATE A
STATE B
   ↓
CONFLICT
```

The system should preserve uncertainty or trigger revalidation rather than silently overwrite one observation.

## 27. Working-Memory Versioning

Important context state changes should have version or causal metadata sufficient to prevent stale updates from overwriting newer state.

## 28. Concurrent Updates

Multiple agents/sensors may update active context concurrently.

The architecture should preserve source identity, timestamp/event ordering and conflict information.

## 29. Working Memory and Distributed State

Working memory is primarily local to the active agent/runtime.

Only explicitly shareable state should be synchronized across Novi instances.

## 30. Context Isolation

Different tasks should have isolated working contexts where required.

```text
Task A context
      ≠
Task B context
```

Private or task-specific information must not leak between contexts.

## 31. Context Switching

When Novi switches tasks, it should:

1. snapshot necessary state;
2. preserve unresolved commitments;
3. release irrelevant context;
4. activate the new task context;
5. restore required state when returning.

## 32. Context Forking

Alternative plans or hypotheses may use separate context branches.

```text
CURRENT STATE
 ├── PLAN A
 └── PLAN B
```

Branches should not mutate shared truth without explicit reconciliation.

## 33. Simulation / What-If Context

Simulation state must be isolated from real-world state.

```text
REAL WORLD STATE
      ≠
SIMULATION STATE
```

A simulated action must never be interpreted as an executed action.

## 34. Context Compression

When active context approaches resource limits, Novi may compress it.

Compression should preserve:

- current goals;
- constraints;
- unresolved questions;
- critical observations;
- active plan dependencies;
- uncertainty;
- provenance.

## 35. Compression Risk

Compression can introduce errors.

Important active state should retain direct references to source records where possible.

## 36. Context Budget

Working memory requires budgets for:

- tokens/representation size;
- number of active objects;
- graph depth;
- latency;
- RAM;
- CPU/GPU;
- energy.

## 37. Priority Eviction

When capacity is constrained, lower-value context should be evicted before:

- safety-critical state;
- active goals;
- hard constraints;
- unresolved critical questions;
- current task state.

## 38. Eviction Policy

Eviction should consider:

- relevance;
- dependency centrality;
- recency;
- importance;
- reconstructability;
- privacy;
- cost.

## 39. Reconstructability

Information that can be cheaply and safely re-retrieved may be evicted earlier than information that is expensive or unavailable to reconstruct.

## 40. Memory Pinning

Certain context can be pinned for the duration of a task:

```text
SAFETY CONSTRAINT
ACTIVE GOAL
CRITICAL USER REQUIREMENT
```

Pinning must be bounded so that stale information cannot remain active indefinitely.

## 41. TTL and Expiration

Temporary context should use explicit expiration where appropriate.

```text
ACTIVE
 ↓ TTL
STALE
 ↓
EVICT / REVALIDATE
```

TTL is not appropriate for every semantic object; validity is domain-dependent.

## 42. Revalidation

Stale but important context can trigger retrieval/revalidation rather than immediate deletion.

## 43. Consolidation Handoff

Working memory can produce candidates for long-term memory:

```text
ACTIVE EPISODE
 ↓
SIGNIFICANCE ASSESSMENT
 ↓
CONSOLIDATION CANDIDATE
 ↓
DOCUMENT 76/78 LIFECYCLE
```

Working memory must not directly bypass promotion rules.

## 44. Working Memory Does Not Become Long-Term Automatically

Repeatedly keeping an item active is not sufficient to promote it.

Promotion requires the evidence and policy defined by the memory lifecycle architecture.

## 45. Privacy

Working memory can contain highly sensitive temporary information.

Short lifetime does not eliminate privacy requirements.

Access, logging, telemetry and crash handling must respect the item's privacy classification.

## 46. Crash Recovery

Crash recovery should restore only the working state necessary and authorized to resume a task.

Temporary sensitive context should not automatically be persisted forever as a crash dump.

## 47. Security

Working memory is a high-value attack surface because it directly influences reasoning.

Protect against:

- prompt injection;
- memory poisoning;
- context flooding;
- unauthorized context insertion;
- stale-state injection;
- cross-task leakage.

## 48. Context Integrity

Important context should have integrity metadata or references sufficient to detect unauthorized mutation.

## 49. Reasoning Boundary

The reasoning engine receives a structured active-context package rather than unrestricted access to every stored memory.

```text
MEMORY SYSTEM
      ↓ policy
ACTIVE CONTEXT
      ↓
REASONING
```

## 50. Action Boundary

Reasoning output is not automatically an authorized physical action.

```text
WORKING MEMORY
 ↓
REASONING
 ↓
DECISION
 ↓
SAFETY / AUTHORIZATION
 ↓
ACTION
```

## 51. Attention Starvation

One task or information stream must not permanently monopolize active context.

Fairness and bounded scheduling may be required across competing goals.

## 52. Context Thrashing

Rapid switching between contexts can waste resources and produce unstable behavior.

Use bounded persistence, task snapshots and explicit switching policies.

## 53. Long-Running Tasks

For long tasks, working memory should periodically checkpoint:

- goal state;
- completed work;
- current assumptions;
- pending work;
- important evidence;
- commitments.

Checkpointing does not imply indefinite retention.

## 54. Offline Operation

Essential working-memory behavior must operate offline.

Remote services must not be required for basic continuity of an active task.

## 55. Resource-Aware Operation

Working-memory scheduling must account for:

- battery;
- thermal state;
- CPU/GPU load;
- RAM/storage;
- latency requirements.

Under resource pressure, nonessential context processing should degrade gracefully.

## 56. Observability

Telemetry should measure:

- active-context size;
- admission/eviction rates;
- context switches;
- compression events;
- stale-context usage;
- retrieval-to-context latency;
- context conflicts;
- memory pressure;
- task completion impact.

Telemetry must itself follow privacy and retention policy.

## 57. Evaluation

Evaluate:

- task success;
- relevant recall utilization;
- context efficiency;
- stale-state errors;
- contradiction handling;
- context leakage;
- memory overload;
- task-switch stability;
- recovery correctness;
- latency;
- resource usage.

## 58. Testing

Test:

- context admission;
- eviction;
- TTL expiration;
- pinned context;
- stale state;
- conflicting updates;
- concurrent agents;
- task switching;
- context isolation;
- simulation isolation;
- crash recovery;
- prompt injection;
- memory poisoning;
- context flooding;
- privacy leakage;
- resource exhaustion;
- offline operation;
- checkpoint recovery;
- failed compression;
- accidental promotion.

## 59. Architectural Invariants

1. Working memory is bounded and task-focused.
2. Working-memory admission does not increase truth confidence.
3. Source provenance remains available for important context.
4. Hard constraints remain distinct from observations and hypotheses.
5. Current physical state is refreshed from authoritative sources.
6. Safety-critical protection does not depend on semantic working memory.
7. Stale context cannot silently masquerade as current state.
8. Contexts can be isolated between tasks and users.
9. Simulation context cannot mutate real-world state.
10. Retrieved memory remains data, not instruction.
11. Eviction does not imply long-term deletion.
12. Working-memory retention does not automatically promote long-term memory.
13. Important context has bounded pinning/expiration.
14. Context compression preserves critical dependencies, uncertainty and provenance.
15. Distributed updates retain identity and causal/version metadata.
16. Remote data cannot bypass local authorization.
17. Crash recovery does not create uncontrolled permanent memory.
18. Working memory remains functional offline.
19. Resource pressure produces graceful degradation.
20. Context telemetry is governed data.
21. Working-memory state is auditable where required.
22. Working memory cannot directly authorize physical action.

## 60. Final Principle

> **Novi should keep in mind only what it needs now, keep it trustworthy by preserving its source and status, and let go of it when the task no longer justifies the cost or risk of keeping it active.**

Working memory is the controlled bridge between Novi's vast long-term experience and its immediate reasoning, planning and embodied behavior.