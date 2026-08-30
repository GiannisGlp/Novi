"""DPO preference training — second experiment (plan 23 §33, step 13-15).

Runs after SFT is stable: 1,000+ preference pairs (datasets/dpo/) train the
adapter to prefer natural, brief, grounded responses (plan §11 categories:
naturalness, brevity, context, memory, clarification, initiative, repair,
social appropriateness).

Real backend: trl's DPOTrainer over the SFT adapter (torch). Smoke mode is
the deterministic CI-safe default.
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
)


def _smoke_report(cfg) -> dict:
    pairs = load_jsonl(ROOT / cfg.dataset)
    from training.schemas import validate_example  # noqa: PLC0415

    bad = [p["example_id"] for p in pairs if validate_example(p, kind="preference")]
    if bad:
        raise ValueError(f"dpo: {len(bad)} preference pairs fail validation, e.g. {bad[:3]}")
    categories: dict[str, int] = {}
    for p in pairs:
        categories[p.get("category", "unknown")] = categories.get(p.get("category", "unknown"), 0) + 1
    prov = capture_provenance(cfg.base_model, cfg.dataset_version, cfg.seed, cfg.hyperparams, ROOT)
    prov.pop("captured_at", None)
    return {
        "dry_run": True,
        "task": "dpo",
        "config": cfg.to_dict(),
        "pairs_loaded": len(pairs),
        "categories": dict(sorted(categories.items())),
        "min_required": cfg.min_examples,
        "framework": prov.pop("framework"),
        "provenance": prov,
        "next_step": "SFT stable -> install trl -> run without --dry-run",
    }


def _real_report(cfg) -> dict:
    try:
        from trl import DPOTrainer  # noqa: PLC0415
    except ImportError:
        print("ERROR: DPO requires trl (`pip install trl`).", file=sys.stderr)
        raise SystemExit(2) from None
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments  # noqa: PLC0415

    pairs = load_jsonl(ROOT / cfg.dataset)
    tokenizer = AutoTokenizer.from_pretrained(cfg.hf_model_id or cfg.base_model)
    model = AutoModelForCausalLM.from_pretrained(cfg.sft_adapter or cfg.hf_model_id or cfg.base_model)
    ref_model = AutoModelForCausalLM.from_pretrained(cfg.hf_model_id or cfg.base_model)

    def _format(pair: dict) -> dict:
        prompt = situation_to_prompt({"situation": pair.get("situation", {})})
        chosen = pair["response_a"] if pair["preferred"] == "A" else pair["response_b"]
        rejected = pair["response_b"] if pair["preferred"] == "A" else pair["response_a"]
        return {"prompt": prompt, "chosen": chosen, "rejected": rejected}

    rows = [_format(p) for p in pairs]
    args = TrainingArguments(
        output_dir=cfg.output_dir,
        per_device_train_batch_size=int(cfg.hyperparams.get("batch_size", 4)),
        learning_rate=float(cfg.hyperparams.get("learning_rate", 1e-5)),
        num_train_epochs=int(cfg.hyperparams.get("epochs", 2)),
        seed=cfg.seed,
        report_to=[],
    )
    trainer = DPOTrainer(
        model=model, ref_model=ref_model, args=args, tokenizer=tokenizer,
        beta=float(cfg.hyperparams.get("beta", 0.1)), train_dataset=rows,
    )
    trainer.train()
    trainer.save_model(cfg.output_dir)
    return {
        "task": "dpo",
        "framework": "torch-peft-trl",
        "adapter_path": cfg.output_dir,
        "pairs_trained": len(rows),
        "provenance": capture_provenance(cfg.base_model, cfg.dataset_version, cfg.seed, cfg.hyperparams),
        "note": "evaluate SFT vs SFT+DPO on the fixed benchmark before registry (plan §33/§15)",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    report = _smoke_report(cfg) if args.dry_run else _real_report(cfg)
    return emit_report(report, args.out_json)


if __name__ == "__main__":
    raise SystemExit(main())
