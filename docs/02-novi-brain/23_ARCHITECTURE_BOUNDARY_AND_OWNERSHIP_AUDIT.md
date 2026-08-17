# 23 — Architecture Boundary & Ownership Audit

**Status:** PASS — CANONICAL BOUNDARY DECISION  
**Scope:** `02-novi-brain`, `03-cognition`, `04-memory-and-knowledge`, `02-autonomy`  

## 1. Executive decision

Novi has four cooperating domains:

```text
02-novi-brain          = embodied brain runtime and integration
03-cognition           = understanding, reasoning and cognitive representation
04-memory-and-knowledge= persistent experience, memory and knowledge
02-autonomy            = behavioral goal pursuit and action coordination
```

They are not four independent brains. One substantive concept must have one canonical owner. Other domains may consume, derive, cache or expose it, but must not redefine it.

> **Brain coordinates. Cognition understands. Memory remembers and knows. Autonomy chooses and pursues. Policy permits or denies. Hardware executes.**

## 2. Canonical boundary

```text
Perception / sensors
        ↓
02-novi-brain
  runtime + embodied state
        ↓
03-cognition
  world / situation / reasoning / prediction
        ↕
04-memory-and-knowledge
  historical experience / knowledge / retrieval
        ↓
02-autonomy
  goals / priorities / task pursuit / behavior
        ↓
policy + safety
        ↓
hardware / controllers
```

## 3. Ownership matrix

| Capability | Canonical owner | Other domains may do |
|---|---|---|
| Brain lifecycle | Brain | consume state |
| Runtime scheduling/execution | Brain | request execution |
| Perception runtime | Brain | Cognition interprets outputs |
| Vision/audio/speech semantics | Cognition | Brain executes pipelines; Memory stores experiences |
| Current physical/body state | Brain + authoritative hardware/runtime | Cognition consumes; Memory stores history |
| Semantic world model | Cognition | Memory supplies historical evidence |
| Situation model | Cognition | Memory supplies context; Autonomy consumes |
| Spatial reasoning | Cognition | Brain supplies localization; Memory owns spatial history |
| Temporal/causal reasoning | Cognition | Brain supplies clocks; Memory owns historical records |
| Identity/social cognition | Cognition | Memory stores history; Autonomy consumes |
| Prediction/expectation | Cognition | Memory stores prediction history |
| Reasoning | Cognition | Brain runs models; Memory supplies context |
| Cognitive model selection | Cognition | Brain owns execution/runtime routing |
| Model registry/lifecycle/runtime | Brain | Cognition declares capability requirements |
| Long-term memory | Memory/Knowledge | Cognition requests/reasons over results |
| Retrieval/consolidation | Memory/Knowledge | Cognition supplies semantic query |
| Knowledge graph | Memory/Knowledge | Cognition consumes |
| Skill/competence history | Memory/Knowledge | Cognition/Autonomy use it |
| Goals and behavioral priority | Autonomy | Cognition proposes; Memory supplies history |
| Planning/behavior sequencing | Autonomy | Cognition supplies candidate plans |
| Action proposal | Cognition/Autonomy boundary | Brain executes approved work |
| Safety/final authorization | Policy/Safety | all others constrained by it |
| Motor control | Hardware/control | Autonomy requests |
| Resource telemetry | Brain/runtime + hardware | Cognition/Autonomy consume |
| Durable semantic storage | System architecture + Memory semantics | Memory defines requirements |

## 4. Critical overlaps and resolution

The repository already has a mature canonical Cognition architecture covering world model, multimodal cognition, reasoning, uncertainty, identity, relationships, temporal/causal reasoning, context, prediction, model routing, APIs, failures, testing and observability. `04-memory-and-knowledge` likewise declares its active `01–18` set the normative semantic memory/knowledge architecture.

Therefore the Brain semantic documents were consolidated rather than allowed to become competing authorities.

### Brain `18_WORLD_MODEL.md`

Canonical semantic ownership: **`03-cognition/02_WORLD_MODEL.md`**.

The Brain document is now explicitly superseded. Unique requirements around epistemic state, prediction, active perception, imagination boundaries and action-outcome grounding were consolidated into the canonical World Model.

### Brain `19_SPATIAL_COGNITION.md`

The document is now explicitly superseded.

Ownership is split by meaning:

- live localization/body state → Brain/runtime + robotics authority;
- current semantic spatial reasoning → Cognition/World Model;
- historical spatial experience → Memory/Knowledge;
- route generation/control → navigation/robotics authority.

