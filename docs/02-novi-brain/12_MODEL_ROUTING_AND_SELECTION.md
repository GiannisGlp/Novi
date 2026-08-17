# Novi Brain — Model Routing and Selection

**Status:** PROPOSED / P0 architecture  
**Date:** 2026-08-17  
**Authority:** Novi brain architecture; implementation requires benchmark evidence and ADRs  
**Depends on:** `10_NEURAL_NETWORK_STRATEGY.md`, `11_MODEL_TAXONOMY.md`, `02_COGNITIVE_ARCHITECTURE.md`, `04_BRAIN_ORCHESTRATOR.md`, system canonical contracts

---

## 1. Purpose

This document defines how Novi selects, schedules, combines, interrupts, degrades and evaluates learned models during continuous operation.

Model routing is not merely an inference optimization problem. It is part of Novi's cognitive architecture because the choice of model affects:

- what Novi can perceive;
- what Novi can understand;
- how quickly Novi can react;
- how much uncertainty Novi has;
- what Novi can predict;
- how much compute Novi consumes;
- how Novi behaves when resources are constrained;
- how Novi maintains continuous embodied presence.

The router therefore operates under both **cognitive objectives** and **engineering constraints**.

---

# 2. Core principle

Novi must not behave like a chatbot that wakes a large language model whenever a new input arrives.

Novi must behave as a continuously operating embodied system with multiple cognitive timescales.

```text
WORLD
  ↓
SENSORS
  ↓
FAST PERCEPTION
  ↓
EVENTS / EVIDENCE
  ↓
ATTENTION
  ↓
ROUTING DECISION
  ├── react immediately
  ├── invoke specialist
  ├── invoke multimodal reasoning
  ├── invoke deliberative reasoning
  ├── invoke world prediction
  ├── invoke skill/policy
  ├── defer
  └── ignore / retain as background evidence
```

The router must optimize for **appropriate cognition**, not maximum model size.

---

# 3. NVIDIA physical-AI evidence

NVIDIA's current Physical AI ecosystem validates the architectural separation between perception, reasoning, world prediction and action rather than requiring a single model for every operation.

NVIDIA Isaac ROS provides CUDA-accelerated robotics packages and AI models for common perception and navigation workloads and supports deployment on workstation GPUs and Jetson. citeturn0search12

NVIDIA Cosmos 3 combines physical reasoning, world generation and action generation in a Mixture-of-Transformers architecture. NVIDIA describes a reasoner tower that interprets multimodal observations and a generator tower that produces future observations and action sequences. citeturn0search0turn0search3

Cosmos 3 can be used as a VLM for physical reasoning, as a world model for future-state prediction, and as a foundation for World Action Models. NVIDIA also provides different model sizes and describes separate deployment/training workflows. citeturn0search1turn0search3

NVIDIA GR00T N1.6 uses a VLM backbone plus a larger action-generation component and predicts state-relative action chunks for supported embodiments. It has been evaluated on simulated and real robotic systems. citeturn0search2

NVIDIA's 2026 terminology distinguishes VLA and World-Action Model approaches: VLA policies adapt pretrained VLM representations to generate robot actions, while WAMs adapt world/video models to represent or predict scene changes and emit actions. citeturn0search11

These technologies are **candidates and evidence**, not automatic Novi dependencies.

---

# 4. Model routing architecture

```text
                         NOVI BRAIN
                             │
                       Brain Orchestrator
                             │
                    ┌────────┴────────┐
                    │ Routing Engine  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   Fast Models          Specialist Models    Cognitive Models
        │                    │                    │
  VAD / tracking       vision / audio       VLM / LLM
  anomaly / motion    depth / pose          reasoning
        │              embeddings            planning
        └────────────────────┼────────────────────┘
                             │
                     Prediction Models
                             │
                    world / trajectory / WAM
                             │
                       Skill / Policy
                             │
                       Action Proposal
                             │
                   Governance + Safety
                             │
                         Controller
```

The routing engine itself does not authorize physical action.

---

# 5. Routing objectives

Every routing decision should consider:

1. **Task relevance** — does the model provide the capability required?
2. **Urgency** — how quickly is an answer required?
3. **Confidence** — how reliable is the upstream evidence?
4. **Complexity** — does the situation require deeper reasoning?
5. **Modality** — which sensors/modalities are required?
6. **Context** — what is Novi currently doing?
7. **Goal relevance** — does the event affect an active goal?
8. **Novelty** — is this situation unusual enough to require additional cognition?
9. **Safety criticality** — what happens if the model is wrong?
10. **Latency budget** — how long can Novi wait?
11. **Compute availability** — CPU/GPU/VRAM capacity.
12. **Thermal state** — available thermal headroom.
13. **Power state** — battery/rail constraints.
14. **Model health** — current failure/error state.
15. **Model provenance/version** — exact model identity.
16. **Privacy policy** — whether the model is permitted to process the data.
17. **Offline availability** — whether the model exists locally.
18. **Fallback availability** — what happens if the selected model fails.

---

# 6. Cognitive timescales

Novi should operate multiple timescales concurrently.

## T0 — deterministic/reactive

Approximate purpose:

- emergency behavior;
- collision constraints;
- controller protection;
- actuator safety;
- hard limits.

No neural model is required for this layer.

## T1 — always-on learned perception

Purpose:

- voice activity detection;
- lightweight object/person detection;
- motion/event detection;
- acoustic event detection;
- low-cost anomaly detection.

These models should run continuously where hardware permits.

## T2 — specialist perception

Purpose:

- object classification;
- segmentation;
- depth estimation;
- pose estimation;
- tracking;
- speaker identification;
- richer audio understanding;
- embeddings.

Triggered continuously or conditionally depending on workload.

## T3 — multimodal understanding

Purpose:

- scene interpretation;
- object relationships;
- human activity/context;
- visual-language grounding;
- audio-visual interpretation.

## T4 — deliberative cognition

Purpose:

- complex reasoning;
- planning;
- dialogue reasoning;
- ambiguity resolution;
- social reasoning;
- goal decomposition.

## T5 — physical prediction / learned action

Purpose:

- future-state prediction;
- world-model imagination;
- learned action generation;
- VLA/WAM policies;
- complex learned skills.

## T6 — offline/slow learning

Purpose:

- memory consolidation;
- dataset curation;
- evaluation;
- model adaptation;
- skill analysis;
- post-training.

T6 must never silently modify protected runtime safety constraints.

---

# 7. Fast-path principle

Novi must have a fast path that does not depend on large generative models.

Example:

```text
person enters room
      ↓
person detector
      ↓
tracking
      ↓
identity/context lookup
      ↓
attention score
      ↓
possible greeting
```

A large language model may be invoked only if the social/context decision actually requires it.

This prevents unnecessary latency and makes continuous interaction practical.

---

# 8. Interrupt principle

The router must support preemption.

Example:

```text
Novi planning a task
       ↓
high-priority acoustic event
       ↓
attention interrupt
       ↓
fast perception
       ↓
urgent world update
       ↓
react / investigate / ignore
       ↓
resume or revise original plan
```

An interruption must carry:

- source;
- timestamp;
- priority;
- reason;
- affected goals;
- affected tasks;
- evidence;
- expiration;
- resolution.

---

# 9. Attention-driven routing

Routing should be downstream of attention, not simply every-input fan-out.

Each event receives an attention assessment based on:

```text
salience
+ urgency
+ novelty
+ goal relevance
+ social relevance
+ safety relevance
+ uncertainty
+ expected information gain
+ persistence
```

The result determines the required cognitive depth.

Example:

```text
small background sound
 → T1

known person enters
 → T1 + identity lookup

known person addresses Novi
 → T2/T3 + dialogue

ambiguous social situation
 → T3/T4

possible physical hazard
 → T0/T1 immediately + T3/T4 if needed

unfamiliar physical situation
 → T2/T3 + prediction

complex manipulation task
 → T3/T4 + T5 policy/world model
```

---

# 10. Confidence-driven escalation

A model should be able to request deeper cognition.

```text
specialist model
      ↓
confidence < threshold
      ↓
escalate
      ↓
multimodal model
      ↓
confidence still low
      ↓
deliberative reasoning
      ↓
possibly request more sensing
```

This is preferable to always running the largest model.

Confidence values must remain associated with the evidence they describe and must not be treated as universal truth probabilities unless calibrated for that exact task.

---

# 11. Active perception

Novi should be able to choose to gather more information when uncertainty is important.

Example:

```text
object detected
      ↓
identity uncertain
      ↓
Novi changes viewpoint
      ↓
new camera evidence
      ↓
updated perception
```

