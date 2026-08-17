# 33 — Memory Goals, Intentions and Commitments

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Research and validation basis

This architecture was cross-checked against established robot/action interfaces and AI risk-management guidance. ROS 2 defines actions specifically for long-running robot behaviors with goals, feedback, results, cancellation and preemption, making them a useful implementation reference for Novi's execution boundary. citeturn0search0turn0search1turn0search7 NIST's AI Risk Management Framework emphasizes explicit risk management, trustworthy operation, and clearly defined human/AI roles and oversight; those principles inform Novi's authority, escalation and commitment boundaries. citeturn0search5turn0search10turn0search12

These sources inform the architecture but do not dictate implementation. Novi's goal system must remain independent from any single framework and work fully offline.

## Purpose

Define how Novi represents, creates, prioritizes, executes, pauses, resumes, revises, abandons and remembers goals, intentions, plans and commitments across autonomous operation and long-term memory.

The goal system connects cognition to action while preserving safety, user authority, resource constraints, uncertainty, provenance and autobiographical continuity.

## Core Principle

> **A goal is an intended outcome, not permission to achieve it by any means.**

Every goal remains subordinate to safety, authorization, policy, resource limits and current world state.

---

## 1. Conceptual Model

Novi should distinguish:

```text
DESIRE
What Novi may want/prefer.

GOAL
An outcome Novi is currently trying to achieve.

INTENTION
A committed goal Novi has selected for execution.

PLAN
A proposed sequence/strategy for achieving an intention.

ACTION
A concrete executable operation.

COMMITMENT
A durable obligation/promise Novi has explicitly accepted.

TASK
A bounded executable unit supporting a goal/plan.

OUTCOME
What actually happened.
```

These must not be collapsed into one object.

---

## 2. Goal Sources

Goals can originate from:

- authenticated user requests;
- autonomous needs/maintenance policies;
- safety requirements;
- scheduled objectives;
- environmental events;
- unfinished prior goals;
- learned preferences;
- system recovery;
- higher-level goals decomposing into subgoals.

Every goal must retain its source and authority.

---

## 3. Goal Authority

Source and authority are separate.

An observation can suggest a goal without authorizing it.

```text
observed event
     ↓
possible goal
     ↓
authority check
     ↓
eligible goal
```

For example, seeing a door does not authorize Novi to open it.

---

## 4. Goal Structure

A durable goal should contain, conceptually:

```text
goal_id
source
authority
created_at
valid_from
deadline / expiry
objective
success criteria
failure criteria
priority
constraints
resources
risk class
privacy class
required capabilities
parent goal
conflicts
current state
provenance
```

Exact schema is implementation-specific.

---

## 5. Goal Lifecycle

Initial lifecycle:

```text
PROPOSED
   ↓
VALIDATING
   ↓
ACCEPTED
   ↓
PLANNING
   ↓
COMMITTED
   ↓
EXECUTING
   ↓
MONITORING
   ├── PAUSED
   ├── REPLANNING
   ├── BLOCKED
   └── CANCEL_REQUESTED
   ↓
SUCCEEDED / FAILED / CANCELLED / EXPIRED / ABANDONED
```

A goal can also be `DEFERRED` when it remains valid but resources or conditions are not currently suitable.

---

## 6. Proposed vs Accepted

A proposed goal is not yet part of Novi's active intention set.

Acceptance requires:

- authority validation;
- capability validation;
- policy validation;
- safety checks;
- resource feasibility;
- conflict assessment;
- temporal validity.

---

## 7. Commitment

A commitment means Novi has decided to pursue a goal under defined conditions.

Commitment does not mean unconditional execution.

```text
commitment
   ↓
continuous validation
   ↓
execute while conditions remain valid
```

A commitment may be suspended or revoked when safety, authority, world state or constraints change.

---

## 8. Commitment Strength

Commitments should have explicit strength/authority levels.

Example:

```text
INFORMATIONAL
PREFERENCE
NORMAL
USER_COMMITMENT
SAFETY_REQUIRED
SYSTEM_CRITICAL
```

Higher strength does not override independent safety mechanisms.

---

## 9. Goal Priority

Priority should be multidimensional rather than one arbitrary number.

Potential dimensions:

- safety urgency;
- deadline urgency;
- user importance;
- system importance;
- reversibility;
- resource cost;
- expected benefit;
- confidence;
- dependency impact.

The scheduler can derive an execution priority while preserving the underlying factors.

---

## 10. Safety Dominance

Goal priority must not permit unsafe execution.

```text
Goal:
"Continue moving."

Safety:
"Obstacle collision risk critical."

Result:
STOP / SAFE RESPONSE
```

Safety controls remain authoritative.

---

## 11. User Authority

User-issued goals must respect authentication and permissions.

Novi should distinguish:

```text
known user
authenticated user
authorized user
authorized for this operation
```

Identity alone does not imply permission for every action.

---

## 12. Autonomous Goals

Autonomous goals may arise from policies and observations.

Examples:

- return to charging when battery is low;
- avoid an unsafe area;
- preserve memory when storage is near capacity;
- perform approved self-diagnostics;
- maintain localization;
- investigate a permitted anomaly.

Autonomous goal generation must operate inside defined policy boundaries.

---

## 13. No Unbounded Goal Creation

Environmental input must not allow unlimited autonomous goal generation.

Controls should include:

- rate limits;
- goal budgets;
- duplicate detection;
- priority thresholds;
- expiration;
- resource budgets;
- policy filters.

This prevents goal storms and feedback loops.

---

## 14. Goal Validity

A goal has a validity interval.

Examples:

```text
valid immediately
valid until 18:00
valid while battery > threshold
valid while user is present
valid until environment changes
```

Expired goals must not remain executable merely because they remain in memory.

---

## 15. Goal Constraints

Goals should explicitly encode constraints such as:

- do not enter restricted areas;
- do not exceed speed limits established by policy;
- do not operate when thermal state is critical;
- remain offline;
- preserve privacy;
- do not interrupt a critical safety action;
- require user confirmation.

Constraints are evaluated during planning and execution.

---

## 16. Preconditions

A goal can define preconditions.

Example:

```text
Goal: navigate outside

preconditions:
  mobility available
  localization sufficient
  battery sufficient
  safety state normal
```

If preconditions fail, the goal becomes blocked/deferred rather than forcing execution.

---

## 17. Success Criteria

Goals require explicit or derived success criteria.

Example:

```text
Goal: reach kitchen

success:
  pose within accepted region
  localization confidence sufficient
```

The LLM must not declare success merely because an action response sounded successful.

---

## 18. Failure Criteria

Failure criteria should be explicit where possible.

Examples:

- target unreachable;
- repeated planner failure;
- safety stop;
- capability unavailable;
- deadline exceeded;
- resource budget exhausted;
- authorization revoked.

Failure is an outcome to learn from, not something to conceal.

---

## 19. Intention Formation

Cognition may select intentions from eligible goals.

```text
candidate goals
      ↓
priority / utility / constraints
      ↓
conflict resolution
      ↓
resource feasibility
      ↓
intention selection
```

The selected intention must retain why it was selected.

---

## 20. Intention Does Not Equal Action

An intention is a commitment at the cognitive level.

It still requires planning and executable actions.

```text
intention
   ↓
plan
   ↓
action
   ↓
outcome
```

This allows Novi to replan without losing the underlying goal.

---

## 21. Planning

Plans should contain:

- ordered/partially ordered steps;
- dependencies;
- expected resources;
- required capabilities;
- risk constraints;
- fallback strategies;
- completion conditions.

Plans are hypotheses about how to achieve a goal, not facts.

---

## 22. Plan Revalidation

Before executing a significant step, Novi should revalidate:

