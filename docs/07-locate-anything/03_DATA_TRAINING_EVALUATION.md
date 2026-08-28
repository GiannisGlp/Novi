# LocateAnything — Data, Training and Evaluation Reference

## 1. Upstream data scale

NVIDIA reports LocateAnything-Data at:

- 12M unique images;
- 138M language queries;
- 785M boxes.

The data covers six major task families: general detection, GUI grounding, referring comprehension, OCR/text localization, layout grounding and pointing.

## 2. Training data representation

The official training pipeline uses ShareGPT-style JSONL records.

Minimal shape:

```json
{
  "conversations": [
    {"from": "human", "value": "..."},
    {"from": "gpt", "value": "..."}
  ],
  "image": "relative/path.jpg"
}
```

It also supports `image_list`, `video`, and `video_list`.

Image placeholders are `<image-1>`, `<image-2>`, etc. If an image is supplied without a placeholder, the upstream preparation code can prepend `<image-1>` to the first user message.

## 3. Coordinate convention

Training labels use integer-normalized coordinates in `[0,1000]`.

Bounding box:

`<ref>label</ref><box><x1><y1><x2><y2></box>`

Point:

`<box><x><y></box>`

No object:

`<box>none</box>`

Special tokens include `<ref>`, `</ref>`, `<box>`, `</box>`, `</c>`, and coordinate tokens `<0>` through `<1000>`.

Novi must preserve this distinction between model-native representation and Novi's canonical pixel-space representation.

## 4. Upstream task formats

### General detection

Multiple categories can be supplied using `</c>` separators in the prompt.

### Single phrase grounding

A single natural-language description identifies one target instance.

### Multi-instance phrase grounding

A description can identify all matching instances.

### OCR

The model can localize scene text and return text references with boxes.

### GUI grounding

A UI element can be returned as a box.

### Pointing

A target can be represented by a point.

### Layout

Document/scene layout elements can be grounded by category.

### Multi-image

The training format can associate multiple images with one conversation.

### Text-only

The training format also allows pure text samples, although Novi's integration is concerned primarily with image-grounding tasks.

## 5. Media support

Upstream data preparation documents:

Images: JPEG, PNG, WebP, BMP, TIFF.  
Video: MP4, AVI, MKV, WebM through `decord`.

There is no fixed image resolution requirement; images are dynamically resized. Higher resolution produces more visual tokens.

Video training arguments include:

- `max_frames`: default 64;
- `target_fps`: default 2;
- `video_total_pixels`: approximately 10M.

## 6. Training architecture

NVIDIA provides continual SFT from the pretrained checkpoint.

Documented reference configuration:

- 8 GPUs on one node;
- H100 80 GB tested;
- 2×8 H100 multi-node tested;
- BF16;
- DeepSpeed ZeRO Stage 2 recommended;
- learning rate 2e-5 in the example;
- 25,000 steps in the example;
- block size 6 in the example;
- 16,384 max sequence length in the long-context Magi configuration.

These settings are **not** a recommended Novi training configuration. They are upstream reproduction settings and require substantially different infrastructure from the current Mac-first development environment.

## 7. Attention implementations

### Magi Attention

NVIDIA documents Magi Attention for Hopper and Blackwell and long sequences (16K–32K+). It is recommended for PBD training.

### SDPA

PyTorch native SDPA works on general GPU hardware but is documented for short-context fine-tuning, around 4K tokens in the upstream guide.

### LA Flash

The newer inference runtime uses FlashAttention variable-length sparse range plans for batched inference and is separate from the standard training path.

## 8. Streaming packing

The training pipeline contains a stateful online packing system:

- lazy JSONL loading with offset indexing;
- deterministic iteration;
- best-fit packing;
- big-rocks-first start of a new batch;
- worker-local state;
- saved RNG state;
- saved iterator positions;
- saved current batch locations;
- saved buffer locations;
- checkpoint restoration designed for bit-wise identical data-order resumption.

This is valuable engineering reference if Novi ever fine-tunes its own grounding model, but it should not be imported into the runtime perception path.

## 9. Upstream evaluation suite

The official evaluation guide uses a combination of datasets and the Rex-Omni `fastevaluate` framework.

Evaluated families include:

- COCO;
- LVIS;
- Dense200;
- VisDrone;
- DocLayNet;
- HierText;
- HumanRef;
- IC15;
- M6Doc;
- RefCOCOg validation/test;
- SROIE;
- TotalText;
- ScreenSpot-Pro.

Point evaluation includes COCO, Dense200, HumanRef, LVIS, RefCOCOg and VisDrone.

## 10. Reported results

| Benchmark | LocateAnything-3B reported result |
|---|---:|
| LVIS F1 mean | 50.7 |
| COCO F1 mean | 54.7 |
| Dense200 F1 mean | 58.7 |
| VisDrone F1 mean | 39.9 |
| DocLayNet F1 mean | 76.8 |
| M6Doc F1 mean | 70.1 |
| TotalText F1 mean | 43.3 |
| ScreenSpot-Pro average | 60.3 |
| HumanRef F1 mean | 78.7 |
| RefCOCOg validation F1 mean | 76.7 |
| RefCOCOg test F1 mean | 77.6 |

Pointing is reported as best on all seven listed benchmark datasets.

## 11. What Novi should benchmark instead of copying the upstream suite

Novi's benchmark must measure robot-relevant behavior:

1. category detection;
2. open-vocabulary grounding;
3. referring expressions;
4. multiple-instance grounding;
5. point localization;
6. small-object localization;
7. clutter/occlusion;
8. lighting changes;
9. motion blur;
10. camera compression;
11. repeated observations;
12. temporal consistency;
13. false-positive rate;
14. latency;
15. memory consumption;
16. thermal behavior on target hardware;
17. fallback behavior;
18. effect on planner decisions.

## 12. Required Novi benchmark split

Create a fixed local corpus containing:

- canonical Novi test image;
- robot-like room scenes;
- household objects;
- multiple visually similar objects;
- people and hands;
- cluttered tables;
- objects partially occluded;
- text/signage;
- known objects and novel descriptions;
- intentionally ambiguous queries.

Each sample should store expected geometric ground truth and the exact query.

## 13. Quality metrics Novi should record

### Localization

- IoU at 0.5;
- IoU at 0.75;
- IoU at 0.90/0.95 for high precision;
- mean IoU;
- center-point error;
- missed-target rate;
- false-positive rate.

### System

- cold-start latency;
- warm inference latency;
- p50/p95/p99 latency;
- images/queries per second;
- peak memory;
- model load time;
- fallback frequency;
- Fast→Slow fallback rate;
- invalid-output rate;
- query success rate.

### Cognitive usefulness

- whether the result changes the correct world state;
- whether identity/tracking remains consistent;
- whether the planner receives enough information;
- whether incorrect localization causes unsafe downstream behavior.

## 14. Sources

- NVIDIA research: https://research.nvidia.com/labs/lpr/locate-anything/
- Training: https://github.com/NVlabs/Eagle/blob/main/Embodied/document/TRAINING.md
- Data preparation: https://github.com/NVlabs/Eagle/blob/main/Embodied/document/DATA_PREPARATION.md
- Evaluation: https://github.com/NVlabs/Eagle/blob/main/Embodied/evaluation/README.md
- Results: https://github.com/NVlabs/Eagle/blob/main/Embodied/document/RESULTS.md
- Streaming packing: https://github.com/NVlabs/Eagle/blob/main/Embodied/document/STREAMING_PACKING.md
