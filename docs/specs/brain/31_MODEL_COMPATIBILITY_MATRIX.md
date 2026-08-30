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

## 5. Evidence log

| Date | Evidence artifact | Claim |
|---|---|---|
| 2026-08-30 | `benchmarks/inference-audit.json` | 57 inference call sites inventoried; 24 classified migrate-to-runtime; all LLM inference is local Ollama with deterministic fallbacks |
| 2026-08-30 | Brain suite: 1758 passed | Inference abstraction introduced without regressing the Mac Brain |
| pending | Qwen3.8-27B AirLLM preparation + smoke | any `supported` capability claim for airllm backend |

## 6. Router hypotheses (provisional — benchmark-settable, plan 12 §23/§46)

| Deliberation | Model hypothesis | Backend hypothesis |
|---|---|---|
| FAST | qwen3-4b | existing |
| NORMAL | qwen3-8b | existing |
| DELIBERATE | nemotron-3.5-lightning | existing |
| DEEP | qwen3.8-27b | airllm (only after artifact resolution + validation) |

No hypothesis is a permanent architecture fact; the benchmark suite can overturn any of them (plan 12 §18).
