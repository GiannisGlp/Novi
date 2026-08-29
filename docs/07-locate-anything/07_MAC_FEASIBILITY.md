# LocateAnything — Mac Feasibility Evidence (Phase 4)

**Experiment:** `scripts/mac-locateanything-experiment.py`, run 2026-08-29
**Machine:** Mac (Apple Silicon), 36 GB RAM, macOS 26.5.1
**Model:** `nvidia/LocateAnything-3B` @ `c32291ca5e996f5a7a485845b4f57a233936bba0` (freeze record: `06_ARCHITECTURE_DECISION.md` §0)
**Runtime:** isolated `.venv-locateanything` (Python 3.11.15, torch 2.13.0, transformers 4.57.1, timm, sentencepiece, peft, accelerate, opencv-headless, lmdb, requests; decord stubbed — no macOS arm64 wheel, image path never touches it)
**Evidence files:** `evidence/mac-feasibility-20260829-131115.json` (final), `evidence/mac-feasibility-live.json` (incremental)
**Image under test:** `novi/assets/test-image.png` — actually **4112×2658 RGBA** (kitchen scene), not 640×480.

---

## Step 4.2 — Load-only test

| Item | Value |
|---|---|
| Python / torch / transformers | 3.11.15 / 2.13.0 / 4.57.1 |
| Device | **MPS** (`torch.backends.mps.is_available() == true`) |
| Dtype | **bfloat16** (first attempt succeeded; float32 never tried) |
| Load time | **7.5 s** (cold first run 8.5 s; weights cached in `~/.cache/novi/models/locateanything-hf`) |
| Process RSS before / after load | 0.26 GB → 1.13 GB (ru_maxrss; undercounts MPS *device* memory — the ~7.6 GB bf16 weights live in the MPS allocator) |
| Attention backends | `magi_attention` unavailable → SDPA; `flash_attn` unavailable for MoonViT → SDPA (warnings from remote code) |
| Capability probe | `available` (state machine in `locate_anything_runtime.probe_capabilities`) |

Compatibility notes:
- **transformers 5.16.1 is incompatible** with the remote model code (`_check_and_adjust_attn_implementation` kwarg) → pinned **4.57.1 + tokenizers 0.22.0** (upstream `pyproject.toml` pins).
- **decord has no macOS arm64 wheel**; the processor file `processing_locateanything.py` imports it at top level but only *uses* it for video. A loud-failing stub satisfies the import; image grounding never reaches it.

## Step 4.3 — Single inference

`locate all objects visible in the image` → model output:

```text
<ref>object</ref><box><0><562><22><593></box>开口
```

- Strict parser: **1 typed box** (`object`, source (0,562,22,593) → pixel (0, 1493, 91, 84) on the 4112×2658 image)
- **`success=False`** because the model leaked stray text (`开口`, Chinese) after the box token — the fail-closed contract (plan Step 9.4) worked as designed: malformed output is never admitted as a clean observation.
- Latency 40.2 s (prefill-dominated: vision encoder on a 4112×2658 image).

## Step 4.4 — Grounding queries

| Query | Output (raw) | Parsed | Latency | Verdict |
|---|---|---|---|---|
| locate the person | `<ref>the person</ref><box><483><945><500><990></box>` | 1 box, `success=True` | 39.4 s | ✅ |
| locate the largest object | `<ref>the largest</ref><box><23><604><228><943></box>` | 1 box, `success=True` | 41.1 s | ✅ |
| locate the object nearest the center | `<ref>the the center</ref><box><392><357><443><371></box>` | 1 box, `success=True` | 38.9 s | ✅ (label echoes query oddly — cosmetic) |
| locate a unicorn (absent object) | `<ref>a unicorn</ref><box>None</box>` | **`no_object=True`**, `success=True` | 38.0 s | ✅ negative query handled |
| locate all objects | `<ref>object</ref><box>…</box>开口` | 1 box + stray text error, `success=False` | 40.2 s | ⚠️ fail-closed on stray tail text |

**Model output contract confirmed as documented:** coordinates are special tokens `<N>` (e.g. `<4><207><20><231>`); the no-object marker is **`None`** (capitalized); occasional **stray text** (e.g. `开口`) can trail the grounding block — the strict parser flags it, never repairs it.

## Step 4.5 — Stress test

| Battery | Latencies (ms) |
|---|---|
| 1× "locate the person" | 38 922 |
| 5× | 40 144, 40 151, 40 136, 38 810, 39 257 |
| 10× | 39 613, 39 748, 39 006, 40 182, 40 168, 40 163, 40 731, 39 941, 40 653, 39 159 |
| multiple boxes (base image) | 39 585 |
| large image (1920×1080 synthetic) | 11 276 (ok=False: stray tail text; note: *smaller* than base 4112×2658) |
| small image (64×64) | **1 376** (ok=True) |
| cluttered image (640×480) | 7 200 (ok=False: stray tail text) |

**p50 = 39 681 ms · p95 = 40 653 ms · p99 = 40 653 ms** · peak process RSS 1.43 GB

Interpretation:
- Latency is **prefill-bound, scaling with image resolution**: 4112×2658 → ~40 s, 1920×1080 → ~11 s, 640×480 → ~7 s, 64×64 → 1.4 s. Decode adds almost nothing (answers are ~7–11 tokens).
- Stability is excellent: 16 repeated identical queries within 38.8–40.7 s.
- **Memory mitigation required**: macOS jetsam SIGKILLed the process after ~4 generations (MPS caching allocator retention). `torch.mps.empty_cache()` + `gc.collect()` after each generation fixed it (full 24-query battery completed, RSS flat).

