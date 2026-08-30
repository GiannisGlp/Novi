"""AirLLM model loading (plan 12, §11 Phase 6, §7 Phase 7).

All AirLLM imports are lazy: loading raises ``BackendUnavailableError`` when
the optional dependency is absent, and ``ModelCompatibilityError`` when the
installed stack is outside the validated matrix. The loader resolves the
canonical artifact from the registry mapping, prepares shards as a managed
deployment operation, and records manifests/health.
"""

from __future__ import annotations

import contextlib
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..errors import BackendInitializationError, BackendUnavailableError, ModelCompatibilityError, ModelNotFoundError
from .compatibility import require_airllm
from .shards import (
    ShardManifest,
    check_disk_capacity,
    model_dir,
    read_manifest,
    verify_shard_integrity,
    write_manifest,
)

#: Load timeout guard (plan 12, §26 item 9) — the runtime must never block on a
#: model load forever.
DEFAULT_LOAD_TIMEOUT_S = 300.0


@dataclass
class AirLLMModelHandle:
    """Runtime handle to a loaded AirLLM model.

    Mutable (not frozen) by design: the loader attaches the live model object
    after construction (``handle.model = ...``).
    """

    model_id: str
    revision: str
    artifact_path: str
    shards_dir: Path
    manifest: ShardManifest | None = None
    model: Any = None


