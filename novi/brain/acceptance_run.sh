#!/bin/sh
# One-command on-device acceptance for plan 03 (Gap 1 + long legs).
#
# Runs, in order: live-model benchmark -> quality gates -> pairwise
# vs the frozen deterministic baseline (v6) -> CI soak. Everything the
# sandbox cannot do (live Ollama backend, wall-clock soak) happens here,
# on the machine, in one step.
#
# Usage:
#   ollama serve            # once, in another terminal (or the app)
#   LLM_MODEL=qwen3:8b novi/brain/acceptance_run.sh
#
# Env:
#   LLM_MODEL   Ollama model tag (default: nemotron-3.5-lightning:latest,
#               the repo-verified default)
#   LLM_URL     Ollama base URL (default: http://localhost:11434)
#   SOAK_TURNS  acceptance soak length (default: 300; ~1-2h legs use 2000+)
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 1

LLM_MODEL="${LLM_MODEL:-nemotron-3.5-lightning:latest}"
LLM_URL="${LLM_URL:-http://localhost:11434}"
SOAK_TURNS="${SOAK_TURNS:-300}"
PY=".venv/bin/python"

echo "== 0/4 Ollama reachable? ($LLM_URL, $LLM_MODEL)"
if ! curl -s -m 5 "$LLM_URL/api/tags" | grep -q '"name"'; then
  echo "FAIL: Ollama is not reachable at $LLM_URL."
  echo "Start it first:  ollama serve   (then: ollama pull $LLM_MODEL)"
  exit 1
fi
if ! curl -s -m 10 "$LLM_URL/api/tags" | grep -q "\"$LLM_MODEL\""; then
  echo "WARN: model tag \"$LLM_MODEL\" not listed; pulling it now."
  ollama pull "$LLM_MODEL" || exit 1
fi

STAMP="$(date +%Y%m%d-%H%M)"
OUT="docs/plans/EVIDENCE/conversation-baseline-live-$STAMP"
mkdir -p "$OUT"

echo "== 1/4 live-model benchmark -> $OUT"
# shellcheck disable=SC2086
$PY -m novi.brain.conversation_replay --brain-llm --llm-url "$LLM_URL" \
  --llm-model "$LLM_MODEL" --evidence-dir "$OUT"
REPLAY_STATUS=$?
if [ "$REPLAY_STATUS" -ne 0 ]; then
  if [ -f "$OUT/baseline.json" ]; then
    # A measured FAIL (scenarios ran, checks failed) is a RESULT, not a
    # crash: the gates/pairwise/soak legs still need to run so the
    # evidence pack is complete. Only a genuine crash (no evidence
    # written) aborts the chain here.
    echo "note: replay finished with status $REPLAY_STATUS (measured FAIL); continuing with gates/pairwise/soak"
  else
    echo "FAIL: live replay crashed with no evidence; see $OUT"; exit 1
  fi
fi

echo "== 2/4 quality gates"
GATE_STATUS=0
$PY -m novi.brain.conversation_gates check --evidence-dir "$OUT" \
  --out "$OUT/gates.json" || GATE_STATUS=$?

echo "== 3/4 pairwise vs frozen deterministic baseline (v6)"
$PY -m novi.brain.conversation_pairwise compare \
  --old docs/plans/EVIDENCE/conversation-baseline-v6 \
  --new "$OUT" --out "$OUT/pairwise-vs-v6" || {
  echo "FAIL: pairwise compare crashed"; exit 1; }

echo "== 4/4 acceptance soak ($SOAK_TURNS turns, live backend)"
$PY -m novi.brain.conversation_soak --turns "$SOAK_TURNS" --probe-every 50 \
  --brain-llm --llm-url "$LLM_URL" --llm-model "$LLM_MODEL" \
  --evidence-dir "$OUT/soak" || {
  echo "FAIL: live soak failed; see $OUT/soak/soak.json"; exit 1; }

echo
echo "Acceptance complete: $OUT"
echo "  baseline : $OUT/baseline.json"
echo "  gates    : $OUT/gates.json (status: $([ "$GATE_STATUS" -eq 0 ] && echo PASS || echo FAIL))"
echo "  pairwise : $OUT/pairwise-vs-v6/pairwise.json + ratings-template.jsonl"
echo "  soak     : $OUT/soak/soak.json"
echo "Next: fill the ratings template (human preference half), grade a"
echo "real session with conversation_grade, then commit the evidence dir."
exit "$GATE_STATUS"
