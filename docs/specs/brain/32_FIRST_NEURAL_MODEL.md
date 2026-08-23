# Mac Brain — First Neural Model

## Objective

Introduce the first real neural capability into the Mac Brain without coupling the Brain architecture to a specific model family or runtime.

## Capability

**Object detection.**

The flow is:

```text
Mac camera frame
      ↓
ObjectDetector
      ↓
normalized Detection evidence
      ↓
Novi perception/world state
      ↓
Cognition
```

## Implementation

The repository now contains:

- `MAC_BRAIN/models/object_detection.py` — canonical capability contract;
- `MAC_BRAIN/models/local_detector.py` — real local-neural adapter;
- `MAC_BRAIN/models/__init__.py` — public model exports.

## Why the exact model is not hard-coded

The Mac must prove which candidate is actually viable. A model is selected only after successful execution on the user's real Mac, with representative inputs and valid outputs.

Candidates may include RT-DETR variants or other Mac-compatible detectors. Runtime options may include PyTorch/MPS, Core ML or ONNX Runtime where compatibility is demonstrated.

## Acceptance

A concrete model becomes the Mac Brain's first neural provider only after:

1. installation succeeds in the project environment;
2. weights/checkpoint load successfully;
3. inference executes on the Mac;
4. output normalization succeeds;
5. representative images produce sensible detections;
6. latency and memory are recorded;
7. the provider can run through the canonical `ObjectDetector` interface;
8. CI remains deterministic through the separate test provider.

## Next step

On the Mac, evaluate candidate detector runtimes and select the first concrete provider. Then wire it into `MacBrain` and run the camera → neural detector → perception → world-state path.
