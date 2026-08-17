# 12 — Autonomy Boundary & Ownership Audit

**Status:** CRITICAL — CANONICAL BOUNDARY AUDIT  
**Scope:** `02-autonomy`, `02-novi-brain`, `03-cognition`, `04-memory-and-knowledge`, `01-system-architecture`

## 1. Decision

The Autonomy domain is the canonical owner of **behavioral goal pursuit and task lifecycle**. It must not become a second owner of cognition, world state, memory, model execution, system runtime, or safety authority.

> **Brain coordinates. Cognition understands. Memory remembers and knows. Autonomy chooses and pursues. Policy permits or denies. Hardware executes.**

This audit follows the architecture-boundary decision already established in `docs/02-novi-brain/23_ARCHITECTURE_BOUNDARY_AND_OWNERSHIP_AUDIT.md`.

## 2. Canonical ownership matrix

| Capability | Canonical owner | Autonomy role |
|---|---|---|
| Current semantic World Model | Cognition | consume |
| Situation Model | Cognition | consume; decide behavioral response |
| Temporal/causal reasoning | Cognition | consume |
| Identity/social semantic interpretation | Cognition | consume |
| Prediction/expectation | Cognition | consume; use prediction error for task adaptation |
| Long-term memory | Memory/Knowledge | request/retrieve; emit learning candidates |
| Knowledge graph / verified knowledge | Memory/Knowledge | consume |
| Cognitive model selection | Cognition | request capability; provide behavioral requirements |
| Model execution/runtime | Brain/System | consume through capability contracts |
| Process lifecycle/scheduling implementation | Brain/System | declare runtime requirements |
| Behavioral attention decision | Autonomy | own |
| Goal lifecycle | Autonomy | own |
| Goal priority | Autonomy | own, subject to policy/safety constraints |
| Task sequencing/pursuit | Autonomy | own |
| High-level behavioral planning | Autonomy | own; consume candidate strategies from Cognition |
| Action-request lifecycle | Autonomy | own |
| Capability execution | Brain/Hardware through governed interfaces | request |
| Final authorization | Policy/Safety | never override |
| Motor control | Hardware/Control | never own |
| Behavioral audit records | Autonomy for behavioral events; System for platform/audit infrastructure | emit structured records |

## 3. Boundary findings

### 3.1 Continuous cognitive loop

`02-autonomy/01_CONTINUOUS_COGNITIVE_LOOP.md` must describe the behavioral loop only. It must not redefine the semantic meaning of World Model, Situation Model, memory, or reasoning.

The system-level continuous event loop remains owned by System/Brain runtime infrastructure. Autonomy owns the behavioral interpretation and task lifecycle within that loop.

### 3.2 Attention

Autonomy owns the **behavioral decision** of whether an event should cause action, observation, interaction, or no action. Cognition owns semantic salience and interpretation.

Therefore:

```text
perception/event
    ↓
Cognition: what is it / why might it matter?
    ↓
Autonomy: should behavior respond?
    ↓
Policy/Safety: is the proposed consequential action permitted/safe?
```

Autonomy must not implement a competing semantic attention model.

### 3.3 Goals and curiosity

Goals, priorities, suspension, resumption, completion, curiosity decisions and behavioral commitments are Autonomy concerns.

Curiosity must not become an implicit authority to modify knowledge or memory. It produces bounded information-seeking goals; Memory/Knowledge owns persistence and consolidation.

### 3.4 Planning

Autonomy owns **behavioral task planning and sequencing**. Cognition owns semantic reasoning and may generate candidate strategies/plans.

A useful distinction is:

```text
Cognition → candidate interpretation / strategy / predicted consequence
Autonomy → choose and pursue behavioral task
Policy/Safety → permit or deny consequential execution
Hardware → execute control
```

No LLM or Cognition result is itself an authorized action.

### 3.5 Runtime

`02-autonomy/11_AUTONOMY_RUNTIME.md` is correctly framed as requirements rather than implementation authority. Brain/System owns process lifecycle, scheduling, model execution, orchestration and resource-management implementation.

Autonomy may require deadlines, cancellation, preemption, resource admission and health signals, but must not implement a competing runtime architecture.

### 3.6 Internal state and affect

Autonomy may maintain operational behavioral state such as task phase, commitment, urgency and interruption state.

Semantic personality, emotion and affect interpretation remain Cognition-owned where they are part of cognitive/social representation. Durable personal history remains Memory-owned.

### 3.7 Safety

`09_AUTONOMY_SAFETY_BOUNDARIES.md` may define autonomy-side constraints and behavioral fail-safe requirements, but it must not become the canonical safety authority.

Final safety policy, emergency behavior and physical safety constraints remain outside Autonomy.

### 3.8 Event bus

`10_AUTONOMY_EVENT_BUS.md` should define the Autonomy-facing event contract, not become a second system-wide event transport architecture.

System-level durable events, transactions, replication and infrastructure semantics remain owned by System Architecture.

## 4. Required invariants

### A1 — No semantic duplication

Autonomy must not redefine canonical Cognition semantics for world state, situations, identity, prediction, temporal reasoning or reasoning-model selection.

### A2 — No memory authority

Autonomy may create learning candidates and request memory operations but cannot directly redefine durable memory/knowledge semantics.

### A3 — No runtime authority

Autonomy specifies runtime guarantees; Brain/System owns implementation.

### A4 — No safety authority

Autonomy may stop or abandon its own tasks, but cannot weaken or bypass policy/safety constraints.

### A5 — No direct hardware authority

Autonomy communicates through bounded capabilities. It never receives unrestricted motor, filesystem, database or network access.

### A6 — Stale-plan protection

Before consequential execution, the action request must be revalidated against current state and policy. A plan generated against an older cognitive/world-state version is not automatically executable.

### A7 — Traceability

Every consequential behavioral decision must reference its trigger, relevant state/evidence identifiers, task/goal, capability request, policy result and observed outcome without storing unnecessary hidden reasoning or sensitive raw data.

### A8 — Silence is valid

Autonomy must support `NO_ACTION` / observation-only outcomes. Continuous operation does not imply continuous interaction.

## 5. Current architecture assessment

The high-level Autonomy specification is already substantially aligned with the boundary model: it explicitly excludes canonical World Model/Situation Model ownership, raw sensors, motor control, safety-critical control, memory storage, model internals and runtime implementation.

The main remaining risk is **document drift**: lower-level Autonomy documents can gradually reintroduce concepts that are already canonical elsewhere. Any future Autonomy document must therefore identify its owner boundary explicitly and link to the canonical semantic owner rather than restating it.

## 6. Documentation rules

Before adding or substantially expanding an Autonomy document:

1. Search the entire repository for the concept.
2. Identify the canonical owner.
3. Define only the Autonomy-specific contract or behavior.
4. Link to the canonical owner instead of copying its semantics.
5. If a genuinely new cross-domain concept is discovered, establish ownership through System Architecture/ADR before creating another normative document.

## 7. Definition of done

The Autonomy boundary audit passes when:

- goals and behavioral task lifecycle have one owner;
- cognition remains authoritative for semantic interpretation;
- memory remains authoritative for durable experience/knowledge;
- Brain/System remains authoritative for runtime implementation;
- policy/safety remains authoritative for consequential authorization;
- hardware remains authoritative for physical control;
- event infrastructure is not duplicated;
- stale plans cannot bypass current-state validation;
- every consequential action is traceable;
- lower-level Autonomy documents contain no competing semantic authorities.
