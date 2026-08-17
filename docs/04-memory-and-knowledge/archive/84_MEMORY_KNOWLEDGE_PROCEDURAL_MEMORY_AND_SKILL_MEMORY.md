# 84 — Memory Knowledge Procedural Memory and Skill Memory

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi stores, retrieves, evaluates, adapts and improves knowledge about **how to perform tasks**: procedures, skills, routines, action sequences, prerequisites, expected outcomes, failure modes and learned adaptations.

## Core Principle

> **Knowing how to perform an action is not the same as being authorized or safe to perform it.**

Procedural memory informs planning and execution but never bypasses safety, authorization, capability, or real-time control boundaries.

## 1. Position in Architecture

```text
EPISODES / OBSERVATIONS
        ↓
SKILL / PROCEDURE LEARNING
        ↓
PROCEDURAL MEMORY
        ↓
RETRIEVAL
        ↓
WORKING MEMORY
        ↓
PLANNING
        ↓
AUTHORIZATION + SAFETY
        ↓
EXECUTION
        ↓
OUTCOME
        ↓
SKILL UPDATE
```

## 2. Procedure vs Skill

A **procedure** is an explicit ordered method for achieving an outcome.

A **skill** is a reusable capability for performing a class of actions, potentially with adaptation.

```text
Procedure: "open this specific cabinet"
Skill: "open a compatible cabinet"
```

## 3. Skill Components

A skill can include:

- name;
- purpose;
- prerequisites;
- required capabilities;
- inputs;
- outputs;
- action sequence;
- parameters;
- constraints;
- expected outcomes;
- failure modes;
- recovery strategies;
- evidence;
- confidence/status;
- version;
- provenance.

## 4. Primitive Actions

Complex skills should decompose into primitives:

```text
NAVIGATE
ALIGN
GRASP
MOVE
RELEASE
PRESS
WAIT
OBSERVE
```

Primitive actions must map to actual actuator capabilities and safety constraints.

## 5. Preconditions

Every executable procedure should identify relevant preconditions:

```text
REQUIRED OBJECT
REQUIRED LOCATION
REQUIRED CAPABILITY
REQUIRED ENVIRONMENT
REQUIRED AUTHORIZATION
REQUIRED SAFETY STATE
```

Failure to establish a required precondition should prevent execution or trigger a safe recovery path.

## 6. Postconditions

A successful procedure should define observable postconditions.

```text
ACTION
 ↓
OBSERVED POSTCONDITION
```

Expected completion must not be assumed merely because commands were issued.

## 7. Preconditions vs Assumptions

```text
VERIFIED PRECONDITION
 ≠
UNVERIFIED ASSUMPTION
```

Important assumptions must be explicitly represented.

## 8. Skill Preconditions Can Be Dynamic

A skill may be valid only under certain conditions:

- battery level;
- temperature;
- payload;
- surface type;
- lighting;
- network availability;
- localization quality;
- obstacle state.

## 9. Capability Model

Novi must distinguish:

```text
KNOWS HOW
HAS CAPABILITY
CURRENTLY CAPABLE
AUTHORIZED
SAFE TO EXECUTE
```

These are independent properties.

## 10. Skill Applicability

A skill should declare where and when it applies.

```text
skill
 ↓
context compatibility
 ↓
applicable / not applicable / uncertain
```

## 11. Parameterization

Procedures should avoid hardcoding values where the same skill can adapt parameters.

Example:

```text
navigate(destination, speed_limit, obstacle_policy)
```

Parameters must remain bounded by safety and authorization constraints.

## 12. Skill Variants

A single capability may have variants:

```text
OPEN_DOOR
 ├── handle
 ├── push
 └── pull
```

Variant selection should use current observations and validated applicability.

## 13. Hierarchical Skills

Skills can compose:

```text
MAKE_COFFEE
 ├── NAVIGATE_TO_KITCHEN
 ├── LOCATE_CUP
 ├── PICK_UP_CUP
 ├── FILL_CUP
 └── PLACE_CUP
```

Each child skill retains its own preconditions, safety constraints and outcome validation.

## 14. Skill Dependencies

A skill may depend on other skills:

```text
Skill A
 ↓ requires
Skill B
```

Dependency changes should trigger applicability re-evaluation.

## 15. Skill Provenance

Every important procedural capability should retain:

- source episode(s);
- author/user instruction if applicable;
- model-generated derivation;
- external documentation where used;
- validation history;
- version history.

## 16. Explicit User Instruction

A user can explicitly teach a procedure.

The resulting procedure should record that it was user-provided and remain subject to safety/capability validation.

## 17. Demonstration Learning

Novi may infer a procedure from observed demonstrations:

```text
DEMONSTRATION
 ↓
ACTION SEGMENTATION
 ↓
PROCEDURE CANDIDATE
 ↓
VALIDATION
 ↓
SKILL
```

Observation of a demonstration does not automatically authorize Novi to repeat every action.

## 18. Learning from Episodes

Repeated successful episodes can support skill refinement:

```text
Episode 1
Episode 2
Episode 3
    ↓
procedure pattern
```

The source episodes remain distinct.

## 19. Skill Confidence

Skill confidence should consider:

- successful trials;
- independent evidence;
- environment diversity;
- failure rate;
- recent performance;
- sensor quality;
- hardware/software version;
- safety margin.

A single score should not hide these dimensions.

## 20. Skill Status

Possible states:

```text
CANDIDATE
VALIDATED
ACTIVE
DEGRADED
CONTESTED
SUSPENDED
DEPRECATED
RETIRED
```

## 21. Skill Validation

Before promotion, evaluate:

- repeatability;
- outcome correctness;
- safety;
- capability compatibility;
- environmental robustness;
- recovery behavior.

## 22. Simulation Validation

Where practical, skills may be tested in simulation before physical execution.

Simulation evidence must remain distinct from physical-world evidence.

## 23. Simulation ≠ Execution

```text
SIMULATED SUCCESS
 ≠
PHYSICAL SUCCESS
```

Physical execution requires its own validation.

## 24. Safe Skill Execution

Execution pipeline:

```text
RETRIEVE SKILL
      ↓
CHECK APPLICABILITY
      ↓
CHECK CAPABILITY
      ↓
CHECK AUTHORIZATION
      ↓
CHECK SAFETY
      ↓
PLAN
      ↓
EXECUTE
      ↓
OBSERVE
      ↓
VALIDATE OUTCOME
```

## 25. Safety Overrides

No procedural memory may override:

- collision avoidance;
- emergency stop;
- thermal protection;
- battery protection;
- actuator limits;
- human-presence safety rules;
- authorization gates.

## 26. Action-Level Validation

For physical actions, validate continuously where required rather than only before the first step.

```text
STEP
 ↓
OBSERVE
 ↓
SAFETY CHECK
 ↓
NEXT STEP
```

## 27. Interruptibility

Skills should support safe interruption where practical.

Examples:

```text
STOP
PAUSE
SAFE RETREAT
RETURN TO SAFE STATE
```

## 28. Recovery Procedures

A skill should define known recovery paths for common failures.

```text
FAILURE
 ↓
DIAGNOSE
 ↓
RECOVERY
 ↓
RETRY / ABORT / ESCALATE
```

Retries must be bounded.

## 29. Failure Memory

Failures are valuable procedural evidence.

Record:

- failed step;
- context;
- observed cause/hypothesis;
- outcome;
- recovery result.

Failure must not automatically mean the entire skill is invalid.

## 30. Adaptive Procedures

Novi may adapt parameters or sequences when conditions differ.

Adaptation must remain within validated safety and capability boundaries.

## 31. Learned Adaptation vs Novel Behavior

```text
KNOWN SKILL + SAFE PARAMETER ADAPTATION
        ≠
UNVALIDATED NOVEL ACTION SEQUENCE
```

Novel behavior requires stronger controls.

## 32. Skill Generalization

A procedure learned in one environment may not generalize to another.

```text
HOUSE A
 ≠
HOUSE B
```

Generalization requires evidence across relevant environments.

## 33. Contextual Skill Variants

The same task can have context-specific variants:

```text
OPEN_DOOR
 ├── known handle
 ├── unknown handle
 └── powered door
```

The world model determines which variant is applicable.

## 34. Spatial Skills

Novi may learn:

- routes;
- docking;
- room traversal;
- landmark approach;
- object-location procedures.

Spatial skills must account for map and localization uncertainty.

## 35. Outdoor Skills

Outdoor navigation skills should integrate:

```text
GNSS
LOCALIZATION
MAP
OBSTACLE PERCEPTION
VISITED HISTORY
CURRENT WEATHER/ENVIRONMENT WHEN AVAILABLE
```

Historical routes cannot override current obstacle or safety information.

## 36. Manipulation Skills

Manipulation procedures can include:

- grasp selection;
- approach angle;
- force limits;
- release conditions;
- verification.

Current perception and force/torque safety controls remain authoritative.

## 37. Communication Skills

Procedural memory may store workflows for interacting with software, devices or users.

External communication remains subject to authorization and privacy policy.

## 38. Tool-Use Skills

Tool procedures should record:

- tool identity;
- required permissions;
- input schema;
- expected output;
- failure handling;
- side effects.

A stored tool procedure must never bypass current permission checks.

## 39. Skill Side Effects

Every procedure should identify known side effects where possible.

```text
ACTION
 ↓
EXPECTED SIDE EFFECTS
 ↓
OBSERVE ACTUAL SIDE EFFECTS
```

Unexpected side effects should trigger evaluation.

## 40. Idempotency

Where relevant, procedures should identify whether repeating an action is safe.

```text
IDEMPOTENT
NON-IDEMPOTENT
UNKNOWN
```

Unknown repeatability should be treated conservatively for consequential actions.

## 41. Transactional Procedures

Multi-step procedures with consequential side effects should define checkpoints and recovery/rollback where physically possible.

Physical actions are not always reversible; the procedure must represent that limitation.

