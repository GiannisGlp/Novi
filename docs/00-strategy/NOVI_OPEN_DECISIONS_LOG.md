# Novi — Open Design Decisions Log

**Status:** Decision log (proposals for the human decision owner to confirm)
**Date:** 2026-08-22
**Method:** scientific-brainstorming skill — each decision is scoped, options are labeled (idea/assumption/evidence), tradeoffs are recorded, and a recommendation is given as a **proposal**, not a finding. The accountable decision owner is the user; nothing here is final until confirmed.
**Source:** `docs/00-strategy/NOVI_BRAIN_GAP_ANALYSIS_AND_NEXT_STEPS.md` §6 (10 open decisions), reconciled against the current code.

> **How to read this log.** Each entry: **Decision** (the question), **Options** (labeled), **Evidence** (what the session actually established), **Tradeoffs**, **Proposal** (recommendation, marked as such), **Revisit trigger**. Several decisions are already effectively resolved by work that landed this session; those are marked **RESOLVED** and only need confirmation.

---

## D1 — Brain-phase scope: keep real-model/hardware/ROS2 out vs start thin seams now

- **Options**
  - (idea) Keep real-model selection (B2.9), hardware, and ROS2/Isaac entirely out of the brain-phase core; the Mac brain stays deterministic + Ollama-hosted.
  - (idea) Start thin seams now (interfaces + adapters) so the edge phase is a drop-in.
- **Evidence** — The Mac brain already has thin adapters (`b2_nemotron.py`, `b2_cosmos_reason.py`, `b2_perception.py`) and the `NoviEpisode` schema + LeRobot/IsaacLab/ROSBag adapters. Real inference (TensorRT/CUDA/Jetson) is deferred by policy.
- **Tradeoffs** — Keeping it out avoids premature NVIDIA coupling and keeps the Mac suite green; thin seams now reduce later integration risk but add surface area with no hardware to test against.
- **Proposal** — Keep real-model/hardware/ROS2 out of the brain-phase core; keep the existing thin adapters as the seam. **Revisit** when a Jetson/Thor board is available for benchmarks.

## D2 — Acceptance priority: cognition world/context first vs memory hardening first

- **Options**
  - (idea) Cognition world/context first (Step 1).
  - (idea) Memory hardening first (Step 2).
- **Evidence** — Step 1 (typed cognition layer: `cognition/contracts/`, `cognition/validation/`, `cognition/replay/`, `spatial_map.py`, `cognition_typed.py`) is **already built and passing** (34 contract + 9 typed-emission tests). Step 2 (memory) is largely done too (WriteGate, retrieval states, IndependenceTracker wired into durable path).
- **Tradeoffs** — Both are now substantially complete; the remaining question is which to *accept* first, not which to build.
- **Proposal** — Accept cognition world/context first (it is the biggest functional leverage and is done). **Revisit** if a memory-specific defect surfaces first.

## D3 — Minimum governance guard: deterministic only vs GovernanceRequest/Decision contract

- **Options**
  - (idea) Deterministic-only guard.
  - (idea) A `GovernanceRequest`/`GovernanceDecision` contract between proposal and execution.
- **Evidence** — `GovernanceGuard` already implements "no action executes without grant," degraded-mode blocking, and confirmation grants; the runtime surfaces `REQUIRE_CONFIRMATION` and holds execution. The docs require the contract guard.
- **Tradeoffs** — The contract guard is more auditable and matches the docs; deterministic-only is simpler but weaker.
- **Proposal** — Keep the contract guard (already implemented). **Revisit** only if it becomes a performance bottleneck.

## D4 — Which memory classes to implement now vs defer

- **Options**
  - (idea) Implement procedural, prospective, metamemory, autobiographical-continuity now.
  - (idea) Defer them to the body phase.
- **Evidence** — `memory_classes.py` (205 lines) + `test_memory_classes.py` (120 lines) landed this session; the memory-class decision + schema-evolution hooks are documented as done (10 tests).
- **Tradeoffs** — These classes are heavy and benefit from real embodiment; deferring avoids speculative work.
- **Proposal** — Defer the heavy classes to the body phase; keep the schema-evolution hooks. **Revisit** when the body/hardware phase starts.

## D5 — Which local LLM/embedding providers to standardize

- **Options**
  - (idea) Standardize on Ollama (current default: qwen3.8, nemotron-3.5-lightning switchable).
  - (idea) Add a second provider behind the model runtime.
