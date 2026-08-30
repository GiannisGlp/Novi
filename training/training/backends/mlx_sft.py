"""MLX-LM LoRA SFT backend (plan 23 §32, first experiment).

Requires `mlx-lm` (not installed in the audit venv — Python 3.14 lacks mlx
wheels; a 3.11/3.12 venv is the intended home). Code follows the standard
mlx-lm LoRA workflow; the exact API is version-sensitive, so failures raise
with the install/version guidance instead of guessing.

EXPERIMENTAL — validated on the first real training run.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from training.config import capture_provenance


def run_mlx_sft(cfg: Any) -> dict[str, Any]:
    try:
        from mlx_lm import load  # noqa: PLC0415
        from mlx_lm.lora import train as lora_train  # noqa: PLC0415
        from mlx_lm.utils import save_adapter  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "mlx-lm backend unavailable. Install in a Python 3.11/3.12 venv: "
            "`pip install mlx mlx-lm` (mlx has no 3.14 wheels yet)."
        ) from exc
    model, tokenizer = load(cfg.hf_model_id or cfg.base_model)
    dataset_path = str(Path(cfg.source).resolve().parents[1] / cfg.dataset)

    # mlx-lm LoRA: text -> 'train'/'valid' jsonl with {"text": ...} rows.
    # The canonical examples are converted to SFT text beforehand by the
    # caller (train_sft._build_rows) — see training/training/common.py.
    # NOTE: mlx-lm's lora_train signature varies by release; epochs/steps are
    # passed explicitly at run time. The adapter output lands in cfg.output_dir.
    adapter_dir = Path(cfg.output_dir)
    adapter_dir.mkdir(parents=True, exist_ok=True)
    lora_train(
        model=model,
        tokenizer=tokenizer,
        train_batch_size=int(cfg.hyperparams.get("batch_size", 4)),
        learning_rate=float(cfg.hyperparams.get("learning_rate", 2e-4)),
        num_layers=int(cfg.hyperparams.get("lora_r", 16)),
        adapter_path=str(adapter_dir),
        data=dataset_path,
        seed=cfg.seed,
    )
    save_adapter(adapter_dir, model)

    return {
        "task": "sft",
        "framework": "mlx",
        "base_model": cfg.base_model,
        "adapter_path": str(adapter_dir),
        "provenance": capture_provenance(cfg.base_model, cfg.dataset_version, cfg.seed, cfg.hyperparams),
        "note": "adapter saved; run training/training/evaluate.py --candidate-dir <dir> to compare vs baseline",
    }
