"""AirLLM compatibility surface (plan 12, §10 Phase 5, §11 Phase 6).

Everything AirLLM-specific lives here, behind the Novi inference contract.
Cognition/autonomy modules must never import this package directly — they only
ever see the ``InferenceBackend`` / ``InferenceRuntime`` abstraction.
"""

from __future__ import annotations

from .adapter import AirLLMAdapter
from .cache import CacheKey, InferenceCache, build_cache_key, context_hash
from .compatibility import (
    AirLLMCompatibility,
    CompatibilityRecord,
    architecture_compatibility,
    matrix_cell,
    probe_airllm_environment,
    require_airllm,
)
from .loader import DEFAULT_LOAD_TIMEOUT_S, AirLLMLoader, AirLLMModelHandle
from .process import WorkerConfig, WorkerMode, build_worker_command
from .shards import (
    ShardManifest,
    check_disk_capacity,
    model_dir,
    read_manifest,
    verify_shard_integrity,
    write_health,
    write_manifest,
)

__all__ = [
    "AirLLMAdapter",
    "AirLLMCompatibility",
    "AirLLMLoader",
    "AirLLMModelHandle",
    "CacheKey",
    "CompatibilityRecord",
    "DEFAULT_LOAD_TIMEOUT_S",
    "InferenceCache",
    "ShardManifest",
    "WorkerConfig",
    "WorkerMode",
    "build_cache_key",
    "build_worker_command",
    "check_disk_capacity",
    "architecture_compatibility",
    "context_hash",
    "matrix_cell",
    "model_dir",
    "probe_airllm_environment",
    "read_manifest",
    "require_airllm",
    "verify_shard_integrity",
    "write_health",
    "write_manifest",
]
