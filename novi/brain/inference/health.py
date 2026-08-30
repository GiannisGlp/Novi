"""Inference runtime health (plan 12, §7 health(), §18 recovery).

``BackendHealth`` aggregates backend health snapshots; ``InferenceHealth``
combines backend health with scheduler and telemetry state into a single
dashboard-visible view (plan 12, §52). The runtime must never assume a model is
ready merely because its files exist — health reflects the lifecycle state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .lifecycle import ModelLifecycle, ModelResidency


@dataclass(frozen=True)
class ModelHealthEntry:
    model_id: str
    lifecycle: ModelLifecycle
    residency: ModelResidency
    backend_id: str = ""
    last_error: str = ""
    detail: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "lifecycle": self.lifecycle.value,
            "residency": self.residency.value,
            "backend_id": self.backend_id,
            "last_error": self.last_error,
            "detail": dict(self.detail),
        }


class InferenceHealth:
    """Mutable health aggregator owned by the runtime."""

    def __init__(self) -> None:
        self._models: dict[str, ModelHealthEntry] = {}
        self._backend_health: dict[str, dict[str, Any]] = {}
        self._scheduler_state: dict[str, Any] = {}
        self._telemetry_summary: dict[str, Any] = {}

    def upsert_model(self, entry: ModelHealthEntry) -> None:
        self._models[entry.model_id] = entry

    def update_backend(self, backend_id: str, snapshot: dict[str, Any]) -> None:
        self._backend_health[backend_id] = snapshot

    def update_scheduler(self, snapshot: dict[str, Any]) -> None:
        self._scheduler_state = snapshot

    def update_telemetry(self, summary: dict[str, Any]) -> None:
        self._telemetry_summary = summary

    def get(self, model_id: str) -> ModelHealthEntry | None:
        return self._models.get(model_id)

    def snapshot(self) -> dict[str, Any]:
        return {
            "models": {mid: entry.as_dict() for mid, entry in self._models.items()},
            "backends": dict(self._backend_health),
            "scheduler": dict(self._scheduler_state),
            "telemetry": dict(self._telemetry_summary),
        }

    def ok(self) -> bool:
        """True when no model is FAILED and no backend reports unhealthy."""
        for entry in self._models.values():
            if entry.lifecycle is ModelLifecycle.FAILED:
                return False
        return all(snapshot.get("status") != "unhealthy" for snapshot in self._backend_health.values())
