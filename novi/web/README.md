# Novi Web App

The **Novi web app** is a dependency-free (Python stdlib only) local HTTP server that
owns a running [`Brain`](../brain/engine.py) (`Brain`/`MacBrain`) and serves a browser UI for live
interaction with Novi. The UI lives in [`static/index.html`](static/index.html); the
server lives in [`server.py`](server.py).

The brain runs on a background thread (a bounded auto-step loop). All brain access is
serialized through a single lock, so the UI never races the background loop. No external
web framework, and no network access beyond your local Ollama instance, is required.

---

## What the app does

- **Chat / "hear this" input** — type a line (e.g. `alice moved the door`); Novi
  ingests it as speech, steps the brain, and replies. When a local LLM is configured and
  reachable the reply is rendered through it; otherwise Novi gives a natural
  deterministic fallback (it always *distinguishes* the communication type internally,
  but never replies with the internal cognition label).
- **Live state dashboard** — cycle, health, the current reasoning trace (conclusion,
  confidence, action, rationale), detections, and the multi-speed resource mode.
- **Action buttons** — `step`, adopt a reach `goal (x, y)`, start/stop episode
  recording, switch the active chat model, and listen (real microphone STT).
- **Live event log** — a running feed of the brain's emitted events (sensor frames,
  cognition, reasoning, failure, resource telemetry, speech, etc.).
- **One database for everything** — all state (memory, chat, identity,
  face/voice enrollments, goals, soul) lives in the single canonical store
  `novi/data/novi.db` (SQLite, WAL). The web app, CLI, and the future body all
  resolve this same file; pass `--store PATH` to override if you must.

### API endpoints (all under `/api/...`)

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/state` | GET | Serialized brain state + health |
| `/api/model` | GET | Current + available chat models |
| `/api/model` | POST | Switch the chat/reasoning model |
| `/api/p0-gate` | GET | P0 completion-gate summary |
| `/api/hear` | POST | Ingest a transcript as speech and step the brain |
| `/api/chat` | POST | Compose a chat reply to a message |
| `/api/audio` | POST | Feed a synthetic audio event |
| `/api/listen` | POST | Record + transcribe from the microphone (needs `--camera real`) |
| `/api/chat/clear` | POST | Clear the in-memory chat transcript |
| `/api/step` | POST | Advance the brain one manual cycle |
| `/api/goal` | POST | Adopt a bounded reach goal `(x, y)` |
| `/api/health` | GET | Health report |
| `/api/episode/start` | POST | Start recording an episode |
| `/api/episode/stop` | POST | Stop recording the current episode |
| `/api/episode/status` | GET | Current episode recording status |

---

## Starting the app

You can start the web app in several ways. All commands are run from the repository
root (`/Users/vanonatobaidze/projects/Novi`). Prefer the launcher script; it sets up
`PYTHONPATH` and uses the project virtualenv automatically.

### 1. Launcher script (recommended)

```bash
./scripts/mac-web.sh
# or, if execute permission isn't enabled in your checkout:
bash scripts/mac-web.sh
```

Launches at **http://127.0.0.1:8080** with a durable store of `novi/data/novi.db` and an
auto-step every 0.8s. Override with env vars:

```bash
NOVI_HOST=127.0.0.1 NOVI_PORT=8080 NOVI_STORE=~/novi/data/novi.db NOVI_TICK=0.8 ./scripts/mac-web.sh
```

Pass through extra server flags after the script name, e.g.
`./scripts/mac-web.sh --reasoning router --camera real`.

### 2. Direct Python invocation

```bash
.venv/bin/python -m novi.web.server --host 127.0.0.1 --port 8080 --store novi/data/novi.db --tick 0.8
```

Same flags as the launcher (they are forwarded verbatim).

### 3. Installed console script

If the project was installed into the environment (`pip install -e .`), a
`novi-web` entry point exists:

```bash
novi-web --host 127.0.0.1 --port 8080
```

### Web server flags

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

> Note: chat replies are composed through a local **Ollama** LLM at
> `http://localhost:11434` (the default `ollama-model` is `nemotron-3.5-lightning`).
> If Ollama isn't running (or was still loading its model when the server started),
> Novi serves a natural deterministic fallback reply and **re-probes** Ollama every
> few seconds, so it reconnects automatically without a restart.

