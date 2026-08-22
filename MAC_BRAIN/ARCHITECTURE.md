# MAC_BRAIN Architecture

**MAC_BRAIN is the canonical Novi Brain implementation.** All brain-phase development targets this package.

## Package relationship

```
┌──────────────────────────────────────────────┐
│  MAC_BRAIN/   (canonical brain — 1013 tests) │
│  ├── runtime.py       MacBrain orchestrator  │
│  ├── cognition.py     BeliefSystem, etc.     │
│  ├── cognition2.py    MacCognition           │
│  ├── cognition_typed.py  typed contracts     │
│  ├── soul.py          Soul, Identity, Affect │
│  ├── social.py        Relationships          │
│  ├── dialogue.py      Natural conversation   │
│  ├── storage.py       DurableMemoryStore     │
│  ├── world_model.py   UnifiedWorldModel      │
│  ├── spatial_map.py   SpatialModel           │
│  ├── learning_pipeline.py  promotion/correction/routines/counterfactuals │
│  ├── memory_classes.py   memory-class decision + schema-evolution hooks │
│  ├── ...              (60+ modules)          │
│  │                                           │
│  │  imports from:                            │
│  ▼                                           │
│  brain/   (portable library — 105 tests)     │
│  ├── b1_cognition.py   Situation, etc.       │
│  ├── b1_memory.py      MemoryRecord, etc.    │
│  ├── b1_world.py       TemporalWorldModel    │
│  ├── b2_perception.py  Detection, etc.       │
│  ├── b2_model_runtime.py  ModelRuntime       │
│  ├── runtime.py        BrainSupervisor       │
│  └── contracts.py      utc_now, registry     │
│                                              │
│  b1_loop.py is NOT used by MAC_BRAIN.        │
│  It is a Stage-0 simulation scaffold,        │
│  retained only for its own test suite.       │
└──────────────────────────────────────────────┘
```

## Dependency direction

**One-way: `MAC_BRAIN → brain`.** Never reversed.

- `brain/` must never import from `MAC_BRAIN/`
- `brain/` owns portable types: perception, memory, contracts, model runtime, supervisor lifecycle
- `MAC_BRAIN/` adds Mac-specific adapters: camera, microphone, virtual body, Whisper STT, web server
- `MAC_BRAIN/` extends cognition, memory, and autonomy beyond the portable base

## What MAC_BRAIN owns (not in brain/)

| Module | Responsibility |
|--------|---------------|
| `runtime.py` | Main `MacBrain` orchestrator (2217 lines) |
| `soul.py` | Identity, personality, affect, values, motivations |
| `social.py` | Multi-dimensional relationships, social intelligence |
| `dialogue.py` | Natural conversation engine (50+ handler types) |
| `lexicon.py` | Living lexicon, learned preferences |
| `storage.py` | Durable SQLite/WAL store (10 domain tables) |
| `cognition.py` | BeliefSystem, ExpectationSystem |
| `cognition2.py` | MacCognition: situation-grounded reasoning |
| `world_model.py` | UnifiedWorldModel with epistemic status |
| `situation_model.py` | Situation interpretation from world state |
| `fusion.py` | Multimodal fusion (vision+speech) |
| `temporal.py` | Temporal/causal event model |
| `vector.py` | Semantic/vector memory (embeddings) |
| `kgraph.py` | Entity knowledge graph |
| `planner.py` | Multi-step goal planning |
| `privacy.py` | Privacy governance, erasure |
| `identity.py` | Person identity recognition |
| `consolidation.py` | Memory consolidation/decay/summarization |
| `reflection.py` | Action reflection/self-correction |
| `autonomy.py` | Bounded goals, curiosity, scheduling |
| `autonomy_state_machine.py` | Autonomy state transitions |
| `audio.py` | Non-speech hearing/audio events |
| `observability.py` | Health, metrics, diagnostics |
| `failure_modes.py` | Cognitive failure-mode handling |
| `multi_speed_runtime.py` | Multi-tier runtime scheduling |
| `skill_contract.py` | Skill interface contracts |
| `governance_guard.py` | Authorization/governance boundary |
| `io.py` | Mac camera, microphone, speaker, virtual body |
| `cli.py` | CLI launcher |
| `live.py` | Interactive live demo session |
| `closed_loop.py` | Closed-loop operation |
| `self_model.py` | Novi's self-model and capabilities |
| `context_assembler.py` | Context assembly for reasoning |
| `memory_hardening.py` | Hardened memory manager |
| `nvidia_experiments.py` | NVIDIA experiment harness |
| `event_bus.py` | Canonical doc-10 event envelope, replay, dedup, backpressure |
| `audit_trail.py` | Append-only decision trace with retention |
| `soul_acceptance.py` | P0–P3 acceptance catalog + gate evaluator |
| `p0_gate_runner.py` | Acceptance-gate runners (all priorities) |
| `spatial_map.py` | Spatial frames/regions/doors/occupancy model |
| `cognition_typed.py` | Typed cognitive emission (SituationState, IntentHypothesis, Prediction, CognitiveDecisionRecord, CognitiveEvent, PersonContext) |
| `learning_pipeline.py` | Knowledge promotion, user corrections, routine detection, counterfactual engine |
| `memory_classes.py` | Memory-class decision (now vs defer) + L0–L6 schema-evolution gate |
| `models/` | Neural model providers (STT, reasoning, detection, etc.) |

