# Novi Mac Brain — First Run Guide

## Purpose

This guide takes the developer from a clean Mac checkout to the first real Mac neural-model experiment. Hardware/CI validation can remain parked until the Mac is available.

## 0. Requirements

- macOS
- preferably Apple Silicon
- Git
- Python version required by the repository
- Terminal
- working camera for the later camera stage
- internet access for initial dependency/model downloads

Do not install Jetson/NVIDIA dependencies for this stage.

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

Record the results for the eventual evidence package.

## 3. Set up the project environment

From the Novi root:

```bash
bash scripts/mac/setup.sh
source .venv/bin/activate
```

Verify:

```bash
which python
python --version
```

The Python executable should come from `.venv`.

Do not install project packages globally.

## 4. Run the Mac environment doctor

```bash
bash scripts/mac/doctor.sh
```

**Checkpoint:** if this fails, stop and capture the complete output. Do not add ad-hoc packages or bypass environment protections before diagnosing the failure.

## 5. Run the deterministic Mac Brain tests

```bash
bash scripts/mac-brain-test.sh
```

This validates the Mac runtime and existing Brain integration without requiring a real neural model.

## 6. Start the Mac Brain runtime

```bash
bash scripts/mac-brain.sh
```

Capture the startup output. This is the runtime smoke stage, not yet the real neural inference stage.

## 7. Verify camera permissions

When camera access is needed, grant the relevant terminal/application permission in:

**System Settings → Privacy & Security → Camera**

Do not introduce a second camera implementation; use Novi's Mac I/O adapter.

## 8. Inspect neural runtime support

With the virtual environment active:

```bash
python -c "import platform; print(platform.platform()); print(platform.machine())"
```

If PyTorch is already provided by the repository:

```bash
python -c "import torch; print('PyTorch:', torch.__version__); print('MPS:', torch.backends.mps.is_available())"
```

If PyTorch is not installed, do not independently choose a version yet. Use the repository's dependency configuration or resolve the required version before installing it.

## 9. Verify Apple MPS when available

If PyTorch is installed:

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

MPS being unavailable does not automatically block the prototype; a CPU or other verified Mac runtime may still be usable.

## 10. Select the first real neural detector

Do not assume RT-DETR is Mac-compatible before testing it. Evaluate candidates through the canonical `ObjectDetector` interface.

Candidate flow:

```text
candidate
  ↓
installation
  ↓
checkpoint load
  ↓
real inference
  ↓
representative image
  ↓
valid normalized detections
  ↓
latency/memory measurement
  ↓
ACCEPT / REJECT
```

The first implementation target is object detection. Candidates may include RT-DETR variants or another detector that is demonstrably practical on the actual Mac.

## 11. First neural inference

Once a candidate is selected, run it first against a known image rather than the live camera.

Expected path:

```text
known image
  ↓
local neural detector
  ↓
Detection[]
  ↓
canonical Novi evidence
```

Record model ID/checkpoint, runtime, device, load result, inference result, latency and memory.

## 12. Connect the real camera

Only after known-image inference succeeds:

```text
Mac camera
  ↓
CameraFrame
  ↓
local neural detector
  ↓
Detection evidence
  ↓
Novi perception
  ↓
world state
```

This separates camera/debugging problems from model/inference problems.

## 13. First Mac Brain neural milestone

The first meaningful target is:

```text
CAMERA
  ↓
REAL NEURAL OBJECT DETECTOR
  ↓
PERCEPTION
  ↓
WORLD STATE
  ↓
COGNITION
```

The system should produce valid, provenance-rich evidence from real sensory input.

## Evidence

Each formal run should record:

- repository and commit SHA;
- Mac hardware/macOS;
- Python/runtime versions;
- model/checkpoint ID;
- inference runtime/device;
- configuration;
- input/fixture ID;
- load success/failure;
- inference success/failure;
- output validation;
- latency;
- memory where measurable;
- logs/errors.

## Rules

- Do not treat package installation as model compatibility.
- Do not claim Mac performance as NVIDIA performance.
- Do not bypass project dependency constraints.
- Do not commit credentials or downloaded model weights unless explicitly intended by repository policy.
- Do not replace the existing Novi Brain with a parallel Mac-only Brain architecture.
