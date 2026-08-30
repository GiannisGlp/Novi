"""Inference telemetry (plan 12, §28 Phase 28).

Records the per-request fields required by plan 12, §33. Prompts are NOT logged
by default (privacy policy): only token counts, timing, model/backend identity,
and failure class are recorded. RAM/VRAM before/after are sampled best-effort
via the existing ``ResourceTelemetry`` when available.

Exposed through existing Novi diagnostics via ``snapshot()`` — no independent
monitoring system is created (plan 12, §52).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .request import InferenceRequest
from .response import InferenceResponse

_MAX_RETAINED_RECORDS = 500


@dataclass(frozen=True)
class InferenceTelemetryRecord:
    request_id: str
    trace_id: str
    model_id: str
    backend_id: str
    start_time: float
    end_time: float = 0.0
    queue_time_ms: float = 0.0
    load_time_ms: float = 0.0
    ttft_ms: float = 0.0
    generation_time_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    tokens_per_second: float = 0.0
    ram_before_mib: float | None = None
    ram_after_mib: float | None = None
    failure_class: str = ""
    fallback_used: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "model_id": self.model_id,
            "backend_id": self.backend_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "queue_time_ms": round(self.queue_time_ms, 3),
            "load_time_ms": round(self.load_time_ms, 3),
            "ttft_ms": round(self.ttft_ms, 3),
            "generation_time_ms": round(self.generation_time_ms, 3),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "tokens_per_second": round(self.tokens_per_second, 3),
            "ram_before_mib": self.ram_before_mib,
            "ram_after_mib": self.ram_after_mib,
            "failure_class": self.failure_class,
            "fallback_used": self.fallback_used,
        }


def _sample_rss_mib() -> float | None:
    """Best-effort current process RSS in MiB (stdlib)."""
    try:
        import resource

        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0  # macOS: KB -> MiB
    except Exception:
        return None


class InferenceTelemetry:
    """Bounded telemetry store for the inference runtime."""

    def __init__(self, *, retain: int = _MAX_RETAINED_RECORDS) -> None:
        self._records: list[InferenceTelemetryRecord] = []
        self._retain = max(1, int(retain))
        self._counters: dict[str, int] = {}
        self._failure_counts: dict[str, int] = {}
        self._fallback_counts: dict[str, int] = {}
        self._model_switch_count = 0
        self._last_request_time: float = 0.0
        self._lock_placeholder = None  # runtime is single-threaded today

    def record_request(
        self,
        *,
        request: InferenceRequest,
        response: InferenceResponse | None,
        start_time: float,
        end_time: float,
        queue_time_ms: float = 0.0,
        load_time_ms: float = 0.0,
        failure_class: str = "",
        fallback_used: str = "",
        ram_before_mib: float | None = None,
        ram_after_mib: float | None = None,
    ) -> InferenceTelemetryRecord:
        ttft = response.time_to_first_token_ms if response else 0.0
        gen_ms = max(0.0, (end_time - start_time) * 1000.0 - ttft)
        record = InferenceTelemetryRecord(
            request_id=request.request_id,
            trace_id=request.trace_id,
            model_id=response.model_id if response else (request.model_hint or ""),
            backend_id=response.backend_id if response else "",
            start_time=start_time,
            end_time=end_time,
            queue_time_ms=queue_time_ms,
            load_time_ms=load_time_ms,
            ttft_ms=ttft,
            generation_time_ms=gen_ms,
            input_tokens=response.input_tokens if response else 0,
            output_tokens=response.output_tokens if response else 0,
            tokens_per_second=response.generation_tokens_per_second if response else 0.0,
            ram_before_mib=ram_before_mib,
            ram_after_mib=ram_after_mib,
            failure_class=failure_class,
            fallback_used=fallback_used,
        )
        self._records.append(record)
        if len(self._records) > self._retain:
            del self._records[: len(self._records) - self._retain]
        self._counters["requests"] = self._counters.get("requests", 0) + 1
        if failure_class:
            self._failure_counts[failure_class] = self._failure_counts.get(failure_class, 0) + 1
        if fallback_used:
            self._fallback_counts[fallback_used] = self._fallback_counts.get(fallback_used, 0) + 1
        self._last_request_time = end_time
        return record

    def record_model_switch(self) -> None:
        self._model_switch_count += 1

    @property
    def request_count(self) -> int:
        return self._counters.get("requests", 0)

    def snapshot(self) -> dict[str, Any]:
        return {
            "request_count": self.request_count,
            "failure_counts": dict(self._failure_counts),
            "fallback_counts": dict(self._fallback_counts),
            "model_switch_count": self._model_switch_count,
            "last_request_time": self._last_request_time,
            "recent": [r.as_dict() for r in self._records[-20:]],
        }

    def summary(self) -> dict[str, Any]:
        """Aggregated metrics for the observability dashboard (plan 12, §52)."""
        recent = self._records[-50:]
        ttfts = [r.ttft_ms for r in recent if r.ttft_ms > 0]
        tps = [r.tokens_per_second for r in recent if r.tokens_per_second > 0]
        return {
            "requests": self.request_count,
            "failures": dict(self._failure_counts),
            "fallbacks": dict(self._fallback_counts),
            "model_switches": self._model_switch_count,
            "avg_ttft_ms": round(sum(ttfts) / len(ttfts), 3) if ttfts else None,
            "avg_tokens_per_second": round(sum(tps) / len(tps), 3) if tps else None,
            "last_model_id": self._records[-1].model_id if self._records else None,
            "last_backend_id": self._records[-1].backend_id if self._records else None,
        }
