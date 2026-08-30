# Model Compatibility Matrix

**Status:** EVALUATING — initial matrix from the registry; every `true` capability must gain execution evidence (plan `12_AIRLLM_ADAPTATION_AND_INFERENCE_RUNTIME_PLAN.md` §32).
**Owner:** Novi project

## 1. Matrix contract

Every capability cell is tri-state: `supported | unsupported | unknown`.

- Every `supported` must have execution evidence (test/benchmark artifact).
- Every `unknown` is unavailable to the router until validated.
- The router only ever selects approved models (`status == "approved"` in the registry); nothing is routable by default.

## 2. Current model set (exactly the five approved aliases — plan 12 §9)

| Registry id | Local alias | Source | Role candidates | AirLLM eligibility |
|---|---|---|---|---|
| `qwen3-4b` | `qwen3:4b` | ollama `qwen3:4b` | lightweight reasoning, classification, intent parsing, simple dialogue, background summarization, cheap fallback | optional evaluation target, not mandatory |
| `qwen3-8b` | `qwen3:8b` | ollama `qwen3:8b` | default general cognition, ordinary dialogue, lightweight planning, tool selection, context interpretation | benchmark only unless constrained HW shows an advantage |
| `nemotron-3.5-lightning` | `nemotron-3.5-lightning:latest` | ollama | agentic planning, long-running task orchestration, tool-oriented reasoning, multi-step cognitive work | benchmark-driven; never assumed from family name |
| `qwen3.8-27b` | `qwen3.8:27b` | huggingface `Qwen/Qwen3.8-27B` | deep reasoning, multimodal reasoning | **primary evaluation target**; artifact mapping required (Step 17) |
| `qwen3.8-latest` | `qwen3.8:latest` | ollama `qwen3.8:latest` | unresolved | **not routable** until exact artifact identity/capabilities recorded (§9.5) |

## 3. Capability matrix (provisional)

Machine-readable form lives in the registry (`novi.brain.inference.registry.ModelRegistry`) and `novi/brain/inference/capabilities.py` (`ModelCapabilityRecord`).

```yaml
model: qwen3-4b
backend: existing
status: candidate
capabilities:
  text_generation: true      # evidence: pending baseline benchmark
  vision: false
  tool_calling: unknown
  structured_output: unknown
  streaming: unknown
hardware:
  mac_apple_silicon: unknown
  cuda: unknown

model: qwen3.8-27b
backend: airllm
status: evaluating
capabilities:
  text_generation: unknown   # requires AirLLM smoke test on target hardware
  vision: unknown
  tool_calling: unknown
  structured_output: unknown
  streaming: unknown
hardware:
  mac_apple_silicon: unknown # must be executed on the actual dev machine
  cuda: unknown
```

## 4. Compatibility matrix (software stack — plan 12 §33)

Captured at runtime by `probe_airllm_environment()` in `novi/brain/inference/airllm/compatibility.py`; cells below are the current environment (subject to change — re-probe before any claim):

| Component | Constraint | Notes |
|---|---|---|
| Python | >= 3.11 (repo) | probe records exact |
| Torch | per AirLLM stack | lazy probe |
| Transformers | `< 5.13` (AirLLM metadata constraint) | `require_airllm()` refuses majors >= 5 rather than upgrading project-wide |
| Accelerate / Safetensors / HF Hub | per AirLLM stack | lazy probe |
| AirLLM | optional extra `novi[airllm]` | never a base dependency |
| OS | macOS (dev) / NVIDIA Linux (target) | Mac/MPS and CUDA tested separately |
| GPU backend | `cuda` / `mps` / `cpu` / `unknown` | `unknown` never promoted to `supported` |

### 4.1 Validated environment (2026-08-30, `benchmarks/compatibility-matrix.json`)

AirLLM 3.3.0 installed in an isolated environment; `import airllm` smoke test **PASSES on the Mac** (requires `mlx` on darwin). Recorded: Python 3.11.15, torch 2.13.0, transformers 4.57.1, accelerate 1.14.0, safetensors 0.8.0, OS Darwin/arm64, GPU backend `mps`. `require_airllm()` passes (transformers major 4 < 5).

### 4.2 Step 17 artifact resolution — Qwen3.8-27B

