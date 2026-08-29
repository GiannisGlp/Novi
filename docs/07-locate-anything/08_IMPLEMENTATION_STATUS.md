# LocateAnything — Implementation Status

Tracking document for [`docs/plans/LOCATE_ANYTHING_IMPLEMENTATION_PLAN_2026-08-28.md`](../plans/LOCATE_ANYTHING_IMPLEMENTATION_PLAN_2026-08-28.md).
Updated after every implementation session. Evidence files land in `evidence/`.

**Session 1 — 2026-08-29:** steps 1–9 complete, steps 10–14 in the Mac
feasibility experiment (see `07_MAC_FEASIBILITY.md`), perception-side of
steps 16–20/23/28 complete. Brain-zone steps deferred honestly (the
`novi/brain/` workstream owns that surface).

**Session 1 addendum (experiment findings):**
- the released model renders coordinates as special tokens `<N>` and the
  no-object marker as `None` — the strict parser accepts both documented
  encodings (still integer/[0,1000]-validated);
- the remote `generate` already returns decoded text — the runtime does not
  decode again and strips chat-template framing (`<|im_start|>/<|im_end|>`);
- bf16 loads on MPS in ~5–9 s; per-call latency is prefill-dominated (~40 s
  at 4112×2658, ~1.7 s at 640×480 — camera resolution is interactive);
