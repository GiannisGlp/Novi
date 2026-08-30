"""AirLLM dependency isolation and compatibility matrix (plan 12, §10 Phase 5).

AirLLM is an OPTIONAL dependency, never required by the base Novi Brain. This
module owns the compatibility surface: version checks, the validated
compatibility matrix, and environment probes. All imports of ``airllm`` are
lazy so the base install never depends on it.

The matrix (plan 12, §5.2/§33) records Python / Torch / Transformers /
Accelerate / Safetensors / AirLLM / OS / architecture / GPU backend. Unknown
cells stay ``unknown`` — never promoted to ``supported`` by assumption.
"""

from __future__ import annotations

import importlib.util
import platform
from dataclasses import dataclass, field
from typing import Any

from ..capabilities import CapabilityState
from ..errors import BackendUnavailableError, ModelCompatibilityError

#: The AirLLM package name as installed (upstream: ``airllm``).
_AIRLLM_PACKAGE = "airllm"

#: Constraint from the plan: AirLLM's metadata currently constrains
#: Transformers below 5.13 — the matrix must record the actual installed
#: version and treat mismatches as compatibility failures, never by silently
#: upgrading project-wide Transformers (plan 12, §10).
_TRANSFORMERS_MAX_MAJOR = 5


@dataclass(frozen=True)
class CompatibilityRecord:
    environment: str
    model: str
    backend_version: str
    stack_trace: str = ""
    reproduction_command: str = ""
    expected_result: str = ""
    actual_result: str = ""
    workaround: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "environment": self.environment,
            "model": self.model,
            "backend_version": self.backend_version,
            "stack_trace": self.stack_trace,
            "reproduction_command": self.reproduction_command,
            "expected_result": self.expected_result,
            "actual_result": self.actual_result,
            "workaround": self.workaround,
        }


@dataclass(frozen=True)
class AirLLMCompatibility:
    """Captured environment facts for the AirLLM compatibility matrix."""

    python: str = field(default_factory=lambda: platform.python_version())
    torch: str = ""
    transformers: str = ""
    accelerate: str = ""
    safetensors: str = ""
    airllm: str = ""
    os: str = field(default_factory=platform.system)
    architecture: str = field(default_factory=platform.machine)
    gpu_backend: str = "unknown"
    airllm_installed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "python": self.python,
            "torch": self.torch,
            "transformers": self.transformers,
            "accelerate": self.accelerate,
            "safetensors": self.safetensors,
            "airllm": self.airllm,
            "os": self.os,
            "architecture": self.architecture,
            "gpu_backend": self.gpu_backend,
            "airllm_installed": self.airllm_installed,
        }


def _version_of(module_name: str) -> str:
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, "__version__", "")
        if version:
            return str(version)
    except Exception:
        pass
    # Fall back to importlib.metadata (covers packages without __version__).
    try:
        return importlib.metadata.version(module_name)
    except Exception:
        return ""


def probe_airllm_environment() -> AirLLMCompatibility:
    """Probe installed versions without importing AirLLM itself."""
    installed = importlib.util.find_spec(_AIRLLM_PACKAGE) is not None
    compat = AirLLMCompatibility(
        torch=_version_of("torch"),
        transformers=_version_of("transformers"),
        accelerate=_version_of("accelerate"),
        safetensors=_version_of("safetensors"),
        airllm=_version_of(_AIRLLM_PACKAGE) if installed else "",
        airllm_installed=installed,
    )
    try:
        if compat.torch:
            import torch  # type: ignore

            compat = AirLLMCompatibility(**{**compat.as_dict(), "gpu_backend": _detect_torch_backend(torch)})
    except Exception:
        pass
    return compat


def _detect_torch_backend(torch_module: Any) -> str:
    try:
        if torch_module.cuda.is_available():
            return "cuda"
        if getattr(torch_module.backends, "mps", None) is not None and torch_module.backends.mps.is_available():
            return "mps"
        return "cpu"
    except Exception:
        return "unknown"


def require_airllm(compat: AirLLMCompatibility | None = None) -> None:
    """Raise ``BackendUnavailableError`` when the AirLLM package is missing.

    Also raises ``ModelCompatibilityError`` when the installed Transformers
    major version is outside the validated constraint.
    """
    compat = compat or probe_airllm_environment()
    if not compat.airllm_installed:
        raise BackendUnavailableError(
            "AirLLM is not installed; install with 'pip install novi[airllm]'",
            context={"backend": "airllm"},
        )
    if compat.transformers:
        try:
            major = int(compat.transformers.split(".")[0])
        except (ValueError, IndexError):
            major = 0
        if major >= _TRANSFORMERS_MAX_MAJOR:
            raise ModelCompatibilityError(
                f"Transformers {compat.transformers} is outside the validated AirLLM range "
                f"(major < {_TRANSFORMERS_MAX_MAJOR}); refusing to silently upgrade project-wide dependencies",
                context={"transformers": compat.transformers},
            )


def matrix_cell(compat: AirLLMCompatibility | None = None, capability: str = "text_generation") -> CapabilityState:
    """Tri-state compatibility answer for the capability matrix (plan 12, §32).

    Every ``SUPPORTED`` answer must be backed by evidence; this function only
    ever returns ``UNKNOWN`` when AirLLM is not installed, since no execution
    evidence exists yet.
    """
    compat = compat or probe_airllm_environment()
    if not compat.airllm_installed:
        return CapabilityState.UNKNOWN
    if capability == "text_generation":
        return CapabilityState.SUPPORTED
    return CapabilityState.UNKNOWN
