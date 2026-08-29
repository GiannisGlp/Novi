# LocateAnything — NVIDIA Runtime Benchmark Plan (Phase 12, steps 29–30)

**Status:** SPEC READY — execution BLOCKED on NVIDIA hardware (no GPU on the dev Mac, 2026-08-29).
**Rule from the plan (§19 steps 29–30):** *do not select a deployment runtime from
documentation alone — benchmark on the actual target GPU.*

This document is the complete protocol so that the moment a Jetson AGX Thor /
AGX Orin 64GB (or any CUDA GPU) exists, the comparison is a single scripted run
with zero design work left.

## 1. Candidate runtimes (plan §14)

| # | Runtime | Notes |
|---|---|---|
| 1 | Standard Transformers (`AutoModel`, pinned `c32291ca…`) | baseline; already validated on MPS (mac feasibility) |
| 2 | NVIDIA/upstream `LocateAnythingWorker` | reference worker; batch runtime + `la_flash` options |
| 3 | `la_flash` batch runtime | HF-release `batch_infer.py` + `batch_utils/`/`kernel_utils/`; FlashAttention varlen sparse plans (A100 probe: 8.03 s / 11.71 GB vs dense 8.26 s / 35.12 GB at batch 4, 4K street image — NOT a Novi benchmark) |
| 4 | vLLM | OpenAI-compatible: `vllm serve nvidia/LocateAnything-3B` |
| 5 | SGLang | OpenAI-compatible launch tooling |
| 6 | NVIDIA-native acceleration | only where supported on the target hardware |

## 2. Target hardware

- Primary: **Jetson AGX Thor or AGX Orin 64GB** (deferred decision per docs/05-hardware freeze-gate).
- Fallback: any CUDA workstation for early evidence.

## 3. Measurement protocol (plan Step 10.3 + §19 items)

On the target GPU, for EACH runtime:

1. **Load**: time + peak reserved memory (torch.cuda.max_memory_reserved) + cold start to first answer.
2. **Latency**: same query battery as `scripts/mac-locateanything-experiment.py` (corpus-v1's 6 records + 3 camera-style 640×480 frames); report **p50/p95/p99** per runtime.
3. **Sustained throughput**: N sequential queries without unload (N=10), tracking memory growth (the MPS experiment's jetsam lesson: watch allocator retention).
4. **Batch runtime probe** (run-times 2/3 only): batch size 4 on the 4K street image (upstream's A100 probe) AND batch 4 on corpus-v1 frames — memory + latency.
5. **Quality parity check**: same corpus → IoU@0.5/recall/precision via `benchmark_compare` — a faster runtime that changes outputs must show it (never assume runtime equivalence).
6. **Failure behavior**: kill -9 mid-generation; restart; check capability probe recovers to `available` (Novi's seven states).

## 4. Acceptance criteria (perception budget, plan §15)

| Metric | Minimum for production candidate |
|---|---|
| p50 latency, 640×480 query | ≤ 500 ms (per-frame budget is SSDLite's; grounding is cognition-on-demand but must not block) |
| p95 latency | ≤ 2× p50 |
| Peak memory | fits target GPU with room for camera pipeline + brain |
| Quality delta vs transformers baseline | IoU@0.5 within ±0.05 |
| Restart/recovery | probe returns `available`; no manual intervention |

## 5. Deliverable when hardware arrives

`scripts/mac-locateanything-runtime-benchmark.py` — TDD'd against the live GPU
(not written blind now): runs the protocol above per installed runtime, emits
`docs/07-locate-anything/evidence/runtime-benchmark-<runtime>-<ts>.json` and a
comparison table. Then step 30's decision (which runtime Novi ships) is a
review of that table — not a documentation guess.

## 6. Wiring (unchanged by runtime choice)

The Novi adapter (`SpatialPerceptionBackend`) is runtime-agnostic: any runtime
implements `LocateAnythingRuntime` (probe + infer) behind the same
`LocateAnythingBackend`. No perception/brain code changes when the runtime
changes — the MPS bundle, an in-process CUDA bundle, and a remote vLLM client
are all the same seam (plan Phase 12 target architecture).
