"""Inference request contract (plan 12, §6.1–6.2).

``InferenceRequest`` is the single typed, immutable request contract every
backend consumes. It is deliberately backend-neutral: no AirLLM, Ollama,
Transformers, or CUDA-specific field may appear here. Provider-specific options
travel through ``backend_options`` (validated capability-scoped options, never
required by cognition).

Priority rule (plan 12, §6.2): inference priority never overrides the
deterministic safety system. A CRITICAL inference request still cannot directly
authorize an action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Sequence
from uuid import uuid4


class RequestPriority(str, Enum):
    """Request priorities, highest first (plan 12, §6.2)."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"
    BACKGROUND = "BACKGROUND"

    @property
    def rank(self) -> int:
        return _PRIORITY_RANK[self]


_PRIORITY_RANK: dict[RequestPriority, int] = {
    RequestPriority.CRITICAL: 4,
    RequestPriority.HIGH: 3,
    RequestPriority.NORMAL: 2,
    RequestPriority.LOW: 1,
    RequestPriority.BACKGROUND: 0,
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class InferenceRequest:
    """A backend-neutral inference request.

    Required contract fields (plan 12, §6.1):

    - request_id / trace_id / created_at: identity and tracing;
    - caller / purpose: auditability (who asked and why);
    - model_policy / model_hint: routing inputs;
    - messages: the bounded context package (never direct memory access);
    - max_input_tokens / max_output_tokens: token accounting bounds;
    - temperature / top_p / top_k / stop_sequences: sampling;
    - stream: streaming request flag;
    - priority / deadline / latency_budget: scheduling inputs;
    - reasoning_budget: semantic deliberation level;
    - allow_background: whether background execution is acceptable;
    - conversation_id / mission_id: session scoping.

    ``backend_options`` is the only place for backend-specific options and is
    never required by cognition; it must be validated against the backend's
    declared capabilities.
    """

    # identity / tracing
    request_id: str = field(default_factory=lambda: str(uuid4()))
    trace_id: str = ""
    created_at: datetime = field(default_factory=_utcnow)
    caller: str = "unknown"
    purpose: str = ""

    # routing inputs
    model_policy: str = "default"
    model_hint: str = ""

    # content
    messages: Sequence[dict[str, Any]] = field(default_factory=tuple)
    system: str = ""
    max_input_tokens: int = 4096
    max_output_tokens: int = 1024

    # sampling
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int | None = None
    stop_sequences: Sequence[str] = field(default_factory=tuple)

    # scheduling
    stream: bool = False
    priority: RequestPriority = RequestPriority.NORMAL
    deadline: datetime | None = None
    latency_budget_ms: float | None = None
    reasoning_budget: str = "NORMAL"  # FAST | NORMAL | DELIBERATE | DEEP
    allow_background: bool = False

    # session scoping
    conversation_id: str = ""
    mission_id: str = ""

    # backend-specific, validated against capabilities, never required
    backend_options: dict[str, Any] = field(default_factory=dict)

    def with_deadline(self, deadline: datetime) -> "InferenceRequest":
        return InferenceRequest(**{**self.__dict__, "deadline": deadline})

    @property
    def is_expired(self) -> bool:
        if self.deadline is None:
            return False
        return _utcnow() > self.deadline