- world state;
- safety state;
- capability state;
- authorization;
- resources;
- goal validity.

This prevents stale plans from driving current behavior.

---

## 23. Replanning

Replanning should occur when:

- environment changes;
- localization degrades;
- obstacle appears;
- resource pressure changes;
- sensor fails;
- action fails;
- higher-priority goal arrives;
- safety state changes;
- commitment becomes invalid.

A replan should preserve goal lineage.

---

## 24. Preemption

Higher-priority goals may preempt lower-priority intentions when policy permits.

```text
Goal A executing
      ↓
critical Goal B
      ↓
A paused/preempted
      ↓
B executed
      ↓
A reevaluated
```

ROS 2 actions provide a useful implementation reference because long-running actions support feedback and cancellation/preemption. citeturn0search1turn0search7

---

## 25. Pause and Resume

Paused goals retain state sufficient for safe resumption or explicit restart.

Before resuming, Novi must revalidate the environment and all relevant preconditions.

Never assume the world is unchanged merely because the goal remained active.

---

## 26. Cancellation

Goals must support cancellation.

Cancellation should be explicit and auditable.

A cancellation request is not always identical to immediate physical stopping; safety-critical controllers determine safe stopping behavior.

---

## 27. Abandonment

Novi may abandon a goal when:

- it is no longer useful;
- the goal is invalid;
- required resources are unavailable;
- repeated attempts indicate low feasibility;
- a policy makes it ineligible.

Abandonment should record reason and evidence.

---

## 28. Goal Conflicts

Two goals may conflict:

```text
Goal A: save battery
Goal B: explore outdoors
```

Conflict resolution should consider:

- safety;
- authority;
- deadlines;
- utility;
- reversibility;
- dependencies;
- resource constraints.

The resolution must be recorded.

---

## 29. Goal Dependencies

Goals can depend on other goals.

Example:

```text
Main goal: go outside
   ↓
Subgoal: charge battery
   ↓
Subgoal: localize
   ↓
Subgoal: navigate to exit
```

Dependency relationships must be explicit.

---

## 30. Goal Hierarchies

Novi may maintain hierarchical goals:

```text
Maintain health
 ├── monitor battery
 ├── monitor thermal state
 └── perform diagnostics

Explore outside
 ├── reach doorway
 ├── localize
 └── map new area
```

Child goals inherit applicable constraints but do not automatically inherit unlimited authority.

---

## 31. Goal Memory

Completed and significant failed goals can become episodic memories.

```text
goal
 ↓
actions
 ↓
outcome
 ↓
episode
 ↓
learning
```

Routine transient goals may not need long-term retention.

---

## 32. Goal-to-Memory Lineage

Important goal records should reference:

- originating events;
- relevant memories;
- knowledge used;
- plan versions;
- actions;
- outcomes;
- environmental context;
- resource state.

This supports later questions such as:

> Why did Novi decide to do this?

---

## 33. Commitment Memory

Some commitments should persist across restart.

Examples:

- user-approved scheduled task;
- active maintenance requirement;
- approved recurring objective.

Transient intentions may be reconstructed or discarded according to lifecycle policy.

---

## 34. Restart Semantics

After restart, Novi must reconstruct active goals from durable state.

Each recovered goal must be classified:

```text
safe to resume
needs revalidation
expired
cancelled
requires user confirmation
```

Never blindly resume physical actions after reboot.

---

## 35. Crash Recovery

Incomplete goals should produce explicit recovery state.

Example:

```text
goal: navigate to kitchen
state before crash: EXECUTING

restart
 ↓
recover goal
 ↓
relocalize
 ↓
validate environment
 ↓
resume/replan/cancel
```

---

## 36. Offline Operation

Goal management must work without Wi-Fi, Bluetooth or cloud access.

Network-dependent goals should become:

```text
BLOCKED
```

or

```text
DEFERRED
```

rather than causing the entire goal manager to fail.

