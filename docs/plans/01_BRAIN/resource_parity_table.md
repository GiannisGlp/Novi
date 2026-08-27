# Brain — Resource Parity Table

**Purpose:** map each capability Novi uses on the Mac to its local provider and a
board-plausible Jetson (Orin/Thor) deployment-class equivalent, per the resource-parity
rule in `14_BRAIN_EXIT_CONTRACT.md` §Resource-parity rules.

**Status:** living maintenance artifact — the Mac column is implemented; the Jetson column
is a *plausibility* mapping (not yet hardware-validated) and re-opens when edge hardware
arrives.

| Capability | Mac provider | Jetson deployment-class equivalent | Status |
|---|---|---|---|
| Perception (deterministic) | `SpecialistPerception` (fixture backend) | same deterministic backend | implemented |
| Perception (neural) | torchvision SSDLite320-MobileNetV3 (MPS) | TensorRT-optimized detector | Mac implemented; Jetson to validate |
| Perception cadence (plan 19 P5) | `perception_every_n_cycles` throttles neural backend | same cadence knob on Jetson (power-aware) | implemented |
| STT | local Whisper (`base`) | Whisper/ONNX on Jetson | Mac implemented; Jetson to validate |
| TTS | macOS `say` | Piper/edge TTS | Mac implemented; Jetson to validate |
| Reasoning (fast path) | `DeliberativeReasoningProvider` (deterministic) | same deterministic path | implemented |
| Reasoning (deliberative) | local Ollama (llama-server) | Ollama/llama.cpp on Jetson | Mac implemented; Jetson to validate |
| Embedding | MiniLM (sentence-transformers) + hash fallback | ONNX MiniLM | Mac implemented; Jetson to validate |
| Memory | `DurableMemoryStore` (SQLite + FTS5) | same SQLite/FTS5 | implemented |
| Camera | `MacCamera` (OpenCV optional) | V4L2/GStreamer | Mac implemented; Jetson to validate |
| Microphone | `MacMicrophone` (sounddevice optional) | ALSA/PulseAudio | Mac implemented; Jetson to validate |
| Speaker | `MacSpeaker` (native `say`) | ALSA/PulseAudio | Mac implemented; Jetson to validate |

**Rule (unchanged):** no cloud API calls in the cognitive path; no model whose
memory/bandwidth profile has no Orin/Thor-plausible mapping; no power-blind autonomy logic.