| Fact | Value |
|---|---|
| Exact model | `Qwen/Qwen3.8-27B` |
| Revision | `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0` |
| Architecture | `Qwen3_5ForConditionalGeneration` (`model_type: qwen3_5`) |
| Modality | multimodal |
| License | apache-2.0 |
| Config-required Transformers | `5.8.0.dev0` |
| Installed (validated) Transformers | 4.57.1 |

**Compatibility finding:** the model's `config.json` declares `transformers_version: 5.8.0.dev0`, which conflicts with the plan's rule (§10) *"Do not globally upgrade Transformers solely to satisfy AirLLM"* and the validated matrix cap (`<5.13`). Per plan §9.5 the registry records `airllm_eligible=false` and the blocker; the model is **not admitted to the AirLLM production pool** until the Transformers conflict is resolved on validated hardware. No checkpoint substitution is permitted.

### 4.3 Mac (Apple Silicon) path — AirLLM 3.3.0 MLX backend

Verified by source inspection + isolated install on the dev machine (2026-08-30):

- On macOS, `airllm.AutoModel.from_pretrained(...)` routes to **`AirLLMLlamaMlx`** (a pure-MLX reimplementation) for every architecture; the CUDA layer-streaming path (`AirLLMBaseModel`) is used on non-Mac only.
- The MLX path only supports the **standard Llama-style layout** (`model.embed_tokens` / `model.layers.N` / `model.norm` / `lm_head`) with a compatible config (hidden_size, intermediate_size, num_attention_heads, num_key_value_heads, num_hidden_layers, vocab_size, rms_norm_eps, rope_theta).
- **Qwen3.8-27B is NOT supported on the Mac path**: its `Qwen3_5ForConditionalGeneration` nests the decoder at `model.language_model.layers` (dedicated CUDA subclass `AirLLMQwen3_5`), which the MLX path cannot stream.
- **Qwen3-4B/8B are also NOT supported on the Mac path** (execution-verified 2026-08-30): Qwen3 uses QK-norm (`q_norm`/`k_norm` per-head norms) and the MLX `TransformerBlock` has no such parameters → `ValueError: Module does not have parameter named "q_norm"` during generation. Evidence: `benchmarks/airllm-mac/qwen3-4b-finding.json`. This overturns the plan §9.1/§9.2 optional-evaluation hypothesis for Qwen3 on Mac.
- The MLX API differs from CUDA: `generate(x, temperature=0, max_new_tokens=...)` takes a **token tensor** (no `top_k`), and the loader must pass `layer_shards_saving_path=` (not `shard_dir`), with `compression=None` (not `"none"`) for the disabled state. The Novi adapter (`novi/brain/inference/airllm/adapter.py`) and loader branch on the platform (`_is_mlx`, `_default_device`, `_airllm_compression`).
- **Mac-viable AirLLM targets** (plain Llama-style, no QK-norm): `TinyLlama/TinyLlama-1.1B-Chat-v1.0` — **execution-verified end-to-end on the Mac** (prepare 20 s, cold generation 56.8 s/27 tokens, warm 28.2 s, unload ok; evidence `benchmarks/airllm-mac/tinyllama-1.1b.json`). Validation runner: `novi/brain/benchmarks/airllm_mac_validate.py`.

## 5. Evidence log

| Date | Evidence artifact | Claim |
|---|---|---|
| 2026-08-30 | `benchmarks/inference-audit.json` | 57 inference call sites inventoried; 24 classified migrate-to-runtime; all LLM inference is local Ollama with deterministic fallbacks |
| 2026-08-30 | Brain suite: 1758 passed | Inference abstraction introduced without regressing the Mac Brain |
| 2026-08-30 | `benchmarks/compatibility-matrix.json` | AirLLM 3.3.0 import smoke passes on Mac (mlx, MPS); Qwen3.8-27B artifact resolved — architecture `Qwen3_5ForConditionalGeneration`, config requires transformers 5.8.0.dev0, recorded `airllm_eligible=false` |
| pending | Qwen3.8-27B AirLLM preparation + smoke | any `supported` capability claim for airllm backend |

## 6. Router hypotheses (provisional — benchmark-settable, plan 12 §23/§46)

| Deliberation | Model hypothesis | Backend hypothesis |
|---|---|---|
| FAST | qwen3-4b | existing |
| NORMAL | qwen3-8b | existing |
| DELIBERATE | nemotron-3.5-lightning | existing |
| DEEP | qwen3.8-27b | airllm (only after artifact resolution + validation) |

No hypothesis is a permanent architecture fact; the benchmark suite can overturn any of them (plan 12 §18).
