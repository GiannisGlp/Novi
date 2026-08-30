"""Backend base classes (plan 12, §7, §2.2).

``ModelBackendState`` gives each backend a per-model lifecycle + residency
tracker so backends share one validated state implementation; ``AbstractInferenceBackend``
is re-exported from the contract module.
"""

from __future__ import annotations

from typing import Any

from ..contracts import AbstractInferenceBackend  # noqa: F401 (re-export)
from ..lifecycle import LifecycleMachine, ModelLifecycle, ModelResidency, new_model_lifecycle, new_residency


class ModelBackendState:
    """Per-backend per-model lifecycle + residency tracking."""

    def __init__(self) -> None:
        self._models: dict[str, tuple[LifecycleMachine, LifecycleMachine]] = {}

    def lifecycle(self, model_id: str) -> LifecycleMachine:
        return self._models.setdefault(model_id, (new_model_lifecycle(), new_residency()))[0]

    def residency(self, model_id: str) -> LifecycleMachine:
        return self._models.setdefault(model_id, (new_model_lifecycle(), new_residency()))[1]

    def set_lifecycle(self, model_id: str, state: ModelLifecycle | str) -> None:
        machine = self.lifecycle(model_id)
        target = ModelLifecycle(state) if isinstance(state, str) else state
        machine.transition_to(target)

    def set_residency(self, model_id: str, state: ModelResidency | str) -> None:
        machine = self.residency(model_id)
        target = ModelResidency(state) if isinstance(state, str) else state
        machine.transition_to(target)

    def snapshot(self) -> dict[str, Any]:
        return {
            model_id: {
                "lifecycle": machines[0].state.value,
                "residency": machines[1].state.value,
            }
            for model_id, machines in self._models.items()
        }
