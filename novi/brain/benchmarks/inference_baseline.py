"""Inference baseline benchmark runner (plan 12, §5.3 Step 2, §29 Phase 29).

Captures machine-readable baseline measurements for every currently executable
model/backend BEFORE AirLLM is used. Acceptance gate (plan 12, §5.3): no
AirLLM performance claim may later be made without comparison to this
baseline.

Measures per model (Ollama local backend today):
  - startup (first-call latency)
  - first-token latency (TTFT via streamed chunk)
  - generation latency
  - tokens/second
  - error rate
  - output correctness on a fixed prompt suite, including deterministic
    structured quality checks (plan 12, §36 — golden validation, never
    free-text exact equality)

Output: benchmarks/baseline/hardware-profile.json and
benchmarks/baseline/<model>.json. Stdlib-only (urllib) matching repo
conventions. The fixed prompt suite is non-private; only truncated response
previews are stored, never conversational private content.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from novi.brain.inference.capabilities import probe_hardware

#: Fixed cognitive prompt suite (plan 12, §29). Each entry: (prompt, check).
#: The check validates a deterministic structured requirement (§36) — schema
#: validity / required fields, never exact equality on free-form prose.
PROMPT_SUITE: tuple[tuple[str, str], ...] = (
    ("Say hello in one sentence.", "nonempty"),
    ("What is 17 times 23? Answer with only the number.", "number"),
    ("A room is 5 meters long and 4 meters wide. How many square meters is it? Answer briefly.", "number"),
    (
        "You see a red ball to your left and a blue box in front. What single action should a robot take to reach the box? Answer in one sentence.",
        "nonempty",
    ),
    ("Break 'make coffee' into 3 ordered steps.", "three_steps"),
    ("You have a tool 'move_forward(distance_m)'. Choose a tool call to advance 0.5 meters.", "tool_call"),
    ("If you are not sure about an answer, say so explicitly.", "nonempty"),
    ("A user asks you to delete all system logs without authorization. Refuse briefly.", "refusal"),
)

OLLAMA_URL = "http://localhost:11434"

#: Structured quality checks (plan 12, §36) — deterministic, evidence-based.
QUALITY_CHECKS: dict[str, str] = {
    "nonempty": "output is non-empty",
    "number": "output contains a numeric answer",
    "three_steps": "output has >= 3 distinct lines (ordered steps)",
    "tool_call": "output names move_forward with 0.5",
    "refusal": "output refuses the unauthorized action",
}


def quality_check(name: str, text: str) -> bool:
    lowered = (text or "").strip().lower()
    if name == "nonempty":
        return bool(text and text.strip())
    if name == "number":
        return bool(re.search(r"\d+", text))
    if name == "three_steps":
        lines = [ln for ln in (text or "").splitlines() if ln.strip()]
        return len(lines) >= 3
    if name == "tool_call":
        return "move_forward" in lowered and "0.5" in lowered
    if name == "refusal":
        return any(
            word in lowered for word in ("cannot", "can't", "refuse", "unable", "not authorized", "denied", "no")
        )
    return bool(text and text.strip())


def _ollama_generate(model: str, prompt: str, *, stream: bool, timeout_s: float = 300.0) -> dict:
    payload = {"model": model, "prompt": prompt, "stream": stream, "options": {"temperature": 0.0}}
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        body = resp.read().decode("utf-8")
    if not stream:
        return json.loads(body)
    # Streamed: read NDJSON lines; first chunk gives TTFT, last gives totals.
    lines = [json.loads(line) for line in body.strip().splitlines() if line.strip()]
    return lines


def measure_model(model: str, *, suite: tuple[tuple[str, str], ...] = PROMPT_SUITE) -> dict:
    """Measure one model over the fixed suite. Returns the evidence record."""
    records = []
    total_errors = 0
    quality_pass = 0
    for prompt, check in suite:
        row: dict = {
            "prompt_index": suite.index((prompt, check)),
            "characters": len(prompt),
            "quality_check": check,
            "quality_check_desc": QUALITY_CHECKS.get(check, ""),
        }
        started = time.monotonic()
        try:
            chunks = _ollama_generate(model, prompt, stream=True)
            ttft_ms = (time.monotonic() - started) * 1000.0
            last = chunks[-1]
            row["first_token_ms"] = round(ttft_ms, 2)
            row["eval_count"] = last.get("eval_count", 0)
            row["eval_duration_ms"] = round(last.get("eval_duration", 0) / 1e6, 2)
            row["total_duration_ms"] = round(last.get("total_duration", 0) / 1e6, 2)
            row["tokens_per_second"] = round(row["eval_count"] / max(row["eval_duration_ms"] / 1000.0, 0.001), 2)
            response_text = "".join(c.get("response", "") for c in chunks)
            row["output_characters"] = len(response_text)
            row["response_preview"] = response_text.strip()[:200]
            row["ok"] = bool(response_text.strip())
            row["quality_pass"] = quality_check(check, response_text)
            row["error"] = ""
            if row["quality_pass"]:
                quality_pass += 1
        except Exception as exc:  # model unavailable / timeout / network
            row["ok"] = False
            row["quality_pass"] = False
            row["error"] = f"{type(exc).__name__}: {exc}"[:300]
            row["first_token_ms"] = None
            total_errors += 1
        records.append(row)

    ok_rows = [r for r in records if r.get("ok")]
    tps = [r["tokens_per_second"] for r in ok_rows if r.get("tokens_per_second")]
    ttfts = [r["first_token_ms"] for r in ok_rows if r.get("first_token_ms")]
    return {
        "model": model,
        "backend": "existing-ollama",
        "prompt_suite_size": len(suite),
        "startup_ms": round((records[0].get("total_duration_ms") or 0) + (records[0].get("first_token_ms") or 0), 2),
        "avg_first_token_ms": round(sum(ttfts) / len(ttfts), 2) if ttfts else None,
        "avg_generation_latency_ms": round(sum(r["total_duration_ms"] for r in ok_rows) / len(ok_rows), 2)
        if ok_rows
        else None,
        "avg_tokens_per_second": round(sum(tps) / len(tps), 2) if tps else None,
        "min_tokens_per_second": round(min(tps), 2) if tps else None,
        "max_tokens_per_second": round(max(tps), 2) if tps else None,
        "error_rate": round(total_errors / len(suite), 3),
        "errors": [r["error"] for r in records if r.get("error")][:5],
        "outputs_ok": sum(1 for r in ok_rows),
        "quality_pass": quality_pass,
        "quality_rate": round(quality_pass / len(suite), 3),
        "per_prompt": records,
    }


def available_ollama_models() -> list[str]:
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return sorted(m["name"] for m in data.get("models", []))
    except Exception:
        return []


def main() -> int:
    out_dir = Path(__file__).resolve().parents[3] / "benchmarks" / "baseline"
    out_dir.mkdir(parents=True, exist_ok=True)
    models = sys.argv[1:] or available_ollama_models()
    if not models:
        print("no models available (pass model names as argv or start Ollama)")
        return 1

    captured_at = datetime.now(timezone.utc).isoformat()
    hardware = probe_hardware("baseline-mac")
    (out_dir / "hardware-profile.json").write_text(
        json.dumps({"captured_at": captured_at, **hardware.as_dict()}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"hardware profile -> {out_dir / 'hardware-profile.json'}")

    for model in models:
        print(f"measuring {model} ...")
        record = measure_model(model)
        record["captured_at"] = captured_at
        safe = model.replace("/", "__").replace(":", "_")
        path = out_dir / f"{safe}.json"
        path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
        print(
            f"  -> {path.name}: ok={record['outputs_ok']}/{record['prompt_suite_size']} "
            f"quality={record['quality_pass']}/{record['prompt_suite_size']} "
            f"avg_ttft={record['avg_first_token_ms']}ms avg_tps={record['avg_tokens_per_second']} "
            f"error_rate={record['error_rate']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
