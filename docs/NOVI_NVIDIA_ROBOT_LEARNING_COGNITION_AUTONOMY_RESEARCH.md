# NVIDIA Robot Learning, Cognition & Autonomy Research for NOVI

**Date:** 22 August 2026  
**Status:** Research and architecture input  
**Scope:** Analysis of NVIDIA's Robot Learning material and adjacent official NVIDIA/GR00T resources, focused on robot brain training, cognition, context awareness, autonomy, data, simulation, and practical adoption for Novi.

---

## 1. Executive conclusion

NVIDIA's current robot-learning stack is highly relevant to Novi, but it does **not** provide a single “robot brain” product that should replace Novi's architecture.

The strongest pattern across NVIDIA's material is an iterative physical-AI loop:

```text
REAL / INTERNET / SYNTHETIC DATA
            ↓
      DATA PROCESSING
            ↓
   DEMONSTRATIONS + POLICIES
            ↓
 IMITATION / RL / FOUNDATION MODEL
            ↓
   ISAAC LAB TRAINING + EVALUATION
            ↓
 ISAAC SIM / PHYSICS / SENSOR VALIDATION
            ↓
      REAL ROBOT DEPLOYMENT
            ↓
 PERCEIVE → DECIDE → ACT → OBSERVE
            ↓
      NEW EXPERIENCE / DATA
            ↺
```

For Novi, this should be expanded into a cognitive architecture:

```text
SENSORS
  ↓
PERCEPTION
  ↓
EVIDENCE + UNCERTAINTY
  ↓
WORLD STATE / CONTEXT
  ↔
MEMORY + KNOWLEDGE
  ↓
REASONING / DIALOGUE / GOAL MANAGEMENT
  ↓
PLANNING
  ↓
SKILL SELECTION / LEARNED POLICY
  ↓
ACTION PROPOSAL
  ↓
GOVERNANCE + SAFETY
  ↓
ROS 2 / CONTROLLER
  ↓
ROBOT
  ↓
OBSERVATION / OUTCOME
  ↺
```

**Key decision:** NVIDIA technologies should accelerate specific capabilities, while Novi owns cognition, identity, memory semantics, world-state semantics, autonomy policy, provenance, safety boundaries, and the contracts between components.

---

# 2. What NVIDIA means by robot learning

NVIDIA's Robot Learning material describes a transition from fixed, hand-programmed behaviors to learned policies that map observations and robot state to actions.

The learning methods explicitly highlighted are:

1. **Imitation learning** — learn from demonstrations by humans or robots.
2. **Reinforcement learning** — improve behavior using rewards and penalties.
3. **Supervised learning** — learn a task from labeled examples.
4. **Self-supervised learning** — derive useful learning signals from unlabeled data.

For Novi these are not alternatives. They should occupy different roles.

| Novi problem | Preferred approach |
|---|---|
| Understand objects/people | supervised + foundation models |
| Learn a manipulation skill | imitation learning |
| Improve robustness in simulation | reinforcement learning |
| Recover from unusual states | corrective demonstrations / DAgger-style data aggregation |
| Learn reusable representations | self-supervised / foundation-model pretraining |
| Long-horizon task sequencing | planning + reasoning, not raw motor RL alone |
| Social/context-aware interaction | multimodal context + memory + language models |

**Important:** a learned policy is not equivalent to cognition. A policy can perform a skill; Novi's cognitive layer should decide *whether*, *when*, *why*, and *under what constraints* that skill is invoked.

---

# 3. The NVIDIA end-to-end learning workflow

The official workflow can be interpreted as:

```text
1. COLLECT / CURATE DATA
        ↓
2. GENERATE SYNTHETIC VARIATIONS
        ↓
3. TRAIN OR POST-TRAIN MODEL
        ↓
4. VALIDATE IN SIMULATION
        ↓
5. EVALUATE POLICY
        ↓
6. DEPLOY TO ROBOT
        ↓
7. RUN CLOSED LOOP
        ↓
8. COLLECT FAILURES / CORRECTIONS
        ↓
9. UPDATE DATASET
        ↺
```

For Novi, every transition should produce an artifact with provenance:

```text
episode
sensor configuration
robot embodiment
task
environment version
simulation version
model version
policy version
prompt / goal representation
actions
outcomes
failure reason
human intervention
safety events
timestamp
```

