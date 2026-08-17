# 16 — Autonomy Architecture Boundary Audit

**Status:** P0 — CRITICAL / CANONICAL BOUNDARY DECISION

**Scope:** `02-autonomy` against `02-novi-brain`, `03-cognition`, `04-memory-and-knowledge`, policy/safety, and hardware/control.

**Purpose:** prevent the Autonomy domain from becoming a duplicate Brain, Cognition, Memory, or Safety system.

---

## 1. Executive decision

Autonomy is the **behavioral agency and goal-pursuit layer** of Novi.

It answers:

> Given what Novi currently understands, what should Novi pursue, whether should it act, how should the task be managed, and what should happen next?

Autonomy does **not** own the underlying facts, semantic world representation, long-term memory, model internals, physical control, or final safety authority.

The canonical separation is:

```text
Brain
  coordinates and executes the embodied runtime

Cognition
  understands, reasons, predicts and represents current semantic state

Memory / Knowledge
  remembers, retrieves and maintains durable knowledge

Autonomy
  chooses and pursues behavioral goals and tasks

Policy / Safety
  permits, constrains or denies consequential behavior

Hardware / Controllers
  execute physical control
```

> **Brain coordinates. Cognition understands. Memory remembers and knows. Autonomy chooses and pursues. Policy permits or denies. Hardware executes.**

---

## 2. What Autonomy actually owns

Autonomy owns the **behavioral control problem above cognition and below policy**.

Canonical responsibilities:

- continuous behavioral loop orchestration;
- attention-to-behavior decisions;
- goal creation and lifecycle;
- goal prioritization;
- goal conflict handling;
- curiosity and information-seeking decisions;
- high-level behavioral planning;
- task sequencing;
- deciding whether to pursue a cognitive proposal;
- selecting among already-authorized capabilities at the behavioral level;
- action request lifecycle;
- interruption and replanning;
- outcome-driven task management;
- autonomous state machine;
- resource-aware behavioral adaptation;
- controlled learning triggers;
- autonomy-specific audit/telemetry.

Autonomy therefore owns **behavioral intent and pursuit**, not semantic truth or physical execution.

---

## 3. What Autonomy does NOT own

### Brain owns

- process/runtime lifecycle;
- scheduling infrastructure;
- model execution runtime;
- perception pipeline runtime;
- sensor adapters;
- embodied state integration;
- runtime health and degradation infrastructure;
- execution-level model routing;
- system resource telemetry.

### Cognition owns

- current semantic world model;
- situation interpretation;
- identity and social cognition;
- temporal/causal reasoning;
- prediction/expectation semantics;
- cognitive reasoning;
- cognitive model selection;
- semantic interpretation of multimodal evidence.

### Memory / Knowledge owns

- durable memory;
- knowledge persistence;
- retrieval implementation;
- consolidation;
- provenance of stored knowledge;
- knowledge graph;
- historical spatial/temporal/causal records;
- skill/competence history.

### Policy / Safety owns

- final authorization;
- immutable constraints;
- emergency stop behavior;
- physical safety limits;
- protected security rules;
- risk policy;
- mandatory confirmation requirements.

### Hardware / Controllers own

- actuator control;
- motor control;
- low-level stabilization;
- hardware safety interlocks;
- physical execution truth.

---

## 4. Canonical ownership matrix

