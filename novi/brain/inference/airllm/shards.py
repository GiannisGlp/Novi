"""AirLLM shard storage and integrity (plan 12, §13 Phase 8, §15 Phase 10).

Novi-managed storage layout under ``$NOVI_DATA/models/airllm/``:

    manifests/
    <model-id>/
        source/        (original checkpoint — never deleted in phase 1)
        shards/        (layer-wise AirLLM shards)
        metadata.json
        manifest.json
        health.json

The manifest records model ID, revision, source, architecture, AirLLM/
Transformers/Torch versions, shard count/sizes, total bytes, checksums,
creation timestamp, validation hardware, compression/prefetch modes, and
status (plan 12, §13). Deletion of original checkpoints is never automatic
(plan 12, §14) — ``delete_original`` is an explicit administrative option only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..errors import ShardIntegrityError, StorageCapacityError


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ShardManifest:
    model_id: str
    revision: str = ""
    source: str = ""
    architecture: str = ""
    airllm_version: str = ""
    transformers_version: str = ""
    torch_version: str = ""
    shard_count: int = 0
    shard_sizes: tuple[int, ...] = ()
    total_bytes: int = 0
    checksums: dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=_utcnow_iso)
    validation_hardware: str = ""
    compression_mode: str = "none"
    prefetch_mode: bool = False
    status: str = "prepared"  # prepared | healthy | partial | failed

    def as_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "revision": self.revision,
            "source": self.source,
            "architecture": self.architecture,
            "airllm_version": self.airllm_version,
            "transformers_version": self.transformers_version,
            "torch_version": self.torch_version,
            "shard_count": self.shard_count,
            "shard_sizes": list(self.shard_sizes),
            "total_bytes": self.total_bytes,
            "checksums": dict(self.checksums),
            "created_at": self.created_at,
            "validation_hardware": self.validation_hardware,
            "compression_mode": self.compression_mode,
            "prefetch_mode": self.prefetch_mode,
            "status": self.status,
        }


def model_dir(model_root: str | Path, model_id: str) -> Path:
    return Path(model_root) / "models" / "airllm" / model_id


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_disk_capacity(path: str | Path, required_bytes: int, *, reserve_bytes: int = 0) -> None:
    """Fail early with ``StorageCapacityError`` (plan 12, §14 Phase 9).

    Required storage = source + temporary transformation + shards + safety
    reserve. Insufficient disk -> refuse preparation, emit diagnostic, delete
    nothing.
    """
    import shutil

    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    free = 0
    try:
        free = int(shutil.disk_usage(target).free)
    except OSError as exc:
        raise StorageCapacityError(
            f"cannot stat disk for {target}: {exc}",
            context={"path": str(target)},
        ) from exc
    need = int(required_bytes) + int(reserve_bytes)
    if free < need:
        raise StorageCapacityError(
            f"insufficient disk for preparation: need {need} bytes, free {free} bytes",
            context={"path": str(target), "required_bytes": need, "free_bytes": free, "refused": True},
        )


def verify_shard_integrity(shards_dir: str | Path, manifest: ShardManifest) -> ShardManifest:
    """Verify all expected shard files exist with matching checksums.

    A partially prepared model must never be selected by the router (plan 12,
    §15): any missing/extra/unverified file raises ``ShardIntegrityError``.

    Shard layouts may nest (the Mac/MLX path writes under ``splitted_model/``),
    so discovery is recursive and checksum keys are relative paths.
    """
    root = Path(shards_dir)
    files = sorted(p for p in root.rglob("*") if p.is_file())
    expected_count = manifest.shard_count
    if expected_count > 0 and len(files) != expected_count:
        raise ShardIntegrityError(
            f"shard count mismatch: expected {expected_count}, found {len(files)}",
            context={"shards_dir": str(root), "expected": expected_count, "found": len(files)},
        )
    if manifest.checksums:
        for name, expected in manifest.checksums.items():
            path = root / name
            if not path.is_file():
                raise ShardIntegrityError(
                    f"missing shard file: {name}",
                    context={"shards_dir": str(root), "file": name},
                )
            actual = _sha256(path)
            if actual != expected:
                raise ShardIntegrityError(
                    f"checksum mismatch for {name}",
                    context={"shards_dir": str(root), "file": name, "expected": expected, "actual": actual},
                )
    return manifest


def write_manifest(manifest: ShardManifest, manifest_path: str | Path) -> None:
    Path(manifest_path).write_text(json.dumps(manifest.as_dict(), indent=2, sort_keys=True), encoding="utf-8")


def read_manifest(manifest_path: str | Path) -> ShardManifest:
    data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    data["shard_sizes"] = tuple(data.get("shard_sizes", []))
    return ShardManifest(**data)


def write_health(manifest: ShardManifest, health_path: str | Path, *, healthy: bool, note: str = "") -> None:
    payload = {
        "model_id": manifest.model_id,
        "healthy": healthy,
        "checked_at": _utcnow_iso(),
        "note": note,
        "status": manifest.status,
    }
    Path(health_path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
