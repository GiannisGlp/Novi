"""AirLLM adapter (plan 12, §11 Phase 6).

Responsible ONLY for: resolving the canonical artifact, validating the
architecture, creating/loading the AirLLM model, configuring shard dir /
compression / prefetching, tokenizing, generating, decoding, translating
errors, collecting telemetry, and unloading resources cleanly.

The adapter must NOT contain goal logic, planning logic, memory semantics,
safety decisions, autonomy state transitions, relationship logic, or action
authorization (plan 12, §11).
"""

from __future__ import annotations

import time
from typing import Any, AsyncIterator

from ..errors import (
    BackendProtocolError,
    ContextLimitError,
    GenerationError,
    InferenceError,
    ModelCompatibilityError,
    TokenizationError,
)
from ..request import InferenceRequest
from ..response import FinishReason, InferenceResponse
from .loader import AirLLMModelHandle


class AirLLMAdapter:
    """Translates between the Novi inference contract and AirLLM calls."""

    def __init__(self, model: Any, handle: AirLLMModelHandle, *, context_limit: int | None = None) -> None:
        self.model = model
        self.handle = handle
        self._context_limit_value = context_limit

    # ------------------------------------------------------------- generation
    def generate(self, request: InferenceRequest) -> InferenceResponse:
        """Execute generation, translating every AirLLM error to a Novi error.

        The backend guarantees AirLLM is installed and the model loaded before
        an adapter is created; this method does not re-check installation so
        the adapter stays testable with a fake model.
        """
        if not request.messages and not request.system:
            raise GenerationError(
                "empty request: no messages and no system prompt", context={"request_id": request.request_id}
            )

        prompt = self._compose_prompt(request)
        context_limit = self._context_limit()
        if context_limit and len(prompt) > context_limit:
            raise ContextLimitError(
                f"input exceeds context limit {context_limit}",
                context={"request_id": request.request_id, "context_limit": context_limit, "input_chars": len(prompt)},
            )

        start = time.monotonic()
        try:
            output = self.model.generate(prompt, max_new_tokens=request.max_output_tokens, top_k=request.top_k or 1)
        except InferenceError:
            raise
        except Exception as exc:
            raise self._translate(exc, request) from exc

        text = self._decode(output, request)
        elapsed_ms = (time.monotonic() - start) * 1000.0
        output_tokens = self._count_tokens(text)
        return InferenceResponse(
            request_id=request.request_id,
            model_id=self.handle.model_id,
            backend_id="airllm",
            trace_id=request.trace_id,
            text=text,
            finish_reason=FinishReason.STOP,
            input_tokens=self._count_tokens(prompt),
            output_tokens=output_tokens,
            latency_ms=elapsed_ms,
            time_to_first_token_ms=elapsed_ms,
            generation_tokens_per_second=output_tokens / max(elapsed_ms / 1000.0, 0.001),
            cache_status="none",
            hardware_profile_id=self.handle.manifest.validation_hardware if self.handle.manifest else "",
            provider_metadata={"revision": self.handle.revision, "airllm": True},
        )

    def stream(self, request: InferenceRequest) -> AsyncIterator[InferenceResponse]:
        """Streaming is unsupported until AirLLM's incremental output is proven
        safe (plan 12, §21 Phase 21) — raise a typed protocol error."""
        raise BackendProtocolError(
            "airllm streaming not supported until incremental output is validated",
            context={"backend": "airllm"},
        )

    # ---------------------------------------------------------------- helpers
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

    def _context_limit(self) -> int | None:
        return self._context_limit_value

    @staticmethod
    def _count_tokens(text: str) -> int:
        return max(1, int(len(text or "") / 4))

    @staticmethod
    def _decode(output: Any, request: InferenceRequest) -> str:
        if isinstance(output, str):
            return output
        if isinstance(output, list):
            return "".join(str(t) for t in output)
        if isinstance(output, dict):
            for key in ("text", "output", "generated_text"):
                value = output.get(key)
                if isinstance(value, str):
                    return value
            raise BackendProtocolError(
                "unexpected AirLLM output shape",
                context={"request_id": request.request_id, "keys": sorted(output.keys())},
            )
        try:
            text = str(output)
        except Exception as exc:
            raise TokenizationError(
                f"cannot decode AirLLM output: {exc}",
                context={"request_id": request.request_id},
            ) from exc
        return text

    @staticmethod
    def _translate(exc: BaseException, request: InferenceRequest) -> InferenceError:
        """Translate an AirLLM exception into a typed Novi error (never leak)."""
        from ..errors import BackendInitializationError, OutOfMemoryError, classify_backend_exception

        name = type(exc).__name__
        message = str(exc)
        context = {"request_id": request.request_id, "source_type": name}
        lowered = f"{name} {message}".lower()
        if "memory" in lowered or "cuda out of memory" in lowered or "oom" in lowered:
            return OutOfMemoryError(message, context=context)
        if "tokenizer" in lowered:
            return TokenizationError(message, context=context)
        if "architecture" in lowered or "not supported" in lowered:
            return ModelCompatibilityError(message, context=context)
        if "initialization" in lowered or "load" in lowered:
            return BackendInitializationError(message, context=context)
        return classify_backend_exception(exc)
