# Novi — Scripts & How to Run

This is the complete reference for launching Novi: the web app, the interactive
CLI brain, the demo modes, and the Mac test/tooling scripts.

> **Run directory:** every command in this document is meant to be run from the
> **repository root** — `/Users/vanonatobaidze/projects/Novi`. The launchers
> compute `ROOT` from their own location, but relative paths like
> `novi/assets/test-image.png` and the `.venv` reference assume you are at the
> repo root. Use `bash scripts/...` explicitly unless execute permission is
> enabled in your checkout.

---

## 1. Web app

A dependency-free local HTTP server (`novi/web/server.py`) that owns a running
`Brain` on a background thread and serves a browser UI.

| Start method | Command (run from repo root) |
| --- | --- |
| Launcher (recommended) | `./scripts/mac-web.sh` (or `bash scripts/mac-web.sh`) |
| Direct Python | `.venv/bin/python -m novi.web.server --host 127.0.0.1 --port 8080` |
| Installed entry point | `novi-web --host 127.0.0.1 --port 8080` |

Launches at **http://127.0.0.1:8080** with a durable store of
`novi/db/novi_web.db` and an auto-step every 0.8s. Stop it with **Ctrl-C** in
the foreground, or `kill <PID>` (find it with `lsof -nP -iTCP:8080
-sTCP:LISTEN`) for a background job.

### Web server flags (`scripts/mac-web.sh` forwards these, or use `-m novi.web.server`)

| Flag | Default | Description |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Bind address |
| `--port` | `8080` | Bind port |
| `--store PATH` | *disabled* | Enable durable SQLite storage at `PATH` |
| `--tick` | `0.8` | Seconds per auto-step of the background brain loop |
| `--no-auto-step` | off | Advance only on a manual `/api/step` |
| `--camera demo\|real` | `demo` | `demo` = no-hardware camera; `real` = webcam + real STT |
| `--reasoning deterministic\|ollama\|router` | `deterministic` | Brain decision backend; `router` escalates uncertain steps to the local LLM |
| `--route-threshold` | `0.6` | Confidence below which the router escalates to the LLM |
| `--ollama-model` | `nemotron-3.5-lightning` | Ollama model for reasoning + chat replies |
| `--model` | `nemotron-3.5-lightning` | Default chat model (switchable at runtime in the UI) |
| `--stt-model` | `base` | faster-whisper model size for real STT (`tiny/base/small`) |
| `--stt-device` | `cpu` | STT device (`cpu` or `mps`) |
| `--listen-seconds` | `3.0` | Microphone recording length for the Listen button |

Launcher env overrides: `NOVI_HOST`, `NOVI_PORT`, `NOVI_STORE`, `NOVI_TICK`.

> Chat replies go through a local **Ollama** LLM at `http://localhost:11434`
> (default model `nemotron-3.5-lightning`). If Ollama isn't running, Novi serves
> a natural deterministic fallback and **re-probes Ollama every few seconds**,
> reconnecting automatically without a restart.

**UI:** chat / "hear this", live state dashboard, action buttons (`step`,
adopt a reach goal, episode record, model switch, listen), live event log.
Full API reference (all under `/api/`): `/api/state`, `/api/model` (GET/POST),
`/api/p0-gate`, `/api/hear`, `/api/chat`, `/api/audio`, `/api/listen`,
`/api/chat/clear`, `/api/step`, `/api/goal`, `/api/health`,
`/api/episode/start|stop|status`.

---

## 2. Interactive CLI brain

`scripts/brain.sh` wraps `python -m novi.brain.cli`. Anything after the script
name is passed through verbatim.

```bash
./scripts/brain.sh --cycles 5                      # deterministic, 5 cycles
./scripts/brain.sh --live --rounds 3               # live demo loop
./scripts/brain.sh --reasoning ollama --ollama-model qwen3.8:27b
```

### CLI brain flags

| Flag | Default | Description |
| --- | --- | --- |
| `--live` | off | Interactive live loop (camera + STT + decide + soul + TTS) |
| `--rounds` | `1` | Live rounds (use a large value for a sustained session) |
| `--live-steps` | `1` | Vision steps per live round |
| `--live-camera` | off | Use the Mac camera instead of the deterministic camera |
| `--neural` | off | Real Mac neural (MPS) object-detection backend |
| `--neural-image PATH` | `novi/assets/test-image.png` | Static image as camera input (no hardware) |
| `--device` | auto | Torch device for neural inference (`mps` if available, else `cpu`) |
| `--cycles` | `1` | Number of deterministic cycles |
| `--listen SECONDS` | `0.0` | Record from mic and transcribe locally |
| `--transcribe PATH` | – | Transcribe an existing audio file |
| `--stt-model` | `base` | faster-whisper size (`tiny/base/small`) |
| `--stt-device` | `cpu` | STT device (`cpu` or `mps`) |
| `--reasoning deterministic\|ollama\|router` | `deterministic` | Reasoning backend |
| `--route-threshold` | `0.6` | Router escalate threshold |
| `--ollama-model` | `qwen3.8:27b` | Ollama model for `ollama`/`router` reasoning |
| `--goal-target X,Y` | – | Adopt a bounded reach goal to `(X, Y)` in meters |
| `--goal-steps` | `100` | Step budget for the reach goal |
| `--store PATH` | – | Persist memory + goals to a SQLite DB |
| `--evidence PATH` | `brain_evidence.json` | Write JSON evidence |
| `--speak TEXT` | – | Emit speech text |
| `--demo-hear TEXT` | – | Inject deterministic transcript (offline/test) |
| `--say` | off | Enable TTS via macOS `say` |
| `--say-voice` | – | macOS `say` voice name |