This creates a closed loop:

```text
perceive
 ↓
uncertainty
 ↓
choose observation
 ↓
move/sense
 ↓
new evidence
 ↓
update belief
```

Any physical movement used for active perception remains subject to navigation, control and safety constraints.

---

# 12. Model selection score

The initial conceptual routing score is:

```text
Score(model, task) =
    capability_fit
  + evidence_quality
  + confidence_gain
  + latency_fit
  + resource_fit
  + context_fit
  + reliability
  + privacy_fit
  - compute_cost
  - thermal_cost
  - power_cost
  - latency_cost
  - failure_risk
```

This is a decision framework, not an implementation formula. The final scoring method must be validated empirically.

Hard constraints must override scores.

For example:

```text
model capable
BUT
privacy policy forbids input
→ cannot select
```

or:

```text
model capable
BUT
latency exceeds safety-relevant deadline
→ cannot select for that task
```

---

# 13. Model registry requirements

Every routable model requires a registry record containing:

- model ID;
- model family;
- exact version;
- artifact digest;
- source;
- license;
- modalities;
- input schema;
- output schema;
- capabilities;
- supported hardware;
- runtime;
- quantization;
- memory requirement;
- expected latency;
- benchmark results;
- confidence calibration status;
- known failure modes;
- safety classification;
- privacy classification;
- fallback model;
- health status;
- provenance.

No unregistered model may enter the production routing pool.

---

# 14. Model health

Each model should have a runtime health state:

```text
AVAILABLE
WARMING
DEGRADED
OVERLOADED
THERMALLY_LIMITED
POWER_LIMITED
FAILED
DISABLED
INCOMPATIBLE
QUARANTINED
```

Routing must account for health before selection.

---

# 15. Resource-aware routing

The router must see system resource state:

```text
CPU
GPU
VRAM
RAM
NPU/accelerators where available
storage I/O
network
thermal headroom
battery
power budget
active workloads
```

Example:

```text
normal battery
+ thermal headroom
→ richer cognition allowed

low battery
→ reduce background cognition
→ preserve safety/navigation

high temperature
→ reduce optional model workloads
→ preserve safety/control

GPU unavailable
→ specialist CPU fallback
→ degraded cognition
```

Resource governance remains separate from model reasoning.

---

# 16. Model concurrency

Novi should support concurrent models when the workload requires it.

Example:

```text
camera perception ───────┐
audio perception ────────┤
localization ────────────┤
                         ↓
                    brain state
                         ↓
                    orchestrator
                         ↓
              reasoning + dialogue
```

The router must avoid duplicate expensive computation when an existing representation can be reused.

It must also prevent resource starvation of safety/control workloads.

---

# 17. Context routing

A model must receive only the context necessary for its task.

Possible context sources:

- current observations;
- recent events;
- active goal;
- active plan;
- relevant memory;
- spatial state;
- temporal state;
- person/context state;
- uncertainty;
- model/tool results;
- hardware health;
- resource state.

The router must not indiscriminately inject the complete Novi memory into every model call.

Context assembly must preserve provenance.

---

# 18. Memory-aware routing

Model selection may depend on whether relevant memory exists.

Example:

```text
known person
 ↓
retrieve relationship context
 ↓
small interaction model may be sufficient
```

versus:

```text
unknown situation
 ↓
no useful memory
 ↓
higher uncertainty
 ↓
multimodal reasoning / additional sensing
```

Memory retrieval itself must remain deterministic and auditable even when embeddings or neural rerankers are used.

---

# 19. Personality-aware routing

Personality should influence behavior and expression, not safety or factual evidence.

For example, a social decision may select a conversational style based on Novi's persistent personality state.

But:

```text
personality
≠
authorization

personality
≠
truth

personality
≠
safety policy
```

The model router may condition expressive behavior on personality while keeping safety/governance independent.

---

# 20. Reactive versus deliberative routing

Every meaningful behavior should be classifiable as one or more of:

### Reactive

Immediate response to a stimulus.

Examples:

- stop;
- avoid obstacle;
- orient toward sound;
- acknowledge known person.

### Deliberative

Requires explicit reasoning/planning.

Examples:

- plan a route with constraints;
- decide how to help someone;
- solve a complex task;
- compare alternative actions.

### Background

Continuous low-priority cognition.

Examples:

- memory consolidation;
- environment statistics;
- skill analysis;
- curiosity monitoring.

The router decides which execution mode applies.

---

# 21. World-model routing

World models should not be used simply because they are available.

Use a world/prediction model when:

- future state matters;
- the environment is uncertain;
- alternative actions need comparison;
- a learned physical interaction is difficult to model deterministically;
- simulation/imagination can reduce physical experimentation.

NVIDIA describes Cosmos 3 as supporting future-world prediction, closed-loop simulation and action-conditioned workflows, making it a strong candidate for these workloads. citeturn0search1turn0search3

However:

```text
predicted future
≠
observed reality
```

World-model output must remain explicitly tagged as prediction/simulation.

---

# 22. VLA/WAM routing

A learned action model should be selected only when:

- the task is within its supported embodiment/task distribution;
- required sensor inputs are available;
- action representation is compatible;
- latency meets requirements;
- output passes schema validation;
- governance permits the task;
- deterministic controllers remain between policy output and actuators.

NVIDIA's GR00T N1.6 demonstrates state-relative action chunks for supported embodiments, while Cosmos 3 provides a foundation for World Action Models and action post-training. citeturn0search2turn0search3

A VLA/WAM must never bypass the safety/controller boundary.

---

# 23. Action-model output contract

A learned action model should output a structured proposal rather than raw uncontrolled actuator commands.

Conceptually:

```text
ActionProposal
├── proposal_id
├── model_id
├── model_version
├── timestamp
├── target_skill
├── target_entity
├── action_type
├── trajectory / action chunk
├── expected_duration
├── confidence
├── predicted_outcome
├── uncertainty
├── preconditions
├── constraints
└── provenance
```

Then:

```text
ActionProposal
 ↓
validation
 ↓
governance
 ↓
safety
 ↓
controller
 ↓
actuator
```

---

# 24. Fallback hierarchy

Every important model capability requires a fallback.

Example:

```text
Primary VLM
   ↓ failure
Secondary VLM
   ↓ failure
Specialist perception
   ↓ failure
Reduced capability
   ↓ failure
Safe degraded mode
```

For physical actions:

```text
learned policy failure
 ↓
deterministic controller/fallback
 ↓
stop / safe state
```

No model failure may automatically become unrestricted physical behavior.

---

# 25. Offline-first routing

Core operation must remain functional without cloud services.

The router should distinguish:

```text
LOCAL
REMOTE-OPTIONAL
UNAVAILABLE
```

Remote services may provide optional enrichment but must not be required for:

- safety;
- core perception;
- physical control;
- essential memory;
- basic navigation;
- emergency behavior.

---

# 26. Privacy-aware routing

Routing must consider data sensitivity.

Examples:

- camera/audio data may be prohibited from leaving the robot;
- identity-related data may require local processing;
- private conversations should not be sent to optional remote models;
- retention rules must be applied before persistent storage.

The privacy policy must therefore be queryable by the router before model invocation.

---

# 27. Model ensembles

Multiple models may be combined when this improves reliability.

Examples:

```text
object detector
      +
tracker
      +
VLM
      ↓
scene interpretation
```

or:

```text
ASR
 +
speaker identification
 +
conversation context
 ↓
dialogue understanding
```

Ensemble outputs must preserve the provenance of each contributing model.

---

# 28. Avoiding model cascades

Routing must prevent unnecessary chains such as:

```text
model A
 ↓
model B
 ↓
model C
 ↓
LLM
 ↓
VLM
 ↓
LLM again
```

unless the cascade has demonstrated measurable benefit.

Every cascade should have:

- expected benefit;
- latency budget;
- resource budget;
- failure handling;
- evidence.

---

# 29. Self-observation of the routing system

Novi must be able to observe its own cognitive runtime.

The router should record:

- selected model;
- rejected candidates;
- routing reason;
- latency;
- resource cost;
- model result;
- confidence;
- fallback;
- interruption;
- failure;
- outcome.

This enables later analysis of whether Novi is choosing models intelligently.

---

# 30. Routing audit event

Every significant routing decision should produce an auditable event:

```text
ModelRoutingDecision
├── decision_id
├── timestamp
├── trigger_event
├── task
├── candidate_models
├── selected_model
├── selection_reason
├── constraints
├── resource_state
├── privacy_state
├── model_health
├── expected_latency
├── actual_latency
├── result
├── confidence
└── outcome_reference
```

