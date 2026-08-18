# 20 — Safety and Authorization Architecture

**Status:** P0 normative system architecture  
**Owner:** System Architecture / Safety boundary  
**Scope:** all consequential Novi actions, from cognitive proposals to physical execution  
**Depends on:** `16_CANONICAL_SYSTEM_CONTRACTS.md`, `17_CONTRACT_IMPLEMENTATION_AND_SCHEMA_STANDARD.md`, `19_TIME_SYNCHRONIZATION_AND_CLOCK_SEMANTICS.md`, Autonomy architecture, Brain runtime, Hardware/Control architecture

---

## 1. Purpose

This document defines the system-wide safety and authorization boundary for Novi.

The central rule is:

> **Intelligence may propose. Autonomy may pursue. Safety may constrain or deny. Controllers may execute only permitted commands.**

Safety is not an LLM prompt, a personality trait, a confidence score, or a post-hoc monitor.

It is an independent control boundary between decision-making and physical actuation.

---

## 2. Safety hierarchy

```text
PERCEPTION / SENSORS
        ↓
COGNITION
        ↓
AUTONOMY
        ↓
ACTION PROPOSAL
        ↓
SAFETY / AUTHORIZATION
        ↓
CONTROLLER
        ↓
ACTUATOR
        ↓
PHYSICAL WORLD
        ↓
OBSERVED OUTCOME
```

Any layer above Safety can request an action, but none can bypass Safety for consequential physical behavior.

---

## 3. Safety authority

Safety authority is deliberately outside probabilistic cognition.

The following must never be authoritative safety mechanisms by themselves:

- LLM output;
- VLM output;
- neural-network confidence;
- natural-language instruction;
- personality policy;
- learned reward;
- planner intent;
- memory content;
- a boolean embedded in an arbitrary message.

These may provide evidence or proposals to safety logic, but safety-critical authorization must be enforced by deterministic, validated mechanisms wherever practical.

---

## 4. Safety domains

Novi safety must cover at least:

### Physical safety

- collision avoidance;
- speed/acceleration limits;
- force/torque limits where applicable;
- workspace limits;
- forbidden regions;
- safe stopping;
- actuator faults;
- emergency stop.

### Software safety

- stale commands;
- malformed commands;
- invalid contract versions;
- watchdog failures;
- process crashes;
- timing violations;
- resource exhaustion;
- unsafe configuration;
- invalid state transitions.

### Perception safety

- sensor loss;
- degraded perception;
- contradictory observations;
- invalid localization;
- unknown obstacle state;
- insufficient confidence for required operation.

### Behavioral safety

- prohibited actions;
- authorization scope;
- user/environment constraints;
- task boundaries;
- escalation requirements;
- safe behavior under uncertainty.

### Security safety

- unauthorized commands;
- compromised components;
- credential misuse;
- malicious input;
- unsafe remote control;
- integrity failures.

---

## 5. Action classes

Every consequential action must have a declared safety class.

Example classes:

```text
S0 — informational / no physical consequence
S1 — internal computational action
S2 — reversible low-energy physical action
S3 — consequential physical action
S4 — high-risk / restricted action
```

The exact classification table must be defined by hardware and risk analysis before real-world deployment.

Higher classes require stronger authorization and validation.

---

## 6. Action proposal

Cognition and Autonomy may produce an `ActionProposal`.

An action proposal must include enough information for safety evaluation, including:

- action identity;
- source component;
- initiating goal/task;
- target/entity where applicable;
- intended effect;
- required capabilities;
- expected duration;
- validity window;
- resource requirements;
- confidence/uncertainty where relevant;
- contract version;
- correlation/causation identifiers.

The proposal is **not an authorization**.

---

## 7. Authorization decision

Safety evaluates the proposal against authoritative constraints.

The result must be an explicit decision:

```text
ALLOW
ALLOW_WITH_CONSTRAINTS
DEFER
DENY
EMERGENCY_STOP
```

A missing decision is not permission.

Silence, timeout or component failure must resolve according to the action's declared fail-safe policy and never implicitly mean `ALLOW`.

---

## 8. Safety decision inputs

Safety may consider:

- robot state;
- actuator state;
- sensor health;
- localization validity;
- obstacle state;
- current speed;
- workspace restrictions;
- environmental hazards;
- action class;
- authorization scope;
- time validity;
- system mode;
- battery/thermal constraints;
- hardware limits;
- fault state;
- active emergency stop;
- policy constraints.

Safety must prefer authoritative state over model-generated assertions.

---

## 9. Hard constraints vs soft preferences

Safety constraints must be separated from ordinary optimization preferences.

```text
HARD CONSTRAINT
  robot must not exceed physical limit

SOFT PREFERENCE
  robot prefers slower movement near people
```

A soft preference may be optimized.

A hard constraint cannot be traded away to improve task success, user satisfaction, model reward or conversational quality.

---

## 10. Emergency stop

Emergency stop is an independent safety path.

It must not depend on:

- an LLM response;
- network availability;
- successful memory retrieval;
- planner completion;
- normal autonomy execution.

The physical implementation and exact electrical architecture belong to the Hardware/Safety design and must comply with the selected robot platform and applicable regulations.

Software must recognize emergency-stop state and prevent ordinary autonomy from resuming motion until the required recovery conditions are satisfied.

---

## 11. Watchdogs

Safety-critical command paths require watchdog behavior appropriate to their risk class.

A watchdog should detect conditions such as:

- command stream stopped;
- controller heartbeat lost;
- safety process unavailable;
- stale command;
- missed deadline;
- invalid state transition;
- communication failure.

The safe response must be explicitly defined per action/controller.

For physical motion, a stale command must never remain valid indefinitely.

---

## 12. Command validity

Every consequential command must have a bounded validity period where appropriate.

```text
command issued
     ↓
valid_until
     ↓
if current_time > valid_until
     ↓
REJECT / SAFE STOP
```

Time semantics must follow `19_TIME_SYNCHRONIZATION_AND_CLOCK_SEMANTICS.md`.

A command with an unknown or invalid timestamp must be rejected whenever timing is safety-critical.

---

## 13. Capability safety

Authorization requires capability validity.

The system must distinguish:

```text
capability exists
capability installed
capability validated
capability available
capability safe_now
capability authorized_now
```

An action cannot be authorized merely because a model claims the robot can perform it.

---

## 14. Uncertainty handling

Uncertainty must be explicit.

Examples:

```text
localization uncertain
obstacle state unknown
sensor degraded
object identity uncertain
human intent uncertain
```

The correct response depends on risk class.

For high-risk actions, insufficient evidence should normally cause `DEFER`, `DENY`, or a transition to a safer state rather than optimistic execution.

---

## 15. Human presence

When humans are present, safety requirements must be stricter where the hardware/risk analysis requires it.

Novi must not infer permission to physically interact with a person merely from:

- conversation;
- visual recognition;
- inferred intent;
- previous permission;
- memory.

Physical interaction requires explicit capability, authorization and safety validation appropriate to the action.

---

## 16. Human commands

Natural-language commands are inputs to cognition/autonomy, not direct actuator commands.

```text
Human:
"Move over there."
        ↓
Language understanding
        ↓
Goal / Action Proposal
        ↓
Safety evaluation
        ↓
Controller command
```

Ambiguous language must not bypass safety checks.

---

## 17. Policy hierarchy

The system should apply constraints in a deterministic precedence order.

A baseline ordering is:

```text
Emergency stop
      ↓
Hardware physical limits
      ↓
Safety constraints
      ↓
Security / authorization constraints
      ↓
Operational restrictions
      ↓
Task constraints
      ↓
User preferences
      ↓
Optimization preferences
```

A lower-level preference cannot override a higher-level safety constraint.

---

## 18. Safety modes

Novi should expose explicit operational safety modes, such as:

```text
SAFE_STOP
INITIALIZING
LIMITED
NORMAL
DEGRADED
RECOVERY
MAINTENANCE
EMERGENCY
```

Exact modes and transition conditions belong to the hardware/system safety design.

Mode transitions must be explicit, observable and auditable.

---

## 19. Degraded operation

When safety-relevant capability degrades, Novi must not silently continue with the same authority.

Example:

```text
localization lost
      ↓
normal navigation capability revoked
      ↓
restricted behavior
      ↓
relocalization / recovery
```

Another example:

```text
obstacle sensor degraded
      ↓
movement capability restricted
      ↓
safe stop or reduced-risk mode
```

The permitted degraded behavior must be validated before physical deployment.

---

## 20. Safety and neural networks

Neural networks may participate in safety-related perception or prediction, but their output must be treated according to validated risk architecture.

For example:

```text
NN obstacle detector
        ↓
obstacle evidence
        ↓
validated safety fusion / conservative policy
        ↓
authorization
```

Do not implement:

```text
NN says safe = true
        ↓
move robot
```

without an independently justified safety architecture.

---

## 21. Safety and NVIDIA Physical AI

NVIDIA's current robotics stack demonstrates the architectural pattern of keeping learned policy execution behind safety controls. NVIDIA's Isaac ROS Deploy documentation describes a safety controller around runtime policy output and includes controllers such as `SafetyController`, `FreezeController`, `DisableController`, and `ImpedanceController`. citeturn0search4

Isaac Sim also exposes ROS 2 controller integration where commands flow through controllers before reaching simulated articulation. citeturn0search0turn0search3

These technologies are implementation candidates, not the definition of Novi's safety authority.

---

## 22. Simulation safety validation

Before real hardware:

```text
software-in-the-loop
        ↓
simulation safety tests
        ↓
hardware-in-the-loop where justified
        ↓
controlled physical tests
        ↓
progressive capability enablement
```

NVIDIA's Physical AI learning material explicitly supports SIL/HIL workflows and validation from simulation toward Jetson hardware. citeturn0search2

Novi must never treat simulation success as proof that an unrestricted physical action is safe.