---

## 3. Demo modes (`scripts/brain-demo.sh` / `scripts/mac-brain-demo.sh`)

```bash
./scripts/brain-demo.sh live      # default: webcam + neural vision + STT + router reasoning + TTS
./scripts/brain-demo.sh neural    # MPS object detection on novi/assets/test-image.png
./scripts/brain-demo.sh image     # alias of neural
./scripts/brain-demo.sh hear      # offline deterministic speech (no microphone)
./scripts/brain-demo.sh quick     # deterministic brain, no camera/mic/model
./scripts/brain-demo.sh <anything> # passed straight through to the CLI
```

Demo env overrides: `NOVI_ROUNDS=3`, `NOVI_LIVE_STEPS=1`,
`NOVI_LISTEN_SECONDS=2`, `NOVI_STT_MODEL=base`, `NOVI_VOICE=Samantha`,
`NOVI_STORE=novi/db/novi_demo.db`, `NOVI_GOAL_TARGET=1,2`,
`NOVI_NO_CAMERA=1` (use deterministic camera instead of webcam), `NOVI_CYCLES`.

---

## 4. Tests & tooling (`scripts/mac/`)

Standard workflow (all from repo root):

```bash
bash scripts/mac/setup.sh         # create/update .venv + install deps
bash scripts/mac/doctor.sh        # inspect Mac/toolchain/repo state
bash scripts/mac/test.sh          # run full deterministic suite + collect evidence
bash scripts/mac/collect-evidence.sh  # snapshot the run to docs/plans/EVIDENCE/mac/
```

| Script | Description |
| --- | --- |
| `scripts/mac/setup.sh` | Create/update `.venv` and install declared dependencies. |
| `scripts/mac/doctor.sh` | Print Mac/toolchain/repo state (OS, Python, Git, pytest, coverage, ruff, mypy, Node, Docker). |
| `scripts/mac/test.sh` | Complete deterministic suite; logs, JUnit XML, coverage, env metadata → `mac_test_results/<run-id>/`. |
| `scripts/mac/test-brain.sh` | Brain test suite with the same evidence. |
| `scripts/mac/benchmark.sh` | Deterministic Brain benchmark (not NVIDIA GPU evidence). |
| `scripts/mac/collect-evidence.sh` | Snapshot the latest run into `docs/plans/EVIDENCE/mac/<timestamp>/`. |
| `scripts/mac/m1-run.sh` | Full M1 bring-up: env check + image inference + brain integration. |
| `scripts/mac/m1-image-test.sh` | Real neural (MPS) detection on a static image. |
| `scripts/mac/m1-camera-test.sh` | Real neural (MPS) detection from the camera. |
| `scripts/mac/neural-setup.sh` | Install neural deps and verify MPS. |
| `scripts/mac/neural-doctor.sh` | Print neural env metadata. |
| `scripts/mac/neural-smoke.sh` | Neural smoke test on an image path. |
| `scripts/mac/io-test.sh` | Test speaker/microphone audio I/O. |
| `scripts/mac/test.sh` / `test-unit.sh` / `test-full.sh` / `test-brain.sh` | Shorthand test runners. |
| `scripts/mac/runner.py` | Underlying Python orchestrator for test/benchmark scripts. |

Run results land in `mac_test_results/<UTC-run-id>/` with `latest/` symlink.

> **Important:** A Mac result proves local software/test behavior. It does not
> prove Jetson TensorRT performance, GPU power/thermal behavior, or the
> Orin-vs-Thor hardware decision.

---

## 5. Python module entry points

When the project is installed (`pip install -e .`), these console scripts exist:

| Entry point | Runs |
| --- | --- |
| `novi-brain` | `novi.brain.cli:main` |
| `novi-web` | `novi.web.server:main` |
| `brain-cli` | `novi.brain.cli:main` |

Equivalent direct module invocations: `python -m novi.brain.cli ...` and
`python -m novi.web.server ...` (prefer the `.venv/bin/python` interpreter).
