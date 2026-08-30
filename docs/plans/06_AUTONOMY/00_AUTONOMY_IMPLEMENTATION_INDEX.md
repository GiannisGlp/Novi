# Autonomy Implementation Workstream

## Purpose

Build Novi from a cognition-capable software brain into a bounded, measurable, embodied autonomous system that can perceive, understand, choose goals, plan, act, verify outcomes, recover from failure, learn from experience, and safely continue operating without requiring a human to specify every intermediate step.

This workstream is the bridge between Novi's existing cognition/memory/perception capabilities and a real robot autonomy loop.

## North-star autonomy loop

```text
Sensors
  ↓
Perception
  ↓
World State + Uncertainty
  ↓
Memory + Prediction
  ↓
Goal Manager
  ↓
Decision / Deliberation
  ↓
Planner
  ↓
Policy / Safety Gate
  ↓
Skill Executor
  ↓
Verification
  ↓
Learning / Memory Update
  ↓
World State
  ↺
```

Autonomy is successful only when this loop can run repeatedly, remain bounded, recover from expected failures, and produce evidence of what it believed, attempted, observed, changed, and learned.

## Existing starting point

Novi already has a planned autonomy boundary covering decision-making, goals, behavior selection, planning orchestration, memory use, bounded behavior, interruption handling and eventual simulation validation. The current repository also has the perception, tracking, memory, knowledge, prediction, reasoning, BrainDriver and response infrastructure developed in earlier work.

## Plan documents

| Plan | Scope | Priority |
|---|---|---:|
| `01_AUTONOMY_ARCHITECTURE.md` | autonomy architecture, lifecycle, authority model, control loop | P0 |
| `02_GOALS_AND_MOTIVATION.md` | goals, priorities, deadlines, autonomy modes, goal arbitration | P0 |
| `03_WORLD_STATE_MEMORY_PREDICTION.md` | grounded world state, spatial memory, temporal prediction, belief revision | P0 |
| `04_ACTIVE_PERCEPTION.md` | query-driven perception, LocateAnything, information gathering | P0 |
| `05_PLANNING_AND_SKILLS.md` | hierarchical planning, behavior trees, skills, execution and verification | P0 |
| `06_EXPLORATION_AND_CURIOSITY.md` | novelty, uncertainty reduction, exploration and information gain | P1 |
| `07_METACOGNITION_RECOVERY_LEARNING.md` | confidence, self-monitoring, failure recovery, continual learning | P1 |
| `08_SAFETY_GOVERNANCE_HUMAN_OVERRIDE.md` | safety monitors, authority boundaries, vetoes, emergency handling | P0 |
| `09_SIMULATION_EVALUATION_EVIDENCE.md` | simulation-first validation, scenarios, metrics, evidence and regression | P0 |
| `10_RUNTIME_DEPLOYMENT_AND_HARDWARE.md` | Mac development, NVIDIA/Jetson transition, ROS2 and runtime architecture | P1 |
| `11_IMPLEMENTATION_SEQUENCE.md` | exact dependency-ordered execution sequence and acceptance gates | P0 |
| `12_AIRLLM_ADAPTATION_AND_INFERENCE_RUNTIME_PLAN.md` | Novi-owned inference runtime, AirLLM backend adaptation, model routing, scheduling, compatibility, benchmarking and future large-model readiness | P0/P1 |

## Priority model

- **P0:** required before claiming embodied autonomy.
- **P1:** required for robust long-running autonomy.
- **P2:** advanced capability after the closed loop is reliable.

## Core design principles

1. **The LLM/VLM is not the safety controller.** Models propose; deterministic systems validate and execute.
2. **Every autonomous action has a reason, authority, precondition, postcondition and timeout.**
3. **No action is considered successful merely because a model said it succeeded.** The world must provide verification evidence.
4. **Uncertainty is first-class data.** Unknown, stale and contradictory information must remain distinguishable from facts.
5. **Autonomy must be interruptible at every stage.**
6. **Memory must distinguish observation, belief, inference, intention, action and verified outcome.**
7. **Perception is active.** Novi should spend expensive computation only when additional information can change a decision.
8. **Simulation precedes risky physical execution.**
9. **Hardware-specific systems stay behind interfaces.** Mac/MPS is the development platform; NVIDIA/Jetson/ROS2 is a future deployment backend.
10. **Every milestone must have machine-readable evidence.**
11. **Inference infrastructure stays behind a Novi-owned contract.** AirLLM, Transformers, vLLM, TensorRT-LLM or any future backend must not become a cognitive dependency.
12. **Model choice is evidence-driven.** Current model roles are hypotheses until Novi benchmarks establish quality, latency, resource and reliability characteristics.

## Definition of done for autonomy

Novi must eventually demonstrate a long-running scenario in which it:

1. receives an open-ended goal;
2. determines whether it has authority to pursue it;
3. decomposes it into bounded subgoals;
4. gathers missing information;
5. maintains a grounded world model;
6. selects and executes skills;
7. handles interruption and changing conditions;
8. detects failed or unverifiable actions;
9. replans or asks for help when appropriate;
10. verifies successful completion;
11. records the experience;
12. improves future decisions without silently corrupting trusted knowledge.

## Recommended order

Do **not** implement autonomy as one giant agent loop. Implement the contracts first, then the deterministic control loop, then perception/planning integration, then learning and exploration, and only then increase autonomy duration and physical authority.

For inference specifically, implement the Novi-owned inference contract and preserve the current Mac Brain path before enabling AirLLM. The AirLLM workstream's first concrete target is Qwen3.8-27B, with AirLLM remaining an optional backend rather than a cognitive layer. The current approved model set is `qwen3.8:27b`, `qwen3:8b`, `nemotron-3.5-lightning:latest`, `qwen3.8:latest`, and `qwen3:4b`; future larger models must enter through the same registry, compatibility, benchmark and acceptance gates.
