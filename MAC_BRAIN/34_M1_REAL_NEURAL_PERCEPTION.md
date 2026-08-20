# M1 — Real Neural Perception

## Objective

Move Novi's Mac Brain from deterministic perception fixtures to real neural inference while preserving the existing Brain contracts.

## Execution order

1. Verify Python, PyTorch and torchvision in the Mac project environment.
2. Verify Apple MPS availability; CPU remains an allowed fallback.
3. Load the existing Torchvision SSDLite320 MobileNetV3 provider.
4. Run inference against the committed `test-image.png` fixture.
5. Validate normalized detections and provenance.
6. Record model identity, runtime/device, latency, confidence and memory where available.
7. Run the detector against a real Mac camera frame.
8. Feed detections into Novi perception and world-state interfaces.
9. Run repeated perception cycles through the Mac Brain runtime.
10. Preserve machine-readable evidence for the run.

## Acceptance criteria

M1 is PASS only when:

- the real model loads on the Mac;
- inference succeeds on the test image;
- outputs contain valid labels, confidence values and bounding boxes;
- model/runtime/device provenance is recorded;
- representative detections are sensible;
- real camera input can be processed;
- detections reach the canonical Novi perception/world-state path;
- deterministic CI tests remain green;
- a reproducible evidence package is produced.

## Model policy

The current first candidate is `torchvision:ssdlite320_mobilenet_v3_large`. This is a Mac implementation candidate, not a permanent model selection. The implementation must remain behind the `ObjectDetector` capability boundary so another detector can replace it without changing Brain semantics.

## Safety boundary

M1 is perception-only. No physical motor control is introduced. The existing bounded virtual-action and safety policies remain in force.

## Runtime integration (status: IMPLEMENTED)

M1 now runs real neural perception **through the live `MacBrain` runtime**, not only as a standalone detector.

- `MAC_BRAIN/models/neural_backend.py` — `NeuralPerceptionBackend` bridges the torchvision detector output (`MAC_BRAIN.models.Detection`, `bbox`) into the canonical `brain.b2_perception.PerceptionBackend` contract (`Detection`, `bbox_xyxy`).
- `MAC_BRAIN/cli.py` — `--neural` selects the real backend; `--neural-image PATH` serves a static image (no camera required) for reproducible headless runs; `--neural --live-camera` runs real Mac camera + real detection.
- Verified on-device (MPS): `python -m MAC_BRAIN.cli --neural --neural-image test-image.png --cycles 2` produced detections `["tv", "laptop"]` through perception → world state → cognition → authorized `inspect` action.

```text
Mac camera / static image
   ↓
NeuralPerceptionBackend (SSDLite320 MobileNetV3 on MPS)
   ↓
SpecialistPerception
   ↓
TemporalWorldModel
   ↓
DeterministicCognition
   ↓
BrainSupervisor / safety
   ↓
VirtualBody
```

## Live camera validation (status: PASS)

Real Mac camera + real neural perception validated on-device through the runtime:

```text
python -m MAC_BRAIN.cli --neural --live-camera --cycles 3
```

- Camera device 0 opened via OpenCV (640×480).
- Real SSDLite320-MobileNetV3 inference on MPS per frame.
- 3-cycle detections: `[], ["person"], ["person"]` — the model detected a person in frames 2–3 (frame 1 had nothing above the confidence threshold).
- Detections flowed perception → world state → cognition → authorized `inspect` action each cycle.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/M1-camera-runtime-latest.json`.

Camera validation evidence is collected; review the raw detections/bboxes before declaring M1 fully accepted.

## Evidence

The evidence should include:

- Mac/OS and Python environment;
- PyTorch/torchvision versions;
- MPS availability and selected device;
- model identifier and weights provenance;
- input fixture identity;
- detection output;
- latency measurements;
- errors/failures;
- camera inference result;
- Git commit SHA.
