# LocateAnything — Novi Integration Analysis

## 1. Current Novi perception baseline

Novi already has a perception abstraction:

- `novi/perception/detection.py` defines `Detection` and `ObjectDetector`.
- `novi/perception/pipeline.py` runs detector -> tracker -> optional face identity and returns `WorldObservation`.
- `novi/perception/real_backends.py` adapts the real Torchvision SSDLite320-MobileNetV3 detector to that contract.
- `novi/integration/real_io.py` adapts the Mac camera into the perception pipeline and converts frames to portable JPEG bytes for preview/integration.

The current `Detection` contract is pixel-space `(x, y, w, h)` plus confidence and frame provenance.

This is an excellent insertion point: LocateAnything should implement a second `ObjectDetector`-compatible backend for ordinary category detection, but its richer language-grounding capabilities require an additional explicit spatial-query interface.

## 2. Do not replace SSDLite

The recommended Novi architecture is a two-speed perception system.

### Fast baseline

`TorchvisionSSDLiteDetector`

Use for:

- continuous camera perception;
- common object categories;
- low-cost tracking updates;
- cheap candidate generation.

### Language-conditioned grounding

`LocateAnythingBackend`

Use for:

- open-vocabulary queries;
- natural-language descriptions;
- referring expressions;
- multi-instance grounding;
- fine localization;
- point localization;
- ambiguous or novel objects;
- cognition-driven active perception.

This preserves the current deterministic/performance baseline while adding a much more expressive perception mode.

## 3. Proposed Novi abstraction

Do not expose raw NVIDIA APIs to the rest of Novi.

Define a narrow internal contract:

```text
SpatialPerceptionBackend
    ground(image, query, policy) -> GroundingResult
    point(image, query, policy) -> PointingResult
    detect(image, labels, policy) -> GroundingResult
    capabilities() -> CapabilityReport
```

`GroundingResult` should contain:

- query;
- observations;
- normalized coordinates;
- pixel coordinates;
- image dimensions;
- mode used (`fast`, `slow`, `hybrid`);
- model ID and revision;
- backend version;
- confidence/quality metadata if available;
- raw output hash, not necessarily raw output;
- frame ID;
- timestamp;
- provenance;
- fallback/repair information;
- latency;
- error state.

## 4. Do not misuse Detection for everything

A standard `Detection` means:

> an object category was detected in this frame.

A grounding result means:

> this natural-language description was mapped to one or more spatial regions.

These are different semantics.

Recommended hierarchy:

```text
PerceptionObservation
├── DetectionObservation
├── GroundingObservation
├── PointObservation
├── TextObservation
└── IdentityObservation
```

The existing `Detection` class can remain stable while a new typed grounding model is added.

## 5. Canonical coordinate policy

LocateAnything uses normalized `[0,1000]` corner coordinates.

Novi continues to use pixel-space boxes internally for the current perception contract.

The adapter must retain both representations:

```text
source_box_normalized_1000
        ↓
canonical_pixel_box
        ↓
WorldObservation / spatial memory
```

This prevents irreversible loss of source precision and makes later debugging possible.

## 6. Query ownership

The cognitive system should own the semantic query.

Example:

```text
Goal: find my keys
        ↓
Memory: last seen near desk
        ↓
Cognition creates query:
"small keyring on or near the desk"
        ↓
LocateAnything
```

LocateAnything should not decide the robot's goal. It should answer the visual localization request.

## 7. Active perception

This is the most important integration opportunity.

Novi should be able to decide when to spend more compute on perception.

Example:

```text
SSDLite sees "cup"
       ↓
confidence 0.62
       ↓
planner needs exact target
       ↓
Novi issues grounding query
       ↓
LocateAnything("the blue cup beside the laptop")
       ↓
precise region
       ↓
world model update
```

This creates a perception loop rather than a passive detector.

## 8. Fast / Slow / Hybrid policy in Novi

Recommended default:

`hybrid`.

Policy factors:

- task urgency;
- downstream action risk;
- query ambiguity;
- prior prediction error;
- detector disagreement;
- object density;
- latency budget;
- available compute;
- privacy policy;
- hardware capability.

Example:

```text
low risk + routine + low ambiguity -> fast/hybrid
high precision + ambiguous -> hybrid/slow
offline annotation -> slow
irreversible action -> slow + independent verification
```

The model output never bypasses Novi governance.

## 9. Fusion with existing tracking

LocateAnything returns per-frame geometry. Novi's `ObjectTracker` remains responsible for temporal continuity.

Do not use model-generated labels as persistent identity IDs.

Pipeline:

```text
frame
  ↓
LocateAnything
  ↓
GroundingObservation
  ↓
association/tracking
  ↓
track ID
  ↓
world state
```

A future identity layer may combine:

- category;
- visual embedding;
- face identity where permitted;
- spatial continuity;
- temporal evidence;
- semantic description.

## 10. 3D warning

LocateAnything is a 2D grounding model. A bounding box is not a metric 3D position.

Do not convert a 2D box directly into `(x,y,z)` without depth and camera geometry.

Future spatial fusion should be:

```text
LocateAnything 2D box
        +
depth measurement
        +
camera intrinsics
        +
extrinsics / robot pose
        ↓
3D spatial observation
```

This is where the future localization/mapping workstreams connect.

## 11. World-model integration

The output should be admitted as an observation with provenance, not as a fact.

Example conceptual record:

```text
Observation:
  entity_candidate = "blue cup"
  source = locate_anything
  frame_id = cam_000123
  bbox_px = (...)
  bbox_norm = (...)
  confidence = backend-specific
  timestamp = ...
  modality = vision
  status = observed
```

The world model can then fuse this with other observations.

## 12. Memory integration

Do not persist every raw grounding result indefinitely.

Persist selectively:

- salient objects;
- stable locations;
- object identity candidates;
- search results;
- important corrections;
- recurring spatial relationships;
- successful/failed queries;
- prediction confirmations/violations.

This aligns with Novi's existing memory importance and consolidation design.

## 13. Prediction integration

LocateAnything becomes especially valuable when combined with Novi's new sequence prediction.

Example:

```text
A: person enters kitchen
B: person approaches counter
C: person picks up cup
```

Novi can predict B/C and use LocateAnything to verify expected spatial targets.

Prediction error can trigger a new grounding query.

## 14. Deliberation integration

If a grounding query is ambiguous, Novi should record the decision:

```text
query:
  "find the cup"

candidate observations:
  cup_1
  cup_2

chosen target:
  cup_1

reason:
  closer to requested person / prior memory / visual descriptor

rejected:
  cup_2
```

This can feed the existing deliberation memory.

## 15. Safety integration

LocateAnything must never directly actuate the robot.

Required chain:

```text
LocateAnything
   ↓
validated observation
   ↓
world model
   ↓
reasoning
   ↓
planner
   ↓
governance
   ↓
action proposal
   ↓
independent verification
   ↓
actuation
```

For safety-sensitive actions, require a second observation or independent sensor confirmation.

## 16. Privacy

Novi already has explicit privacy behavior around face identity. LocateAnything can localize people or body parts, so the same governance principle applies.

Default policy:

- localization is not identity;
- do not infer a person's identity from a box alone;
- face/biometric processing remains separately governed;
- sensitive observations receive appropriate privacy classes;
- raw frames are not retained merely because grounding was invoked.

## 17. Mac-first strategy

Apple MPS is Novi's current development target.

NVIDIA's LocateAnything release is documented and benchmarked on NVIDIA GPU hardware, not Apple MPS.

Therefore the first phase must be a compatibility experiment:

1. attempt isolated model loading;
2. measure memory;
3. run one image;
4. run one grounding query;
5. measure latency;
6. run repeated queries;
7. test failure/degradation behavior.

If MPS is impractical, keep the adapter and move the backend to a local NVIDIA machine/Jetson later.

## 18. Future NVIDIA path

The same interface should support:

```text
Mac backend
  -> experimental MPS/CPU implementation

NVIDIA backend
  -> CUDA / TensorRT or NVIDIA-supported runtime where applicable
```

Do not bake CUDA assumptions into `novi/perception`.

## 19. Licensing decision

The current model license permits research/evaluation use only and explicitly restricts commercial use of the Work and derivative works.

Therefore:

- research branch/prototype: permitted subject to license compliance;
- commercial Novi product: **not cleared** using the released weights;
- future commercial use requires a suitable NVIDIA agreement/license or a replacement model with compatible rights.

The adapter architecture is therefore mandatory, not optional.

## 20. Integration conclusion

LocateAnything belongs at the **spatial-perception boundary** of Novi.

It should enhance perception without becoming the world model, identity system, planner, safety system or robot controller.

The highest-value first capability is:

**cognition-driven natural-language grounding over real camera frames, followed by typed world-state observations and temporal tracking.**

Sources:

- NVIDIA research: https://research.nvidia.com/labs/lpr/locate-anything/
- NVIDIA code: https://github.com/NVlabs/Eagle/tree/main/Embodied
- NVIDIA model: https://huggingface.co/nvidia/LocateAnything-3B
- Novi perception: `novi/perception/`
- Novi real I/O: `novi/integration/real_io.py`