| Capability | Canonical owner | Autonomy role |
|---|---|---|
| Runtime lifecycle | Brain | consumes health/state |
| Runtime scheduling | Brain | submits behavioral work |
| Sensor drivers | Brain/hardware | consumes observations |
| Perception execution | Brain | consumes interpreted outputs |
| Current body state | Brain + hardware authority | consumes |
| Semantic world model | Cognition | consumes |
| Situation model | Cognition | consumes |
| Identity/social interpretation | Cognition | consumes |
| Temporal/causal reasoning | Cognition | consumes |
| Prediction semantics | Cognition | uses predictions for behavior |
| Long-term memory | Memory | requests context |
| Knowledge | Memory/Knowledge | requests facts/evidence |
| Memory retrieval | Memory | submits semantic/context requests |
| Cognitive reasoning | Cognition | consumes candidate interpretations/plans |
| Cognitive model selection | Cognition | consumes result |
| Runtime model routing | Brain | requests execution through contract |
| Attention semantics | Cognition + Autonomy boundary | **Autonomy owns behavioral attention decision** |
| Goal creation | **Autonomy** | owner |
| Goal prioritization | **Autonomy** | owner, constrained by policy/user priority |
| Curiosity goals | **Autonomy** | owner |
| Behavioral task lifecycle | **Autonomy** | owner |
| High-level behavioral planning | **Autonomy** | owner |
| Candidate reasoning/plan generation | Cognition | consumes/proposes |
| Plan/task pursuit | **Autonomy** | owner |
| Capability request lifecycle | **Autonomy** | owner |
| Capability implementation | Brain/robotics/system | consumer of request |
| Action authorization | Policy/Safety | cannot override |
| Motor control | Hardware/controller | cannot bypass |
| Outcome observation | Brain/Cognition/HW evidence | Autonomy evaluates for task progress |
| Goal completion | **Autonomy** | owner based on verified outcome |
| Learning trigger | **Autonomy** | decides when experience is worth learning |
| Memory admission/consolidation | Memory | owner |
| Persistent knowledge update | Memory/Knowledge | owner |
| Autonomy state machine | **Autonomy** | owner |
| Runtime service state machine | Brain/runtime | owner |
| Safety state machine | Policy/Safety | owner |
| Resource telemetry | Brain/hardware | Autonomy consumes |
| Resource-aware behavior | **Autonomy** | owner of behavioral adaptation |
| Audit of autonomous decisions | **Autonomy** | owns behavioral trace; system-wide audit is cross-domain |

---

## 5. The critical Attention boundary

The repository currently uses the word **attention** in both Cognition and Autonomy. This is valid only if the meanings are separated.

### Cognition: attentional representation

Cognition determines semantic salience and provides information such as:

- what is novel;
- what is relevant;
- what is uncertain;
- what entities matter;
- what situation is active;
- what evidence requires more processing.

### Autonomy: behavioral attention decision

Autonomy decides:

```text
Does this matter enough to change what Novi does?
```

Possible outcomes:

```text
IGNORE
OBSERVE
INTERNAL_UPDATE
REMEMBER
NONVERBAL_SIGNAL
SPEAK
ASK
PLAN
ACT
ESCALATE
```

Therefore there is **one attention concept with two explicit stages**, not two competing attention systems.

```text
Cognition
  semantic salience / relevance
          ↓
Autonomy
  behavioral response decision
```

---

## 6. Continuous loop ownership

The phrase `continuous cognitive loop` appears in Autonomy, but the complete loop is cross-domain.

Autonomy owns the **behavioral control loop**:

```text
observe relevant state
    ↓
assess salience
    ↓
maintain goals
    ↓
decide whether to act
    ↓
pursue task
    ↓
observe outcome
    ↓
update task/goal state
    ↓
continue
```

Brain owns the runtime that keeps this loop executing.

Cognition owns the semantic interpretation steps inside it.

Memory owns persistent experience.

Policy/Safety gates consequential actions.

Therefore `02-autonomy/01_CONTINUOUS_COGNITIVE_LOOP.md` should be understood as the **autonomous behavioral loop**, not a replacement for the Brain runtime or Cognition architecture.

---

## 7. Situation model boundary

Autonomy documents currently describe a `situation` data object.

This does not make Autonomy the owner of the Situation Model.

```text
Cognition
  → interprets world state into situations

Autonomy
  → consumes situations to determine behavior

Memory
  → supplies historical context about situations
```

The `Situation` event/data contract may live in Autonomy because it is needed by the behavioral engine, but its semantic interpretation remains owned by Cognition.

