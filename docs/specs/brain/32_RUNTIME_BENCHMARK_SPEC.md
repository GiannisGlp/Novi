# Runtime Benchmark Specification

**Status:** EVALUATING — baseline capture procedure defined; no AirLLM performance claim may be made without comparison to the captured baseline (plan `12_AIRLLM_ADAPTATION_AND_INFERENCE_RUNTIME_PLAN.md` §5.3, §29, §35).
**Owner:** Novi project

## 1. Purpose

All performance claims must be backed by machine-readable execution evidence, not screenshots or manual claims. This spec defines the benchmark suite, the evidence schema, and the acceptance rule: **no AirLLM performance claim may later be made without comparison to the baseline.**

## 2. Baseline capture (plan 12 §5.3)

Before AirLLM is installed, record for each currently executable model/backend:

```text
startup time
first-token latency
generation latency
tokens/second
peak RAM
peak VRAM when applicable
CPU utilization
disk I/O
power if measurable
error rate
output correctness on a fixed prompt suite
```

Evidence lives under `benchmarks/` as JSON with timestamps and software/model versions.

## 3. Infrastructure benchmarks (plan 12 §29)

- cold start (process start → backend init → model load → first generation)
- warm request (model prepared → request → generation)
- reload (model A → unload → model B → generation)
- model switch (Qwen 8B → Nemotron → Qwen 27B → Qwen 8B; verify no leaked memory, no stale tokenizer/KV state, no cross-model conversation corruption, correct model metadata in telemetry — plan 12 §38)
- first token (TTFT)
- tokens/sec
- peak memory
- disk throughput
- repeated requests
- long context
- cancellation
- failure recovery

## 4. Novi cognitive benchmarks (plan 12 §29)

Dialogue, instruction following, scene interpretation (text/structured input), spatial reasoning, task decomposition, planning, replanning, tool selection, tool argument generation, uncertainty expression, memory-grounded answers, contradiction handling, refusal of unauthorized actions, recovery after failed tool execution.

## 5. AirLLM vs baseline comparison (plan 12 §35)

For Qwen3.8-27B, compare existing/native backend vs AirLLM using **exactly the same** model revision, prompt suite, tokenizer, generation settings, hardware, temperature, and max output tokens. Report:

```text
quality delta
TTFT delta
throughput delta
peak VRAM delta
peak RAM delta
disk IO delta
startup delta
failure rate delta
```

**No adoption decision may be made from VRAM alone** (plan 12 §35, §59 weighted decision).

## 6. Evidence schema

```yaml
benchmarks/
  hardware-profile.json
  qwen3.8-27b-airllm.json
  qwen3.8-27b-baseline.json
  compatibility-matrix.json
  soak-test.json
  failure-injection.json
  inference-audit.json        # Phase 0 audit (captured 2026-08-30)
```

Each evidence file includes `captured_at` timestamp and the software/model versions (`airllm`, `transformers`, `torch`, model revision).

## 7. Execution paths (plan 12 §19)

The router must know which path a latency measurement belongs to:

- **Cold path**: process start → backend init → model load → first generation
- **Warm path**: model prepared → request → generation
- **Re-load path**: model A → unload → model B → generation
- **Recovery path**: model load failure → cleanup → health check → fallback model

## 8. Soak and failure injection (plan 12 §50–51)

Soak durations: 1h, 4h, 8h, 24h (hardware permitting). Track memory growth, disk usage, shard corruption, reload failures, latency drift, thermal behavior, generation failures, scheduler starvation, stale state.

Failure injection: remove shard, corrupt shard, fill disk, kill worker, interrupt generation, force OOM, break tokenizer, kill network, restart runtime, restart Mac. Expected outcome: failure detected → classified → resources cleaned → fallback selected → autonomy bounded.

## 9. Current evidence state

| Artifact | Status |
|---|---|
| `benchmarks/inference-audit.json` | captured 2026-08-30 (57 call sites) |
| hardware profile | `probe_hardware()` implemented; machine-readable capture pending |
| qwen3.8-27b baseline | pending (needs executable model path) |
| qwen3.8-27b airllm | pending (needs AirLLM install + Step 17 artifact resolution) |
| soak / failure-injection | pending (post AirLLM smoke) |

## 10. Status vocabulary

`DESIGNED → PROPOSED → EVALUATING → PROTOTYPE → IMPLEMENTED → TESTED → INTEGRATED`. The inference runtime contract is `PROTOTYPE`; the AirLLM backend is `PROTOTYPE` (implemented behind the contract, hardware validation pending).
