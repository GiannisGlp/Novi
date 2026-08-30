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