- **Evidence** — The model runtime routes via Ollama; the web dashboard has a model switcher. No embedding provider is confirmed.
- **Tradeoffs** — One provider is simplest and offline-first; a second adds resilience but more surface.
- **Proposal** — Standardize on Ollama for the brain phase; confirm the embedding provider (recommend a local one, e.g. a sentence-transformer via the `neural` extra). **Revisit** when real Nemotron/Cosmos inference lands.

## D6 — Stand up the NoviEpisode schema + adapters now

- **Options**
  - (idea) Stand up now.
  - (idea) Defer.
- **Evidence** — **RESOLVED**: `EpisodeRecorder` + `NoviEpisode` schema + LeRobot/IsaacLab/ROSBag/NoviNative adapters are already implemented and wired into the runtime (`nvidia_experiments.py`, 20 tests; NVIDIA Exp 3 evidence recorded).
- **Tradeoffs** — Already done; the only question is whether to keep it in the brain phase.
- **Proposal** — Keep it (it keeps future Isaac/GR00T data portable). **Revisit** only if the schema needs to change for a new data source.

## D7 — Hardware: Jetson AGX Orin 64GB vs Thor

- **Options**
  - (idea) Jetson AGX Orin 64GB.
  - (idea) Jetson AGX Thor.
- **Evidence** — No representative workload benchmarks exist yet; the decision is OPEN by design.
- **Tradeoffs** — Orin is proven/available; Thor is newer with more headroom but less ecosystem maturity.
- **Proposal** — Defer until representative workload benchmarks exist (per the plan). **Revisit** when a board is available to benchmark.

## D8 — Typed contract layer: Pydantic v2 vs existing dataclasses

- **Options**
  - (idea) Pydantic v2 (as docs 25/26 prescribe).
  - (idea) Build on the existing dataclass WorldModel.
- **Evidence** — **RESOLVED**: the typed contract layer was built with Pydantic v2 (`cognition/contracts/`, JSON Schema generation, validators, replay). The dataclass WorldModel is bridged via `to_world_state()`/adapters, and the full suite stays green (1180).
- **Tradeoffs** — Pydantic v2 matches the docs and gives generated JSON Schema; the bridge avoids a disruptive migration.
- **Proposal** — Keep Pydantic v2 + the bridge. **Revisit** if the bridge becomes a maintenance burden.

## D9 — Legacy docs disposition: SUPERSEDED vs removed; PERFECTING_PLAN plan-only?

- **Options**
  - (idea) Keep SUPERSEDED docs in place.
  - (idea) Remove them.
  - (idea) Treat PERFECTING_PLAN as plan-only, with implementation decisions going through ADR.
- **Evidence** — `docs/02-novi-brain` 01,02,05,18-22 are marked SUPERSEDED; the canonical implementation lives in `MAC_BRAIN/`. The gap doc corrected the false "PERFECTING_PLAN missing" claim.
- **Tradeoffs** — Keeping SUPERSEDED docs preserves history but adds noise; removing them is cleaner but loses context.
- **Proposal** — Keep SUPERSEDED docs but ensure they are clearly marked and not treated as authoritative; treat PERFECTING_PLAN as plan-only. **Revisit** during a docs cleanup pass.

## D10 — Virtual body actuation for active perception / spatial fusion

- **Options**
  - (idea) Add movement actuation to the Mac virtual body.
  - (idea) Keep the virtual body static.
- **Evidence** — The spatial model (`spatial_map.py`) is built; active perception (repositioning to reduce uncertainty) is unimplemented and deferred to the body phase.
- **Tradeoffs** — Actuation would exercise active perception and spatial fusion on the Mac; it adds virtual-body surface with no physical payoff yet.
- **Proposal** — Defer actuation to the body phase; keep the spatial model for reachability/visibility queries. **Revisit** when the body phase starts.

---

## Summary of proposals

| # | Decision | Proposal | Status |
|---|----------|----------|--------|
| D1 | Brain-phase scope | Keep real-model/hardware/ROS2 out; keep thin seams | Open |
| D2 | Acceptance priority | Cognition world/context first | Open |
| D3 | Governance guard | Keep the contract guard | Open |
| D4 | Memory classes | Defer heavy classes to body phase | Open |
| D5 | LLM/embedding providers | Standardize on Ollama; confirm embedding provider | Open |
| D6 | NoviEpisode schema | Keep (already implemented) | RESOLVED |
| D7 | Hardware | Defer until benchmarks | Open |
| D8 | Typed contract layer | Keep Pydantic v2 + bridge | RESOLVED |
| D9 | Legacy docs | Keep SUPERSEDED, marked; PERFECTING_PLAN plan-only | Open |
| D10 | Virtual body actuation | Defer to body phase | Open |

**Decision owner:** the user. Each proposal is a recommendation; confirm or override per row. Revisit triggers are noted per entry.
