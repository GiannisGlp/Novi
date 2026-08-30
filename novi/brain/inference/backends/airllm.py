"""AirLLM backend (plan 12, §11 Phase 6, §34 Phase 34).

``AirLLMBackend`` implements the ``InferenceBackend`` contract. All AirLLM
imports are lazy; without the optional dependency installed (or with
``enabled=False``) the backend reports ``unavailable`` and raises
``BackendUnavailableError`` on use. Conservative defaults (plan 12, §34):
``enabled=False`` until validated, ``compression=none``, ``delete_original=False``,
``preparation_allowed=False`` in the live runtime, ``max_concurrent_requests=1``.
"""

from __future__ import annotations

import os
from typing import Any, AsyncIterator

from ..airllm.adapter import AirLLMAdapter
from ..airllm.compatibility import probe_airllm_environment, require_airllm
from ..airllm.loader import AirLLMLoader
from ..capabilities import BackendCapabilities, CapabilityState
from ..contracts import AbstractInferenceBackend
from ..errors import BackendUnavailableError, InferenceConfigurationError
from ..request import InferenceRequest
from ..response import InferenceResponse
from .base import ModelBackendState

_BACKEND_ID = "airllm"


class AirLLMBackend(AbstractInferenceBackend):
    """Optional AirLLM backend behind the Novi inference contract."""

    def __init__(
        self,
        *,
        model_root: str | os.PathLike[str] = "",
        enabled: bool = False,
        compression: str = "none",
        prefetching: bool = False,
        delete_original: bool = False,
        preparation_allowed: bool = False,
        max_concurrent_requests: int = 1,
    ) -> None:
        if compression not in ("none", "8bit", "4bit"):
            raise InferenceConfigurationError(
                f"invalid compression mode {compression!r}; choose from none|8bit|4bit",
                context={"backend": _BACKEND_ID},
            )
        if delete_original:
            raise InferenceConfigurationError(
                "delete_original is disabled in the first adoption phase (plan 12, §14)",
                context={"backend": _BACKEND_ID},
            )
        self.enabled = bool(enabled)
        self.compression = compression
        self.prefetching = bool(prefetching)
        self.delete_original = False
        self.preparation_allowed = bool(preparation_allowed)
        self.max_concurrent_requests = max(1, int(max_concurrent_requests))
        self.model_root = str(model_root) or os.environ.get("NOVI_DATA", "") or "brain_data"
        self._state = ModelBackendState()
        self._loader: AirLLMLoader | None = None
        self._adapter: AirLLMAdapter | None = None
        self._current_model_id: str = ""
        self._shutdown = False
        self._compat = probe_airllm_environment()

    @property
    def backend_id(self) -> str:
        return _BACKEND_ID

    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            backend_id=_BACKEND_ID,
            streaming=False,  # plan 12, §21: only when safe incremental output is proven
            structured_output=False,
            tool_calling=False,
            max_concurrent_requests=self.max_concurrent_requests,
            option_keys=frozenset({"airllm_top_k"}),
            hardware={
                "cuda": CapabilityState.UNKNOWN,
                "mps": CapabilityState.UNKNOWN,
                "cpu": CapabilityState.UNKNOWN,
            },
        )

    def _ensure_enabled(self) -> None:
        if not self.enabled:
            raise BackendUnavailableError(
                "airllm backend is disabled (enabled=false until validated)",
                context={"backend": _BACKEND_ID},
            )
        require_airllm(self._compat)

    def validate_model(self, model_spec: Any) -> None:
        self._ensure_enabled()
        artifact = model_spec.resolve_backend_artifact(_BACKEND_ID)
        if not artifact.get("architecture"):
            raise InferenceConfigurationError(
                f"model {getattr(model_spec, 'id', '?')} has unresolved architecture for airllm",
                context={"backend": _BACKEND_ID},
            )

    def prepare(self, model_spec: Any) -> Any:
        self._ensure_enabled()
        if not self.preparation_allowed:
            raise BackendUnavailableError(
                "model preparation is not allowed in the live runtime (preparation_allowed=false)",
                context={"backend": _BACKEND_ID, "model": getattr(model_spec, "id", "?")},
            )
        loader = self._loader_for()
        return loader.prepare(
            model_spec,
            compression=self.compression,
            prefetching=self.prefetching,
            delete_original=self.delete_original,
        )

    def _loader_for(self) -> AirLLMLoader:
        if self._loader is None:
            self._loader = AirLLMLoader(model_root=self.model_root)
        return self._loader

    def load(self, model_spec: Any) -> None:
        self._ensure_enabled()
        loader = self._loader_for()
        handle = loader.load(model_spec)

        self._adapter = AirLLMAdapter(
            handle.model,
            handle,
            context_limit=getattr(model_spec, "context_limit", None),
        )
        self._current_model_id = handle.model_id
        self._state.set_lifecycle(handle.model_id, "LOADED")
        self._state.set_residency(handle.model_id, "WARM")

    def unload(self, model_spec: Any) -> None:
        model_id = getattr(model_spec, "id", self._current_model_id)
        self._adapter = None
        self._current_model_id = ""
        self._state.set_lifecycle(model_id, "UNLOADED")
        self._state.set_residency(model_id, "COLD")

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        self._ensure_enabled()
        if self._adapter is None:
            raise BackendUnavailableError(
                "airllm model not loaded",
                context={"backend": _BACKEND_ID, "request_id": request.request_id},
            )
        return self._adapter.generate(request)

    async def stream(self, request: InferenceRequest) -> AsyncIterator[InferenceResponse]:
        self._ensure_enabled()
        if self._adapter is None:
            raise BackendUnavailableError(
                "airllm model not loaded",
                context={"backend": _BACKEND_ID, "request_id": request.request_id},
            )
        raise self._adapter.stream(request)

    def health(self) -> dict[str, Any]:
        installed = self._compat.airllm_installed
        if not self.enabled:
            return {"status": "disabled", "backend": _BACKEND_ID, "airllm_installed": installed}
        if not installed:
            return {"status": "unavailable", "backend": _BACKEND_ID, "airllm_installed": False}
        return {
            "status": "healthy" if self._adapter is not None else "idle",
            "backend": _BACKEND_ID,
            "airllm_installed": True,
            "loaded_model": self._current_model_id,
            "compatibility": self._compat.as_dict(),
        }

    def metrics(self) -> dict[str, Any]:
        return {
            "backend": _BACKEND_ID,
            "enabled": self.enabled,
            "compression": self.compression,
            "prefetching": self.prefetching,
            "loaded_model": self._current_model_id,
            "compatibility": self._compat.as_dict(),
        }

    def shutdown(self) -> None:
        self._adapter = None
        self._current_model_id = ""
        self._shutdown = True
