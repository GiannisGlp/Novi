# Mac Neural Model Dependencies

The first real neural provider is `TorchvisionSSDLiteDetector`.

From the Novi root on Apple Silicon:

```bash
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install torch torchvision pillow
```

Verify:

```bash
./.venv/bin/python -c "import torch; print('PyTorch:', torch.__version__); print('MPS:', torch.backends.mps.is_available())"
```

The first model load downloads the pretrained SSDLite320 MobileNetV3 weights from the torchvision model source. Keep the resulting model cache local; do not commit model weights to Git.

## Providers

- **Perception** — `NeuralPerceptionBackend` wraps `TorchvisionSSDLiteDetector` (`torchvision:ssdlite320_mobilenet_v3_large`), run on MPS when available.
- **Speech-to-text** — `WhisperSTTProvider` (faster-whisper, offline). One-time model download into the git-ignored `mac_test_results/STT/models` cache. `DeterministicSTTProvider` is the CI/test fallback.
- **Reasoning** — `DeterministicReasoningProvider` (bounded symbolic, default) and `LLMReasoningProvider`/`OllamaReasoningProvider` (real local LLM via Ollama, action-allowlist-constrained).

## Local / offline requirement (robot deployment)

These models will eventually run **on the robot**, so every model must be **locally hosted and run fully offline**. No cloud/API inference is allowed for core cognition, memory, safety, or action.

- The current implementation already satisfies this: the only network reference in the model layer is the **local** Ollama server (`http://localhost:11434`); model weights are downloaded once to a local, git-ignored cache at install time and then run offline.
- Do not add any provider that calls a remote API (OpenAI, Bedrock, Vertex, etc.) for core capabilities. If a hosted API is ever used, it must be non-core and optional.

### Robot-hardware implication for model selection
- The Mac prototype runs whatever fits a 36 GB Apple Silicon laptop (via Ollama/Metal). The robot's compute is a different target (reference: NVIDIA Jetson AGX Orin/Thor — ARM `aarch64`, CUDA), so a model that is convenient on the Mac is not automatically right for the robot.
- Prefer models that run on `aarch64`/Jetson and quantized for embedded memory:
  - NVIDIA-native weights (e.g. Nemotron NVFP4 / NIM) are well-suited to Jetson and are strong robot candidates.
  - Qwen/llama GGUFs run on Jetson via Ollama as a hardware-neutral fallback.
- Final model selection is deferred until the robot compute, memory budget, and workload are measured (per the hardware-selection policy). The `ReasoningProvider`/`MacModelProvider`/`ObjectDetector` boundaries exist so the same Brain semantics keep working when the model is swapped for the robot.

## Dependencies

Install with `bash scripts/mac/neural-setup.sh` (adds `sounddevice`, `faster-whisper` for STT). Local-LLM reasoning is optional and requires Ollama (`brew install ollama`, `ollama serve`).