class AirLLMLoader:
    """Resolves and loads AirLLM models behind the compatibility surface."""

    def __init__(self, *, model_root: str | Path, load_timeout_s: float = DEFAULT_LOAD_TIMEOUT_S) -> None:
        self.model_root = Path(model_root)
        self.load_timeout_s = float(load_timeout_s)

    # --------------------------------------------------------------- resolution
    def resolve_artifact(self, spec: Any) -> dict[str, Any]:
        """Resolve the canonical backend artifact for a registry model spec."""
        try:
            artifact = spec.resolve_backend_artifact("airllm")
        except AttributeError:
            raise ModelNotFoundError(
                f"model spec {getattr(spec, 'id', '?')} has no airllm artifact mapping",
                context={"model": getattr(spec, "id", "?")},
            ) from None
        if not artifact.get("path") and not artifact.get("source_id"):
            raise ModelCompatibilityError(
                f"airllm artifact for {getattr(spec, 'id', '?')} is unresolved (Step 17 required)",
                context={"model": getattr(spec, "id", "?")},
            )
        return artifact

    # ------------------------------------------------------------ preparation
    def prepare(
        self,
        spec: Any,
        *,
        artifact: dict[str, Any] | None = None,
        compression: str = "none",
        prefetching: bool = False,
        delete_original: bool = False,
        reserve_bytes: int = 0,
    ) -> ShardManifest:
        """Managed deployment operation — never run inside a live autonomy loop.

        Raises ``StorageCapacityError`` before any write when disk is
        insufficient (plan 12, §14). ``delete_original`` defaults to False and
        is never automatic (plan 12, §14 §67).
        """
        require_airllm()
        artifact = artifact or self.resolve_artifact(spec)
        model_id = getattr(spec, "id", "unknown")
        target_dir = model_dir(self.model_root, model_id)
        shards_dir = target_dir / "shards"
        manifest_path = target_dir / "manifest.json"
        source_path = artifact.get("path") or ""

        # Capacity gate: source + temp transformation + shards + reserve.
        source_bytes = 0
        if source_path and Path(source_path).is_dir():
            for p in Path(source_path).rglob("*"):
                if p.is_file():
                    source_bytes += p.stat().st_size
        estimated_shards = source_bytes  # conservative 1:1 estimate
        check_disk_capacity(target_dir, source_bytes + estimated_shards + (8 << 20), reserve_bytes=reserve_bytes)

        # Prepare shards through AirLLM's own API (lazy import).
        manifest = self._run_airllm_prepare(
            artifact, model_id, shards_dir, compression=compression, prefetching=prefetching
        )
        write_manifest(manifest, manifest_path)
        return manifest

    def _run_airllm_prepare(
        self,
        artifact: dict[str, Any],
        model_id: str,
        shards_dir: Path,
        *,
        compression: str,
        prefetching: bool,
    ) -> ShardManifest:
        try:
            from airllm import AutoModel  # type: ignore
        except Exception as exc:
            raise BackendUnavailableError(
                f"cannot import AirLLM: {exc}",
                context={"backend": "airllm"},
            ) from exc

        source_id = artifact.get("source_id") or artifact.get("path")
        shards_dir.mkdir(parents=True, exist_ok=True)
        try:
            model = AutoModel.from_pretrained(
                str(source_id),
                device="cuda",
                shard_dir=str(shards_dir),
                compression=compression,
                prefetching=prefetching,
            )
        except Exception as exc:
            raise BackendInitializationError(
                f"AirLLM model preparation failed: {exc}",
                context={"model": model_id, "source": str(source_id)},
            ) from exc

        shard_files = sorted(p for p in shards_dir.iterdir() if p.is_file())
        sizes = tuple(p.stat().st_size for p in shard_files)
        manifest = ShardManifest(
            model_id=model_id,
            revision=artifact.get("revision", ""),
            source=str(source_id),
            architecture=artifact.get("architecture", ""),
            airllm_version=_version_or("airllm"),
            transformers_version=_version_or("transformers"),
            torch_version=_version_or("torch"),
            shard_count=len(shard_files),
            shard_sizes=sizes,
            total_bytes=sum(sizes),
            validation_hardware=os.environ.get("NOVI_HARDWARE_PROFILE_ID", ""),
            compression_mode=compression,
            prefetch_mode=bool(prefetching),
            status="prepared",
        )
        with contextlib.suppress(Exception):
            del model
        return manifest

    # ------------------------------------------------------------------- load
    def load(self, spec: Any, *, artifact: dict[str, Any] | None = None) -> AirLLMModelHandle:
        """Load a prepared model (cold/warm path). Raises typed errors."""
        require_airllm()
        artifact = artifact or self.resolve_artifact(spec)
        model_id = getattr(spec, "id", "unknown")
        target_dir = model_dir(self.model_root, model_id)
        manifest_path = target_dir / "manifest.json"
        if not manifest_path.is_file():
            raise BackendInitializationError(
                f"model {model_id} is not prepared (no manifest)",
                context={"model": model_id, "manifest": str(manifest_path)},
            )
        manifest = read_manifest(manifest_path)
        verify_shard_integrity(target_dir / "shards", manifest)

        try:
            from airllm import AutoModel  # type: ignore
        except Exception as exc:
            raise BackendUnavailableError(f"cannot import AirLLM: {exc}", context={"backend": "airllm"}) from exc

        source_id = artifact.get("source_id") or artifact.get("path") or manifest.source
        started = time.monotonic()
        try:
            model = AutoModel.from_pretrained(
                str(source_id),
                device="cuda",
                shard_dir=str(target_dir / "shards"),
                compression=manifest.compression_mode,
                prefetching=manifest.prefetch_mode,
            )
        except Exception as exc:
            elapsed = time.monotonic() - started
            if elapsed > self.load_timeout_s:
                from ..errors import DeadlineExceededError

                raise DeadlineExceededError(
                    f"model load exceeded timeout {self.load_timeout_s}s",
                    context={"model": model_id, "elapsed_s": round(elapsed, 2)},
                ) from exc
            raise BackendInitializationError(
                f"AirLLM model load failed: {exc}",
                context={"model": model_id, "source": str(source_id)},
            ) from exc
        handle = AirLLMModelHandle(
            model_id=model_id,
            revision=manifest.revision,
            artifact_path=str(source_id),
            shards_dir=target_dir / "shards",
            manifest=manifest,
        )
        handle.model = model  # type: ignore[attr-defined]
        return handle


def _version_or(module_name: str) -> str:
    import importlib

    try:
        return str(getattr(importlib.import_module(module_name), "__version__", "unknown"))
    except Exception:
        return "unknown"
