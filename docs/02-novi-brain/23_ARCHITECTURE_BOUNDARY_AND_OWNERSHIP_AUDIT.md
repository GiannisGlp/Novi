# 23 — Architecture Boundary & Ownership Audit

**Status:** CRITICAL — CANONICAL BOUNDARY DECISION  
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

## 4. Critical current overlaps

The repository already has a mature canonical Cognition architecture covering world model, multimodal cognition, reasoning, uncertainty, identity, relationships, temporal/causal reasoning, context, prediction, model routing, APIs, failures, testing and observability. `04-memory-and-knowledge` likewise declares its active `01–18` set the normative semantic memory/knowledge architecture.

Therefore the newer Brain documents must not become a competing semantic architecture.

### Brain `18_WORLD_MODEL.md`

Canonical semantic ownership: **`03-cognition/02_WORLD_MODEL.md`**.

Keep useful embodied/runtime material only in Brain; merge unique semantic material into Cognition; then mark the Brain document superseded or replace it with a boundary/interface document.

### Brain `19_SPATIAL_COGNITION.md`

Split by meaning:

- live localization/body state → Brain/runtime authority;
- current semantic spatial reasoning → Cognition;
- historical spatial experience → Memory/Knowledge.

### Brain `20_TEMPORAL_COGNITION.md`

Split by meaning:

- clocks/timestamps/runtime synchronization → Brain/system;
- current temporal and causal reasoning → Cognition;
- historical temporal memory → Memory/Knowledge.

### Brain `21_SITUATION_MODEL.md`

Canonical semantic ownership: **Cognition**. Brain may define runtime lifecycle/interfaces but not a second situation interpretation system.

### Brain `22_SELF_MODEL.md`

Treat as a cross-domain specification:

- embodied self-state → Brain/runtime;
- semantic self-knowledge and self/other reasoning → Cognition;
- autobiographical/self-history → Memory;
- behavioral goals/tasks → Autonomy.

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

## 10. Required consolidation sequence

1. Freeze creation of overlapping semantic Brain documents.
2. Audit Brain `18–22` against canonical Cognition/Memory owners.
3. Merge unique content into canonical owners.
4. Mark superseded documents explicitly instead of deleting provenance.
5. Audit `02-autonomy` against Brain/Cognition boundaries.
6. Update READMEs, indexes and cross-references.
7. Run a final duplicate-topic search.
8. Resume Brain documentation only after the boundary audit passes.

## 11. Definition of done

The boundary audit passes when:

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
