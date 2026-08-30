"""Training configuration loading + provenance (plan 23 §31).

Every training run is governed by a committed, deterministic YAML config
(`training/configs/`) and records full provenance: base model, training code
commit, dataset version, hyperparameters, hardware, random seed, framework.
No training run may start without a config; no checkpoint may be registered
without its provenance (plan §22, §31).
"""

from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ALLOWED_KINDS = ("sft", "dpo", "retrieval", "grounding", "policy", "evaluation")

_REQUIRED_KEYS = ("kind", "base_model", "dataset", "dataset_version", "seed")


@dataclass(frozen=True)
class TrainConfig:
    kind: str
    base_model: str
    dataset: str
    dataset_version: str
    seed: int
    output_dir: str = "training/models/adapters"
    min_examples: int = 0
    max_seq_len: int = 2048
    eval_after: bool = False
    hf_model_id: str = ""
    hyperparams: dict[str, Any] = field(default_factory=dict)
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind, "base_model": self.base_model, "hf_model_id": self.hf_model_id,
            "dataset": self.dataset, "dataset_version": self.dataset_version,
            "seed": self.seed, "output_dir": self.output_dir, "min_examples": self.min_examples,
            "max_seq_len": self.max_seq_len, "eval_after": self.eval_after,
            "hyperparams": dict(self.hyperparams), "source": self.source,
        }


def load_config(path: str | Path) -> TrainConfig:
    """Load and validate a committed training config."""
    p = Path(path)
    raw = yaml.safe_load(p.read_text()) or {}
    for key in _REQUIRED_KEYS:
        if key not in raw:
            raise ValueError(f"config {p.name}: missing required key {key!r}")
    if raw["kind"] not in ALLOWED_KINDS:
        raise ValueError(f"config {p.name}: unknown kind {raw['kind']!r}")
    if not isinstance(raw["seed"], int):
        raise ValueError(f"config {p.name}: seed must be an int")
    return TrainConfig(
        kind=raw["kind"],
        base_model=str(raw["base_model"]),
        dataset=str(raw["dataset"]),
        dataset_version=str(raw["dataset_version"]),
        seed=int(raw["seed"]),
        output_dir=str(raw.get("output_dir", "training/models/adapters")),
        min_examples=int(raw.get("min_examples", 0)),
        max_seq_len=int(raw.get("max_seq_len", 2048)),
        eval_after=bool(raw.get("eval_after", False)),
        hf_model_id=str(raw.get("hf_model_id", "")),
        hyperparams=dict(raw.get("hyperparams") or {}),
        source=str(p.resolve()),
    )


def detect_framework() -> str:
    """Detect the available training backend (plan §31 audit result)."""
    import importlib.util

    if importlib.util.find_spec("mlx_lm"):
        return "mlx"
    if importlib.util.find_spec("peft") and importlib.util.find_spec("transformers"):
        return "torch-peft"
    if importlib.util.find_spec("transformers"):
        return "transformers-only"  # peft missing: real LoRA training unavailable
    return "none"


def hardware_description() -> str:
    try:
        mem_gb = round(
            int(open("/proc/meminfo").read().splitlines()[0].split()[1]) / 1024 / 1024, 1  # noqa: SIM115
        )
    except (OSError, IndexError, ValueError):
        import subprocess as sp

        mem_gb = round(float(sp.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout or 0) / 1e9, 1)
    return f"{platform.system()} {platform.machine()} {mem_gb}GB"


def git_head(repo_root: str | Path | None = None) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=repo_root
        )
        return out.stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def capture_provenance(base_model: str, dataset_version: str, seed: int = 0,
                       hyperparams: dict[str, Any] | None = None,
                       repo_root: str | Path | None = None) -> dict[str, Any]:
    """Deterministic provenance record for a training run (plan §31/§22)."""
    return {
        "base_model": base_model,
        "training_commit": git_head(repo_root),
        "dataset_version": dataset_version,
        "hyperparameters": dict(hyperparams or {}),
        "hardware": hardware_description(),
        "random_seed": int(seed),
        "framework": detect_framework(),
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
