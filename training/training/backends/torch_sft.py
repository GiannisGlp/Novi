"""Transformers+Peft LoRA SFT backend (plan 23 §32, first experiment).

Requires `peft` (missing in the audit venv: torch 2.13 + transformers are
present, peft is not — `pip install peft`). Standard causal-LM SFT with a
LoRA adapter; MPS is available on this Mac (torch 2.13, mps: True).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from training.config import capture_provenance


_IM_START = "<|im_start|>"
_IM_END = "<|im_end|>"


def _chatml_prompt(example: dict) -> str:
    """Production-shaped ChatML prompt (system + user + assistant header).

    The system carries the persona + cognitive-state block; the user carries the
    real utterance — the same roles the brain sends in production, so the
    adapter learns to talk like a human against the real prompt shape.
    """
    from training.training.common import render_chatml  # noqa: PLC0415

    system, user = render_chatml(example)
    return (
        f"{_IM_START}system\n{system}{_IM_END}\n"
        f"{_IM_START}user\n{user}{_IM_END}\n"
        f"{_IM_START}assistant\n"
    )


def _has_user_utterance(example: dict) -> bool:
    from training.training.common import user_utterance  # noqa: PLC0415

    return bool(user_utterance(example))


def _training_text(example: dict) -> str:
    """The complete SFT text (prompt + assistant response + im_end).

    ChatML for rows with a real user utterance; legacy flat-prompt suffix for
    rows without one.
    """
    response = example.get("preferred_response") or example.get("response") or ""
    prompt = _prompt_text(example)
    if _has_user_utterance(example):
        return f"{prompt}{response}{_IM_END}"
    return f"{prompt}\n{_IM_START}assistant\n{response}{_IM_END}"


def _build_chat_dataset(examples: list[dict], tokenizer, max_seq_len: int) -> list[dict]:
    """Canonical examples -> tokenized chat rows.

    Rows with a real user utterance use explicit ChatML roles (system/user/
    assistant) matching production; legacy rows with no user text keep the
    historical flat-prompt shape so ``sft_v1.jsonl`` still trains unchanged.
    Labels mask everything before the assistant response.
    """
    rows = []
    for ex in examples:
        prompt = _prompt_text(ex)
        text = _training_text(ex)
        enc_prompt = tokenizer(prompt, truncation=True, max_length=max_seq_len, return_tensors="pt")
        enc_full = tokenizer(text, truncation=True, max_length=max_seq_len, return_tensors="pt")
        labels = enc_full["input_ids"][0].clone()
        labels[: enc_prompt["input_ids"].shape[1]] = -100
        rows.append({
            "input_ids": enc_full["input_ids"][0],
            "attention_mask": enc_full["attention_mask"][0],
            "labels": labels,
        })
    return rows


def _prompt_text(example: dict) -> str:
    if _has_user_utterance(example):
        return _chatml_prompt(example)
    from training.training.common import prompt_for  # noqa: PLC0415

    return prompt_for(example)


def run_torch_sft(cfg: Any) -> dict[str, Any]:
    try:
        import torch  # noqa: PLC0415
        from peft import LoraConfig, get_peft_model  # noqa: PLC0415
        from transformers import (  # noqa: PLC0415
            AutoModelForCausalLM,
            AutoTokenizer,
            DataCollatorForSeq2Seq,
            Trainer,
            TrainingArguments,
        )
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "torch-peft backend unavailable. Install: `pip install peft` "
            "(torch and transformers are already present)."
        ) from exc

    from training.training.common import load_jsonl  # noqa: PLC0415

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    repo_root = Path(cfg.source).resolve().parents[2]
    examples = load_jsonl(repo_root / cfg.dataset)

    # Dedicated adapter directory per run (kept separate from scorer artifacts).
    # The adapter name comes from the config (e.g. novi-qwen3-8b-emotional-v1);
    # the plan-23 default is preserved for the first experiment.
    run_dir = Path(cfg.output_dir) / (cfg.adapter_name or "novi-qwen3-8b-dialogue-v1")
    run_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(cfg.hf_model_id or cfg.base_model)
    model = AutoModelForCausalLM.from_pretrained(
        cfg.hf_model_id or cfg.base_model, torch_dtype=torch.float16
    )
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
        output_dir=str(run_dir),
        per_device_train_batch_size=int(cfg.hyperparams.get("batch_size", 4)),
        learning_rate=float(cfg.hyperparams.get("learning_rate", 2e-4)),
        num_train_epochs=int(cfg.hyperparams.get("epochs", 3)),
        seed=cfg.seed,
        logging_steps=10,
        save_strategy="epoch",
        report_to=[],
    )
    trainer = Trainer(
        model=model, args=args, train_dataset=dataset,
        data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, padding=True, label_pad_token_id=-100),
    )
    trainer.train()
    trainer.save_model(str(run_dir))

    return {
        "task": "sft",
        "framework": "torch-peft",
        "device": device,
        "base_model": cfg.base_model,
        "adapter_path": str(run_dir),
        "examples_trained": len(dataset),
        "provenance": capture_provenance(cfg.base_model, cfg.dataset_version, cfg.seed, cfg.hyperparams),
        "note": "adapter saved; register + evaluate before any deployment (plan §22/§39)",
    }