## What brain/ owns (imported by MAC_BRAIN)

| Module | Key types |
|--------|-----------|
| `b2_perception.py` | `Detection`, `SpecialistPerception`, `DeterministicPerceptionBackend` |
| `b1_memory.py` | `MemoryRecord`, `DeterministicMemoryManager` |
| `b1_cognition.py` | `DeterministicCognition`, `Situation`, `ReasoningResult` |
| `b1_world.py` | `TemporalWorldModel`, `WorldModelState` |
| `runtime.py` | `BrainSupervisor`, `Lifecycle`, `ActionProposal` |
| `b2_model_runtime.py` | `ModelRuntime`, `ModelBackend` |
| `b2_real_inference.py` | `InferencePolicy`, `RealModelInvoker` |
| `contracts.py` | `utc_now`, `ContractRegistry` |

## brain/b1_loop.py — NOT used by MAC_BRAIN

`brain/b1_loop.py` is a Stage-0 closed-simulation-loop scaffold. It defines
`SimulatedPerception`, `SimulatedCognition`, `SimulatedMemory`, `SimulatedAutonomy`,
`ClosedSimulatedLoop`, and their data classes — none of which MAC_BRAIN imports.

These types are **retained only for the brain/tests/ suite** (105 tests) and
should be considered legacy. They do not need to be maintained or extended for
the brain phase.

## Test ownership

| Suite | Count | Owner | Status |
|-------|-------|-------|--------|
| `MAC_BRAIN/tests/` | 1013 | MAC_BRAIN canonical | ✅ All green |
| `brain/tests/` | 105 | brain portable library | ✅ All green |
| `web/tests/` | 41 | Web server integration | ⚠️ Slow (~70s), not in fast suite |
| `contracts/tests/` | 13 | Contract validation (via pytest shim) | ✅ All green |
| `cognition/tests/` | 34 | Typed cognition contracts + replay | ✅ All green |
| **Fast suite total** | **1165** | MAC_BRAIN + brain + contracts + cognition | ✅ All green |

## Key architecture rules

1. `MAC_BRAIN → brain` dependency only. Never reverse.
2. Models are capability providers behind protocol boundaries — never semantic authorities.
3. Every neural/LLM path has a deterministic fallback (CI-safe).
4. Safety/authorization is outside adaptive model authority.
5. Evidence-backed: every capability has timestamped verification with commit SHA.
6. Soul, social, and dialogue live in MAC_BRAIN (not the portable library).