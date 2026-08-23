# Novi Architecture Clarity

*Written 2026-08-23 as gap-audit plan item E3 (closes G13). This document is
the single-page answer to "what is Novi and how do the pieces fit?" — written
from the code as it exists today, not from intent.*

## What Novi is

Novi is a persistent, autonomous, embodied AI companion that runs locally on a
Mac (Apple Silicon). It perceives through real sensors (camera, microphone),
maintains beliefs about its world and the people in it, learns continuously
from experience, and converses as itself — not as an assistant. Everything
runs offline: no cloud APIs, no model downloads at runtime beyond the pinned
local models (MiniLM embeddings, Whisper STT, optional Ollama LLM).

The canonical implementation lives in **`novi/brain/`** (~23k lines across 76
modules). The legacy `mac_brain/` tree is fully merged; `novi/cognition`,
`novi/perception`, `novi/storage`, `novi/voice` hold shared contracts and
supporting implementations.

## The loop

One brain cycle (`MacBrain.step()`, `novi/brain/engine.py`) runs:

```
camera/mic → perceive → attention rank → world model update → beliefs/predictions
          → situations → cognition conclusion → goals/autonomy → memory admits
          → (on speech) discourse resolution → grounded reply → soul/affect update
```

Every step emits structured events on the brain's event bus; the web layer
(`novi/web/server.py`) streams them to the browser over SSE.

## Layers and their modules

| Layer | Modules | Responsibility |
|---|---|---|
| I/O | `io.py`, `audio.py`, `b2_perception.py`, `models/stt.py` | Sensors in; detections/transcriptions out. Deterministic fakes replace every sensor. |
| World & attention | `world_model.py`, `attention.py`, `spatial_map.py` | Unified entity/relation state with epistemic status; salience ranking; metric + semantic places. |
| Memory | `storage.py`, `memory_hardening.py`, `b1_memory.py`, `consolidation.py`, `memory_classes.py`, `importance.py` | Durable records with provenance/privacy; write-gate pipeline; consolidation ranked by importance × recency; class taxonomy enforced at admission. |
| Knowledge | `kgraph.py`, `triple_index.py`, `knowledge_extraction.py` | Entity-relation graph with contradiction preservation; semantic search over `"subject predicate object"` embeddings; constrained LLM extraction behind the FORBIDDEN guard. |
| Cognition | `cognition.py`, `prediction.py`, `typed_cognition.py` | Bayesian belief fusion (source-weighted noisy-OR); expectation learning; deterministic persistence predictions scored next cycle; typed situation contracts. |
| Identity | `identity.py`, `speaker_id.py`, `face_id.py`, `discourse.py` | Person identity tiering from cross-modal evidence; voice/face providers; conversation-state tracking for anaphora. |
| Soul & dialogue | `soul.py`, `dialogue.py`, `chat.py`, `preferences.py`, `relationships.py` | Stable traits/values + transient affect; slow personality learning (≤0.01 per interaction, ~100-cycle decay); rule-guarded natural replies grounded in one auditable ContextPackage. |
| Autonomy | `goals.py`, `plans.py`, `routines.py`, `autonomy_state_machine.py`, `closed_loop.py` | Curiosity-driven goal formation, planning, routine detection, execution verification. |
| Governance | `privacy.py`, `governance.py`, `audit_trail.py`, `observability.py` | Privacy classification on every admit, purpose-scoped authorization, audit trail, metrics/health (incl. `prediction_accuracy`). |
| Interface | `web/server.py`, `web/` UI, `cli.py` | SSE streaming, chat/hear endpoints, `/api/context`; one-command smoke cycles. |

## Non-negotiable boundaries

1. **Evidence, never assertion.** Recognition (face/voice), predictions, and
   learned routines are evidence that tiers up identity/beliefs — never direct
   writes to observed state. Predictions never touch the unified world model.
2. **Privacy before storage.** Every admission passes classification +
   governance; raw media never enters the audit trail.
3. **Honest degradation.** Optional capabilities (MiniLM, OpenCV, Ollama,
   networkx) degrade to deterministic fallbacks; the core loop is stdlib-only
   and runs without any of them.
4. **Determinism where it counts.** Same input ⇒ same output for cognition,
   memory ids (context fields are part of the identity hash — wall-clock stays
   out of them by design), consolidation, and all tests.
5. **The model advises; the rules decide.** LLM output is always validated
   (JSON constraints, FORBIDDEN guard, entity grounding) and can be refused;
   refusal paths produce honest replies, never confabulation.

## Verification surface

- `pytest -q` — 1,400+ tests, fully offline/deterministic.
- Smoke gate: `python -m novi.brain.cli --cycles 1`.
- Benchmarks: `benchmarks/vector_bench.py` (p99 < 50ms @ 5k records),
  `benchmarks/reasoning_calibration.py` (Brier/ECE + prediction accuracy);
  results under `mac_test_results/`.
- CI gates: architecture-integrity (`scripts/validate_architecture_integrity.py`),
  ruff lint, contract validation workflows.

## Where to read next

- Strategy: `docs/00-strategy/`
- System architecture: `docs/01-system-architecture/` (traceability matrix:
  `50_ARCH_CLOSE_009_FINAL_TRACEABILITY_MATRIX_2026-08-19.md`)
- Cognition/memory design: `docs/03-cognition/`, `docs/04-memory-and-knowledge/`
- Gap-audit plan (this document's origin): `docs/plans/01_BRAIN/13_GAP_AUDIT_IMPLEMENTATION_PLAN_2026-08-23.md`
