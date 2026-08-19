from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic, time
from typing import Any


@dataclass(frozen=True)
class HealthSnapshot:
    status: str
    detail: str
    checks: dict[str, str] = field(default_factory=dict)
    wall_time: float = field(default_factory=time)
    monotonic_time: float = field(default_factory=monotonic)


@dataclass(frozen=True)
class RuntimeMetric:
    name: str
    value: float
    unit: str
    labels: dict[str, str] = field(default_factory=dict)


class HealthRegistry:
    """In-process health registry for the Stage-0 Brain runtime."""

    def __init__(self) -> None:
        self._checks: dict[str, str] = {}
        self._detail = "initializing"

    def set(self, name: str, status: str, *, detail: str = "") -> None:
        if not name:
            raise ValueError("health check name must not be empty")
        if status not in {"PASS", "WARN", "FAIL", "UNKNOWN"}:
            raise ValueError(f"invalid health status: {status}")
        self._checks[name] = status
        if detail:
            self._detail = detail

    def snapshot(self) -> HealthSnapshot:
        values = set(self._checks.values())
        if "FAIL" in values:
            status = "FAIL"
        elif "WARN" in values:
            status = "WARN"
        elif values and values == {"PASS"}:
            status = "PASS"
        else:
            status = "UNKNOWN"
        return HealthSnapshot(status, self._detail, dict(sorted(self._checks.items())))


class MetricsRegistry:
    """Small deterministic metric registry; export is intentionally deferred."""

    def __init__(self) -> None:
        self._metrics: dict[tuple[str, tuple[tuple[str, str], ...]], RuntimeMetric] = {}

    def set(self, name: str, value: float, unit: str, *, labels: dict[str, str] | None = None) -> None:
        if not name or not unit:
            raise ValueError("metric name and unit are required")
        normalized = tuple(sorted((labels or {}).items()))
        self._metrics[(name, normalized)] = RuntimeMetric(name, float(value), unit, dict(normalized))

    def snapshot(self) -> tuple[RuntimeMetric, ...]:
        return tuple(self._metrics[key] for key in sorted(self._metrics))


class RuntimeObservability:
    """Unified health, metric and structured diagnostic boundary."""

    def __init__(self) -> None:
        self.health = HealthRegistry()
        self.metrics = MetricsRegistry()
        self.diagnostics: list[dict[str, Any]] = []

    def record(self, level: str, message: str, *, context: dict[str, Any] | None = None) -> None:
        if level not in {"DEBUG", "INFO", "WARN", "ERROR"}:
            raise ValueError(f"invalid diagnostic level: {level}")
        self.diagnostics.append(
            {
                "level": level,
                "message": message,
                "context": dict(context or {}),
                "wall_time": time(),
                "monotonic_time": monotonic(),
            }
        )