---

## 8. Decision boundary

Autonomy documentation correctly distinguishes reasoning from authorization.

The canonical sequence is:

```text
Cognition
  ↓
interpretation / candidate strategy / candidate plan
  ↓
Autonomy
  ↓
goal + priority + task lifecycle + behavioral plan
  ↓
Policy / Safety
  ↓
authorization / constraints
  ↓
Capability Gateway
  ↓
Hardware / external system
```

A model-generated plan is therefore **not** automatically an autonomous decision.

Autonomy makes the behavioral commitment to pursue a task, subject to policy.

---

## 9. Planning boundary

There are two planning activities and they must not be conflated.

### Cognition planning

Cognition may reason about:

- possible strategies;
- candidate plans;
- consequences;
- assumptions;
- alternative futures;
- ambiguity.

This is **deliberative reasoning**.

### Autonomy planning

Autonomy owns:

- selecting whether to pursue a goal;
- selecting/committing a behavioral task;
- sequencing task steps;
- starting/pausing/cancelling tasks;
- handling interruptions;
- replanning after environmental changes;
- determining when a goal is complete.

This is **behavioral task management**.

```text
Cognition:
  "These are plausible ways to solve it."

Autonomy:
  "I will pursue option B as my current task."

Policy:
  "Option B is/is not permitted."

Controller:
  "The permitted command was/was not physically executed."
```

---

## 10. Action ownership

Autonomy does not directly execute physical actions.

It owns the lifecycle of an action request:

```text
candidate
→ validated
→ policy requested
→ authorized / denied
→ dispatched
→ running
→ completed / failed / cancelled
→ outcome verified
```

The physical truth is supplied by execution systems and sensors.

Autonomy must never infer success solely because a capability accepted a command.

---

## 11. Goal ownership

Goals are explicitly Autonomy-owned behavioral objects.

Cognition may propose a goal.

Memory may provide evidence for or against a goal.

Policy may prohibit it.

Brain may report resource limitations.

But Autonomy owns:

- goal lifecycle;
- priority;
- dependencies;
- suspension;
- resumption;
- cancellation;
- completion;
- conflict resolution.

Example:

```text
Cognition:
  "The battery is low. Returning to charge may be appropriate."

Autonomy:
  creates goal RETURN_TO_CHARGE

Brain:
  reports navigation capability degraded

Policy:
  permits safe return

Autonomy:
  selects fallback behavior
```

---

## 12. Curiosity and learning boundary

Autonomy owns **when to investigate**.

Cognition owns **how to interpret the unknown**.

Memory owns **what becomes persistent knowledge/experience**.

```text
unknown detected
      ↓
Cognition:
  uncertainty / interpretation
      ↓
Autonomy:
  is investigation worth pursuing?
      ↓
Memory/Knowledge:
  retrieve existing explanation
      ↓
Cognition:
  evaluate evidence
      ↓
Autonomy:
  decide next behavioral step
      ↓
Memory:
  admit/consolidate verified experience
```

Curiosity must therefore not become an uncontrolled learning engine inside Autonomy.

---

## 13. Internal state and affect boundary

`08_INTERNAL_STATE_AND_AFFECT.md` is valid as an **autonomy operating state**, but it must not become a duplicate personality, emotion, identity, or self-model system.

### Autonomy owns transient behavioral state

Examples:

- current interaction mode;
- current focus;
- attention level;
- task pressure;
- resource pressure;
- temporary curiosity intensity;
- transient behavioral affect used to modulate behavior.

### Cognition owns semantic interpretation

Examples:

- social/emotional hypotheses about people;
- identity;
- personality representation;
- self/other reasoning.

### Memory owns history

Examples:

- previous interactions;
- persistent preferences;
- relationship history;
- autobiographical experiences.

The autonomy affect model must remain transient and bounded.

---

## 14. Runtime boundary