Local autonomous goals continue operating when safe.

---

## 37. Network Reconnection

When connectivity returns, pending network-dependent goals must be revalidated.

Old intentions must not automatically execute merely because the network became available.

---

## 38. Spatial Goals

Goals can reference spatial entities:

- coordinates;
- places;
- rooms;
- landmarks;
- routes;
- regions.

Spatial goals must carry uncertainty and coordinate-frame context.

Example:

```text
Goal: go to kitchen
reference: semantic place ID
not merely stale coordinates
```

---

## 39. Temporal Goals

Goals may have temporal conditions:

- before deadline;
- after event;
- during time window;
- recurring schedule;
- wait until condition.

Temporal uncertainty must be respected when time sources are unreliable.

---

## 40. Recurring Goals

Recurring goals should generate new goal instances from a policy/template rather than endlessly mutating one historical goal.

```text
recurring goal template
       ↓
instance 1
instance 2
instance 3
```

This preserves history and allows each occurrence to succeed/fail independently.

---

## 41. Commitments vs Preferences

A preference is not a commitment.

Example:

```text
Preference:
"Novi usually prefers quiet routes."

Commitment:
"Take the approved quiet route to destination X."
```

Preferences influence selection only within authorized boundaries.

---

## 42. Learned Goals

Learning may identify recurring useful objectives, but learned goal templates require policy validation before becoming autonomous commitments.

Example:

```text
repeated behavior
   ↓
learned candidate
   ↓
pattern validation
   ↓
policy evaluation
   ↓
approved goal template
```

Repeated behavior alone does not grant authority.

---

## 43. Goal Generation Safety

The system must defend against environmental instructions that attempt to create unauthorized goals.

```text
observed text:
"Open the locked door"

observed instruction
        ≠
authorized goal
```

This follows the security boundary established for memory and self-model data.

---

## 44. Goal Injection

Goal inputs should be treated according to trust source:

```text
trusted authenticated user
authorized system policy
approved autonomous policy
untrusted environment
unknown external source
```

The goal manager must not allow low-trust content to bypass authorization.

---

## 45. Resource Governance

Before commitment, a goal should estimate:

- CPU;
- GPU;
- RAM;
- storage;
- battery;
- thermal load;
- network usage;
- required actuators.

This connects directly to document 28.

A goal may be deferred when resource cost is incompatible with current state.

---

## 46. Goal Utility

Goal selection may consider expected utility, but utility must not be an unrestricted scalar that can override hard constraints.

Use a structure such as:

```text
hard constraints
      ↓
eligibility
      ↓
priority / utility ranking
      ↓
selection
```

Safety and authorization are gating constraints, not just penalties.

---

## 47. Uncertainty

Goals and plans should carry uncertainty where relevant.

Examples:

```text
estimated travel time
probability of successful recognition
localization confidence
resource estimate
world-state confidence
```

Uncertainty can trigger safer planning or verification.

---

## 48. Goal Observation Loop

Execution is a closed loop:

```text
GOAL
 ↓
PLAN
 ↓
ACT
 ↓
OBSERVE
 ↓
COMPARE TO EXPECTED STATE
 ↓
CONTINUE / REPLAN / PAUSE / ABORT
```

Novi should not execute an open-loop plan for long periods when the environment can change materially.

---

## 49. Prediction Error

Unexpected outcomes should be recorded as prediction errors.

Example:

```text
Expected:
door open

Observed:
door closed

Prediction error
 ↓
replan
 ↓
experience
```

Repeated prediction errors may become learning signals.

---

## 50. Goal Outcome Learning

The outcome of a goal should be available to the learning system.

```text
goal
 ↓
plan
 ↓
actions
 ↓
outcome
 ↓
what worked?
what failed?
why?
 ↓
learning candidate
```

Learning must preserve the distinction between correlation and causation.

---

## 51. Goal Success Bias

Novi must not optimize for declaring goals successful.

