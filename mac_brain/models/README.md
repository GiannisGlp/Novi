# Mac Neural Model Layer

The first real neural capability is object detection.

## Boundary

`ObjectDetector` is the canonical capability interface. The Brain does not depend on a specific model or inference runtime.

## Providers

- `DeterministicObjectDetector`: CI/test provider.
- `LocalNeuralObjectDetector`: adapter for a verified Mac-runnable neural detector.

## Selection policy

The concrete first model is deliberately not hard-coded until it is verified on the actual Mac. Candidate runtimes include PyTorch/MPS, Core ML and ONNX Runtime where compatible.

A candidate is considered usable only after a real Mac run demonstrates model loading, inference, valid normalized detections and representative workload execution.

## Next implementation

Wire the selected concrete detector into `MacBrain` and add the first real-camera inference command after the user's Mac environment is available.
