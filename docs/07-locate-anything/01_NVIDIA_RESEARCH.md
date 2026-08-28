# LocateAnything — NVIDIA Research Analysis

## 1. Identity

**Project:** LocateAnything  
**Paper:** *LocateAnything: Fast and High-Quality Vision-Language Grounding with Parallel Box Decoding*  
**Authors:** Shihao Wang, Shilong Liu, Yuanguo Kuang, Xinyu Wei, Yangzhou Liu, Zhiqi Li, Yunze Man, Guo Chen, Andrew Tao, Guilin Liu, Jan Kautz, Lei Zhang, Zhiding Yu.  
**Release:** 2026-05-26.  
**Paper:** https://arxiv.org/abs/2605.27365  
**NVIDIA project:** https://research.nvidia.com/labs/lpr/locate-anything/

The NVIDIA research page identifies LocateAnything as a unified vision-language framework for visual detection and grounding. It is explicitly positioned for Enterprise Intelligence and Physical AI, including robotics and embodied agents.

## 2. Problem being solved

Conventional VLM grounding often generates box coordinates as a sequence of individual coordinate tokens. A 2D bounding box has coupled geometry, but token-by-token autoregressive generation treats coordinates as a sequential language problem. That creates two problems:

1. inference is inherently sequential and therefore slow;
2. independent coordinate-token generation does not naturally preserve the geometric coupling inside one box.

LocateAnything changes the output representation so a complete geometric unit is decoded together.

## 3. Parallel Box Decoding (PBD)

PBD is the central contribution.

For a box:

`(x1, y1, x2, y2)`

is treated as one atomic block rather than four independently generated coordinate tokens.

For a point:

`(x, y)`

is treated as one atomic geometric unit.

The vision encoder works at native resolution to preserve fine spatial detail. The decoder then predicts complete box/point units in parallel.

### Why PBD matters for Novi

Novi needs a perception layer that can answer language-conditioned spatial questions without forcing every visual query through a large, slow reasoning model. PBD provides a model-level mechanism for making localization a high-throughput operation.

The architectural benefit is not merely speed. The atomic unit gives Novi a cleaner contract:

`natural-language spatial intent -> geometric observation`.

## 4. Three inference modes

### Fast / MTP

Multi-token/parallel decoding predicts geometric blocks in parallel. NVIDIA positions this mode for latency- and compute-constrained applications such as on-device robotics and embodied agents.

### Slow / NTP

Autoregressive next-token decoding. It is slower but more stable and is appropriate for high-precision labeling, data curation and offline evaluation.

### Hybrid

Fast MTP is used by default. When the fast output is unreliable, the affected block is discarded and NTP is used to regenerate it. This is the recommended operational mode for Novi's first integration.

## 5. Corrected NTP re-decoding

NVIDIA identifies two important failure classes in parallel decoding:

- **Format irregularity:** malformed output around category/block boundaries.
- **Spatial ambiguity:** intermediate coordinates become ambiguous when objects are dense or overlapping.

The hybrid procedure does not accept a corrupted block blindly. It returns to the last verified prefix, regenerates the problematic block using NTP, and then resumes parallel decoding.

For Novi, this should remain an internal model-runtime detail. Novi should receive a validated response object and must not treat raw model text as authoritative world state.

## 6. Model architecture

The released 3B model combines:

- **Vision:** MoonViT / MoonViT-SO-400M.
- **Language decoder:** Qwen2.5-3B-Instruct.
- **Connector:** MLP projector.
- **Output:** structured block-based visual grounding representation.

The model combines ordinary language/VLM reasoning capability with a localization-specific block formulation.

## 7. Training concept

NVIDIA describes a four-stage training pipeline in the model card: initial multimodal knowledge adaptation using captioning, VQA, OCR and related data, followed by grounding and dense-scene localization fine-tuning.