---

## 23. Progressive enablement

Physical capabilities should be enabled gradually.

Example:

```text
motion disabled
    ↓
telemetry only
    ↓
command validation
    ↓
zero-output controller
    ↓
very low speed
    ↓
restricted workspace
    ↓
supervised operation
    ↓
validated autonomous operation
```

NVIDIA's Isaac ROS Deploy guidance similarly recommends starting policy blending at zero and increasing gradually, while testing policies in simulation before real deployment. citeturn0search4

---

## 24. Safety telemetry

Every consequential authorization should be auditable.

Record at minimum:

```text
action_proposal_id
action_class
authorization_decision
constraints_applied
safety_mode
robot_state_reference
sensor_state_reference
policy_version
controller_version
time_validity
reason_code
correlation_id
causation_id
```

Safety logs must be append-only or otherwise integrity-protected according to the system's security requirements.

---

## 25. Failure semantics

Safety components must fail predictably.

Examples:

```text
safety service unavailable
      ↓
no new consequential authorization
      ↓
existing actions follow explicit safe-stop policy
```

```text
controller heartbeat lost
      ↓
watchdog
      ↓
safe controller state
```

```text
invalid action contract
      ↓
reject
      ↓
record reason
```

The exact safe state is action/hardware dependent and must be specified by the corresponding controller safety design.

---

## 26. Separation of concerns

### Cognition

Interprets the world and reasons about possible actions.

### Autonomy

Selects and pursues goals and behavioral plans.

### Safety

Evaluates whether proposed consequential behavior is permitted under current constraints.

### Brain/runtime

Provides execution, scheduling, health and communication infrastructure.

### Hardware/control

Enforces physical limits and executes authorized commands.

No layer should silently assume another layer's authority.

---

## 27. Safety contract mapping

The canonical contracts in `16_CANONICAL_SYSTEM_CONTRACTS.md` must be used consistently:

```text
ActionProposal
      ↓
AuthorizationDecision
      ↓
SafetyDecision
      ↓
ActionExecution
      ↓
ActionOutcome
```

The exact contract schemas are governed by `17_CONTRACT_IMPLEMENTATION_AND_SCHEMA_STANDARD.md`.

---

## 28. Testing requirements

Minimum safety test classes:

### Command tests

- stale command rejection;
- malformed command rejection;
- unknown capability rejection;
- expired authorization rejection;
- duplicate-command handling.

### Watchdog tests

- heartbeat loss;
- process crash;
- network loss;
- scheduler starvation;
- missed deadline.

### Sensor tests

- sensor disconnect;
- contradictory sensors;
- stale sensor data;
- invalid localization;
- degraded obstacle detection.

### Safety tests

- emergency stop;
- safe-stop transition;
- recovery gating;
- hard-limit enforcement;
- policy conflict resolution;
- authorization expiry.

### AI tests

- adversarial language requests;
- hallucinated capability claims;
- incorrect model confidence;
- perception false positives/negatives;
- unsafe learned policy output;
- model/runtime version mismatch.

### Integration tests

- Cognition → Autonomy → Safety → Controller;
- simulation → ROS 2 → controller;
- restart/recovery;
- degraded mode;
- audit trace completeness.

---

## 29. Required acceptance scenarios

The architecture is not considered validated until at least these scenarios work:

1. **Normal movement:** authorized proposal reaches controller and produces observed motion.
2. **Stale command:** expired command is rejected.
3. **Obstacle:** safety blocks or constrains movement.
4. **Emergency stop:** physical/safety stop prevents ordinary movement and blocks unauthorized resume.
5. **Localization loss:** navigation authority is revoked or restricted.
6. **Sensor failure:** dependent capabilities degrade explicitly.
7. **LLM unsafe request:** language model cannot bypass safety.
8. **Capability hallucination:** model cannot authorize an unsupported action.
9. **Controller failure:** watchdog produces defined safe state.
10. **Network loss:** local safety remains effective without cloud/network dependence.
11. **Version mismatch:** incompatible action contract is rejected.
12. **Recovery:** Novi cannot resume consequential behavior until recovery conditions are satisfied.

---

## 30. Definition of done

Safety architecture is complete when:

- every consequential action has a defined safety class;
- action proposals are distinct from authorization;
- safety authority is independent of probabilistic cognition;
- emergency stop is independently implemented;
- command validity and watchdog semantics are defined;
- hard constraints cannot be traded away;
- capability validity is checked before authorization;
- uncertainty has explicit safety behavior;
- degraded modes are defined;
- human commands cannot bypass safety;
- all safety decisions are traceable;
- simulation and HIL validation paths exist;
- progressive physical enablement is defined;
- controller/hardware limits remain authoritative;
- failure behavior is deterministic and tested.

## 31. Architectural invariant

> **No thought, prediction, memory, language-model output, learned policy, goal, plan or user request is itself permission to move the robot.**

Only an explicitly authorized and safety-valid command may cross the boundary into physical execution.
