# Novi Mac Brain — First Run & M1 Execution Guide

## Purpose

This is the operational guide for running the Mac Brain from a clean Mac checkout through the first real neural-perception experiment.

The Mac is the first development body for Novi. The goal is to exercise real local AI where practical while keeping the Brain architecture, safety boundaries and model interfaces vendor-neutral.

## Important working rule

Run these commands **from the repository root**, the directory containing `README.md` and `MAC_BRAIN/`.

```text
Novi/
├── README.md
├── MAC_BRAIN/
├── scripts/
└── test-image.png
```

Do not run the scripts from inside `MAC_BRAIN/`.

## Script map

| Script | Purpose | Hardware required |
|---|---|---|
| `bash scripts/mac/setup.sh` | Create/update the base Python environment | Mac only |
| `bash scripts/mac/doctor.sh` | Inspect the Mac and collect environment evidence | Mac only |
| `bash scripts/mac/neural-setup.sh` | Install the first local neural dependencies | Mac only |
| `bash scripts/mac/neural-doctor.sh` | Verify PyTorch/torchvision/MPS/OpenCV/Pillow | Mac only |
| `bash scripts/mac-brain-test.sh` | Run deterministic Mac Brain integration tests | No camera/model required |
| `bash scripts/mac-brain.sh` | Start the Mac Brain runtime | No camera/model required |
| `bash scripts/mac/m1-image-test.sh` | Run real SSDLite inference on `test-image.png` | No camera required |
| `bash scripts/mac/m1-camera-test.sh` | Run real SSDLite inference on live camera frames | Camera required |
| `bash scripts/mac/m1-run.sh` | Run the M1 environment + image stage + deterministic Brain tests | Camera not required |
| `bash scripts/mac/collect-evidence.sh` | Snapshot collected Mac evidence into the implementation evidence area | No additional hardware |

All scripts save or reference evidence under `mac_test_results/` and, when formally collected, `IMPLEMENTATION_PLAN/EVIDENCE/mac/`.

## 0. Requirements

- macOS
- Apple Silicon preferred
- Git
- repository-supported Python
- Terminal
- working camera for the camera stage
- internet access for dependency/model downloads

Do **not** install Jetson/NVIDIA dependencies for this stage.

## 1. Clone or update Novi

```bash
cd ~/Projects
git clone https://github.com/GiannisGlp/Novi.git
cd Novi
```

If already cloned:

```bash
cd ~/Projects/Novi
git pull
```

Verify:

```bash
git status
```

## 2. Inspect the Mac

```bash
uname -m
sw_vers
python3 --version
git --version
system_profiler SPHardwareDataType
```

Keep this information as part of the evidence trail.

## 3. Set up the base environment

From the **Novi root**:

```bash
bash scripts/mac/setup.sh
source .venv/bin/activate
```

Verify:

```bash
which python
python --version
```

The executable should be inside `.venv`.

Do not install project packages globally.

## 4. Run the base Mac doctor

```bash
bash scripts/mac/doctor.sh
```

**Checkpoint:** if this fails, stop. Capture the complete output before making changes.

## 5. Run deterministic Mac Brain validation

```bash
bash scripts/mac-brain-test.sh
```

This validates the Mac Brain plumbing without requiring a neural model.

## 6. Start the deterministic Mac Brain runtime

```bash
bash scripts/mac-brain.sh
```

This is a runtime smoke test, not the neural-perception acceptance gate.

## 7. Install the local neural runtime

Only after the base environment is healthy:

```bash
bash scripts/mac/neural-setup.sh
```

This installs the current first neural experiment dependencies:

- PyTorch
- torchvision
- Pillow
- NumPy
- OpenCV

The exact model remains behind the `ObjectDetector` capability boundary.

## 8. Run the neural doctor

```bash
bash scripts/mac/neural-doctor.sh
```

This records:

- Python
- PyTorch
- torchvision
- Pillow
- OpenCV
- machine architecture
- MPS built/available state

Evidence is written to:

```text
mac_test_results/neural_environment.json
```

If this fails, stop and resolve the environment before running M1 inference.

## 9. Verify MPS manually if desired

