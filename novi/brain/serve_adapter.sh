#!/bin/sh
# One-command deployment of a trained MLX adapter for the brain.
#
# Serves an MLX base + LoRA adapter through an OpenAI-compatible /v1 server
# (mlx_lm.server) and prints how to point Novi's brain/replay at it:
#
#   novi/brain/serve_adapter.sh                      # v4 (qwen3:4B) by default
#   BASE_MODEL=Qwen/Qwen3-8B ADAPTER=.../novi-v2-mlx novi/brain/serve_adapter.sh
#
# Then, in another terminal (36GB machine: stop Ollama first to free RAM):
#   ollama stop nemotron-3.5-lightning:latest   # free ~25GB
#   .venv/bin/python -m novi.brain.conversation_replay \
#       --brain-llm --brain-llm-server openai-compatible \
#       --llm-url http://127.0.0.1:8080 --llm-model Qwen/Qwen3-4B \
#       --only C-032,C-120,C-152 --evidence-dir <out>
#
# Env:
#   BASE_MODEL  HF repo or mlx dir (default Qwen/Qwen3-4B)
#   ADAPTER     LoRA adapter dir (default the trained v4 candidate)
#   PORT        server port (default 8080)
#   HF_HOME     huggingface cache (default: repo .hf-cache when present)
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 1

BASE_MODEL="${BASE_MODEL:-Qwen/Qwen3-4B}"
ADAPTER="${ADAPTER:-training/models/adapters/novi-qwen3-4b-dialogue-v4-mlx}"
PORT="${PORT:-8080}"
PYMLX=".venv-mlx/bin/python"

if [ -d "$ROOT/.hf-cache" ]; then
  export HF_HOME="$ROOT/.hf-cache"
fi

if [ ! -x "$PYMLX" ]; then
  echo "FAIL: $PYMLX not found (create the mlx venv first:  uv venv --python 3.13 .venv-mlx && uv pip install --python .venv-mlx mlx mlx-lm)" >&2
  exit 1
fi
if [ ! -f "$ADAPTER/adapter_config.json" ]; then
  echo "FAIL: adapter not found at $ADAPTER" >&2
  exit 1
fi

echo "== serving $BASE_MODEL + adapter $(basename "$ADAPTER") on :$PORT"
echo "   probe: curl http://127.0.0.1:$PORT/v1/models"
echo "   brain: --brain-llm-server openai-compatible --llm-url http://127.0.0.1:$PORT --llm-model <id from probe>"
exec "$PYMLX" -m mlx_lm.server --model "$BASE_MODEL" --adapter-path "$ADAPTER" --port "$PORT" --log-level INFO
