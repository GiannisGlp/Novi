# PERF-PROBE: Novi Brain Per-Step Cost Profile

| | |
|---|---|
| **Audit ID** | PERF-PROBE-2026-08-24 |
| **Harness** | `novi/brain/benchmarks/perf_probe.py` (rev 1.0.0, stdlib-only timing) |
| **Raw JSON** | `/tmp/perf.json` (regenerable via the command below) |
| **Run** | 2026-08-25T05:58:27Z · host `Mac.lan` · Darwin 25.5.0 · arm64 · Python 3.14.7 |
| **Accelerators** | torch 2.13.0 · torchvision 0.28.0 · MPS available **and used** (`neural_device: mps`) |
| **Skips** | none — all phases executed |

All numbers below are **real measurements** from the harness run quoted above. Nothing is
synthesized. Items labeled *estimated* are projections that this probe did not directly measure.

## Methodology

One script, three measurement families, `time.perf_counter` wall-clock throughout:

1. **Whole-brain step latency** — two `MacBrain` instances, identical apart from perception:
   - *deterministic*: `SpecialistPerception()` (fixture backend);
   - *neural*: `SpecialistPerception(NeuralPerceptionBackend(confidence_threshold=0.45))`
     (torchvision SSDLite320-MobileNetV3-Large, auto-selected MPS).
   Both: fake camera (`read()` → `CameraFrame`, BGR 640×480×3 uint8 cv2-drawn synthetic scene:
   rectangles/circles/person-like figure), `MacBrainConfig(curiosity_enabled=False, memory_dir=<tmp>)`,
   `stt=None`, default reasoning. Protocol: `start()` → 3 warmup steps → 20 individually timed
   `brain.step()` calls → `stop()` in `finally`.
2. **Sub-phases outside the brain loop** — same perception object, timed standalone:
   `perception.process(sensor_id='probe', frame_id='p<n>', timestamp='t', frame=payload)` ×30 reps
   after 2 warmups (warmups absorb model load / first-call allocation); fake camera `read()` ×30
   (wrapper overhead only — it wraps a pre-rendered ndarray, no sensor I/O).
3. **Embedding recall** — `DurableMemoryStore(':memory:')`: admit 200 small memories, time 50
   `retrieve_semantic(query, limit=5)` calls with the `'hash'` embedder; repeat with `'minilm'`
   under a 60 s model-load budget (load took 5.82 s, cached — not skipped).

Caveats: warm torch-hub weights (no download in run window); single process, no competing
benchmark load; the fake camera measures dispatch overhead, not sensor capture; step counts are
modest (20 steps / 30 reps) — treat p95 as indicative, not SLA-grade.

## Measured results

Verbatim summary (see `/tmp/perf.json`):

```
deterministic.step            p50=14.253 ms   p95=15.219 ms   mean=14.359 ms   n=20
deterministic.perception      p50= 0.001 ms   (fixture backend)
neural.step                   p50=120.683 ms  p95=144.278 ms  mean=123.251 ms  n=20
neural.perception.process     p50= 47.187 ms  p95= 58.083 ms  mean= 48.433 ms  n=30
fake camera read              p50= 0.001 ms
embed_hash.recall             p50= 2.373 ms   p95= 2.558 ms   (200 memories admitted in 0.021 s)
embed_minilm.load             5.82 s          (one-time, cached)
embed_minilm.recall           p50= 7.790 ms   p95= 9.802 ms   (admit batch 0.941 s)
```

Derived observations (arithmetic on measured numbers only):

- Neural step ÷ deterministic step ≈ **8.5×** at p50.
- Neural `perception.process` standalone is 47.2 ms, yet the neural *step* exceeds the
  deterministic step by ≈106 ms — i.e. roughly **59 ms of step-level cost sits downstream of
  raw inference** (world-model/fusion/memory handling of real multi-object evidence, plus
  per-cycle sync effects). Attribution not yet profiled — see R4.
- Tail spread (p95−p50): neural step 23.6 ms; neural perception 10.9 ms.

## Latency budget vs targets

| Path | Measured p50 | Measured p95 | Target | Headroom @ p95 | Verdict |
|---|---|---|---|---|---|
| Auto-step tick, deterministic | 14.3 ms | 15.2 ms | 800 ms/tick | 98.1% free | ✅ comfortable |
| Auto-step tick, neural | 120.7 ms | 144.3 ms | 800 ms/tick | 82.0% free | ✅ passes today |
| Chat interaction (≈20 neural cycles worst case) | 2.41 s | 2.89 s | < 15 s | ~81% free | ✅ comfortable |
| Hash recall (per query) | 2.4 ms | 2.6 ms | — | negligible | ✅ |
| MiniLM recall (per query) | 7.8 ms | 9.8 ms | — | negligible per query; **5.8 s one-time load** | ⚠️ startup-only |

**Bottom line:** the 800 ms auto-step tick and <15 s chat targets are met with wide margins on
this Mac (MPS). Neural perception is affordable per-cycle *today*, but it consumes ~18% of the
tick budget at p95 and its cost scales with duty cycle — which motivates the duty-cycle
recommendation below before Jetson parity work.

## Top 5 optimization recommendations (ranked by expected win)

| # | Recommendation | Basis |
|---|---|---|
| R1 | **Run neural detection every-Nth auto-tick; interpolate via the world model between detections.** At 1 Hz the SSDLite pass costs 47–58 ms *every* cycle (measured); N=5 drops average perception duty ~80% while tracked objects stay fresh via world-model state. Biggest lever on energy + Jetson thermal headroom. | *Estimated win* on a **measured** per-call cost (47.2 ms p50) |
| R2 | **Cut per-step overhead downstream of inference (~59 ms gap).** Profile one neural `step()` with cProfile; if world-model/fusion/memory updates dominate, make evidence ingestion incremental (diff against last cycle) instead of full re-integration. Would bring neural steps toward ~65 ms. | **Measured gap** (120.7 vs 61.5 ms expected); *estimated* recoverability |
| R3 | **Stabilize the MPS hot path.** Warm-up already helps (3-step warmup precedes timing); keep brains long-lived rather than per-session re-instantiated, pin input tensor shape (fixed 640×480 → 320×320 letterbox) and reuse buffers to attack the 23.6 ms p50→p95 step tail. | *Estimated*; tail size is **measured** |
| R4 | **Pre-scale frames once at acquisition.** SSDLite consumes 320×320; resizing 640×480 per call inside `process()` is pure overhead if the camera layer can deliver a smaller/letterboxed frame directly. Estimated 10–30% off the 47 ms perception call. | *Estimated*; current resize cost included in **measured** 47.2 ms |
| R5 | **Lazy-load heavy models (MiniLM now measured, STT same pattern).** MiniLM adds a 5.82 s one-time load (cached; cold download far worse) while per-query recall is cheap either way. Defer until first chat/semantic-recall use; keep `'hash'` (2.4 ms recall) as the deterministic/CI default. | **Measured** load + recall costs; *estimated* UX impact |

Not recommended now: micro-optimizing the deterministic path (15 ms p95 vs 800 ms budget — no
headroom problem), or caching router confidences (router was not engaged in this probe;
`reasoning=None`). Revisit when a router-bearing profile exists.

## Reproduce

```bash
cd /Users/vanonatobaidze/projects/Novi && \
PYTHONPATH=. .venv/bin/python -m novi.brain.benchmarks.perf_probe --json-out /tmp/perf.json
```

Exits 0 always; absent hardware/deps print explicit `SKIP` reasons instead of crashing.