Not every microsecond-level internal operation needs durable storage; the implementation must define sampling/retention rules.

---

# 31. Evaluation methodology

A model cannot enter the preferred routing pool because it performs well on a public benchmark alone.

It must be evaluated on Novi-specific tasks.

Minimum dimensions:

- capability;
- accuracy;
- robustness;
- latency;
- memory;
- power;
- thermal impact;
- failure behavior;
- calibration;
- privacy;
- offline operation;
- recovery;
- task completion;
- interaction quality where applicable.

Public benchmark evidence is supporting evidence, not final Novi evidence.

---

# 32. Candidate evaluation matrix

The first model evaluation matrix should contain at least:

| Capability | Candidate | Local | Modalities | Latency | Memory | Hardware | Accuracy | Failure behavior | Novi benchmark | Decision |
|---|---|---|---|---|---|---|---|---|---|---|
| VAD | TBD | TBD | audio | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| ASR | Riva / local alternatives | TBD | audio | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Object detection | TBD | TBD | vision | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Tracking | TBD | TBD | vision | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| VLM | Cosmos 3 / alternatives | TBD | vision/text/video | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Reasoning LLM | Nemotron / alternatives | TBD | text/multimodal | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| World model | Cosmos 3 / alternatives | TBD | multimodal/action | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| VLA/WAM | GR00T / Cosmos WAM / alternatives | TBD | vision/language/action | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

No `Decision` field should be set to ADOPTED without evidence and an ADR.

---

# 33. Initial recommended routing architecture

Until benchmarks prove otherwise, the architecture should start with:

```text
ALWAYS-ON
├── deterministic safety/control
├── lightweight perception
├── audio activity detection
├── localization/state estimation
└── event generation

ON-DEMAND
├── specialist vision
├── richer audio
├── VLM
├── LLM/reasoning
└── memory-intensive cognition

PHYSICAL-PREDICTION
├── world model
├── trajectory prediction
└── WAM/VLA

BACKGROUND
├── memory consolidation
├── learning/evaluation
├── curiosity analysis
└── model/skill analysis
```

This is a baseline architecture, not a final model selection.

---

# 34. Recommended NVIDIA evaluation order

For Novi's first physical-AI evaluation cycle:

### Phase A — perception

Evaluate Isaac ROS capabilities and relevant specialist models for:

- camera processing;
- localization;
- 3D reconstruction;
- tracking;
- navigation inputs.

NVIDIA explicitly positions Isaac ROS as a CUDA-accelerated toolkit for perception and navigation on Jetson/workstation platforms. citeturn0search12

### Phase B — multimodal reasoning

Evaluate Cosmos 3 Reasoner and alternative VLMs against Novi scenarios.

### Phase C — language reasoning

Evaluate candidate local reasoning models, including Nemotron-family candidates, against Novi's grounded reasoning, planning and interaction benchmarks.

### Phase D — world prediction

Evaluate Cosmos 3 and alternatives for:

- future-state prediction;
- physical plausibility;
- action-conditioned prediction;
- uncertainty;
- usefulness for planning.

### Phase E — embodied policy

Evaluate GR00T and Cosmos-based WAM approaches only after the embodiment, action space and simulation environment are defined.

### Phase F — integrated routing

Measure whether the complete multi-model system outperforms a simpler architecture at acceptable latency/power/thermal cost.

---

# 35. What the router must never do

The router must never:

- allow a model to bypass safety;
- treat model confidence as authorization;
- treat generated text as physical commands;
- treat a prediction as an observation;
- silently mix model versions;
- select a model prohibited by privacy policy;
- use an unavailable/failed model without fallback handling;
- starve deterministic control;
- require cloud connectivity for core operation;
- silently change routing policy without versioning;
- allow a learned model to rewrite protected routing constraints.

---

# 36. Routing policy versioning

The routing policy itself is an artifact.

Every deployment must identify:

- routing-policy version;
- model registry version;
- model artifact versions;
- benchmark versions;
- configuration version;
- hardware target;
- runtime version.

A routing change must be reproducible.

---

# 37. Learning the router

A future learned routing policy may optimize model selection, but it must initially operate inside deterministic constraints.

Possible future objective:

```text
maximize:
    task success
  + perception quality
  + interaction quality
  + information gain
  + recovery quality

subject to:
    safety
    latency
    compute
    thermal
    power
    privacy
    resource fairness
```

The router may eventually learn from historical routing outcomes, but protected constraints remain outside the learned policy.

---

# 38. Continuous-life requirement

Model routing must support Novi's core behavioral requirement: **Novi should continuously feel alive.**

That requires the router to support simultaneous low-level awareness, opportunistic cognition and intentional behavior.

Novi should be able to:

- continue sensing while speaking;
- continue monitoring while thinking;
- react before deliberation completes when a fast response is required;
- interrupt long reasoning when something more important happens;
- resume interrupted cognition;
- reduce background cognition when resources are constrained;
- become more cognitively active when novelty or importance increases;
- initiate bounded behavior without an external prompt;
- remain observant while apparently idle;
- maintain continuity across interactions.

"Idle" therefore means **low-priority cognition**, not absence of cognition.

---

# 39. Example: person enters the room

```text
Camera
  ↓
T1 person detector
  ↓
tracker
  ↓
identity candidate
  ↓
memory lookup
  ↓
attention score
  ↓
┌──────────────────────────┐
│ Is this socially relevant│
└────────────┬─────────────┘
             │
       yes   │   no
        ↓    │    ↓
      T2/T3  │  continue
        ↓
  social context
        ↓
  decide greet / orient / wait
        ↓
  personality-conditioned expression
        ↓
  action proposal
        ↓
  governance
        ↓
  safe motion / speech
```

The system can react naturally without invoking the largest reasoning model for every frame.

---

# 40. Example: sudden physical event

```text
microphone + camera
       ↓
T1 event detection
       ↓
high salience
       ↓
attention interrupt
       ↓
fast spatial perception
       ↓
possible hazard?
       ├── no → resume
       └── yes
             ↓
        immediate safe response
             ↓
        richer reasoning
             ↓
        investigate / inform / recover
```

Safety-critical immediate response must not depend on a slow generative model.

---

# 41. Example: complex physical task

```text
human instruction
       ↓
ASR
       ↓
VLM / multimodal understanding
       ↓
semantic task
       ↓
memory / context
       ↓
reasoning
       ↓
skill selection
       ↓
VLA/WAM candidate
       ↓
world-model prediction if useful
       ↓
action proposal
       ↓
governance
       ↓
safety
       ↓
controller
       ↓
robot
       ↓
observe outcome
       ↓
update memory / skill evidence
```

---

# 42. Initial implementation boundary

The first Novi implementation should **not** implement the full routing hierarchy.

Stage 1 should establish:

- model registry abstraction;
- inference interface;
- routing interface;
- deterministic fast path;
- one specialist perception model;
- one local language/reasoning model candidate;
- structured context construction;
- routing telemetry;
- fallback handling;
- benchmark harness.

Physical VLA/WAM integration belongs later, after simulation and embodiment definitions exist.

---

# 43. Acceptance criteria

This document is implemented correctly only when Novi can demonstrate:

- appropriate model selection for different task classes;
- fast response without large-model dependency;
- deliberate escalation when uncertainty increases;
- interruption and resumption;
- model failure recovery;
- resource-aware degradation;
- offline operation;
- privacy-aware selection;
- auditable routing decisions;
- reproducible routing configuration;
- no direct model-to-actuator authority;
- measurable improvement over an always-largest-model baseline.

---

# 44. Open decisions

The following remain deliberately unresolved until benchmarking:

1. exact always-on perception models;
2. ASR/TTS implementation;
3. primary VLM;
4. primary reasoning model;
5. world-model candidate;
6. VLA/WAM candidate;
7. model serving runtime;
8. model quantization;
9. GPU partitioning;
10. CPU/GPU scheduling;
11. context cache strategy;
12. routing algorithm;
13. confidence calibration method;
14. learned routing policy;
15. exact fallback models.

These must become ADRs after evidence is collected.

---

# 45. Final architectural rule

> **Novi should not always think harder. Novi should think appropriately.**

The correct model is the model that provides the required capability, at the required latency and reliability, with acceptable resource/privacy cost, while preserving Novi's continuous embodied existence and never bypassing governance or safety.

The purpose of model routing is therefore not merely performance optimization. It is one of the mechanisms by which Novi becomes a coherent, responsive, persistent artificial agent rather than a collection of disconnected AI models.
