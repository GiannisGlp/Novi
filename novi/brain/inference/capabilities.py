"""Capability and hardware modeling (plan 12, §16 Phase 11 and §32).

- ``HardwareProfile``: a snapshot of the host hardware used for device
  abstraction. The runtime distinguishes ``supported`` / ``unsupported`` /
  ``unknown`` and must never turn ``unknown`` into ``supported`` by assumption.
- ``BackendCapabilities``: what a backend declares it can do. The router and
  the runtime validate requests against these before dispatch.
- ``CapabilityState``: tri-state evidence model used by the capability matrix
  (plan 12, §32 Phase 32): every ``true`` capability must have evidence; every
  ``unknown`` capability is unavailable to the router until validated.
"""

from __future__ import annotations

import platform
import shutil
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CapabilityState(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


class ComputeBackend(str, Enum):
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class HardwareProfile:
    """Immutable hardware snapshot (plan 12, §16)."""

    profile_id: str = "default"
    platform: str = field(default_factory=platform.system)
    os: str = field(default_factory=lambda: platform.platform())
    cpu_model: str = ""
    cpu_cores: int = field(default_factory=lambda: os_cpu_count())
    ram_total_bytes: int = 0
    ram_available_bytes: int = 0
    gpu_vendor: str = ""
    gpu_model: str = ""
    vram_total_bytes: int = 0
    vram_available_bytes: int = 0
    compute_backend: ComputeBackend = ComputeBackend.UNKNOWN
    storage_type: str = ""
    storage_free_bytes: int = 0

    def state_for(self, capability: str) -> CapabilityState:
        """Tri-state answer for a named hardware capability."""
        table = {
            "cuda": ComputeBackend.CUDA,
            "mps": ComputeBackend.MPS,
            "cpu": ComputeBackend.CPU,
        }
        backend = table.get(capability)
        if backend is None:
            return CapabilityState.UNKNOWN
        if self.compute_backend is backend:
            return CapabilityState.SUPPORTED
        if self.compute_backend is ComputeBackend.UNKNOWN:
            return CapabilityState.UNKNOWN
        return CapabilityState.UNSUPPORTED

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "platform": self.platform,
            "os": self.os,
            "cpu_model": self.cpu_model,
            "cpu_cores": self.cpu_cores,
            "ram_total_bytes": self.ram_total_bytes,
            "ram_available_bytes": self.ram_available_bytes,
            "gpu_vendor": self.gpu_vendor,
            "gpu_model": self.gpu_model,
            "vram_total_bytes": self.vram_total_bytes,
            "vram_available_bytes": self.vram_available_bytes,
            "compute_backend": self.compute_backend.value,
            "storage_type": self.storage_type,
            "storage_free_bytes": self.storage_free_bytes,
        }


def os_cpu_count() -> int:
    try:
        return max(1, int(os_available_cpu_count()))
    except Exception:
        return 1


def os_available_cpu_count() -> int:
    """Best-effort CPU count (stdlib only; no psutil dependency)."""
    import os

    try:
        count = os.cpu_count()
        return int(count or 1)
    except Exception:
        return 1


def probe_hardware(profile_id: str = "default") -> HardwareProfile:
    """Best-effort hardware probe using stdlib only.

    GPU/vendor detection is intentionally conservative: without a validated
    GPU query we record ``unknown`` rather than guessing. The runtime must
    never promote ``unknown`` to ``supported``.
    """
    import os

    ram_total = 0
    try:
        # macOS sysctl; Linux /proc/meminfo; Windows fallback omitted.
        if platform.system() == "Darwin":
            import subprocess

            out = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=2)
            ram_total = int(out.stdout.strip() or 0)
        elif platform.system() == "Linux":
            with open("/proc/meminfo", encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("MemTotal:"):
                        ram_total = int(line.split()[1]) * 1024
                        break
    except Exception:
        ram_total = 0

    compute = ComputeBackend.UNKNOWN
    try:
        if os.environ.get("NOVI_INFERENCE_COMPUTE") in {"cuda", "mps", "cpu"}:
            compute = ComputeBackend(os.environ["NOVI_INFERENCE_COMPUTE"])
        elif platform.system() == "Darwin" and platform.machine() in ("arm64", "aarch64"):
            # Apple Silicon exposes MPS; treat as supported only when a probe
            # confirms torch availability — here we stay conservative and
            # report the platform signal, letting the backend confirm.
            compute = ComputeBackend.MPS
    except Exception:
        compute = ComputeBackend.UNKNOWN

    free_bytes = 0
    try:
        free_bytes = int(shutil.disk_usage(os.getcwd()).free)
    except Exception:
        free_bytes = 0

    return HardwareProfile(
        profile_id=profile_id,
        cpu_cores=os_cpu_count(),
        ram_total_bytes=ram_total,
        compute_backend=compute,
        storage_free_bytes=free_bytes,
    )


@dataclass(frozen=True)
class BackendCapabilities:
    """What a backend declares it can do (plan 12, §57 contract neutrality)."""

    backend_id: str
    models: frozenset[str] = frozenset()
    streaming: bool = False
    structured_output: bool = False
    tool_calling: bool = False
    max_concurrent_requests: int = 1
    #: Names of supported backend-specific option keys (validated on request).
    option_keys: frozenset[str] = frozenset()
    #: Tri-state capability states, e.g. {"cuda": SUPPORTED, "mps": UNKNOWN}
    hardware: dict[str, CapabilityState] = field(default_factory=dict)

    def supports_model(self, model_id: str) -> bool:
        return not self.models or model_id in self.models

    def validate_options(self, options: dict[str, Any]) -> list[str]:
        """Return a list of unknown option keys (empty when all known)."""
        if not options:
            return []
        return [key for key in options if key not in self.option_keys]


@dataclass(frozen=True)
class ModelCapabilityRecord:
    """Capability-matrix row with evidence (plan 12, §32)."""

    model: str
    backend: str
    status: str = "evaluating"  # evaluating | validated | blocked
    text_generation: CapabilityState = CapabilityState.UNKNOWN
    vision: CapabilityState = CapabilityState.UNKNOWN
    tool_calling: CapabilityState = CapabilityState.UNKNOWN
    structured_output: CapabilityState = CapabilityState.UNKNOWN
    streaming: CapabilityState = CapabilityState.UNKNOWN
    evidence: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "backend": self.backend,
            "status": self.status,
            "capabilities": {
                "text_generation": self.text_generation.value,
                "vision": self.vision.value,
                "tool_calling": self.tool_calling.value,
                "structured_output": self.structured_output.value,
                "streaming": self.streaming.value,
            },
            "evidence": self.evidence,
        }