This is essential if Novi is to learn continuously without becoming impossible to debug.

---

# 4. Isaac Lab: where learned robot skills should be developed

Isaac Lab is NVIDIA's open-source, GPU-accelerated robot-learning framework. It supports reinforcement learning and imitation learning and can operate across multiple robot embodiments and simulation backends.

## Recommended Novi role

Use Isaac Lab for:

- training navigation or manipulation policies;
- imitation learning from demonstrations;
- reinforcement learning for robustness;
- domain randomization;
- perception-in-the-loop training;
- sim-to-real experiments;
- regression testing of learned skills;
- large-scale policy evaluation.

Do **not** use Isaac Lab as Novi's memory or cognition system.

The architectural boundary should be:

```text
Novi Cognitive Layer
        ↓ goal + constraints
Novi Skill Contract
        ↓
Learned Policy Adapter
        ↓
Isaac-trained policy / conventional skill
        ↓
Safety + controller
```

A policy should receive only the state/action representation required for its task.

---

# 5. Isaac Sim: the world where Novi can fail safely

Isaac Sim provides physically based simulation, sensor simulation, testing, and synthetic-data generation.

It can ingest robot and environment descriptions including CAD, URDF and real-world captures, then represent the scene in OpenUSD.

For Novi:

```text
REAL ENVIRONMENT
      ↓ capture / reconstruction
OpenUSD representation
      ↓
ISAAC SIM
      ↓
many controlled variations
      ↓
synthetic observations + trajectories
      ↓
policy training / evaluation
```

Useful randomizations include:

- lighting;
- textures;
- reflections;
- object positions;
- object orientations;
- camera parameters;
- sensor noise;
- friction and mass;
- clutter;
- partial occlusion.

The objective is not “perfect simulation.” The objective is to expose the policy to enough meaningful variation that it transfers more reliably to reality.

---

# 6. Imitation learning: the best initial learning strategy for Novi

For a small autonomous robot, imitation learning is likely to be the most practical first path to learned physical skills.

NVIDIA's current workflow supports:

```text
human demonstration
      ↓
video + robot state + action trajectory
      ↓
clean / synchronize / validate
      ↓
LeRobot-format dataset
      ↓
GR00T or another policy
      ↓
evaluation
      ↓
simulation + real closed-loop testing
```

NVIDIA's GR00T guidance emphasizes that data quality matters heavily. Clean demonstrations, stable motions, diverse approaches, and successful trajectories are more useful than simply accumulating noisy recordings.

## Novi recommendation

Start with a small, measurable skill:

```text
locate object
→ approach object
→ align
→ interact
→ verify result
```

Record:

```json
{
  "episode_id": "uuid",
  "goal": "move_to_object",
  "observations": {
    "rgb": [],
    "depth": [],
    "robot_state": []
  },
  "actions": [],
  "result": {
    "success": true,
    "failure_mode": null
  },
  "provenance": {}
}
```

Do not begin by attempting to train “general intelligence.”

---

# 7. Reinforcement learning: where it fits

RL is powerful when Novi needs to optimize a measurable behavior through repeated simulation.

Good candidates:

- locomotion;
- obstacle avoidance;
- navigation robustness;
- grasp approach;
- recovery;
- energy efficiency;
- trajectory optimization;
- behavior under randomized environments.

Less appropriate as the first solution for:

- natural conversation;
- semantic memory;
- user preference understanding;
- general reasoning.

For Novi, RL should be a **skill optimization mechanism**, not the whole brain.

---

# 8. Isaac GR00T: the closest NVIDIA component to a learned embodied action model

GR00T is NVIDIA's open robot foundation-model platform. Current GR00T N1.7 is a vision-language-action model that accepts multimodal input including language and images and produces continuous robot actions through a vision-language backbone plus a diffusion-transformer action head.

The important conceptual separation is:

```text
COGNITION
What should I achieve?

        ↓

PLANNING
What sequence of capabilities is required?

        ↓

VLA / POLICY
How should this embodied robot execute this skill now?

        ↓

CONTROLLER
How are commands executed safely?
```

Novi should not ask GR00T to become its permanent memory, user model, safety authority, or global planner.

## GR00T data workflow

NVIDIA's current reference workflow is:

```text
robot demonstrations
(video + state + actions)
          ↓
GR00T / LeRobot-compatible format
          ↓
modality + embodiment configuration
          ↓
fine-tuning
          ↓
open-loop evaluation
          ↓
simulation
          ↓
closed-loop robot evaluation
```

Current repository examples include custom-embodiment workflows, meaning Novi can study GR00T even if its embodiment differs from NVIDIA's reference humanoids.

---

# 9. GR00T data available to study

NVIDIA provides several useful forms of data and examples.

## 9.1 Included demonstration data

The GR00T repository includes examples based on datasets/robots such as:

- DROID;
- LIBERO;
- SimplerEnv;
- Google Robot;
- SO-100 custom-embodiment examples.

These are useful primarily for understanding data schemas and the training pipeline.

## 9.2 Physical AI datasets

NVIDIA's Physical AI dataset ecosystem includes robot-learning datasets, including a large GR00T cross-embodiment simulation corpus and tuned task families.

One surfaced NVIDIA dataset guide describes the large GR00T cross-embodiment simulation corpus as approximately 1.91 TB and composed of hundreds of thousands of trajectories across bimanual, humanoid and other robot configurations.

**Novi recommendation:** do not download multi-terabyte datasets simply because they exist. First define the learning objective, embodiment, sensors, action space and benchmark. Then retrieve only relevant subsets.

## 9.3 EgoScale and human video

GR00T N1.7 incorporates large-scale human egocentric video into pretraining to improve generalization and language following.

This suggests an important lesson for Novi:

> Human video can help learn broad visual and behavioral priors, but robot-specific control still requires embodiment-aware data and evaluation.

Internet-scale video should therefore be treated as representation/prior data, not direct motor-command supervision.

---

# 10. Synthetic data: one of the biggest opportunities for Novi

NVIDIA explicitly recommends combining:

```text
REAL ROBOT DATA
        +
SYNTHETIC DATA
        +
INTERNET-SCALE DATA
```

Different sources solve different problems.

| Data | Main use |
|---|---|
| Real robot demonstrations | embodiment-specific behavior |
| Synthetic trajectories | diversity and scale |
| Simulation observations | perception and policy robustness |
| Internet/human video | broad visual/behavior priors |
| Failure/correction data | recovery and edge cases |

## GR00T-Mimic / synthetic demonstrations

NVIDIA provides workflows for expanding a small number of demonstrations into many synthetic trajectories.

The practical pattern is:

```text
small number of expert demonstrations
            ↓
annotate / parameterize task
            ↓
generate variations
            ↓
quality filtering
            ↓
large synthetic trajectory set
            ↓
train policy
```

This is extremely relevant to Novi because collecting physical demonstrations may be slow.

However, generated trajectories must be evaluated. Synthetic quantity is not automatically useful.

---

# 11. The cognition gap: what NVIDIA's robot-learning stack does not solve for Novi by itself

NVIDIA provides strong infrastructure for perception, simulation, policies and physical-AI models. But Novi still needs its own persistent cognitive architecture.

Novi needs explicit answers to:

```text
WHO is interacting with me?
WHERE am I?
WHAT objects exist?
WHAT happened earlier?
WHAT is the current goal?
WHAT is being referred to by “that”?
WHAT do I believe?
HOW certain am I?
WHAT changed?
WHAT am I allowed to do?
WHAT action is currently running?
DID it succeed?
WHAT should I do after failure?
```

This suggests the following Novi Brain layers.

---

# 12. Proposed Novi cognition architecture

```text
                    ┌──────────────────────┐
                    │    MULTIMODAL INPUT  │
                    │ vision / audio / IMU │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │     PERCEPTION       │
                    │ objects / people /   │
                    │ speech / spatial     │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │ EVIDENCE + TRACKING  │
                    │ timestamps/confidence│
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │ WORLD / CONTEXT STATE│
                    │ entities / relations │
                    │ events / beliefs     │
                    └───────┬────────┬─────┘
                            ↕        ↕
                    ┌───────────┐ ┌───────────┐
                    │  MEMORY   │ │ KNOWLEDGE │
                    └─────┬─────┘ └─────┬─────┘
                          └──────┬──────┘
                                 ↓
                    ┌──────────────────────┐
                    │ COGNITION / REASONING│
                    │ goals / uncertainty  │
                    │ dialogue / decisions │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │      PLANNING        │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │ SKILLS / VLA POLICIES│
                    │ GR00T / RL / classic │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │ GOVERNANCE + SAFETY  │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │ ROS 2 / CONTROLLERS  │
                    └──────────────────────┘
```

