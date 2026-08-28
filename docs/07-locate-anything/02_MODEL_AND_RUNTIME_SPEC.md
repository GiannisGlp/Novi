# LocateAnything — Model and Runtime Specification

## 1. Released model

**Model ID:** `nvidia/LocateAnything-3B`  
**Nominal parameters:** 3B  
**Vision encoder:** MoonViT-SO-400M  
**Language model:** Qwen2.5-3B-Instruct  
**Projector:** MLP  
**Weight format:** BF16 safetensors  
**Published model footprint:** approximately 7.8 GB in the Hugging Face repository  
**Release:** 2026-05-26  
**Model card:** https://huggingface.co/nvidia/LocateAnything-3B

NVIDIA's Eagle model table reports a maximum length of 25K for LocateAnything-3B.

## 2. Input contract

Primary input:

- one image;
- one natural-language text query.

The upstream worker also supports optional visual-prompt inputs in its plumbing, including a supplied image or an image crop from a bounding box. However, NVIDIA's current README explicitly states that the released `nvidia/LocateAnything-3B` weights do **not** support visual-prompt inference out of the box. The released weights and the visual-prompt fine-tuning path must therefore not be conflated.

Novi implementation rule: visual prompts remain a future capability and must be feature-gated until a compatible NVIDIA checkpoint is verified.

## 3. Output contract

The released worker/model represents boxes with special tokens conceptually equivalent to:

`<ref>label</ref><box><x1><y1><x2><y2></box>`

Coordinates are integer-normalized to `[0, 1000]`.

Points are represented as:

`<box><x><y></box>`

No-object output is represented by:

`<box>none</box>`

Novi must immediately parse this into typed structures. Raw generated text must never be written directly to the world model.

## 4. Required normalization

Novi's current detection contract uses pixel-space `(x, y, w, h)` integer boxes. LocateAnything emits normalized corner coordinates.

Adapter conversion:

```text
x1_px = x1 / 1000 * image_width
x2_px = x2 / 1000 * image_width
y1_px = y1 / 1000 * image_height
y2_px = y2 / 1000 * image_height

x = x1_px
y = y1_px
w = x2_px - x1_px
h = y2_px - y1_px
```

The adapter must clamp bounds, reject inverted/zero-area boxes, retain the original normalized coordinates for provenance, and retain the image dimensions used for conversion.

## 5. Inference modes

Novi should expose:

```text
fast
slow
hybrid
```

but the default should be **hybrid**.

### Fast
Use when:

- the query is routine;
- latency budget is tight;
- output is expected to be unambiguous;
- the result is used as a candidate observation rather than immediate irreversible action.

### Slow
Use when:

- the query is high precision;
- the result is used for annotation/evaluation;
- the fast path reports ambiguity;
- repeated visual checks disagree;
- the downstream action has materially higher risk.

### Hybrid
Default for Novi. It preserves PBD speed while allowing NVIDIA's corrected NTP re-decoding behavior.

## 6. Generation settings

NVIDIA's current model card recommends:

- `generation_mode="hybrid"`;
- `max_new_tokens=8192`.

Novi should not blindly expose every generation parameter to cognition. The perception backend should own safe defaults and allow bounded configuration through a typed policy.

## 7. Standard worker

Upstream worker class:

`LocateAnythingWorker`

The worker loads the model once and exposes reusable inference operations. It supports standard Hugging Face model loading and an optional batch runtime.

Standard initialization uses:

- `AutoTokenizer.from_pretrained(..., trust_remote_code=True)`;
- `AutoProcessor.from_pretrained(..., trust_remote_code=True)`;
- `AutoModel.from_pretrained(..., trust_remote_code=True)`;
- BF16 by default;
- CUDA by default in upstream code.

Novi must not copy the upstream worker wholesale. We should implement a narrow adapter around a version-pinned external runtime.

## 8. Batch runtime / LA Flash

The current Hugging Face release includes:

- `batch_infer.py`;
- `batch_utils/`;
- `kernel_utils/`.

The optional `la_flash` path uses FlashAttention variable-length sparse range plans and avoids dense SDPA masks. NVIDIA documents it as an inference/evaluation path and says training should continue to use the standard model code path.

NVIDIA's README provides an A100 4K street-image probe at batch size 4:

- dense SDPA: 8.2600 s, 35.12 GB peak reserved memory;
- `la_flash`: 8.0314 s, 11.71 GB peak reserved memory.

This is not a representative Novi benchmark. It is evidence that the batch runtime can materially reduce memory in the tested configuration.

## 9. Deployment paths documented upstream

NVIDIA/Hugging Face currently documents:

### Transformers

Direct local Python loading with `trust_remote_code=True`.

### vLLM

OpenAI-compatible server using:

`vllm serve nvidia/LocateAnything-3B`

### SGLang

OpenAI-compatible server using SGLang launch tooling.

### Docker Model Runner

`docker model run hf.co/nvidia/LocateAnything-3B`

### Docker + SGLang

NVIDIA documents a GPU-enabled container configuration.

Novi should initially prefer an in-process adapter for controlled Mac experiments only if the model can actually run on the target Mac. The production robot path should be benchmarked separately and may use a dedicated local model server/process.

## 10. Hardware compatibility implications

Upstream research measurements are on NVIDIA H100, with the model card documenting H100/A100 testing. The optional `la_flash` release is documented for A100, RTX 4090 and other non-Hopper/Blackwell GPUs.

Novi's Mac currently uses Apple MPS. NVIDIA does not document Apple MPS as a supported LocateAnything deployment target.

Therefore:

**Mac status = experimental compatibility question, not assumed support.**

The implementation must include a capability probe and a clean `unsupported`/`unavailable` state. It must never crash Novi when LocateAnything cannot load.

## 11. Dependency footprint

The upstream package declares a large dependency set including Transformers, tokenizers, sentencepiece, accelerate, PEFT, bitsandbytes, DeepSpeed, timm, Liger Kernel, deepspeed, triton, scipy, datasets, decord, OpenCV and several UI/server packages.

Novi must preserve its stdlib-first core. LocateAnything dependencies should be isolated behind an optional perception extra or separate runtime environment.

Recommended future package shape:

```text
novi/perception/
    detection.py
    pipeline.py
    tracking.py
    locate_anything.py          # thin adapter
    locate_anything_runtime.py  # optional runtime boundary
```

The core package should import neither Transformers nor CUDA-only dependencies during normal startup.

## 12. Trust boundary

`trust_remote_code=True` is used by NVIDIA's upstream loader. This is an explicit supply-chain boundary.

Novi must:

1. pin the model revision/commit used for validation;
2. record the model revision in provenance;
3. isolate optional runtime imports;
4. review upstream custom code before production deployment;
5. avoid silently upgrading the model;
6. keep the model runtime outside the safety authority.

## 13. Visual prompt warning

The upstream worker contains visual-prompt plumbing and crop handling, but current released weights do not support visual prompt inference out of the box. Do not advertise this capability in Novi until NVIDIA-compatible weights are validated.

## 14. Upstream source files

- README: https://github.com/NVlabs/Eagle/blob/main/Embodied/README.md
- Worker: https://github.com/NVlabs/Eagle/blob/main/Embodied/locateanything_worker.py
- Package: https://github.com/NVlabs/Eagle/blob/main/Embodied/pyproject.toml
- Model: https://huggingface.co/nvidia/LocateAnything-3B
- NVIDIA research: https://research.nvidia.com/labs/lpr/locate-anything/
