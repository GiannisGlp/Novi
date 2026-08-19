# Mac Brain M1 — First Real Neural Inference

## Goal

Move the Mac prototype from deterministic perception to a real local neural vision model while preserving the canonical Novi perception contract.

## First provider

`TorchvisionSSDLiteDetector` using `ssdlite320_mobilenet_v3_large` and its default pretrained weights.

The provider is deliberately isolated behind `ObjectDetector` and `LocalNeuralObjectDetector`. The rest of Novi does not depend on torchvision APIs.

## Runtime policy

- PyTorch is the tensor/inference runtime.
- Apple Silicon MPS is selected automatically when available.
- CPU is the fallback.
- The concrete model is provisional until Mac measurements prove it suitable.

## Acceptance evidence

The first real neural milestone is accepted only when the Mac demonstrates:

1. PyTorch imports in the Novi virtual environment.
2. MPS availability is recorded when available.
3. Pretrained weights load successfully.
4. A real representative image reaches the model.
5. At least one valid inference completes.
6. Outputs normalize into Novi `Detection` objects.
7. Model ID, runtime and device are recorded.
8. Latency and memory are captured.
9. Deterministic tests remain independent of downloaded model weights.

## Not yet claimed

This milestone does not yet claim camera integration, autonomous behavior, multimodal reasoning, or robot hardware execution. Those are subsequent stages.

## Next step

Install and verify the Mac neural dependencies, run the provider smoke test against a representative image, collect evidence, then wire the real detector into the Mac Brain perception loop.