NVIDIA technologies plug into this architecture; they do not define it.

---

# 13. World model and context for natural interaction

For Novi to understand:

> “Bring me that.”

the cognitive system needs more than conversation history.

It needs:

```text
CURRENT SPEAKER
CURRENT LOCATION
RECENT DIALOGUE
VISIBLE OBJECTS
OBJECT IDENTITIES
GAZE / GESTURE IF AVAILABLE
RECENT EVENTS
CURRENT TASK
SPATIAL RELATIONS
LONG-TERM RELEVANT MEMORY
UNCERTAINTY
```

Example:

```text
utterance:
"Bring me that."

context:
speaker = person_01
recent_topic = coffee
gaze_target = cup_12
visible_objects = [cup_12, phone_8]
current_goal = none

belief:
referent(cup_12) = 0.94
referent(phone_8) = 0.04
```

Then the cognition layer can decide whether to act or clarify.

This world/context layer is a core Novi responsibility.

---

# 14. Autonomy should be hierarchical

NVIDIA's learning stack supports policies, but a safe autonomous robot should not be a single model directly connected to motors.

Recommended hierarchy:

```text
LEVEL 0 — HARD SAFETY
emergency stop / limits / collision

LEVEL 1 — CONTROL
motor commands / feedback

LEVEL 2 — SKILLS
navigate / inspect / grasp / follow

LEVEL 3 — POLICIES
VLA / RL / imitation

LEVEL 4 — TASK PLANNING
decompose goals

LEVEL 5 — COGNITION
context / memory / reasoning / dialogue

LEVEL 6 — LONG-TERM ADAPTATION
evaluate experience / curate data / retrain offline
```

The most important rule:

```text
FOUNDATION MODEL
      ↓ candidate action
SAFETY / AUTHORIZATION
      ↓
CONTROLLER
      ↓
ROBOT
```

Never:

```text
LLM/VLA → raw motor control with no independent boundary
```

---

# 15. Closed-loop autonomy

NVIDIA's GR00T deployment guidance emphasizes that open-loop evaluation is not sufficient. Final validation must happen in closed loop.

Novi should therefore operate as:

```text
OBSERVE
  ↓
UPDATE WORLD STATE
  ↓
SELECT / CONTINUE GOAL
  ↓
PLAN
  ↓
ACT
  ↓
VERIFY
  ↓
SUCCESS?
 ├── yes → continue / finish
 └── no  → recover / ask / stop
```

Every physical skill should define:

```text
preconditions
expected observations
action
success criteria
failure criteria
timeout
recovery options
safety constraints
```

Example:

```yaml
skill: pick_object

preconditions:
  - object_visible
  - object_reachable

success:
  - object_in_gripper

failure:
  - grasp_timeout
  - object_lost
  - collision_risk

recovery:
  - reobserve
  - reposition
  - retry_limited
  - request_help
```

This is where deterministic engineering and learned policies must work together.

---

# 16. Learning from failure

A promising Novi learning loop is:

```text
INITIAL DEMONSTRATIONS
        ↓
TRAIN INITIAL POLICY
        ↓
RUN IN SIMULATION
        ↓
RUN ON ROBOT
        ↓
FAILURE?
        ↓ yes
CAPTURE CONTEXT + HUMAN CORRECTION
        ↓
ADD HIGH-VALUE EPISODE
        ↓
RETRAIN / POST-TRAIN
        ↺
```

NVIDIA's GR00T FAQ recommends an iterative approach using initial demonstrations followed by human-gated corrections to cover states where pure behavior cloning fails.

For Novi, store failures as first-class training artifacts:

```json
{
  "episode": "uuid",
  "goal": "pick cup",
  "failure": "grasp slipped",
  "world_state_before": {},
  "policy_version": "x",
  "human_correction": {},
  "recovery_success": true
}
```

---

# 17. Isaac TeleOp and demonstrations

Isaac TeleOp is relevant for collecting demonstrations in real and simulated environments.

For Novi, teleoperation should be treated as a data-acquisition capability.

Possible progression:

```text
Phase 1
keyboard/gamepad demonstration

Phase 2
VR / spatial teleoperation

Phase 3
assisted teleoperation

Phase 4
policy-assisted demonstration

Phase 5
human intervention only on failures
```