```bash
python - <<'PY'
import torch

print("PyTorch:", torch.__version__)
print("MPS built:", torch.backends.mps.is_built())
print("MPS available:", torch.backends.mps.is_available())

if torch.backends.mps.is_available():
    device = torch.device("mps")
    x = torch.ones((1000, 1000), device=device)
    y = x @ x
    print("MPS test: PASS")
    print("Device:", y.device)
else:
    print("MPS test: NOT AVAILABLE")
PY
```

MPS unavailable does not automatically block the prototype; the detector can fall back to CPU.

## 10. M1 — real neural inference on the known image

The first concrete neural candidate is:

```text
torchvision:ssdlite320_mobilenet_v3_large
```

Run:

```bash
bash scripts/mac/m1-image-test.sh
```

Or specify another image:

```bash
bash scripts/mac/m1-image-test.sh path/to/image.png
```

The command performs:

```text
 test-image.png
      ↓
SSDLite MobileNetV3
      ↓
real inference
      ↓
normalized Detection[]
      ↓
provenance-rich evidence
```

Evidence is written to:

```text
mac_test_results/M1/latest.json
mac_test_results/M1/image-<timestamp>.json
```

The evidence records model ID, runtime/device, model-load time, inference time, detections, confidence, bounding boxes and provenance.

### M1 image checkpoint

Do not proceed to the camera stage until the image test produces a successful real inference result.

A package importing successfully is **not** enough. The checkpoint requires:

- model weights load;
- inference completes;
- valid detections are produced or a documented no-detection result is produced;
- provenance is present;
- runtime/device is recorded;
- inference latency is recorded.

## 11. M1 — real Mac camera inference

First grant camera access:

**System Settings → Privacy & Security → Camera**

Allow the Terminal/application being used to access the camera.

Then run:

```bash
bash scripts/mac/m1-camera-test.sh
```

Defaults:

```text
camera device: 0
frames:         5
```

You can select another device and frame count:

```bash
bash scripts/mac/m1-camera-test.sh 0 10
```

The path is:

```text
Mac camera
    ↓
CameraFrame
    ↓
SSDLite neural inference
    ↓
Detection[]
    ↓
M1 evidence
```

Camera evidence is written to:

```text
mac_test_results/M1/latest.json
mac_test_results/M1/camera-<timestamp>.json
```

## 12. Run the M1 combined image-stage workflow

For a repeatable M1 run before camera validation:

```bash
bash scripts/mac/m1-run.sh
```

This runs:

1. neural environment doctor;
2. known-image neural inference;
3. deterministic Mac Brain integration tests;
4. evidence-location summary.

It intentionally does **not** access the camera. Camera validation remains an explicit separate step.

## 13. Collect the evidence

After a meaningful run:

```bash
bash scripts/mac/collect-evidence.sh
```

This creates a timestamped evidence snapshot under:

```text
IMPLEMENTATION_PLAN/EVIDENCE/mac/<timestamp>/
```

Do not commit large generated model weights. Evidence should contain metadata, logs, JSON results and only intentionally retained test artifacts.

## 14. M1 acceptance gate

M1 is **PASS** only when all applicable evidence demonstrates:

- real neural model loaded on the Mac;
- inference succeeded on the known image;
- selected device/runtime recorded;
- detections are structurally valid;
- confidence and bounding boxes are valid;
- representative results are sensible;
- real camera inference succeeds;
- detections can enter the canonical Novi perception/world-state path;
- deterministic Brain tests remain green;
- evidence is reproducible from a recorded commit/environment.

Until then use `PROTOTYPE`, `EVALUATING`, or `BLOCKED` rather than claiming `TESTED`/`INTEGRATED`.

## 15. What comes after M1

After real neural perception is accepted:

```text
M1  Real neural vision
 ↓
M2  Audio / speech perception
 ↓
M3  Multimodal reasoning
 ↓
M4  World-state + memory integration
 ↓
M5  Goals / planning / bounded autonomy
 ↓
M6  Continuous closed-loop Mac Brain
```

The Mac remains the development body. NVIDIA-specific models and acceleration remain future providers and do not block the Mac prototype.

## Rules

- Do not treat package installation as model compatibility.
- Do not claim Mac performance as NVIDIA performance.
- Do not bypass project dependency constraints.
- Do not commit credentials or downloaded model weights.
- Do not replace the existing Novi Brain with a parallel Mac-only Brain architecture.
- Do not introduce physical motor control during M1.
- Preserve the canonical `ObjectDetector` boundary so the model can later be replaced.
