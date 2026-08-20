---
name: python-ai-robotics-nvidia
description: Use when working on Python projects that involve artificial intelligence, machine learning, deep learning / neural networks, robotics, or the NVIDIA compute stack — including PyTorch, TensorFlow/JAX, CUDA, cuDNN, TensorRT, and NVIDIA Jetson/Isaac. Guides environment setup, GPU-aware development, model work, robotics integration, and NVIDIA-tooling verification so the agent produces correct, runnable code.
---

# Python · AI · Neural Networks · Robotics · NVIDIA

Reusable guidance for tasks touching Python, ML/DL, robotics, or the NVIDIA stack. Use it to pick correct tooling, verify the environment before assuming CUDA or a GPU, and avoid the common failure modes in this domain.

## First determine the environment

Before writing or running anything that depends on a GPU or an NVIDIA driver, **verify the actual environment**. Do not assume CUDA, cuDNN, TensorRT, or a GPU is present.

- Query the Python interpreter in use (`which python3`, `python3 --version`) and whether a virtualenv is active.
- Detect an NVIDIA GPU and driver: `nvidia-smi` (driver + CUDA runtime version). If it fails, CUDA is not installed or not on `PATH`.
- Check key libraries: `python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.version.cuda)"`, and similarly for `jax`, `tensorflow`, `triton`.
- Note CPU/GPU availability differences: a model that runs on CPU may behave differently (speed, determinism, memory) on GPU.

Keep the environment facts (Python version, torch/CUDA versions, GPU name and driver) in a short note; never silently invent a hardware stack the machine does not have.

## Python conventions

- Prefer a virtualenv or a declared dependency file (`requirements.txt` / `pyproject.toml`) and document how to reproduce the environment.
- Use type hints and docstrings for public functions; keep functions small and testable.
- For scientific/array work default to NumPy; prefer PyTorch tensors over numpy for anything that must move to a GPU.
- Write a minimal smoke test per module so correctness is checked rather than assumed.

## Neural networks / deep learning

- Prefer explicit, deterministic setup: set random seeds (`torch.manual_seed`, `numpy.random.seed`) and pin the device (`torch.device('cuda' if torch.cuda.is_available() else 'cpu')`) once, centrally.
- Put model, loss, and optimizer on the **same** device; move data with `.to(device)` at each batch — the classic error is a CPU tensor fed to a CUDA model.
- Use `model.train()` / `model.eval()` correctly; wrap inference in `torch.no_grad()`.
- Prefer mixed precision (`torch.amp`) and gradient clipping only when the problem calls for them; document the choice.
- Validate shapes before forward passes (layer output vs. expected feature maps) with asserts or prints during debugging.
- For HuggingFace models, pin the library/transformers versions; `pipeline()` / `from_pretrained` may otherwise pull incompatible or updated weights.

## Robotics

- Identify the framework (ROS 1 / ROS 2, MoveIt, Gazebo, Isaac Sim, MuJoCo) from the project, and match the robot description (URDF/SDF, joint limits, actuation) rather than hard-coding arbitrary values.
- Coordinate frames and transforms are the core hazard: specify frame names and units explicitly, and verify a transform lookup before trusting downstream poses.
- Distinguish simulation from hardware. For real hardware, require a dry-run / simulated mode and confirm safety constraints (joint limits, velocities, emergency stop) before commanding motion.
- ROS 2 specific: confirm the distro (`ROS_DISTRO`), source the setup (`source /opt/ros/<distro>/setup.bash`), and build with `colcon`. Use matching QoS for pub/sub.

## NVIDIA stack

- CUDA: check `nvcc --version` for the toolkit and `nvidia-smi` for the driver; the driver's CUDA version can be newer than the installed toolkit — match them.
- cuDNN / TensorRT are separate installs: verify their presence and version independently (`dpkg -l | grep cudnn`, `dpkg -l | grep tensorrt`, or equivalent) rather than assuming them from the driver.
- PyTorch binaries are CUDA-version-specific: install the wheel that matches the machine's CUDA, typically from `pytorch.org` `pip index-url` (e.g. `cu118`, `cu121`, `cu124`). A wrong-CUDA wheel still installs and silently falls back to CPU.
- NVIDIA Jetson (embedded): different userland — confirm JetPack version and platform (`aarch64`), and use `l4t`/Jetson-specific builds, not standard x86 CUDA wheels.
- TensorRT: engine files are architecture-specific; rebuild or re-serialize the engine for the target GPU rather than sharing `.engine` files across devices.

## Verification before finishing

- Run the skill's code or a representative smoke test and report the real output (version prints, a shape assert, a short forward pass) instead of assuming it works.
- Report any environment gaps (no GPU, no CUDA, missing cuDNN) explicitly, and state what the machine would need to run the code fully.
- If a tool says a GPU is present but `torch.cuda.is_available()` is false, the torch/CUDA mismatch is the likely cause — check the wheel's CUDA version.

## When to stop and ask

- If the target hardware (GPU model, NVIDIA driver, ROS distro, JetPack version) is not known and materially changes the solution, ask a concise clarifying question rather than guessing.
- If the task requires physical hardware actuation, offer a simulated/dry-run path first and confirm before any real-motion command.