The research release additionally describes a dual-formulation objective: standard next-token prediction is retained for language reasoning while block-level multi-token prediction trains the PBD representation.

This is important for Novi because the model is not just a detector with a text wrapper. It is a VLM whose localization output has been deliberately structured for geometric prediction.

## 8. LocateAnything-Data

NVIDIA reports:

- **12M unique images**.
- **138M language queries**.
- **785M bounding boxes**.

Approximate query distribution:

| Task | Query share | Novi relevance |
|---|---:|---|
| General object detection | 66.9% | Continuous object inventory and candidate grounding |
| GUI element grounding | 16.5% | Low direct robot value; useful for tools/agent interfaces |
| Referring comprehension | 7.3% | **Very high** for language-conditioned robot perception |
| OCR/text localization | 3.6% | Useful for signs, labels and environment text |
| Layout grounding | 3.5% | Useful for structured scenes and documents, lower robot priority |
| Point-based localization | 2.2% | **High** for pointing, target selection and fine spatial reference |

The data diversity is a major reason to prefer LocateAnything over a closed-category detector for open-world queries.

## 9. Reported benchmark results

NVIDIA reports Hybrid-mode throughput of **12.7 boxes/second (BPS) on one H100**, compared with 1.1 BPS for Qwen3-VL and 5.0 BPS for Rex-Omni in the cited comparison.

Reported mean F1 results include:

- LVIS: 50.7.
- COCO: 54.7.
- Dense200: 58.7.
- VisDrone: 39.9.
- DocLayNet: 76.8.
- M6Doc: 70.1.
- TotalText: 43.3.
- ScreenSpot-Pro: 60.3.
- HumanRef: 78.7 mean F1.
- RefCOCOg validation: 76.7 mean F1.
- RefCOCOg test: 77.6 mean F1.
- Pointing: reported best result on all seven listed benchmarks.

These are NVIDIA-reported benchmark results and must not be interpreted as Novi performance. Novi must benchmark the actual hardware, image resolution, query distribution and runtime configuration it uses.

## 10. Throughput scaling / ablation findings

NVIDIA reports:

- PBD Slow Mode F1 of 52.1 in the COCO ablation.
- PBD 16.9 BPS versus 5.5 BPS for the cited structure-agnostic MTP baseline.
- Hybrid around 13.2 BPS / 51.6 F1 in the ablation.
- With 20–300 target boxes, PBD scales from roughly 12 to ~25 BPS in the cited dense-scene experiment, while NTP suffers a severe latency bottleneck.
- X-Y corner ordering performed best among the tested ordering strategies.

Again, these are H100 research measurements, not Mac measurements.

## 11. Capabilities relevant to Novi

### High priority

- Open-vocabulary object localization.
- Natural-language phrase grounding.
- Multiple-instance grounding.
- Dense-scene detection.
- Point localization.
- Fine-grained spatial reference.
- Referring-expression comprehension.

### Medium priority

- OCR localization.
- GUI grounding for Novi's development/control interfaces.
- Layout understanding.

### Not provided by LocateAnything alone

LocateAnything does **not** provide Novi's:

- persistent object identity;
- world model;
- 3D metric position;
- camera calibration;
- depth;
- odometry;
- SLAM;
- temporal tracking policy;
- safety governance;
- action planning;
- navigation;
- actuator control;
- long-term memory.

Those remain Novi responsibilities.

## 12. Source links

- NVIDIA research: https://research.nvidia.com/labs/lpr/locate-anything/
- NVIDIA paper PDF: https://research.nvidia.com/labs/lpr/locate-anything/LocateAnything.pdf
- arXiv: https://arxiv.org/abs/2605.27365
- NVIDIA code: https://github.com/NVlabs/Eagle/tree/main/Embodied
- NVIDIA model: https://huggingface.co/nvidia/LocateAnything-3B
- NVIDIA demo: https://huggingface.co/spaces/nvidia/LocateAnything