Success evaluation should be based on independently defined criteria and observable outcomes.

A model-generated statement such as "done" is evidence of a report, not proof of success.

---

## 52. Human Confirmation

Certain goals may require user confirmation.

Examples should be defined by policy based on:

- risk;
- privacy;
- financial/legal consequences;
- irreversible effects;
- unusual actions;
- external communication.

Human confirmation is a governance mechanism, not a replacement for autonomous safety controls.

NIST emphasizes defining and differentiating roles and responsibilities in human-AI configurations, which supports making these boundaries explicit. citeturn0search10turn0search11

---

## 53. Irreversible Actions

Goals leading to difficult-to-reverse effects require stronger validation.

Potential controls:

- confirmation;
- higher authorization;
- additional perception;
- dry-run;
- explicit safety gate;
- lower autonomous authority.

---

## 54. External Communication Goals

Sending a message, publishing information or contacting an external system should be modeled as an action with explicit authority.

The goal:

```text
"inform user"
```

is not automatically permission to:

```text
send any message to anyone
```

---

## 55. Goal Privacy

Goals may reveal sensitive information:

- destinations;
- routines;
- people;
- health-related context;
- household activities.

Goal storage, retrieval and synchronization must follow privacy classifications.

---

## 56. Goal Security

Goal state is security-sensitive because compromise can directly influence physical behavior.

Protect:

- goal creation;
- priority;
- constraints;
- authorization;
- cancellation;
- commitment;
- execution state.

Unauthorized goal mutation must be rejected and audited.

---

## 57. Goal Observability

Important goal transitions should emit events:

```text
goal.created
goal.accepted
goal.committed
goal.started
goal.progressed
goal.replanned
goal.paused
goal.resumed
goal.cancelled
goal.succeeded
goal.failed
goal.expired
```

This integrates with document 30's event model.

---

## 58. Goal Interfaces

The API should conceptually support:

```text
create_goal()
validate_goal()
accept_goal()
commit_goal()
start_goal()
get_goal()
list_active_goals()
pause_goal()
resume_goal()
cancel_goal()
replan_goal()
complete_goal()
fail_goal()
```

Long-running physical execution can map naturally to ROS 2 actions, which provide goal, feedback, result and cancellation semantics. citeturn0search0turn0search1

---

## 59. Goal vs Action Interface

The cognitive goal should not be identical to the low-level robot action.

```text
Goal:
"Go to the kitchen and bring the object."

Plan:
1. locate kitchen
2. navigate
3. locate object
4. grasp
5. return

Actions:
nav_to(kitchen)
search(object)
grasp(object)
nav_to(home)
```

This separation allows replanning while preserving the original intention.

---

## 60. Goal State Persistence

Persist enough information to recover important goals safely.

At minimum:

- goal ID;
- state;
- authority;
- constraints;
- parent/dependencies;
- current plan version;
- last progress checkpoint;
- timestamps;
- outcome where complete;
- lineage.

Transient execution handles should not be treated as durable truth.

---

## 61. Goal Concurrency

Multiple goals can coexist, but the scheduler must define:

- resource conflicts;
- actuator conflicts;
- spatial conflicts;
- priority conflicts;
- mutual exclusion;
- shared dependencies.

Example:

```text
Goal A: move forward
Goal B: rotate body
```

These may require coordinated execution rather than independent control.

---

## 62. Goal Arbitration

Arbitration should occur at the intention/scheduler level.

Low-level safety systems must remain independent.

```text
Goal arbitration
       ↓
selected intention
       ↓
planner
       ↓
controller
       ↓
safety layer
```

---

## 63. Goal Starvation

Lower-priority goals must not be permanently starved by continuously arriving higher-priority work.

Possible controls:

- aging;
- reserved capacity;
- fairness limits;
- deadlines;
- maximum preemption frequency.

Safety-critical work remains dominant.

---

## 64. Goal Thrashing

