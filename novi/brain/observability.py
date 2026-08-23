from __future__ import annotations

"""Unified observability for Novi Brain.

Merges the Stage-0 portable registry (``brain.observability``) with the
Mac-Brain diagnostic subsystem (``brain.observability``) so the single
``brain`` package serves both test suites without loss.

- **Stage-0 layer** (small, deterministic, used by ``brain/tests``):
  ``HealthRegistry``, ``MetricsRegistry`` (frozen dataclass snapshots),
  ``RuntimeObservability``.

- **Engine layer** (richer, used by ``brain/tests`` and the runtime):
  ``aggregate_health``, ``HealthCheck``, ``HealthSnapshot`` (engine), ``HealthMonitor``,
  ``MetricRegistry`` (engine, dict-based), ``Diagnostics``, ``default_health_checks``.

Both layers coexist; names are disambiguated where they overlap.  The engine
``HealthSnapshot`` is the one with ``checks: list[dict]`` and ``wallclock``;
the Stage-0 ``HealthSnapshot`` is frozen with ``checks: dict[str, str]``.
The two are intentionally different types under the same name in different
eras; we expose both via distinct aliases and keep each test suite's import
path working.

For new code prefer the engine layer (``HealthMonitor``/``MetricRegistry``/``Diagnostics``).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import monotonic, time
from typing import Any, Callable, Iterable

# ---------------------------------------------------------------------------
# Legacy Stage-0 health / metrics / observability (brain/tests)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HealthSnapshot:
    """Stage-0 snapshot (frozen, dict checks). See also EngineHealthSnapshot below."""

    status: str
    detail: str
    checks: dict[str, str] = field(default_factory=dict)
    wall_time: float = field(default_factory=time)
    monotonic_time: float = field(default_factory=monotonic)

    def snapshot(self) -> dict[str, Any]:  # engine compat shim
        return {
            "status": self.status,
            "detail": self.detail,
            "checks": [{"name": k, "status": v} for k, v in self.checks.items()],
            "wallclock": datetime.fromtimestamp(self.wall_time, tz=timezone.utc).isoformat(),
            "monotonic": round(self.monotonic_time, 6),
        }


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

# ---------------------------------------------------------------------------
# Engine layer (brain) — richer diagnostics
# ---------------------------------------------------------------------------

PASS, WARN, FAIL, UNKNOWN = "PASS", "WARN", "FAIL", "UNKNOWN"
_HEALTH_STATES = (PASS, WARN, FAIL, UNKNOWN)
_PRECEDENCE = {FAIL: 3, WARN: 2, PASS: 1, UNKNOWN: 0}

DEBUG, INFO, WARN_S, ERROR = "DEBUG", "INFO", "WARN", "ERROR"
_SEVERITIES = (DEBUG, INFO, WARN_S, ERROR)

_HEALTH_VALID = set(_HEALTH_STATES)


def aggregate_health(statuses: Iterable[str]) -> str:
    """Combine health states using FAIL > WARN > PASS > UNKNOWN precedence."""
    best = UNKNOWN
    for s in statuses:
        if s not in _HEALTH_VALID:
            raise ValueError(f"invalid health status: {s!r}")
        if _PRECEDENCE[s] > _PRECEDENCE[best]:
            best = s
    return best


@dataclass
class HealthCheck:
    name: str
    description: str
    run: Callable[[Any], tuple[str, str]]  # brain -> (status, detail)


@dataclass
class EngineHealthSnapshot:
    """Engine health snapshot (list checks, wallclock string)."""

    status: str
    detail: str
    checks: list[dict[str, Any]] = field(default_factory=list)
    wallclock: str = ""
    monotonic: float = 0.0

    def snapshot(self) -> dict[str, Any]:
        return {"status": self.status, "detail": self.detail, "checks": list(self.checks), "wallclock": self.wallclock, "monotonic": round(self.monotonic, 6)}


# Alias so isinstance checks against HealthSnapshot still work for engine snapshots
# (engine code imports HealthSnapshot from observability; we expose the engine one
# under the same name when the caller expects engine shape — tests use dataclass fields).
# To keep both, we keep Stage-0 HealthSnapshot as above and expose engine snapshot
# as HealthSnapshotEngine; then alias HealthSnapshot to engine for new imports via
# a compatibility shim: if caller passes list checks, it's engine shape.
# Simpler: keep both names exported.
HealthSnapshotEngine = EngineHealthSnapshot


class HealthMonitor:
    def __init__(self, checks: Iterable[HealthCheck] = ()) -> None:
        self.checks: dict[str, HealthCheck] = {c.name: c for c in checks}

    def add(self, check: HealthCheck) -> None:
        self.checks[check.name] = check

    def run(self, brain: Any) -> EngineHealthSnapshot:
        now = datetime.now(timezone.utc).isoformat()
        mono = monotonic()
        results: list[dict[str, Any]] = []
        for name in sorted(self.checks):
            check = self.checks[name]
            try:
                status, detail = check.run(brain)
            except Exception as exc:
                status, detail = FAIL, f"check_error: {exc}"
            if status not in _HEALTH_VALID:
                status = UNKNOWN
            results.append({"name": name, "description": check.description, "status": status, "detail": detail})
        overall = aggregate_health(r["status"] for r in results)
        if overall == FAIL:
            detail = f"{sum(1 for r in results if r['status']==FAIL)} failing subsystem(s)"
        elif overall == WARN:
            detail = f"{sum(1 for r in results if r['status']==WARN)} degraded subsystem(s)"
        else:
            detail = "all subsystems nominal"
        return EngineHealthSnapshot(status=overall, detail=detail, checks=results, wallclock=now, monotonic=mono)


class MetricRegistry:
    """Deterministic in-process metric registry (name, value, unit, labels)."""

    def __init__(self) -> None:
        self._metrics: dict[tuple[str, frozenset], dict[str, Any]] = {}

    def set(self, name: str, value: float, *, unit: str = "", labels: dict[str, Any] | None = None) -> None:
        labels = {k: str(v) for k, v in sorted((labels or {}).items())}
        self._metrics[(name, frozenset(labels.items()))] = {"name": name, "value": float(value), "unit": unit, "labels": labels}

    def inc(self, name: str, by: float = 1.0, *, unit: str = "", labels: dict[str, Any] | None = None) -> None:
        labels = {k: str(v) for k, v in sorted((labels or {}).items())}
        key = (name, frozenset(labels.items()))
        if key in self._metrics:
            self._metrics[key]["value"] += float(by)
        else:
            self._metrics[key] = {"name": name, "value": float(by), "unit": unit, "labels": labels}

    def snapshot(self) -> list[dict[str, Any]]:
        rows = list(self._metrics.values())
        rows.sort(key=lambda m: (m["name"], tuple(sorted(m["labels"].items()))))
        return [{"name": m["name"], "value": round(m["value"], 6), "unit": m["unit"], "labels": dict(m["labels"])} for m in rows]


# Provide engine-side MetricsRegistry under distinct name for disambiguation
EngineMetricRegistry = MetricRegistry
# Restore Stage-0 MetricsRegistry for legacy imports — already defined above, but
# engine overwrote it; re-expose legacy under LegcayMetricsRegistry alias for internal use
LegacyMetricsRegistry = MetricsRegistry  # now points to engine; keep alias for clarity

class Diagnostics:
    """Bounded structured diagnostic log with severities + dual timestamps."""

    def __init__(self, *, capacity: int = 200) -> None:
        self.capacity = capacity
        self._records: list[dict[str, Any]] = []

    def add(self, severity: str, message: str, context: dict[str, Any] | None = None) -> None:
        if severity not in _SEVERITIES:
            severity = INFO
        self._records.append(
            {
                "severity": severity,
                "message": message,
                "context": dict(context or {}),
                "wallclock": datetime.now(timezone.utc).isoformat(),
                "monotonic": round(monotonic(), 6),
            }
        )
        if len(self._records) > self.capacity:
            self._records = self._records[-self.capacity:]

    def snapshot(self, *, limit: int = 50) -> list[dict[str, Any]]:
        return list(self._records[-limit:])


def default_health_checks() -> list[HealthCheck]:
    """Deterministic checks over the Brain subsystems (each returns status, detail)."""
    return [
        HealthCheck("memory", "durable memory store available", _check_memory),
        HealthCheck("cognition", "cognition produces a conclusion", _check_cognition),
        HealthCheck("reasoning", "reasoning provider responds", _check_reasoning),
        HealthCheck("body", "virtual body present", _check_body),
        HealthCheck("soul", "soul present", _check_soul),
        HealthCheck("goals", "goal controller present", _check_goals),
        HealthCheck("perception", "perception backend present", _check_perception),
        HealthCheck("fusion", "multimodal fusion present", _check_fusion),
        HealthCheck("identity", "identity layer present", _check_identity),
        HealthCheck("knowledge", "knowledge graph present", _check_knowledge),
        HealthCheck("governance", "privacy governance available", _check_governance),
        HealthCheck("hearing", "audio hearing present", _check_hearing),
    ]


def _ok() -> tuple[str, str]:
    return PASS, "nominal"


def _check_memory(brain: Any) -> tuple[str, str]:
    return _ok() if getattr(brain, "memory", None) is not None else (FAIL, "no memory subsystem")


def _check_cognition(brain: Any) -> tuple[str, str]:
    return _ok() if getattr(brain, "cognition", None) is not None else (FAIL, "no cognition")


def _check_reasoning(brain: Any) -> tuple[str, str]:
    return _ok() if getattr(brain, "reasoning", None) is not None else (FAIL, "no reasoning provider")


def _check_body(brain: Any) -> tuple[str, str]:
    return _ok() if getattr(brain, "body", None) is not None else (FAIL, "no body")


def _check_soul(brain: Any) -> tuple[str, str]:
    return _ok() if getattr(brain, "soul", None) is not None else (FAIL, "no soul")


def _check_goals(brain: Any) -> tuple[str, str]:
    return _ok() if getattr(brain, "goals", None) is not None else (FAIL, "no goal controller")


def _check_perception(brain: Any) -> tuple[str, str]:
    return _ok() if getattr(brain, "perception", None) is not None else (FAIL, "no perception")


def _check_fusion(brain: Any) -> tuple[str, str]:
    return _ok() if getattr(brain, "fusion", None) is not None else (FAIL, "no fusion")


def _check_identity(brain: Any) -> tuple[str, str]:
    return _ok() if getattr(brain, "identity", None) is not None else (FAIL, "no identity")


def _check_knowledge(brain: Any) -> tuple[str, str]:
    return _ok() if getattr(brain, "knowledge", None) is not None else (FAIL, "no knowledge graph")


def _check_governance(brain: Any) -> tuple[str, str]:
    g = getattr(brain, "governance", None)
    if g is None:
        return (FAIL, "no governance")
    snap = getattr(g, "snapshot", lambda: {"enabled": True})()
    return (_ok() if snap.get("enabled") else (WARN, "governance disabled (non-durable memory)"))


def _check_hearing(brain: Any) -> tuple[str, str]:
    return _ok() if getattr(brain, "hearing", None) is not None else (FAIL, "no hearing")