`02-autonomy/11_AUTONOMY_RUNTIME.md` currently describes processes, concurrency, scheduling, resource budgets, model invocation, startup/shutdown and health.

These are partly **Brain/runtime responsibilities**.

Therefore the document must be reframed as:

> **Autonomy runtime requirements and behavioral execution profile**

while the implementation of process orchestration, model runtime, resource scheduling and service lifecycle remains owned by Brain/system architecture.

Autonomy specifies what it needs; Brain specifies how those runtime guarantees are implemented.

Example:

```text
Autonomy requirement:
  "Planning requests require bounded latency and cancellation."

Brain/runtime implementation:
  scheduler + executor + timeout + cancellation primitives
```

---

## 15. Event bus boundary

The Autonomy Event Bus is a valid autonomy contract, but the transport itself should not be treated as an autonomy-owned global infrastructure if Brain/system architecture later defines a platform-wide event fabric.

Autonomy owns:

- event vocabulary relevant to autonomous behavior;
- required delivery semantics;
- priority semantics;
- correlation/causation requirements;
- replay requirements for autonomy scenarios.

System/Brain owns, if applicable:

- transport implementation;
- process-level broker;
- networking;
- persistence infrastructure;
- resource/backpressure implementation.

Therefore the contract is Autonomy-owned; transport implementation is not.

---

## 16. Safety boundary

Autonomy safety documentation is **not** the canonical safety authority.

`09_AUTONOMY_SAFETY_BOUNDARIES.md` should be interpreted as the autonomy-facing safety contract:

```text
Autonomy
  → requests permission / receives constraints

Policy/Safety
  → authoritative decision

Capability Gateway
  → enforces permitted action

Hardware
  → physical interlocks / control limits
```

Autonomy may define required safety gates but cannot redefine immutable safety rules.

---

## 17. Model boundary

There are three distinct concerns:

```text
Cognition
  → selects which cognitive capability/model is appropriate

Brain
  → executes the selected model and manages runtime resources

Autonomy
  → requests cognitive work according to behavioral need
```

Therefore the Autonomy domain must not become a third model router.

It may specify task requirements such as:

```text
need = "long-horizon reasoning"
latency_budget = 1500ms
risk = R2
```

Cognition selects the capability/model.

Brain executes it.

---

## 18. NVIDIA boundary

NVIDIA components are implementation choices behind contracts.

Autonomy should specify behavioral requirements, not hard-code NVIDIA internals into its semantic architecture.

For example:

```text
Autonomy requirement:
  "continuous low-latency perception"

Brain / robotics layer:
  may select Isaac ROS / DeepStream / other implementation

Cognition:
  consumes normalized semantic outputs
```

The same principle applies to JetPack, CUDA, TensorRT, Isaac Sim, Nav2, Nemotron and other candidate technologies.

---

## 19. File-by-file disposition

