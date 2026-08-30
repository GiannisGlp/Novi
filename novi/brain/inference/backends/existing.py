"""Existing backend adapter (plan 12, Step 7 / §44 Phase 44).

Adapts the *existing* local model runtime (``MacModelProvider`` /
``ModelRuntime`` / Ollama transport) behind the ``InferenceBackend`` contract
so the runtime can serve requests through the proven local path without
AirLLM. When no transport is configured, the backend stays CI-safe: it reports
``unavailable`` for generation rather than failing loudly.
"""

from __future__ import annotations

import time
from typing import Any, Callable

from ..capabilities import BackendCapabilities, CapabilityState
from ..contracts import AbstractInferenceBackend
from ..errors import BackendUnavailableError, GenerationError, TokenizationError
from ..request import InferenceRequest
from ..response import FinishReason, InferenceResponse
from .base import ModelBackendState

_BACKEND_ID = "existing"

#: A transport is any callable that turns a prompt payload into text
#: (e.g. Ollama chat through urllib, or a MacModelProvider-compatible object
#: exposing ``invoke(payload, *, invocation_id) -> ModelResult``).
Transport = Callable[[dict[str, Any]], Any]


def _estimate_tokens(text: str) -> int:
    """Rough character/4 token estimate (no tokenizer dependency)."""
    return max(1, int(len(text or "") / 4))


class ExistingBackend(AbstractInferenceBackend):
    """Wraps the current local model runtime behind the inference contract."""

    def __init__(self, transport: Transport | None = None, *, model_id: str = "existing-local") -> None:
        self._transport = transport
        self._default_model_id = model_id
        self._state = ModelBackendState()
        self._loaded: set[str] = set()
        self._shutdown = False
        self._last_error: str = ""

    @property
    def backend_id(self) -> str:
        return _BACKEND_ID

    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            backend_id=_BACKEND_ID,
            streaming=False,
            structured_output=False,
            tool_calling=False,
            max_concurrent_requests=1,
            hardware={"cpu": CapabilityState.SUPPORTED},
        )

    def validate_model(self, model_spec: Any) -> None:
        if not getattr(model_spec, "id", None):
            raise ValueError("model_spec requires an id")

    def prepare(self, model_spec: Any) -> Any:
        return {"prepared": True, "model": getattr(model_spec, "id", "unknown"), "backend": _BACKEND_ID}

    def load(self, model_spec: Any) -> None:
        model_id = getattr(model_spec, "id", self._default_model_id)
        self._loaded.add(model_id)
        self._state.set_lifecycle(model_id, "LOADED")
        self._state.set_residency(model_id, "WARM")

    def unload(self, model_spec: Any) -> None:
        model_id = getattr(model_spec, "id", self._default_model_id)
        self._loaded.discard(model_id)
        self._state.set_lifecycle(model_id, "UNLOADED")
        self._state.set_residency(model_id, "COLD")

    def _invoke(self, request: InferenceRequest) -> Any:
        if self._transport is None:
            raise BackendUnavailableError(
                "existing backend has no configured transport (CI-safe: transport-free)",
                context={"backend": _BACKEND_ID},
            )
        prompt = self._compose_prompt(request)
        payload: dict[str, Any] = {
            "prompt": prompt,
            "messages": [dict(m) for m in request.messages],
            "system": request.system,
            "max_output_tokens": request.max_output_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "stream": request.stream,
            "request_id": request.request_id,
        }
        if hasattr(self._transport, "invoke"):
            result = self._transport.invoke(payload, invocation_id=f"inference-{request.request_id}")
            return getattr(result, "output", result)
        return self._transport(payload)

    @staticmethod
    def _compose_prompt(request: InferenceRequest) -> str:
        parts: list[str] = []
        if request.system:
            parts.append(request.system)
        for message in request.messages:
            role = str(message.get("role", "user"))
            content = str(message.get("content", ""))
            parts.append(f"{role}: {content}")
        return "\n".join(parts)

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        if self._shutdown:
            raise GenerationError("existing backend shut down", context={"backend": _BACKEND_ID})
        start = time.monotonic()
        try:
            output = self._invoke(request)
        except BackendUnavailableError:
            raise
        except Exception as exc:
            self._last_error = type(exc).__name__
            raise GenerationError(
                f"existing backend generation failed: {exc}",
                context={"backend": _BACKEND_ID, "request_id": request.request_id, "source_type": type(exc).__name__},
            ) from exc
        text = self._extract_text(output)
        if not text:
            raise TokenizationError(
                "existing backend returned no text",
                context={"backend": _BACKEND_ID, "request_id": request.request_id},
            )
        elapsed_ms = (time.monotonic() - start) * 1000.0
        output_tokens = _estimate_tokens(text)
        return InferenceResponse(
            request_id=request.request_id,
            model_id=request.model_hint or self._default_model_id,
            backend_id=_BACKEND_ID,
            trace_id=request.trace_id,
            text=text,
            finish_reason=FinishReason.STOP,
            input_tokens=_estimate_tokens(self._compose_prompt(request)),
            output_tokens=output_tokens,
            latency_ms=elapsed_ms,
            time_to_first_token_ms=elapsed_ms,
            generation_tokens_per_second=output_tokens / max(elapsed_ms / 1000.0, 0.001),
            cache_status="none",
        )

    @staticmethod
    def _extract_text(output: Any) -> str:
        if isinstance(output, str):
            return output
        if isinstance(output, dict):
            for key in ("text", "output", "content", "response"):
                value = output.get(key)
                if isinstance(value, str):
                    return value
        if hasattr(output, "output") and isinstance(output.output, str):
            return output.output
        return str(output)

    def health(self) -> dict[str, Any]:
        status = "healthy" if self._transport is not None else "unavailable"
        return {"status": status, "backend": _BACKEND_ID, "transport_configured": self._transport is not None}

    def metrics(self) -> dict[str, Any]:
        return {"backend": _BACKEND_ID, "loaded": sorted(self._loaded), "last_error": self._last_error}

    def shutdown(self) -> None:
        self._shutdown = True
        self._loaded.clear()