### Brain `20_TEMPORAL_COGNITION.md`

The document is now explicitly superseded.

Ownership is split by meaning:

- clocks/timestamps/runtime synchronization → System Architecture;
- runtime timing/deadlines/scheduling → Brain/runtime;
- current temporal and causal reasoning → Cognition;
- historical temporal memory → Memory/Knowledge.

### Brain `21_SITUATION_MODEL.md`

The document is now explicitly superseded.

Canonical semantic ownership is Cognition, with the architecture defined through `03-cognition/01_COGNITIVE_ARCHITECTURE.md` and context construction through `03-cognition/09_CONTEXT_ENGINE.md`.

### Brain `22_SELF_MODEL.md`

The document is now explicitly superseded as a single-owner Brain specification.

Self representation is intentionally distributed:

- embodied self-state → Brain/runtime + hardware;
- semantic self-knowledge and self/other reasoning → Cognition;
- autobiographical/self-history → Memory;
- current goals/tasks/behavioral state → Autonomy.

### Brain `01`, `02`, `05`

These were already converted to runtime/boundary references in the previous consolidation pass:

- `01_BRAIN_NORTH_STAR_AND_BEHAVIORAL_CONTRACT.md`
- `02_COGNITIVE_ARCHITECTURE.md`
- `05_COGNITIVE_CYCLE.md`

### Future Brain memory documents

**Do not create them.** Memory/Knowledge already has canonical ownership.

## 5. Model-routing boundary

Two routing concerns are legitimate:

```text
Cognitive routing
  = which capability/model should solve a cognitive task

Runtime routing
  = where/how the selected model executes
```

`03-cognition/12_COGNITIVE_ROUTING_AND_MODEL_SELECTION.md` owns cognitive selection policy.
`02-novi-brain/08_MODEL_ROUTING_AND_SELECTION.md` owns execution/runtime routing.

They must reference each other rather than duplicate selection policy.

## 6. Current state vs memory

```text
Battery now = 31%
    → live authoritative state

Battery was 31% yesterday
    → historical memory
```

Memory must never silently override current physical telemetry.

## 7. World model vs memory

The current semantic world model belongs to Cognition. Memory stores historical observations, experiences, learned knowledge and provenance used to construct/update that current model.

There must never be multiple competing live world-model authorities.

## 8. Self-model boundary

```text
Brain:
  current pose, joints, sensors, actuators, resources, runtime health

Cognition:
  self-related reasoning, capability interpretation, self/other model

Memory:
  previous actions, failures, competencies, autobiographical history

Autonomy:
  current goals, priorities, tasks and behavioral state
```

## 9. Planning/action boundary

Cognition may produce interpretations, candidate goals, predictions and candidate plans.
Autonomy decides whether and when to pursue them, manages task lifecycle and behavioral sequencing.
Policy/safety retains final authority over consequential actions.
Hardware/control executes permitted low-level commands.

## 10. Consolidation result

The consolidation gate is **PASS** for the current documented architecture.

Completed:

1. Canonical owners were assigned.
2. Duplicate Brain semantic documents were converted to explicit superseded/boundary references.
3. Unique World Model requirements were consolidated into Cognition.
4. Temporal/causal reasoning requirements were consolidated into Cognition.
5. Situation Model ownership was consolidated into Cognition/Context Engine.
6. Self Model ownership was split explicitly across Brain, Cognition, Memory and Autonomy.
7. Autonomy was separated from Brain runtime and Cognition semantics.
8. Solution Selection Policy was moved to System Architecture as a cross-cutting policy.
9. Master documentation authority was updated.
10. Historical specifications remain recoverable through Git history.

## 11. Definition of done

The boundary audit passes because:

- every major concept has exactly one canonical owner;
- live physical state cannot be overridden by memory;
- memory is not a second live world model;
- cognition cannot bypass autonomy/policy for consequential actions;
- autonomy cannot invent facts outside cognition/memory;
- Brain runtime does not redefine cognition semantics;
- model selection and model execution are distinct;
- spatial/temporal current-vs-historical ownership is explicit;
- self-state, semantic self-model and self-history are distinct;
- safety remains authoritative outside probabilistic cognition;
- superseded documents are explicitly marked;
- all indexes/cross-references point to canonical owners.

## 12. Freeze rule

Until a new architecture review explicitly changes this decision:

> **Do not create a new document when an existing canonical document can own the requirement. Extend the canonical owner instead.**