## Step 4.6 — Decision gate

### Outcome: **B — MPS works but is heavy; usable for occasional cognition-driven grounding on the dev Mac, not per-frame.**

Reasoning:
1. **It runs**: bf16 load 7.5 s, all grounding queries produce correctly parsed, provenance-stamped observations; negative queries (`no_object`) work.
2. **It is slow per call**: ~40 s on real camera-resolution frames (prefill-bound). This is a *cognition-on-demand* budget (plan Step 6.3 gives grounding requests seconds-to-minutes budgets), **not** a per-frame perception budget.
3. **Therefore**: keep the adapter and the local Mac backend for **experimental, occasional, cognition-driven queries** during brain development; the **realtime/per-frame path stays SSDLite**; the production robot path is a local NVIDIA runtime (plan Phase 12) behind the same adapter.

Consequences for the plan:
- **Step 15 (real backend)**: the adapter + `_RealLocateAnythingBundle` are validated for the viable runtime (MPS bf16, transformers 4.57.1). The runtime's prompt/generation defaults may be tuned (e.g. smaller `max_new_tokens`, `generation_mode` experiments) but the contract works.
- **Steps 16–27**: pipeline grounding, tracking association, active perception, and the benchmark can be exercised **live on the Mac** with occasional queries; per-frame grounding stays out of scope.
- **Known quirk to track**: stray tail text after the grounding block (~1 in 5 observed) → results fail closed; a policy-level retry (bounded by `GroundingBudget.max_retries`) is the natural follow-up, not a parser change.

## Env reproducibility

`scripts/mac-locateanything-env.sh` reproduces the environment (pinned transformers 4.57.1, torch 2.13, opencv-headless/lmdb/requests, decord stub, pinned model snapshot). ⚠️ The script's final state was **not** re-validated from scratch in this session (the venv was patched incrementally); a fresh-run check is a listed follow-up.

---

## Step 27 — Real camera acceptance (2026-08-29, PASSED)

`scripts/mac-locateanything-camera-acceptance.py` — live webcam (MacCamera/OpenCV,
640×480) → real SSDLite + real LocateAnything on MPS → `process_frame` +
`ground_frame` → typed grounding + track associations. Evidence:
`evidence/camera-acceptance-20260829-133304.json` (raw frame NOT persisted).

| Stage | Result |
|---|---|
| Camera open/read | ✅ `mac-camera-2`, 640×480 |
| SSDLite | 0 detections, 0 tracks (real scene, nothing COCO-like — honest) |
| "locate all objects visible in the image" | ✅ success, 1 observation, **1.70 s** |
| "locate the largest object" | ✅ success, 1 observation, **1.65 s** |
| Track association | both → **candidate** (no tracks to match; no invented continuity ✓) |
| Privacy | raw frame never persisted ✓ |

**Key finding — latency at camera resolution:** ~**1.7 s per grounding call at
640×480 on MPS** (vs ~40 s on the 4112×2658 screenshot): grounding is
prefill-bound and real camera frames are small. This materially improves the
decision-gate picture: the Mac backend is *interactive* for cognition-driven
on-demand queries on the dev body (still not per-frame — SSDLite remains the
fast path). Decision gate B stands for large frames; camera-resolution
grounding is genuinely usable on the Mac.
- Model labels for generic queries echo query fragments ("the", "the largest")
  — expected for open-ended prompts; specific descriptions yield better labels.
- Queries were kept generic (no person/identity queries) per plan §16.

---

## Step 26 — Baseline vs +LocateAnything (first real evidence run)

`scripts/mac-locateanything-benchmark.py`, corpus-v1 (6 records on the 4112×2658
VS Code screenshot: menu bar, editor, terminal, largest-object + 2 negatives).
Real backends: SSDLite320-MobileNetV3 on MPS vs LocateAnything-3B on MPS
(bf16, hybrid). Evidence: `evidence/benchmark-compare-20260829-132811.json`.

| Metric | SSDLite-only | +LocateAnything | Delta |
|---|---|---|---|
| recall@0.5 (4 GT boxes) | 0.25 | 0.25 | 0.0 |
| precision | 0.083 | 0.25 | **+0.167** |
| false positives | 11 | 3 | **−8** |
| false negatives | 3 | 3 | 0 |
| mean IoU (matched) | — | 0.208 | — |
| negative-query correctness | — | 0.5 | — |
| latency p50 | — | 40 057 ms | — |

Reading (honest, small corpus, screen-content domain):
- **Both sides matched 1 of 4 GT boxes** (SSDLite: "largest" via its big
  window box; LocateAnything: "menu bar" at IoU 1.0). Screen UIs are
  genuinely hard for both; this is why the corpus needs more domains.
- **The real delta is noise suppression**: SSDLite hallucinated 11 boxes on
  a screenshot (COCO detector on non-COCO content); LocateAnything made 4
  predictions. Precision 3× higher, false positives 8 fewer.
- **Grounding's misses were near-misses**: terminal/editor/largest produced
  loose boxes (mean IoU 0.21, under the 0.5 bar) — part of the miss is GT
  strictness (caveats recorded in the corpus).
- **negative_correct 0.5**: the "person" hallucination (stochastic, seen in
  the feasibility run) — bounded retries / re-observation verification are
  the designed mitigations, not parser changes.
- Cognitive metrics (search success, world-state accuracy, planner success)
  remain brain-zone, per the plan.
