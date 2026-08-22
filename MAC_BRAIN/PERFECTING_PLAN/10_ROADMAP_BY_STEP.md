# 10 — Roadmap (by step)

Dependency-ordered plan to perfect the brain phase. Steps are chosen so each builds on
the last and is verifiable on the Mac without hardware. All logic goes in MAC_BRAIN/
brain (portable); web/server.py stays a thin caller.

## Step 0 — Freeze scope and acceptance bar
- Agree the six-domain delta list (files 03-08) and the Definition of Done per step
  (11_VALIDATION_AND_ACCEPTANCE). No new implementation phase is entered until the
  current one meets its done-bar (global completion gate rule).
- Output: this plan ratified; ADR if any scope change is proposed.
- Done: plan agreed, priority order fixed.

## Step 1 — Cognition world/context (biggest leverage)
Build one coherent **WorldModel / Context** capability:
- Typed entities (Person, Place, Building, Room, Object) with **epistemic status**
  (OBSERVED/INFERRED/PREDICTED/VERIFIED/UNKNOWN) on every node/relation; contradictions
  preserved; snapshots.
- **ContextAssembler**: bounded, provenance-filtered context for dialogue/reasoning
  (feeds compose_reply / deliberation), incl. current speaker, location, visible objects,
  recent events, current goal, spatial relations, uncertainty.
- **AttentionCandidate** emission for Autonomy (salience/novelty/urgency/social/
  relevance/uncertainty).
- Ground dialogue + reasoning in this world model (the "Bring me that cup" case).
- Done-bar: reference-resolution scenario (NVIDIA Exp 1) passes; context is bounded and
  provenance-filtered; epistemic status enforced at the world boundary.

## Step 2 — Memory & Knowledge hardening
Harden storage/admission/retrieval to the canonical **MemoryRecord** contract:
- Full MemoryRecord field set + typed epistemic/verification state at admission.
- Write gate (identity -> integrity -> privacy -> separation -> poisoning -> retention).
- Retrieval failure states (NO_RESULT/AMBIGUOUS/CONFLICTED/STALE/ABSTAIN) surfaced.
- Contextual trust + independence groups.
- Governance/oversight interfaces behind contracts (GovernanceRequest/Decision,
  review machine).
- Ties: world-state labels carry evidence class (OBSERVED/INFERRED/PREDICTED/SIMULATED)
  so simulations never become facts.
- Done: admission/retrieval contract tests green; a simulated episode cannot be
  recalled as a fact.

## Step 3 — Autonomy + skill contract + safety boundary
- **Multi-speed runtime**: deterministic System-0 safety/reactivity tier that never waits
  on an LLM; System-1/2/3 scheduling.
- **Skill contract** module (Navigate/Inspect/FindObject/Pick/Speak) with preconditions,
  success/failure criteria, timeout, recovery, safety constraints — deterministic/mock
  first (NVIDIA Experiment 2).
- **Governance/authorization at the action boundary**: a runtime guard between proposal
  and execution (models never command action); even deterministic actions pass it.
- Autonomy state machine (idle/active/degraded, interruption/resume, attention
  arbitration) + attention + communication decisions as first-class inputs.
- Done: a proposed action cannot execute without a governance grant; skill contract
  tests green; System-0 safety gating proven.

## Step 4 — Soul acceptance + communication
- Implement the (08) behavioral-acceptance harness: scenario format, acceptance classes
  P0-P3, release gates, DoD.
- (07) communication modes + vocabulary-scope model (global vs relationship/context/
  ephemeral), pronunciation, preference schema/workflows.
- Enforce "prefer silence", addressee discrimination, turn-taking, social-fatigue budget.
- Done: P0 gate green (zero constitutional/privacy/escalation/identity/safety violations);
  scenario tests green.

## Step 5 — NVIDIA no-hardware experiments (validate the architecture)
On the Mac with deterministic/mock skills:
- Exp 2: skill-contract invocation independent of implementation (pass).
- Exp 1: context-aware reference resolution.
- Exp 3: a small clean demonstration dataset in the unified **NoviEpisode** schema with
  adapters (LeRobot/IsaacLab/ROSBag/NoviNative seams).
- Record evidence with pinned provenance (OBSERVED/SIMULATED etc.).
- Done: experiment harness + evidence records; docs produce ADR/decisions.

## Step 6 — Closed-loop validation + acceptance gate
- First-class VERIFY step (observe -> plan -> act -> verify -> recover/ask/stop) with
  outcome/failure handling across the loop.
- Cross-system acceptance tests (Soul -> Cognition -> Memory -> Autonomy -> Safety ->
  Brain) and the global completion-gate review.
- Done: full suite green + acceptance evidence for the brain phase.

## Explicitly NOT in this plan (correctly deferred)
- Real neural model selection/benchmarks on sensors (B2.9+; needs hardware + models).
- Jetson/CUDA/TensorRT/ROS2/Isaac integration (hardware phase).
- Physical robot / sim-to-real gap measurement.
- Full episode -> policy training (GR00T/Isaac Lab) — after brain phase.