## 42. Skill Versioning

Skills should be versioned.

```text
SKILL v1
 ↓
SKILL v2
```

Changes should record why the skill changed and what evidence triggered the revision.

## 43. Hardware Compatibility

Skills should declare relevant hardware dependencies:

```text
camera model
actuator type
sensor availability
payload capacity
compute capability
```

Hardware replacement may require skill revalidation.

## 44. Software/Model Compatibility

Skills can depend on perception/model versions.

Model upgrades may alter action preconditions or confidence and should trigger validation when necessary.

## 45. Environment Drift

If the environment changes materially, skill validity should be reevaluated.

Examples:

- furniture moved;
- door hardware replaced;
- route blocked;
- object shape changed.

## 46. Skill Deprecation

A skill should be deprecated when:

- safer method exists;
- hardware is incompatible;
- environment changed;
- failure rate becomes unacceptable;
- authorization changes;
- evidence invalidates assumptions.

## 47. Skill Rollback

A revised skill can be rolled back when a newer version performs worse, provided the older version remains safe and compatible.

## 48. Skill Retrieval

Skill retrieval can use:

- task intent;
- world-model context;
- required capabilities;
- environment;
- previous success;
- failure history.

Retrieved skills remain candidates until execution checks pass.

## 49. Skill Ranking

Ranking may consider:

- applicability;
- validated success;
- safety margin;
- recency;
- environmental similarity;
- resource cost;
- failure history.

Safety and authorization remain hard gates, not ranking preferences.

## 50. Skill Composition

Multiple skills can form a task plan.

Composition must verify compatibility between:

- preconditions;
- postconditions;
- resources;
- timing;
- safety constraints;
- side effects.

## 51. Skill Conflict

Two skills may prescribe incompatible actions.

The planner must detect conflicts rather than arbitrarily executing both.

## 52. Skill Learning Boundaries

Novi should not learn unsafe behavior merely because it produced a successful outcome once.

Successful outcome is evidence, not automatic approval.

## 53. Human Approval

High-risk or novel skills may require explicit human approval before execution or promotion.

Approval should be scoped to the exact action/context where possible.

## 54. Authorization

Authorization is evaluated at execution time.

```text
stored permission
 ≠
current permission
```

Revoked permissions must prevent execution even if the skill remains in memory.

## 55. Privacy

Procedures can encode sensitive personal routines.

Example:

```text
"At 22:00, perform action X for person Y"
```

Skill memory must inherit appropriate privacy and access controls.

## 56. Distributed Skill Sharing

Skills shared between Novi instances must include:

- source;
- version;
- hardware compatibility;
- validation status;
- trust context;
- safety metadata.

Remote skills are not automatically trusted.

## 57. Offline Skills

Core local skills must remain usable offline where their dependencies are local.

Network-dependent skills must explicitly declare the dependency.

## 58. Observability

Track appropriate metrics:

- skill selection;
- execution success/failure;
- precondition failures;
- safety aborts;
- recovery attempts;
- execution latency;
- resource use;
- version performance;
- human interventions.

Telemetry remains subject to privacy and retention policy.

## 59. Testing

Test:

- precondition validation;
- postcondition validation;
- skill retrieval;
- skill ranking;
- composition;
- conflicting skills;
- parameter bounds;
- safety interruption;
- authorization revocation;
- hardware changes;
- model upgrades;
- environment drift;
- simulation/physical separation;
- failure recovery;
- retry limits;
- idempotency;
- side effects;
- distributed skill sharing;
- malicious skill injection;
- prompt injection in procedural content;
- offline execution;
- skill rollback;
- privacy leakage;
- human approval gates.

## 60. Architectural Invariants

1. Procedural knowledge describes how; it does not grant permission to act.
2. Knowing a skill is distinct from capability, authorization and safety.
3. Preconditions must be validated before consequential execution.
4. Important postconditions must be observed or otherwise validated.
5. Simulation success is not physical success.
6. Current safety controls override procedural memory.
7. Action execution remains interruptible where practical.
8. Retries are bounded and context-aware.
9. Failures remain useful evidence without automatically invalidating a skill.
10. Novel behavior is distinct from validated adaptation.
11. Skills remain scoped to their environment and hardware compatibility.
12. Skill versions and validation history remain traceable.
13. Revoked authorization cannot be bypassed by stored procedures.
14. Remote skills are not automatically trusted.
15. Stored procedural content is data, not execution authority.
16. High-risk skills can require human approval.
17. Physical-world outcomes must not be inferred solely from issued commands.
18. Skill updates preserve provenance and revision lineage.
19. Privacy controls apply to procedural knowledge and learned routines.
20. Safety-critical control remains outside ordinary semantic memory.

## 61. Final Principle

> **Novi should remember how to do things as reusable, evidence-backed procedures and skills, while continuously checking whether the skill is applicable, the capability exists, the action is authorized, and the current physical situation makes execution safe.**

Procedural memory therefore turns experience into reusable capability without allowing memory itself to become an uncontrolled action mechanism.