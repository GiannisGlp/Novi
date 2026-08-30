"""Transformers+Peft LoRA SFT backend (plan 23 §32, first experiment).

Requires `peft` (missing in the audit venv: torch 2.13 + transformers are
present, peft is not — `pip install peft`). Standard causal-LM SFT with a
LoRA adapter; MPS is available on this Mac (torch 2.13, mps: True).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from training.config import capture_provenance


def _build_chat_dataset(examples: list[dict], tokenizer, max_seq_len: int) -> list[dict]:
    """Canonical examples -> tokenized chat rows (situation as system context)."""
    rows = []
    for ex in examples:
        prompt = _prompt_text(ex)
        text = f"{prompt}\n<|im_start|>assistant\n{ex['response']}<|im_end|>"
        enc = tokenizer(text, truncation=True, max_length=max_seq_len, return_tensors="pt")
        rows.append({"input_ids": enc["input_ids"][0], "attention_mask": enc["attention_mask"][0], "labels": enc["input_ids"][0]})
    return rows


def _prompt_text(example: dict) -> str:
    from training.training.common import situation_to_prompt  # noqa: PLC0415

    return situation_to_prompt(example)


def run_torch_sft(cfg: Any) -> dict[str, Any]:
    try:
        import torch  # noqa: PLC0415
        from peft import LoraConfig, get_peft_model  # noqa: PLC0415
        from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "torch-peft backend unavailable. Install: `pip install peft` "
            "(torch and transformers are already present)."
        ) from exc

    from training.training.common import load_jsonl  # noqa: PLC0415

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    examples = load_jsonl(Path(cfg.source).resolve().parents[1] / cfg.dataset)

    tokenizer = AutoTokenizer.from_pretrained(cfg.hf_model_id or cfg.base_model)
    model = AutoModelForCausalLM.from_pretrained(cfg.hf_model_id or cfg.base_model, torch_dtype=torch.float16)
    lora = LoraConfig(
        r=int(cfg.hyperparams.get("lora_r", 16)),
        lora_alpha=int(cfg.hyperparams.get("lora_alpha", 32)),
        lora_dropout=float(cfg.hyperparams.get("lora_dropout", 0.05)),
        target_modules=cfg.hyperparams.get("target_modules"),
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora)

    dataset = _build_chat_dataset(examples, tokenizer, int(cfg.max_seq_len))
    args = TrainingArguments(
        output_dir=cfg.output_dir,
        per_device_train_batch_size=int(cfg.hyperparams.get("batch_size", 4)),
        learning_rate=float(cfg.hyperparams.get("learning_rate", 2e-4)),
        num_train_epochs=int(cfg.hyperparams.get("epochs", 3)),
        seed=cfg.seed,
        logging_steps=10,
        save_strategy="epoch",
        report_to=[],
    )
    trainer = Trainer(model=model, args=args, train_dataset=dataset)
    trainer.train()
    adapter_dir = Path(cfg.output_dir)
    adapter_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(adapter_dir))

    return {
        "task": "sft",
        "framework": "torch-peft",
        "device": device,
        "base_model": cfg.base_model,
        "adapter_path": str(adapter_dir),
        "examples_trained": len(dataset),
        "provenance": capture_provenance(cfg.base_model, cfg.dataset_version, cfg.seed, cfg.hyperparams),
        "note": "adapter saved; register + evaluate before any deployment (plan §22/§39)",
    }
