# 09 — Gap Analysis: NVIDIA (brain-phase actionable)

## Docs: NOVI_NVIDIA_ROBOT_LEARNING_COGNITION_AUTONOMY_RESEARCH.md + 02/14, 03/19, 01/18.
NVIDIA is reference acceleration/simulation; it never defines Novi's semantics. Novi
owns cognition, world state, memory, goals, planning, governance, safety, provenance.

## Brain-phase applicable conclusions (from the research)
- Build the cognitive core FIRST: event model, sensor-evidence model, world-state graph,
  working + episodic memory, goal manager, context assembler, action/skill contract,
  safety/authorization boundary, simulation adapter (research 21 Stage A).
- Context-aware reference resolution ("Bring me that cup"): current speaker, location,
  dialogue, visible objects, object identities, recent events, current task, spatial
  relations, uncertainty (13).
- Hierarchical autonomy (7 levels; long-term adaptation top) and closed-loop validation
  (observe -> plan -> act -> verify -> recover/ask/stop) with explicit preconditions,
  success/failure criteria, timeout, recovery, safety constraints per skill (14/15).
- Unified episode dataset schema with provenance + adapters (LeRobot / IsaacLab /
  ROSBag / NoviNative) so NVIDIA formats never become the semantic source of truth (20).
- Simulation-first, not simulation-only; evidence classes OBSERVED/INFERRED/PREDICTED/
  SIMULATED/COUNTERFACTUAL; sim events never silently become facts (18/19).
- Priority experiments with NO hardware: (1) context-aware reference, (2) skill contract,
  (3) demonstration dataset, (4) Isaac Lab transfer, (5) GR00T custom embodiment (24).
- Candidate stack: Nemotron 3 Nano Omni (multimodal), Cosmos Reason2 (spatiotemporal),
  Cosmos 3 (simulation), GR00T (future policy), TensorRT on Jetson; all behind adapters +
  benchmark-before-select (docs/brain).

## Exists today
- Portability seams: ObjectDetector protocol, embedding provider, neural_backend bridge,
  recognition.py (voice/face boundaries), Ollama local LLM, real SSDLite via torchvision.
- No Jetson/CUDA/TensorRT/ROS2/Isaac code (correct: hardware-phase).

## Delta for the brain phase (what to build on the Mac, now)
- **Skill contract** module (NavigateSkill/InspectSkill/FindObjectSkill/PickSkill/
  SpeakSkill) with preconditions, success/failure, recovery — deterministic/mock first
  (NVIDIA Experiment 2). The Plan/Propose/Act path exists but lacks the formal skill
  contract.
- **Unified NoviEpisode schema + adapters** for demonstrations (so data is portability).
- **Context assembler for reference resolution** (Experiment 1) — folds into Cognition.
- **Closed-loop verify step** in the runtime loop (OBSERVE->PLAN->ACT->VERIFY with
  outcome/failure handling) — partial via b1_outcomes; make it first-class.
- **Evidence-class labels** (OBSERVED/INFERRED/PREDICTED/SIMULATED) on world-state and
  memory records so simulations never become facts (ties to Memory).
- **Benchmark/ADR discipline**: any real NVIDIA component selected only behind a pinned
  tuple (JetPack/L4T/ROS2/TensorRT) + Novi benchmark + ADR; keep as gated campaign.

## Next Action (roadmap Step 5) — COMPLETE
Run the no-hardware NVIDIA experiments on the Mac with deterministic/mock skill
implementations: (2) skill contract, (1) context-aware reference resolution, (3) a
small clean demonstration dataset in the NoviEpisode schema. These validate the
architecture and produce the evidence the docs require without a robot.

**Done:** all three experiments implemented in `novi/brain/nvidia_experiments.py`
(`run_nvidia_experiments()`), wired through `EpisodeRecorder` into the runtime,
and green under `test_nvidia_experiments.py` (see status table below).

---

## Implementation status (verified 2026-08-29)

Step 5 (and the brain-phase deltas above) are **implemented and green** in
`novi/brain/`. Evidence class per research §18 is now complete (added
`HYPOTHESIZED`).

