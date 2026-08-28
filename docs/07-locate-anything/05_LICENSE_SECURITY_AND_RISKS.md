# LocateAnything — License, Security, Privacy and Operational Risks

## 1. Code versus model license

NVIDIA's upstream repository separates code licensing from model licensing.

### Code

The Eagle repository code is released under Apache 2.0 according to the repository's code-license badge and repository license.

### LocateAnything model weights

`Embodied/LICENSE_MODEL` applies to the model Work. It grants broad copyright rights subject to restrictions, but Section 3.3 states that the Work and derivative works may only be used or intended for use non-commercially; NVIDIA and its affiliates are excepted.

NVIDIA defines non-commercially as research or evaluation purposes only.

Therefore the released LocateAnything-3B weights are **not cleared for commercial Novi use** under the published license.

Source: https://github.com/NVlabs/Eagle/blob/main/Embodied/LICENSE_MODEL

## 2. What this means for Novi

### Current research prototype

Use may be considered for research/evaluation only, with the NVIDIA license retained and all applicable attribution/copyright notices preserved.

### Future commercial robot

Do not ship the released weights in a commercial Novi product unless an appropriate NVIDIA commercial agreement/license explicitly permits it.

Potential long-term options:

1. obtain a commercial license from NVIDIA;
2. replace the model with a commercially compatible grounding model;
3. train/finetune a model whose complete data/model/code provenance permits commercial deployment.

The adapter architecture must keep these options open.

## 3. Supply-chain risk

The upstream standard loader uses `trust_remote_code=True`.

This means model loading can execute repository-provided Python code and should be treated as a software supply-chain boundary.

Novi requirements:

- pin exact upstream model revision;
- record revision in evidence/provenance;
- review custom code before enabling production use;
- use a locked dependency environment;
- avoid implicit model upgrades;
- verify downloaded artifacts by expected revision/hash where feasible;
- isolate the runtime process if practical;
- expose explicit startup health rather than silently accepting a partially loaded model.

## 4. Optional dependency isolation

The upstream package has a large dependency footprint including Transformers, DeepSpeed, bitsandbytes, Triton, Liger Kernel, PEFT, timm, datasets, decord, OpenCV and web/server packages.

Novi must not make these mandatory for its deterministic core.

Preferred isolation:

```text
Novi core
  |
  +-- optional LocateAnything runtime
         |
         +-- pinned virtual environment / extra
         +-- model cache
         +-- process boundary if needed
```

## 5. Model failure is not a safety failure

If LocateAnything fails, Novi must continue safely without it.

Valid states:

- available;
- loading;
- unavailable;
- unsupported hardware;
- dependency missing;
- model missing;
- inference timeout;
- malformed output;
- confidence/quality insufficient.

None should cause the brain to assume that the queried object is absent or present.

## 6. False positive / false negative risks

Visual grounding is probabilistic.

A missed object can cause:

- incorrect world state;
- failed search;
- wrong planning;
- unsafe navigation or manipulation.

A false localization can be worse when it causes an action toward the wrong target.

Therefore high-risk actions require independent verification.

## 7. Spatial ambiguity

NVIDIA explicitly identifies spatial ambiguity as a failure mode for parallel decoding in dense scenes. Novi should surface the backend's fallback/repair status and, when necessary, issue a second query or use a second sensor.

## 8. Format irregularity

NVIDIA also identifies malformed output structure around category boundaries.

Novi's parser must be strict:

- reject malformed coordinate tokens;
- reject missing closing markers;
- reject out-of-range coordinates;
- reject inverted boxes;
- reject impossible geometry;
- preserve raw response hash for debugging;
- never admit malformed output to world state.

## 9. 2D/3D semantic risk

A 2D box is not a depth measurement.

Do not derive 3D distance from a bounding-box size without an explicit calibrated model and assumptions.

Future 3D fusion must use camera calibration + depth/geometry + robot pose.

## 10. Identity/privacy risk

LocateAnything can localize people, body parts and textual information. Localization should not automatically become identity inference.

Novi must keep:

`localization != identity`

Face identity remains separately governed.

## 11. Data rights

The NVIDIA model card notes that training data is a mixture of human/open-source and automated/model-assisted sources and may contain publicly available or potentially copyrighted content. Users are responsible for applicable rights when using input/media/data.

For Novi's own training/evaluation corpus, every image must have documented provenance and usage rights.

## 12. Security boundary for robot use

Never allow:

`LocateAnything -> actuator`

Required:

`LocateAnything -> typed observation -> world model -> reasoning -> planner -> governance -> action -> verification`.

This is a core Novi safety invariant.

## 13. Commercial readiness gate

LocateAnything cannot be marked production-ready for a commercial Novi product while the current NVIDIA model license remains non-commercial.

The implementation plan therefore has two separate gates:

- **Research Integration Gate:** technically validated and license-compliant for research/evaluation.
- **Commercial Release Gate:** explicit legal/model-license clearance.

## 14. Sources

- Model license: https://github.com/NVlabs/Eagle/blob/main/Embodied/LICENSE_MODEL
- Model card: https://huggingface.co/nvidia/LocateAnything-3B
- NVIDIA research: https://research.nvidia.com/labs/lpr/locate-anything/
- NVIDIA code: https://github.com/NVlabs/Eagle/tree/main/Embodied
