"""Inference response contract (plan 12, §6.3).

``InferenceResponse`` is the single typed, backend-neutral response contract.
Required fields are always populated; optional structured fields
(``tool_calls``, ``reasoning_metadata``, ``structured_output``,
``provider_metadata``) are present only when the backend/model produced them.

``provider_metadata`` must be treated as diagnostic data, never as truth —
cognition may not base decisions on it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class FinishReason(str):
    """Stable finish reasons for Novi inference responses."""

    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CANCELLED = "cancelled"
    ERROR = "error"
    DEADLINE = "deadline"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class InferenceResponse:
    """A backend-neutral inference response (plan 12, §6.3)."""

    # identity
    request_id: str
    model_id: str
    backend_id: str
    trace_id: str = ""

    # content
    text: str = ""
    finish_reason: str = FinishReason.STOP

    # token accounting
    input_tokens: int = 0
    output_tokens: int = 0

    # timing
    latency_ms: float = 0.0
    time_to_first_token_ms: float = 0.0
    generation_tokens_per_second: float = 0.0

    # provenance
    cache_status: str = "none"  # none | cold | warm | hit
    hardware_profile_id: str = ""

    # warnings / diagnostics
    warnings: list[str] = field(default_factory=list)

    # optional structured payloads (validated downstream, never trusted raw)
    tool_calls: list[dict[str, Any]] | None = None
    reasoning_metadata: dict[str, Any] | None = None
    structured_output: dict[str, Any] | None = None
    provider_metadata: dict[str, Any] | None = None

    created_at: datetime = field(default_factory=_utcnow)

    @property
    def ok(self) -> bool:
        return self.finish_reason in (FinishReason.STOP, FinishReason.TOOL_CALLS)

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "model_id": self.model_id,
            "backend_id": self.backend_id,
            "trace_id": self.trace_id,
            "text": self.text,
            "finish_reason": self.finish_reason,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "latency_ms": self.latency_ms,
            "time_to_first_token_ms": self.time_to_first_token_ms,
            "generation_tokens_per_second": self.generation_tokens_per_second,
            "cache_status": self.cache_status,
            "hardware_profile_id": self.hardware_profile_id,
            "warnings": list(self.warnings),
            "tool_calls": self.tool_calls,
            "reasoning_metadata": self.reasoning_metadata,
            "structured_output": self.structured_output,
            "provider_metadata": self.provider_metadata,
        }
