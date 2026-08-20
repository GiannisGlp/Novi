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
