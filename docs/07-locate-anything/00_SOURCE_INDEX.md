# Novi — LocateAnything Source Index

**Date:** 2026-08-28  
**Purpose:** Canonical source map for NVIDIA LocateAnything research and the material required to evaluate and implement it in Novi.

> This directory summarizes and cross-references the upstream material. It does **not** copy NVIDIA's paper, model weights, datasets, or full upstream documentation into Novi. The upstream sources remain authoritative and should be consulted for exact implementation details, releases, licenses, and benchmark updates.

## 1. Primary NVIDIA sources

### NVIDIA Research project page
- https://research.nvidia.com/labs/lpr/locate-anything/
- Authoritative overview of the method, Parallel Box Decoding (PBD), inference modes, data composition, headline benchmarks, ablations, and citation.

### NVIDIA technical report / paper
- https://research.nvidia.com/labs/lpr/locate-anything/LocateAnything.pdf
- Paper: *LocateAnything: Fast and High-Quality Vision-Language Grounding with Parallel Box Decoding*.
- arXiv: https://arxiv.org/abs/2605.27365

### NVIDIA research code
- https://github.com/NVlabs/Eagle/tree/main/Embodied
- LocateAnything implementation, worker API, training, data preparation, evaluation, streaming packing, and model license.

### NVIDIA Eagle repository
- https://github.com/NVlabs/Eagle
- Places LocateAnything in the broader NVIDIA Eagle VLM family and records release history.

## 2. NVIDIA release documents in the upstream repository

| Upstream document | Novi relevance |
|---|---|
| `Embodied/README.md` | Complete release overview, capabilities, installation, inference, output format, training entry point, batch runtime, known visual-prompt limitation. |
| `Embodied/document/TRAINING.md` | Full SFT training procedure, hardware, attention backends, arguments, DeepSpeed and resume behavior. |
| `Embodied/document/DATA_PREPARATION.md` | JSONL/recipe schema, coordinate conventions, task formats, media requirements and training data layout. |
| `Embodied/document/RESULTS.md` | Detailed benchmark tables, ablations and reported performance. |
| `Embodied/document/STREAMING_PACKING.md` | Stateful online packing and deterministic resume implementation. Primarily relevant if Novi ever fine-tunes LocateAnything. |
| `Embodied/evaluation/README.md` | Evaluation datasets, preparation and evaluation commands. |
| `Embodied/LICENSE_MODEL` | Critical model-weight license. Current released weights are restricted to non-commercial research/evaluation use. |
| `Embodied/locateanything_worker.py` | Reusable inference worker, generation modes, visual-prompt plumbing, standard and batch-runtime integration. |
| `Embodied/pyproject.toml` | Upstream dependency footprint and Python package metadata. |

## 3. Official model release

### Hugging Face — NVIDIA LocateAnything-3B
- https://huggingface.co/nvidia/LocateAnything-3B
- Official model card, weights, configuration, tokenizer, processor, batch inference utilities, kernel utilities, examples, and license metadata.

Important current facts:
- Model: `nvidia/LocateAnything-3B`.
- Architecture: MoonViT-SO-400M vision encoder + Qwen2.5-3B-Instruct language decoder + MLP projector.
- Nominal parameter count: 3B.
- Weight format currently published: BF16 safetensors; repository/model footprint is approximately 7.8 GB.
- Maximum context reported by NVIDIA's Eagle model table: 25K.
- Tested inference hardware documented by the model card: H100 and A100.
- The model card recommends `max_new_tokens=8192` and `generation_mode="hybrid"` to balance speed and robustness and avoid truncation.

## 4. Official demo / data

- Demo: https://huggingface.co/spaces/nvidia/LocateAnything
- Dataset release referenced by NVIDIA: https://huggingface.co/datasets/nvidia/LocateAnything-Data

## 5. Release timeline relevant to Novi

- 2026-05-26: LocateAnything released through NVIDIA GitHub, Hugging Face, demo and research page.
- 2026-06: NVIDIA released a visual-prompt fine-tuning script and announced LocateAnything acceptance to ECCV 2026.
- 2026-06: NVIDIA released optional `la_flash` batch inference for A100, RTX 4090 and other non-Hopper/Blackwell GPUs.

## 6. Authority hierarchy for Novi

When sources disagree, use this order:

1. Current NVIDIA model/code release and license files.
2. Current NVIDIA research page.
3. Current NVIDIA technical report / arXiv paper.
4. Current NVIDIA Hugging Face model card/configuration.
5. Novi's integration documentation, which records decisions and compatibility findings but is not authoritative over NVIDIA.

## 7. Novi-specific conclusion

LocateAnything should be treated as an **optional spatial-perception backend**, not as the owner of Novi's world model, safety policy, memory, planning or action authority.

The intended boundary is:

`camera frame + language query -> LocateAnything -> normalized spatial observations -> Novi perception/world model -> cognition/planning`.

The existing SSDLite detector remains the fast baseline. LocateAnything is the language-conditioned, open-vocabulary and precision-grounding path.