| Research item | Implementation | Status |
|---|---|---|
| §21 Stage A — event model | `event_bus.py` (EventEnvelope/EventBus, privacy-ranked) | **DONE** |
| §21 Stage A — sensor evidence model | `canonical.py` + contract `novi.observation` (registry.json), `belief_revision.py` | **DONE** |
| §21 Stage A — world-state graph | `world_model.py` (WorldModel/WorldEntity/WorldRelation/Contradiction), `kgraph.py` | **DONE** |
| §21 Stage A — working + episodic memory | engine memory + `memory_classes.py` (EPISODIC routing), `memory_hardening.py` | **DONE** |
| §21 Stage A — goal manager | `autonomy.py` (`BoundedGoalController`, arbitration, conflicts) | **DONE** |
| §21 Stage A — context assembler | `context_assembler.py` (layered, budgeted, privacy-filtered) | **DONE** |
| §21 Stage A — action/skill contract | `skill_contract.py` (Navigate/Inspect/FindObject/Pick/Speak) | **DONE** |
| §21 Stage A — safety/authorization boundary | `governance_guard.py`, `safety_policy.py` (risk classes R0-R5, invariants) | **DONE** |
| §21 Stage A — simulation adapter | `simulation.py` (SimPy closed-loop model), `virtual_skills.py` (SimBody/SimWorld), `scenario_suite.py` | **DONE** |
| §13 context-aware reference resolution | `context_assembler.resolve_reference` ("Bring me that cup") | **DONE** |
| §14 hierarchical autonomy | `autonomy_state_machine.py`, `autonomy_supervisor.py` (authority levels, leases, authorization) | **DONE** |
| §15 closed-loop + skill lifecycle | `closed_loop.py` (first-class VERIFY, recover/ask/stop) + skill preconditions/success/failure/timeout/recovery | **DONE** |
| §16 learning from failure | `failure_modes.py`, `recovery.py` (FailureClassifier, RecoveryPlanner, CounterfactualRecorder, RegressionMemory) | **DONE** |
| §18 evidence classes (7) | `world_model.py` + `memory_hardening.py` (OBSERVED/INFERRED/PREDICTED/SIMULATED/COUNTERFACTUAL/HYPOTHESIZED/VERIFIED); hypothetical never overwrites observed | **DONE** |
| §19 world-model prediction ≠ observation | `prediction.py`, `b2_cosmos_reason.py`; provenance/uncertainty on predictions | **DONE** |
| §20 unified episode schema + adapters | `nvidia_experiments.py` (NoviEpisode + LeRobot/IsaacLab/ROSBag/NoviNative adapters, evidence preserved) | **DONE** |
| §24 Exp 1 — context-aware reference | `run_nvidia_experiments()` `nvidia_exp_1` (E2) | **DONE** |
| §24 Exp 2 — skill contract | `run_nvidia_experiments()` `nvidia_exp_2` (E2) | **DONE** |
| §24 Exp 3 — demonstration dataset | `run_nvidia_experiments()` `nvidia_exp_3` (E3); `EpisodeRecorder` + runtime wiring | **DONE** |
| §17 TeleOp Phase 1 (keyboard demo) | `teleop.py` (`TeleOpSession` drives `SimBody`/`SimWorld`, records NoviEpisode steps with provenance; `python -m novi.brain.teleop`) | **DONE** (Phases 2–5 VR/assisted/policy/human-gated → hardware) |
| §24 Exp 4 — learned-policy adapter seam | `policy_adapter.py` (`LearnedPolicy`/`PolicySkillAdapter`; `IsaacPolicyBackend` gated loudly on Mac; contract boundary preserved) | **DONE** (seam) |
| §24 Exp 4 — sim transfer benchmark | `policy_adapter.run_policy_benchmark` — success rate, robustness under randomization, failure classes; all results SIMULATED | **DONE** (actual Isaac training → hardware/GPU) |
| §24 Exp 5 — LeRobot data prep | `lerobot_export.export_lerobot_dataset` (LeRobot layout: meta/info.json, meta/episodes, frame data + validation) | **DONE** (prep) |
| §24 Exp 5 — GR00T embodiment config | `lerobot_export.build_gr00t_embodiment_config` (sensors/observation/action space from skill contracts) | **DONE** (template; fine-tune → GR00T/GPU phase) |
| Isaac Sim / ROS 2 / Jetson / TensorRT stack | — | **DEFERRED** (hardware phase; adapters/contracts ready) |

Evidence: `novi/brain/tests/test_nvidia_experiments.py`,
`test_episode_recorder*.py`, `test_context_assembler.py`, `test_closed_loop.py`,
`test_governance_guard.py`, `test_world_model.py` (evidence-class set),
`test_teleop.py`, `test_lerobot_export.py`, `test_policy_adapter.py` — all green.

### Increment 2026-08-29 — TeleOp Phase 1 + Exp 4/5 Mac-feasible halves

Closed the remaining Mac-implementable gap (research §17/§24): keyboard teleoperation
over the simulated embodiment producing NoviEpisode demonstrations, the
learned-policy adapter seam (Isaac/GR00T plug in behind the same `SkillContract`),
the Exp-4 simulation benchmark (success rate / robustness / failure classes, all
SIMULATED), and the LeRobot data export + GR00T embodiment-config template for the
future fine-tune. What remains genuinely deferred needs hardware: real Isaac Lab
training/transfer, real GR00T fine-tuning, Isaac Sim, ROS 2, Jetson/TensorRT.