- **prompt tuning (2026-08-29)**: a system instruction ("Answer using
  grounding tokens only.") eliminated stray tail text in validation runs and
  yields fuller labels ("the largest object" not "the largest").

## Status by plan §19 sequence

| # | Step | Status | Evidence |
|---|---|---|---|
| 1 | Add the architecture decision | ✅ DONE | `06_ARCHITECTURE_DECISION.md` (ADR-LA-01) |
| 2 | Add SpatialQuery/GroundingObservation/GroundingResult contracts | ✅ DONE | `novi/perception/grounding.py` + `test_grounding.py` (29) |
| 3 | Add strict LocateAnything output parser | ✅ DONE | `novi/perception/locate_anything_parse.py` + tests (24) |
| 4 | Add coordinate conversion and geometry validation | ✅ DONE | `novi/perception/locate_anything_geometry.py` + tests (22) |
| 5 | Add mocked LocateAnythingBackend | ✅ DONE | `DeterministicLocateAnythingBackend` in `locate_anything.py` |
| 6 | Add unit tests for every parser/contract edge case | ✅ DONE | 142 new perception tests, all green |
| 7 | Add optional dependency/runtime detection | ✅ DONE | `locate_anything_runtime.py` — seven BackendStates, lazy imports |
| 8 | Create isolated LocateAnything environment | ✅ DONE | `scripts/mac-locateanything-env.sh`; `.venv-locateanything` (py3.11, gitignored) |
| 9 | Pin nvidia/LocateAnything-3B revision | ✅ DONE | `c32291ca5e996f5a7a485845b4f57a233936bba0` (ADR §0) |
| 10 | Attempt model load on the Mac | ✅ DONE | **bf16 loads on MPS in ~7.5 s** (`07_MAC_FEASIBILITY.md`) |
| 11 | Record memory/load results | ✅ DONE | `evidence/mac-feasibility-20260829-131115.json`; RSS 0.26→1.13 GB (process), MPS allocator holds weights |
| 12 | Run one real image/query | ✅ DONE | `novi/assets/test-image.png` (4112×2658) + "locate all objects visible in the image" → typed box |
| 13 | Record inference result and latency | ✅ DONE | p50 39.7 s / p95 40.7 s / p99 40.7 s (prefill-bound, scales with image size) |
| 14 | Decide MPS/CPU/remote-NVIDIA feasibility | ✅ DONE | **Decision gate B** — MPS usable for occasional cognition-driven grounding; per-frame stays SSDLite; production path NVIDIA |
| 15 | Implement the real backend for the viable runtime | ✅ DONE | adapter + `_RealLocateAnythingBundle` validated on MPS bf16 (decision gate B) |
| 16 | Connect one frame to one grounding query | ✅ DONE | `PerceptionPipeline.ground_frame` + `test_pipeline_grounding.py` (7) |
| 17 | Connect grounding observations to tracking | ✅ DONE | `grounding_association.py` + tests (9) — associated/candidate |
| 18 | Connect observations to world state | ✅ DONE (seam) | `world_state_adapter.admit_grounding_outcome` — protocol-based; associated→OBSERVED updates, candidates→CANDIDATE/HYPOTHESIZED entities; brain wiring is its call (documented surface) |
| 19 | Add active-perception escalation from SSDLite uncertainty | ✅ DONE (perception side) | `active_grounding.py` escalation policy + tests (21); brain-side trigger deferred |
| 20 | Add query budgets and deduplication | ✅ DONE | `GroundingBudget`, `GroundingRequestDeduplicator` |
| 21 | Connect prediction verification | ✅ DONE (seam) | `prediction_verification.verify_predicted_presence` — verified-present set feeds `PredictionEngine.observe`; failures = UNKNOWN, never absence |
| 22 | Connect deliberation memory for ambiguous target selection | ✅ DONE (seam) | `deliberation_record.build_deliberation_record` — plan Step 7.4 schema (query/candidates/selected/rejected/evidence/outcome) |
| 23 | Add short-term spatial observation caching | ✅ DONE | `GroundingCache` (LRU, in-process only) |
| 24 | Add selective durable spatial memory | ✅ DONE (seam) | `spatial_memory_promotion.promotion_candidate` — stability criterion (repeated, same-track, bounded drift); candidates never promote; store remains `observation_recorder.py` |
| 25 | Add benchmark corpus and ground truth | ✅ DONE (v1 seed) | `benchmark/corpus-v1.json` — 6 records (4 positive + 2 negative) on test-image.png, vision-annotated GT with provenance; versioned registry + validator (`benchmark_corpus.py`) |
| 26 | Compare SSDLite-only vs SSDLite+LocateAnything | ✅ DONE (first evidence) | harness + real-model run on MPS: precision 0.083→0.25, FP 11→3, recall 0.25 both (`evidence/benchmark-compare-20260829-132811.json`); corpus needs more domains before conclusions |
| 27 | Run real camera acceptance | ✅ DONE (2026-08-29) | live webcam → SSDLite + LocateAnything on MPS: both queries success, **~1.7 s at 640×480** (`evidence/camera-acceptance-20260829-133304.json`); candidates not invented ✓; raw frame not persisted ✓ |
| 28 | Add high-risk re-observation/verification | ✅ DONE (geometry) | `grounding_verification.py` — deterministic re-observation agreement (best-pair IoU, fail-closed); permission chain is governance-owned |
| 29 | Benchmark target NVIDIA hardware | ⛔ BLOCKED (spec ready) | `09_NVIDIA_RUNTIME_BENCHMARK_PLAN.md` — full protocol (load/latency/throughput/quality parity/failure) + acceptance criteria; execution needs GPU |
| 30 | Evaluate deployment runtime options | ⛔ BLOCKED (spec ready) | same doc §1–§4 — 6 runtime candidates, measurement protocol; decision is a table review, not a doc guess |
| 31 | Complete license review | 🟡 RECORDED (legal pending) | `10_LICENSE_GATE.md` — 3.3 research-only finding quoted; clearance checklist (legal review + written permission or model replacement) |
| 32 | Only then consider production integration | ⛔ BLOCKED | depends on 29–31 |

## Milestones (plan §18)

| Milestone | Status | Notes |
|---|---|---|
| LA-0 Research baseline | ✅ DONE | `docs/07-locate-anything/00..05` + gap analysis |
| LA-1 Adapter | ✅ DONE | contracts + strict parser + optional backend + mocked tests |
| LA-2 Mac feasibility | ✅ DONE | isolated runtime; load/inference evidence; **decision gate B** (`07_MAC_FEASIBILITY.md`) |
| LA-3 Perception integration | 🟡 PARTIAL | pipeline grounding + tracking association + provenance done; web/CLI observability pending (web is another workstream's zone) |
| LA-4 Active perception | 🟡 PARTIAL | escalation + budgets + dedup + cache done; cognitive query generation is brain-side |
| LA-5 Cognitive integration | 🟡 PARTIAL | perception-side seams done (world-state admission, prediction verification, deliberation record, promotion criterion); brain-side wiring is the brain workstream's call |
| LA-6 Real-IO closed loop | 🟡 PARTIAL | camera → LocateAnything → grounding → tracker ✅ (camera acceptance, ~1.7 s at 640×480); world-state/cognition leg is brain-zone |
| LA-7 NVIDIA hardware evaluation | ⛔ BLOCKED | needs GPU |
| LA-8 Production decision | ⛔ BLOCKED | needs 26–31 |
| LA-9 (Phase 10) Benchmark | ✅ DONE (v1) | corpus + metrics + runner + comparison harness (241 tests); real-model evidence run complete — precision +0.167, FP −8 vs SSDLite on corpus-v1 |

## Regressions

Perception package: 43 pre-existing tests + 142 new = **185 tests, all green**.
Full-suite check at session end: see session report.
