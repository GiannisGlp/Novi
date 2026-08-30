"""AirLLM Mac validation runner (plan 12, §16-17 Phase 12, Step 18-22).

Executes a representative AirLLM workload on the actual development machine
(Mac) before declaring the backend Mac-compatible — the plan's acceptance
sequence: prepare -> shard integrity -> single prompt -> warm inference ->
unload. Qwen3-4B is the Mac pipeline target (8 GB checkpoint fits the dev
disk; the Qwen3.8-27B checkpoint requires ~112 GB and is documented blocked).

IMPORTANT Mac finding (AirLLM 3.3.0): on macOS ``AutoModel.from_pretrained``
routes to ``AirLLMLlamaMlx``, which only supports the standard Llama-style
layout (``model.embed_tokens`` / ``model.layers`` / ``model.norm`` /
``lm_head``). Qwen3.8-27B (``Qwen3_5ForConditionalGeneration`` with a nested
``model.language_model``) is NOT supported by the Mac path — CUDA only.

Run inside the isolated AirLLM environment:

    PYTHONPATH=. .venv-locateanything/bin/python \\
        novi/brain/benchmarks/airllm_mac_validate.py --prepare --smoke --model Qwen/Qwen3-4B

Evidence: benchmarks/airllm-mac/<model>.json (never the shards themselves).
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from novi.brain.inference.airllm.compatibility import probe_airllm_environment
from novi.brain.inference.backends.airllm import AirLLMBackend
from novi.brain.inference.registry import ModelRegistry, ModelSpec
from novi.brain.inference.request import InferenceRequest

EVIDENCE_DIR = Path(__file__).resolve().parents[3] / "benchmarks" / "airllm-mac"
MODEL_ROOT = Path(os.environ.get("NOVI_AIRLLM_MODEL_ROOT", "/tmp/novi-airllm-mac"))


def build_spec(registry: ModelRegistry, model_id: str, source_id: str, architecture: str) -> ModelSpec:
    """Build an approved registry spec for a model, falling back to a
    standalone spec when the registry has no entry (validation may target any
    standard-Llama-layout model)."""
    try:
        spec = registry.get(model_id)
    except Exception:
        spec = None
    common = dict(
        id=model_id,
        family=model_id.split("-")[0],
        role_candidates=("deep_reasoning",),
        backend_preferences=("airllm", "existing"),
        source_type="huggingface",
        source_id=source_id,
        local_aliases=(),
        status="approved",
        backend_artifacts={"airllm": {"source_id": source_id, "architecture": architecture}},
        resolved={
            "architecture": architecture,
            "parameter_count": _parameter_count(model_id),
        },
    )
    if spec is not None:
        common.update(local_aliases=spec.local_aliases, family=spec.family, context_limit=spec.context_limit)
    return ModelSpec(**common)


def _parameter_count(model_id: str) -> str:
    for token in model_id.split("-")[::-1]:
        if any(ch.isdigit() for ch in token):
            return token
    return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description="AirLLM Mac validation (plan 12 Phase 12)")
    parser.add_argument("--model", default="Qwen/Qwen3-4B", help="HF source id")
    parser.add_argument("--registry-model", default="qwen3-4b", help="registry id to map onto")
    parser.add_argument("--architecture", default="Qwen3ForCausalLM")
    parser.add_argument("--prepare", action="store_true", help="run preparation (download + shard)")
    parser.add_argument("--smoke", action="store_true", help="run load + generate smoke")
    args = parser.parse_args()

    compat = probe_airllm_environment()
    print("environment:", json.dumps(compat.as_dict(), indent=2, sort_keys=True))
    if not compat.airllm_installed:
        print("airllm not installed in this environment; aborting")
        return 2

    registry = ModelRegistry()
    spec = build_spec(registry, args.registry_model, args.model, args.architecture)
    backend = AirLLMBackend(
        model_root=str(MODEL_ROOT),
        enabled=True,
        preparation_allowed=bool(args.prepare),
        compat=compat,
    )
    evidence: dict = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "registry_model": args.registry_model,
        "architecture": args.architecture,
        "compatibility": compat.as_dict(),
        "platform": {"system": os.uname().sysname, "machine": os.uname().machine},
    }

    if args.prepare:
        started = time.monotonic()
        manifest = backend.prepare(spec)
        evidence["prepare"] = {
            "elapsed_s": round(time.monotonic() - started, 2),
            "manifest": manifest.as_dict(),
            "shards_dir": str(MODEL_ROOT / "models" / "airllm" / args.registry_model / "shards"),
        }
        print(f"prepare ok: shard_count={manifest.shard_count} total_bytes={manifest.total_bytes}")

    if args.smoke:
        load_started = time.monotonic()
        backend.load(spec)
        load_elapsed = time.monotonic() - load_started
        print(f"load ok ({load_elapsed:.2f}s)")

        prompt = "Say hello in one short sentence."
        req_started = time.monotonic()
        response = backend.generate(
            InferenceRequest(
                messages=[{"role": "user", "content": prompt}],
                max_output_tokens=32,
                temperature=0.0,
                caller="airllm-mac-validation",
                purpose="smoke",
            )
        )
        gen_elapsed = time.monotonic() - req_started
        evidence["smoke"] = {
            "load_elapsed_s": round(load_elapsed, 2),
            "generation_elapsed_s": round(gen_elapsed, 2),
            "text": response.text,
            "finish_reason": response.finish_reason,
            "output_tokens": response.output_tokens,
            "latency_ms": round(response.latency_ms, 2),
            "backend_id": response.backend_id,
            "ok": response.ok,
        }
        print(f"smoke: {response.text[:80]!r} ({gen_elapsed:.2f}s)")

        # Warm path: second generation without reload.
        warm_started = time.monotonic()
        warm = backend.generate(
            InferenceRequest(
                messages=[{"role": "user", "content": "What is 2 plus 2? Answer with one number."}],
                max_output_tokens=16,
                temperature=0.0,
                caller="airllm-mac-validation",
                purpose="warm",
            )
        )
        evidence["warm"] = {
            "generation_elapsed_s": round(time.monotonic() - warm_started, 2),
            "text": warm.text,
            "ok": warm.ok,
        }
        backend.unload(spec)
        evidence["unload"] = {"ok": True}

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    out = EVIDENCE_DIR / f"{args.registry_model}.json"
    out.write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
    print(f"evidence -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