The goal is to reduce the cost of producing high-quality episodes.

---

# 18. Simulation-first, not simulation-only

The strongest NVIDIA lesson is not “simulate everything forever.”

It is:

```text
SIMULATE EARLY
TEST AT SCALE
FAIL SAFELY
TRANSFER TO REALITY
MEASURE THE GAP
COLLECT REAL FAILURES
UPDATE THE DATA
```

Novi should maintain separate evidence classes:

```text
OBSERVED
INFERRED
PREDICTED
SIMULATED
COUNTERFACTUAL
HYPOTHESIZED
VERIFIED
```

A simulated event must never silently become a remembered real-world fact.

---

# 19. Cosmos and cognition

NVIDIA's robot-learning page now places Cosmos 3 in the physical-AI data and closed-loop simulation workflow.

For Novi, world/foundation models are potentially useful for:

- generating plausible future observations;
- synthetic data;
- scenario generation;
- counterfactual testing;
- physical reasoning experiments;
- training perception or policy components.

But:

```text
WORLD-MODEL PREDICTION != OBSERVATION
```

The Novi world state should retain provenance and uncertainty for predictions.

---

# 20. Data architecture recommended for Novi

Create one conceptual dataset schema capable of representing real, simulated and synthetic episodes.

```text
NOVI EPISODE
│
├── metadata
│   ├── episode_id
│   ├── source
│   ├── timestamp
│   └── provenance
│
├── embodiment
│   ├── robot model
│   ├── sensors
│   └── action space
│
├── task
│   ├── natural language goal
│   ├── structured goal
│   └── constraints
│
├── observations
│   ├── vision
│   ├── depth
│   ├── audio
│   ├── proprioception
│   └── world-state snapshot
│
├── actions
│
├── events
│
├── outcome
│   ├── success
│   ├── failure type
│   └── metrics
│
└── learning annotations
    ├── human correction
    ├── quality
    └── dataset split
```

Then implement adapters:

```text
NoviEpisode
    ├── LeRobotAdapter
    ├── IsaacLabAdapter
    ├── ROSBagAdapter
    └── NoviNativeStorage
```

This prevents NVIDIA formats from becoming the semantic source of truth.

---

# 21. What Novi should actually build first

## Stage A — cognitive core

Before training a neural policy:

1. Event model.
2. Sensor evidence model.
3. World-state graph.
4. Working memory.
5. Episodic memory.
6. Goal manager.
7. Context assembler.
8. Action/skill contract.
9. Safety and authorization boundary.
10. Simulation adapter.

## Stage B — simulated embodiment

Build a simulated robot first.

```text
simulated sensors
      ↓
perception adapters
      ↓
Novi world state
      ↓
reasoning / planner
      ↓
mock skills
      ↓
Isaac / simulation
```

## Stage C — first learned skill

Choose exactly one benchmark:

```text
object identification
→ approach
→ pick / interact
→ verify
```

Collect demonstrations and establish:

- baseline;
- success metric;
- failure taxonomy;
- simulation evaluation;
- real-world evaluation.

## Stage D — synthetic scaling

Use simulation and trajectory generation to diversify the initial demonstrations.

## Stage E — iterative adaptation

Add corrective data from failures.

Only after this should Novi attempt broad generalist policy training.

---

# 22. Recommended technology mapping

| Novi capability | Candidate NVIDIA technology |
|---|---|
| Robot middleware/perception | Isaac ROS / ROS 2 |
| Simulation | Isaac Sim |
| Robot learning | Isaac Lab |
| Generalist VLA research | Isaac GR00T |
| Synthetic manipulation trajectories | GR00T-Mimic / SkillGen workflows |
| Real/sim demonstrations | Isaac TeleOp |
| Physical-AI synthetic/world workflows | Cosmos |
| Scene interchange | OpenUSD |
| Real-world scene reconstruction | NuRec |
| Edge deployment | Jetson |
| Optimized inference | TensorRT |
| Large-scale training orchestration | OSMO |

These are candidate implementations, not mandatory dependencies.

---

# 23. Immediate architecture decision for Novi

The recommended boundary is:

```text
┌──────────────────────────────────────────┐
│               NOVI CORE                  │
│                                          │
│ Context                                  │
│ World State                              │
│ Memory                                   │
│ Knowledge                                │
│ Cognition                                │
│ Dialogue                                 │
│ Goals                                    │
│ Planning                                 │
│ Governance                               │
│ Safety                                   │
│ Provenance                               │
└───────────────────┬──────────────────────┘
                    │ stable contracts
        ┌───────────┼────────────┐
        ↓           ↓            ↓
   NVIDIA stack   Other stack   Reference
        │           │            │
  Isaac Lab      MuJoCo       Mock/sim
  Isaac Sim      ROS          Local model
  GR00T          VLA          Deterministic
  TensorRT
```

This is the strongest long-term architecture because Novi remains portable while benefiting from NVIDIA's rapidly evolving physical-AI ecosystem.

---

# 24. Priority experiments

## Experiment 1 — Context-aware simulation

Goal:

```text
Can Novi correctly resolve language references using world context?
```

Example:

> “Bring me that cup.”

Inputs:

- language;
- visible objects;
- object IDs;
- spatial relations;
- recent conversation.

Metric:

- referent resolution accuracy.

No robot hardware required.

## Experiment 2 — Skill contract

Goal:

```text
Can Novi invoke a skill independently of implementation?
```

Implement:

```text
NavigateSkill
InspectSkill
FindObjectSkill
PickSkill
SpeakSkill
```

Initially use deterministic/mock implementations.

## Experiment 3 — Demonstration dataset

Collect a small number of clean episodes for one task.

Compare:

- direct behavior cloning;
- synthetic augmentation;
- corrective episodes.

## Experiment 4 — Isaac Lab transfer

Run the same skill through simulation.

Measure:

- success rate;
- robustness under randomization;
- failure classes.

## Experiment 5 — GR00T custom embodiment feasibility

Only after the action space and hardware are sufficiently stable:

```text
prepare LeRobot data
→ custom embodiment config
→ fine-tune
→ open-loop evaluation
→ simulation
→ closed-loop evaluation
```

---

# 25. Final recommendation

NVIDIA's current robot-learning ecosystem gives Novi a strong implementation path:

```text
COGNITION
Novi-owned
        ↓
WORLD CONTEXT + MEMORY
Novi-owned
        ↓
GOAL / PLAN
Novi-owned
        ↓
SKILL SELECTION
Novi-owned
        ↓
LEARNED POLICY
Isaac Lab / GR00T candidate
        ↓
PHYSICAL VALIDATION
Isaac Sim
        ↓
SIM-TO-REAL
real robot
        ↓
DATA + FAILURE + CORRECTION
        ↓
CONTINUAL OFFLINE IMPROVEMENT
```

The strategic mistake would be to start by building a giant neural network called “the brain.”

The better path is to build:

1. a persistent cognitive state;
2. a world/context model;
3. memory;
4. goal and planning infrastructure;
5. explicit skills;
6. simulation;
7. one learned policy at a time;
8. a data flywheel based on demonstrations, synthetic variation, failures and corrections.

**North-star principle:**

> Novi should be an embodied autonomous intelligence whose cognition maintains a persistent, uncertain, provenance-aware model of people, objects, places, events and goals; whose learned models provide perception and physical skills; and whose autonomy continuously closes the loop between observation, reasoning, action, verification and offline learning.

---

# Sources reviewed

Primary sources and implementation references:

- NVIDIA Robot Learning use case: https://www.nvidia.com/en-gb/use-cases/robot-learning/
- NVIDIA Isaac Lab: https://developer.nvidia.com/isaac/lab
- NVIDIA Isaac Sim: https://developer.nvidia.com/isaac/sim/
- NVIDIA Isaac platform: https://developer.nvidia.com/isaac/
- NVIDIA Isaac GR00T repository: https://github.com/NVIDIA/Isaac-GR00T
- NVIDIA GR00T end-to-end policy workflow article.
- NVIDIA GR00T synthetic motion generation material.
- Existing Novi NVIDIA research already present in the Library.

## Evidence notes

NVIDIA product pages describe intended capabilities and workflows. Claims about superiority or suitability for Novi should still be validated through reproducible benchmarks, hardware constraints, simulation results, and real-world evaluation.

GR00T N1.7 is currently marked as Early Access in the official repository at the time of this research, so it should be treated as a research/prototyping dependency until its stability and production status meet Novi requirements.