---

## Stopping the app

- **Foreground:** press **Ctrl-C** in the terminal that launched the server. The
  server catches `KeyboardInterrupt`, closes the HTTP server, and stops the brain's
  background loop cleanly.
- **Background job (e.g. started from a harness):** send `SIGTERM`/`SIGKILL` to the
  process on the bound port, or use your job manager's kill command. For example:

  ```bash
  lsof -nP -iTCP:8080 -sTCP:LISTEN   # find the PID
  kill <PID>                          # graceful; use kill -9 if it doesn't stop
  ```

- **Restart after a code change:** stop the current server (see above) and launch it
  again with any of the start methods above.

---

## Other Novi scripts (descriptions)

The web app is one entry point of a larger set of scripts. Brief descriptions:

### Root-level `scripts/` launchers

| Script | Description |
| --- | --- |
| [`scripts/mac-web.sh`](../scripts/mac-web.sh) | **Start the web app.** `python -m novi.web.server` with sensible defaults; env overrides `NOVI_HOST/PORT/STORE/TICK`. |
| [`scripts/brain.sh`](../scripts/brain.sh) | **Start the interactive CLI brain** (`python -m novi.brain.cli`). Pass CLI flags through, e.g. `--live`. |
| [`scripts/brain-demo.sh`](../scripts/brain-demo.sh) | **Start a canned demo.** Modes: `live` (webcam + neural vision + STT + router reasoning + TTS), `neural`/`image` (MPS object detection on a static image), `hear` (offline deterministic speech), `quick` (deterministic brain, no camera/mic/model), or pass through anything else to the CLI. |
| [`scripts/brain-test.sh`](../scripts/brain-test.sh) | **Run the Brain test suite** and write a summarized JSON result to `mac_test_results/brain/<timestamp>/`. |

### Scripts/`mac/` test + tooling helpers

| Script | Description |
| --- | --- |
| `scripts/mac/setup.sh` | Create/update the project-local `.venv` and install declared dependencies. |
| `scripts/mac/doctor.sh` | Print the Mac/toolchain/repository state (OS, Python, Git, pytest, coverage, ruff, mypy, Node, Docker, git branch/commit, working tree). |
| `scripts/mac/test.sh` | Run the complete deterministic suite; collect logs, JUnit XML, coverage, and environment metadata into `mac_test_results/<run-id>/`. |
| `scripts/mac/test-brain.sh` | Run the Brain test suite and collect the same evidence. |
| `scripts/mac/benchmark.sh` | Run the deterministic Brain benchmark entrypoint. **Not** NVIDIA GPU performance evidence. |
| `scripts/mac/collect-evidence.sh` | Snapshot the latest run into `docs/plans/EVIDENCE/mac/<timestamp>/`. |
| `scripts/mac/runner.py` | Underlying Python orchestrator for the test/benchmark scripts. |
| `scripts/mac/m1-run.sh` | Full M1 bring-up: neural environment check, known-image inference, deterministic brain integration, and evidence locations. |
| `scripts/mac/m1-image-test.sh` | Real neural (MPS) object detection on a static image. |
| `scripts/mac/m1-camera-test.sh` | Real neural (MPS) object detection from the camera. |
| `scripts/mac/neural-setup.sh` | Install the neural deps (torch, torchvision, pillow, numpy, opencv, sounddevice, faster-whisper) and verify MPS. |
| `scripts/mac/neural-doctor.sh` | Print neural environment metadata (Python, platform, PyTorch/MPS availability). |
| `scripts/mac/neural-smoke.sh` | Run a neural smoke test on an image path. |
| `scripts/mac/io-test.sh` | Test speaker/microphone audio I/O (speaks and records briefly). |
| `scripts/mac/test.sh`, `test-unit.sh`, `test-full.sh`, `test-brain.sh` | Shorthand test runners for unit / full / brain suites (see each file). |

> For the full test-script workflow (setup → doctor → test → collect-evidence) see
> [`scripts/mac/README.md`](../scripts/mac/README.md).
