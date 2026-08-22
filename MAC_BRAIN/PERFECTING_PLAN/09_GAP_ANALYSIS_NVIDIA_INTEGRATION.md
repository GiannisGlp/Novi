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

## Next Action (roadmap Step 5)
- Run the no-hardware NVIDIA experiments on the Mac with deterministic/mock skill
  implementations: (2) skill contract, (1) context-aware reference resolution, (3) a
  small clean demonstration dataset in the NoviEpisode schema. These validate the
  architecture and produce the evidence the docs require without a robot.

