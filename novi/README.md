# Novi

**Novi** is an autonomous embodied AI system. It runs entirely locally on this
Mac (Python 3.14, PyTorch on MPS) — no cloud services, no ROS, and no NVIDIA
hardware are required. The only network endpoint it touches is your local
[Ollama](https://ollama.com) instance at `http://localhost:11434`, and only if
you opt into LLM-backed reasoning or chat.

The core idea is **capability-boundary architecture**: the Brain orchestrates,
Cognition understands, Memory remembers, Autonomy decides, Policy/Safety
permits, and Hardware executes. Models **propose** — they never authorize.

## Layout

All implementation lives under this `novi/` package:

| Path | What it is |
| --- | --- |
| `novi/brain/` | The executable brain unit — supervisor lifecycle, scheduling, reasoning, soul, memory, knowledge graph, context, and the `Brain`/`MacBrain` runtime. |
| `novi/cognition/` | Typed cognition contracts (Pydantic models) the brain uses for perception, memory, and reasoning records. |
| `novi/contracts/` | Canonical JSON schemas (contracts) plus a runtime validation suite. |
| `novi/web/` | A dependency-free (stdlib-only) HTTP server + browser UI for live interaction with Novi. |
| `novi/db/` | Durable SQLite runtime stores (`novi_demo.db`, `novi_web.db`). Gitignored; created at runtime. |
| `novi/assets/` | Static fixtures used by the demo (e.g. `test-image.png` for camera-less neural vision). |

## Principles

- **Mac-first.** Core tests and the CLI run on this Mac with zero NVIDIA
  tooling. NVIDIA/Jetson targets are external validation/deployment only.
- **Deterministic by default.** Reasoning defaults to a deterministic symbolic
  backend; LLM reasoning is opt-in via `--reasoning ollama` / `router`.
- **Models propose, never authorize.** Safety is enforced by a separate policy
  gateway, not by the LLM.
- **Evidence-graded.** Work is validated against a 12-domain completion gate;
  see `docs/00-strategy/NOVI_GLOBAL_COMPLETION_GATE.md`.

## Quick start

Run all commands from the repository root
(`/Users/vanonatobaidze/projects/Novi`). See [`SCRIPTS.md`](SCRIPTS.md) for the
full launcher/script reference.

```bash
# Interactive CLI brain (deterministic, no camera/mic/model needed)
./scripts/brain.sh --cycles 5

# Web app at http://127.0.0.1:8080
./scripts/mac-web.sh

# Full live demo (webcam + neural vision + STT + TTS + durable memory)
./scripts/brain-demo.sh live

# Run the test suite
./scripts/brain-test.sh
```

> The repo root also has a `docs/` tree (specs, audits, strategy) and a
> `scripts/` tree (launchers + Mac test tooling). Those are not part of the
> `novi/` package; see `SCRIPTS.md` for how to use them.

## Install

```bash
bash scripts/mac/setup.sh        # create/update .venv and install deps
source .venv/bin/activate        # optional: activate the venv
```