| File | Decision | Required action |
|---|---|---|
| `00_HIGH_LEVEL_AUTONOMY.md` | **KEEP / CANONICAL AUTONOMY SCOPE** | clarify boundaries; remove stale project naming |
| `01_CONTINUOUS_COGNITIVE_LOOP.md` | **KEEP / REFRAME** | call it the autonomous behavioral loop; cross-link Brain/Cognition |
| `02_AUTONOMY_DATA_AND_EVENTS.md` | **KEEP / CONTRACT** | keep behavioral data vocabulary; semantic truth remains canonical elsewhere |
| `03_ATTENTION_AND_SOCIAL_BEHAVIOR.md` | **KEEP / AUTONOMY BEHAVIOR** | retain behavioral interaction decision; cognition owns semantic social interpretation |
| `04_GOALS_CURIOSITY_AND_LEARNING.md` | **KEEP / AUTONOMY** | keep goal/curiosity decisions; memory owns persistence |
| `05_DECISION_AND_PLANNING.md` | **KEEP / REFRAME** | separate cognition deliberation from autonomy task commitment |
| `06_ACTION_EXECUTION_AND_FEEDBACK.md` | **KEEP / CONTRACT** | autonomy owns lifecycle; execution implementation remains outside |
| `07_AUTONOMY_STATE_MACHINE.md` | **KEEP / CANONICAL AUTONOMY STATE** | distinguish from Brain runtime and safety state machines |
| `08_INTERNAL_STATE_AND_AFFECT.md` | **KEEP / TRANSIENT STATE** | prevent overlap with personality/self/social cognition |
| `09_AUTONOMY_SAFETY_BOUNDARIES.md` | **KEEP / SAFETY CONTRACT** | explicitly subordinate to canonical policy/safety authority |
| `10_AUTONOMY_EVENT_BUS.md` | **KEEP / CONTRACT** | transport implementation belongs to system/runtime |
| `11_AUTONOMY_RUNTIME.md` | **KEEP / REFRAME** | move runtime implementation authority to Brain/system |
| `12_AUTONOMY_TESTING.md` | **KEEP / AUTONOMY TEST STRATEGY** | cross-link system/Brain/Cognition test layers |
| `13_AUTONOMY_OBSERVABILITY_AND_AUDIT.md` | **KEEP / AUTONOMY TRACE** | distinguish behavioral audit from platform observability |
| `14_AUTONOMY_NVIDIA_INTEGRATION.md` | **KEEP / INTEGRATION CONTRACT** | avoid semantic ownership of NVIDIA components |
| `15_AUTONOMY_IMPLEMENTATION_ROADMAP.md` | **KEEP / ROADMAP** | align phase ownership with Brain/Cognition/Memory boundaries |

No Autonomy file needs deletion at this stage. The problem is boundary language and duplicated authority, not lack of useful material.

---

## 20. Critical stale references found

The Autonomy documentation contains references to **Wheely** even though this repository is Novi.

Examples include the physical release wording in `00_HIGH_LEVEL_AUTONOMY.md` and `15_AUTONOMY_IMPLEMENTATION_ROADMAP.md`.

These must be corrected to Novi before the autonomy documentation is considered canonical.

This is a documentation-integrity issue, not merely a naming preference.

---

## 21. Consolidation order

Perform the following in order:

1. Keep this audit as the Autonomy boundary authority.
2. Correct stale `Wheely` references to `Novi`.
3. Add explicit cross-domain boundary sections to the Autonomy README.
4. Reframe `01` as the autonomous behavioral loop.
5. Reconcile `05` with Cognition's reasoning/planning responsibilities.
6. Reframe `11` so Brain owns runtime implementation.
7. Reframe `09` as the autonomy-facing safety contract.
8. Reconcile routing language with Cognition and Brain routing documents.
9. Cross-link event/data contracts to canonical Cognition and Memory semantics.
10. Audit Brain `18–22` and migrate unique material into canonical owners.
11. Run duplicate-topic search across all four domains.
12. Only then resume sequential Brain documentation.

---

## 22. Definition of done

The Autonomy boundary passes when:

- Autonomy has exactly one clear purpose: behavioral agency and goal pursuit;
- Cognition remains the semantic reasoning authority;
- Memory remains the persistent experience/knowledge authority;
- Brain remains runtime/embodiment authority;
- Policy/Safety remains final action authority;
- Hardware remains physical execution authority;
- attention has an explicit cognition-to-behavior boundary;
- planning has an explicit deliberation-to-task-commitment boundary;
- action lifecycle is separated from physical execution;
- runtime implementation is not duplicated;
- event transport is not duplicated;
- safety is not duplicated;
- model routing is not duplicated;
- stale Wheely references are removed;
- cross-links identify canonical owners;
- no new overlapping semantic document is created.

---

## 23. Final Autonomy rule

> **Autonomy does not decide what is true. It decides what Novi should pursue with what it currently knows, within policy, and manages that pursuit until the goal is completed, abandoned, interrupted, or superseded.**
