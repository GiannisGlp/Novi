# 08 — Novi Model Routing and Selection

**Status:** P0 — critical

## Purpose

Define how Novi decides which learned model, deterministic capability or cognitive pathway should operate for a situation. Model routing is part of Novi's intelligence, but routing must remain observable, bounded and governed.

## Core principle

Novi should never use its largest model for every event.

```text
stimulus → evidence → attention → task classification
→ routing decision → model/capability → result → validation
```

## Routing dimensions

Every routing decision considers:

- task type;
- modality;
- urgency;
- consequence/risk;
- confidence;
- novelty;
- context complexity;
- current goal;
- interaction state;
- memory requirements;
- latency budget;
- CPU/GPU/RAM/VRAM availability;
- power and thermal state;
- battery;
- privacy requirements;
- offline requirement;
- model health/version;
- capability availability.

## Cognitive routes

### Route A — deterministic/reactive

Use for safety, hard constraints, exact geometry, control, simple threshold decisions and urgent local responses.

### Route B — always-on specialist

Use lightweight perception, tracking, VAD and acoustic-event models for continuous awareness.

### Route C — specialist perception

Use detection, segmentation, depth, pose, tracking, ASR and embedding models when their capability is required.

### Route D — multimodal interpretation

Escalate to VLM/audio-visual models when multiple modalities or complex scene/social interpretation are required.

### Route E — deliberative reasoning

Escalate to an LLM/reasoner when ambiguity, long-horizon planning, task decomposition or complex dialogue requires it.

### Route F — prediction/world model

Use world/predictive models when comparing future outcomes, simulating alternatives or generating policy-evaluation scenarios.

### Route G — embodied policy/VLA

Use a VLA/robot policy when a learned physical skill is appropriate and has passed its embodiment/safety gates.

### Route H — background learning

Use offline resources for consolidation, evaluation, training and adaptation. Never let background learning starve safety or interaction.

## Escalation policy

Routing should escalate only when the current capability cannot satisfy the task.

```text
cheap/fast capability
      ↓
confidence sufficient?
 ├── yes → continue
 └── no → richer capability
```

Escalation must have a maximum depth and deadline.

## De-escalation

When resources become constrained, Novi should prefer a safe lower-cost route rather than collapse entirely.

```text
full reasoning
 ↓ resource pressure
light reasoning
 ↓ further pressure
specialist/reactive
 ↓ severe degradation
safe minimum
```

## Interruption and preemption

A new event can preempt an existing cognitive task when its priority is higher. Preemption records the interrupted task, reason, state snapshot and resume/replan policy.

Safety events do not wait for ordinary routing.

## Model disagreement

When models disagree:

1. preserve both outputs;
2. compare provenance/confidence;
3. seek additional evidence if valuable;
4. escalate if consequence warrants;
5. represent uncertainty if unresolved;
6. never choose an answer solely because a larger model produced it.

## Active perception

Novi may deliberately change sensing to reduce uncertainty, for example:

```text
uncertain object identity
 ↓
attention
 ↓
reposition / change viewpoint / inspect
 ↓
new observation
 ↓
re-evaluate
```

Any movement used for active perception follows normal action governance and safety.

## Example: person enters room

```text
camera
 ↓
person detector
 ↓
tracking
 ↓
identity estimate
 ↓
attention/social relevance
 ↓
known / unknown / uncertain
 ↓
interaction decision
 ├── continue task
 ├── orient
 ├── greet
 ├── approach
 └── wait
```

A large reasoning model is only invoked if the situation actually requires it.

## Example: sudden object falls

```text
audio + vision
 ↓
fast event detection
 ↓
attention escalation
 ↓
local perception
 ↓
react / inspect if warranted
```

Novi does not wait for an LLM before taking a safe local response.

## Example: complex request during navigation

```text
navigation active
 ↓
speech detected
 ↓
ASR
 ↓
interaction attention
 ↓
VLM/LLM only if needed
 ↓
update goal/plan
 ↓
navigation resumes or changes
```

## NVIDIA candidates

NVIDIA Isaac ROS provides GPU-accelerated ROS 2 components for perception, localization/mapping, 3D reconstruction and related robotics workflows. NVIDIA explicitly positions Isaac ROS as modular and compatible with ROS 2 nodes, making it suitable as a specialist capability layer rather than the cognitive authority. citeturn0search0turn0search6

NVIDIA Cosmos 3 is a candidate for multimodal physical reasoning and world/action modeling; NVIDIA describes it as supporting vision reasoning plus world and action generation. citeturn0search12turn0search14

Isaac Sim provides a reference workflow for connecting simulated sensors and robot state to ROS 2 and validating software in simulation/HIL. citeturn0search1turn0search3

## Routing record

Every production routing decision should record:

- routing policy version;
- input/event ID;
- task classification;
- candidates considered;
- selected capability/model;
- model version;
- reason/features used;
- resource state;
- confidence;
- latency/deadline;
- fallback;
- result;
- outcome.

## Anti-patterns

Novi must not:

- route every event to an LLM;
- route based only on model size;
- hide routing decisions inside prompts;
- let a model select an unauthorized capability;
- ignore resource/thermal state;
- silently fall back to a materially different model;
- confuse prediction with evidence;
- bypass safety because a model has high confidence.

## Acceptance criteria

The routing architecture must demonstrate:

1. continuous low-cost perception;
2. correct escalation under ambiguity;
3. fast reaction to urgent events;
4. interruption and resume;
5. resource-aware degradation;
6. model failure fallback;
7. model disagreement handling;
8. active perception;
9. offline operation;
10. complete routing audit records;
11. no direct model-to-motor authority.