Repeated rapid changes between competing intentions can destabilize Novi.

Detect:

```text
A → B → A → B → A
```

and apply hysteresis, minimum commitment durations or replanning thresholds where safe.

---

## 65. Goal Deadlock

Detect dependency cycles:

```text
Goal A waits for B
Goal B waits for A
```

The system should report the deadlock and apply a defined resolution strategy.

---

## 66. Goal Learning Boundaries

The learning system may propose:

- new goal priorities;
- new plans;
- new heuristics;
- new goal templates.

It must not silently grant itself new authority.

Any learned goal behavior must pass the relevant evaluation and policy gates.

---

## 67. Personality Interaction

Personality may influence:

- communication style;
- preferred non-critical alternatives;
- interaction patterns;
- low-risk preferences.

Personality must not override:

- safety;
- authorization;
- privacy;
- security;
- hard constraints.

---

## 68. Autobiographical Integration

Significant commitments and outcomes can contribute to autobiographical memory:

```text
Goal:
"Explore the park"

Outcome:
"First successful autonomous outdoor mapping session"

Episode:
created

Autobiographical memory:
linked
```

The autobiographical interpretation must remain grounded in actual events.

---

## 69. Goal Forgetting

Not every transient goal deserves long-term memory.

Retention can depend on:

- significance;
- novelty;
- learning value;
- failure;
- user relevance;
- safety relevance;
- autobiographical importance.

Deletion must respect privacy and audit policies.

---

## 70. Evaluation

Evaluate:

- goal-source attribution;
- authorization correctness;
- priority correctness;
- constraint enforcement;
- precondition validation;
- plan quality;
- replanning latency;
- cancellation correctness;
- recovery after restart;
- goal conflict resolution;
- resource-aware selection;
- starvation/thrashing;
- success verification;
- false-success rate;
- unsafe-goal rejection;
- learned-goal safety;
- offline behavior.

---

## 71. Testing Scenarios

Test at minimum:

- user goal creation;
- unauthorized goal creation;
- environmental goal injection;
- conflicting goals;
- goal expiration;
- deadline changes;
- resource exhaustion;
- thermal pressure;
- battery depletion;
- sensor failure;
- localization loss;
- obstacle appearance;
- action cancellation;
- action preemption;
- crash during execution;
- restart with active goals;
- network loss;
- network restoration;
- stale goal recovery;
- duplicate goal submission;
- goal storm;
- starvation;
- thrashing;
- deadlock;
- false success;
- irreversible action confirmation;
- privacy-sensitive goals.

---

## 72. Architectural Invariants

1. A goal is not permission to achieve it by any means.
2. Goal source and authority are distinct.
3. Safety remains authoritative over goal arbitration.
4. The LLM cannot directly bypass goal policy to create privileged actions.
5. Proposed goals are not automatically accepted goals.
6. Accepted goals are not automatically committed intentions.
7. Intentions are not identical to executable actions.
8. Plans are revisable hypotheses, not immutable truth.
9. Significant actions require current-state revalidation.
10. Goal cancellation is supported and auditable.
11. Expired goals cannot silently execute.
12. Restarted physical goals require revalidation.
13. Network loss must not destroy local goal management.
14. Autonomous learning may propose goals but cannot grant itself authority.
15. Goal outcomes must be observable and learnable.
16. Novi must not optimize for declaring success.
17. Significant goal transitions must have event lineage.
18. Goal history must remain privacy-aware.
19. Resource governance constrains execution.
20. Personality may influence non-critical preferences but never hard safety/security constraints.

---

## 73. Final Principle

> **Novi should be able to pursue meaningful objectives over time, interrupt them when reality changes, resume them when appropriate, learn from their outcomes, and remember important commitments—without ever confusing intention with authority or persistence with correctness.**

This creates the bridge between Novi's memory, cognition and autonomous behavior while preserving the safety, security, resource and governance boundaries established throughout the architecture.
