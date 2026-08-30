"""Model registry + manifests (plan 23 §22, step 25; §29).

Every adapter gets a named manifest with full provenance. Status lifecycle:
candidate -> staged -> active, with rejected/retired/rolled_back terminal-ish
states. "Never deploy an unnamed checkpoint" (§22) is enforced structurally:
registration requires a model_id matching the `novi-<base>-<kind>-v<N>` scheme.

Schema-version compatibility (§29): a model declares which context/memory/
world/dialogue schemas it expects; the runtime must refuse incompatible
combinations or apply an explicit migration.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from training.schemas import SCHEMA_VERSIONS

STATUSES = ("candidate", "staged", "active", "retired", "rolled_back", "rejected")

# Lifecycle edges (deterministic; no skipping).
_TRANSITIONS: dict[str, frozenset[str]] = {
    "candidate": frozenset({"staged", "rejected"}),
    "staged": frozenset({"active", "rejected", "candidate"}),
    "active": frozenset({"retired", "rolled_back"}),
    "retired": frozenset(),
    "rolled_back": frozenset({"candidate"}),
    "rejected": frozenset(),
}

_MODEL_ID_RE = re.compile(r"^novi-[a-z0-9-]+-v\d+$")

_REQUIRED_FIELDS = (
    "model_id", "base_model", "adapter_type", "training_dataset", "training_commit",
    "training_config", "created_at", "evaluation_suite", "metrics", "status",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_manifest(
    base_model: str,
    training_dataset: str,
    training_config: str,
    training_commit: str = "",
    evaluation_suite: str = "social-v1",
    metrics: dict[str, float] | None = None,
    adapter_type: str = "lora",
    model_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Construct a complete manifest (plan §22)."""
    from training.config import git_head  # noqa: PLC0415

    kind = training_config.split("-")[0] if "-" in training_config else training_config
    base_slug = base_model.replace(":", "-").replace(".", "")
    model_id = model_id or f"novi-{base_slug}-{kind}-v1"
    manifest = {
        "model_id": model_id,
        "base_model": base_model,
        "adapter_type": adapter_type,
        "training_dataset": training_dataset,
        "training_commit": training_commit or git_head(),
        "training_config": training_config,
        "created_at": created_at or utc_now_iso(),
        "evaluation_suite": evaluation_suite,
        "metrics": dict(metrics or {}),
        "status": "candidate",
        "context_schema": SCHEMA_VERSIONS["context"],
        "memory_schema": SCHEMA_VERSIONS["memory"],
        "world_schema": SCHEMA_VERSIONS["world"],
        "dialogue_schema": SCHEMA_VERSIONS["dialogue"],
    }
    return manifest


def compatible_schemas(manifest: dict[str, Any]) -> list[str]:
    """§29: declared schema versions vs the runtime's current schemas."""
    errors: list[str] = []
    for key, expected in SCHEMA_VERSIONS.items():
        declared = manifest.get(f"{key}_schema")
        if declared != expected:
            errors.append(
                f"{key}_schema: manifest declares {declared}, runtime requires {expected} "
                "(refuse or apply explicit migration)"
            )
    return errors


class ModelRegistry:
    """Filesystem-backed registry of named adapter manifests."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, model_id: str) -> Path:
        return self.root / f"{model_id}.json"

    def register(self, manifest: dict[str, Any]) -> Path:
        model_id = manifest.get("model_id", "")
        if not model_id or not _MODEL_ID_RE.match(model_id):
            raise ValueError(
                f"refusing unnamed checkpoint: model_id must match novi-<base>-<kind>-v<N> "
                f"(plan §22: never deploy an unnamed checkpoint), got {model_id!r}"
            )
        for field in _REQUIRED_FIELDS:
            if field not in manifest:
                raise ValueError(f"manifest {model_id}: missing required field {field!r}")
        if manifest.get("status") not in STATUSES:
            raise ValueError(f"manifest {model_id}: unknown status {manifest.get('status')!r}")
        path = self._path(model_id)
        if path.exists():
            raise ValueError(f"manifest {model_id}: already registered (refuse silent overwrite)")
        path.write_text(json.dumps(manifest, indent=2) + "\n")
        return path

    def get(self, model_id: str) -> dict[str, Any]:
        path = self._path(model_id)
        if not path.exists():
            raise KeyError(f"no manifest for {model_id!r}")
        return json.loads(path.read_text())

    def list(self) -> list[dict[str, Any]]:
        out = []
        for path in sorted(self.root.glob("*.json")):
            out.append(json.loads(path.read_text()))
        return out

    def set_status(self, model_id: str, status: str) -> dict[str, Any]:
        if status not in STATUSES:
            raise ValueError(f"unknown status {status!r}")
        manifest = self.get(model_id)
        current = manifest["status"]
        if status not in _TRANSITIONS[current]:
            raise ValueError(f"invalid transition {current} -> {status}")
        manifest["status"] = status
        self._path(model_id).write_text(json.dumps(manifest, indent=2) + "\n")
        return manifest
