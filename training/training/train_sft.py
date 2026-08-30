"""LoRA SFT training — first experiment (plan 23 §32, step 10).

Target: situation + communicative act -> natural Novi response, on qwen3:8b.

Backends (framework audit 2026-08-30): mlx-lm if installed, else
transformers+peft (torch). `--dry-run` runs a deterministic smoke pass
(no model, no weights) that reports dataset readiness and provenance —
the default CI-safe path.

    python -m training.training.train_sft --config training/configs/sft.yaml --dry-run
    python -m training.training.train_sft --config training/configs/sft.yaml   # real
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.config import capture_provenance, load_config  # noqa: E402
from training.training.common import (  # noqa: E402
    add_common_args,
    emit_report,
    load_jsonl,
    situation_to_prompt,
    task_counts,
)


def _build_rows(examples: list[dict]) -> list[dict]:
    return [
        {"example_id": ex["example_id"], "prompt": situation_to_prompt(ex), "response": ex["response"]}
        for ex in examples
    ]


def _smoke_report(cfg) -> dict:
    examples = load_jsonl(ROOT / cfg.dataset)
    # Dry-run is a readiness probe: it reports the dataset state and whether
    # the experiment target is met. The real run enforces the gate.
    rows = _build_rows(examples)
    prov = capture_provenance(cfg.base_model, cfg.dataset_version, cfg.seed, cfg.hyperparams, ROOT)
    prov.pop("captured_at", None)  # keep the smoke report deterministic
    return {
        "dry_run": True,
        "task": "sft",
        "config": cfg.to_dict(),
        "examples_loaded": len(rows),
        "min_required": cfg.min_examples,
        "meets_target": len(rows) >= cfg.min_examples,
        "task_counts": task_counts(examples),
        "sample_prompt": rows[0]["prompt"],
        "framework": prov.pop("framework"),
        "provenance": prov,
        "next_step": "install mlx-lm or peft, grow curated dataset to target, then run without --dry-run",
    }


def _real_report(cfg) -> dict:
    from training.config import detect_framework

    framework = detect_framework()
    if framework == "mlx":
        from training.training.backends.mlx_sft import run_mlx_sft  # noqa: PLC0415

        return run_mlx_sft(cfg)
    if framework == "torch-peft":
        from training.training.backends.torch_sft import run_torch_sft  # noqa: PLC0415

        return run_torch_sft(cfg)
    print(
        "ERROR: no training backend available (need mlx-lm or peft+transformers). "
        "Install one, or run with --dry-run for the deterministic smoke pass.",
        file=sys.stderr,
    )
    raise SystemExit(2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    if not args.dry_run:
        from training.training.common import check_min_examples  # noqa: PLC0415

        check_min_examples(load_jsonl(ROOT / cfg.dataset), cfg.min_examples, "sft")
    report = _smoke_report(cfg) if args.dry_run else _real_report(cfg)
    return emit_report(report, args.out_json)


if __name__ == "__main__":
    raise SystemExit(main())
