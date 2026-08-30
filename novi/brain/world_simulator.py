"""Deterministic world simulator (plan 22, Phase 22).

A scripted timeline of people / objects / rooms / events / time / speech /
gaze / gestures / sensor noise. The exact utterance can vary; the decision,
grounding, evidence and safety invariants cannot (plan §26).

The simulator is a pure replay source: an observer (the brain or its policy
layers) receives each event in order and the test asserts the expected
trace invariants.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class SimEvent:
    at: str  # timeline label, e.g. "T1"
    kind: str  # person.entered | speech | object.placed | ...
    entity: str = ""
    detail: dict[str, Any] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        return {"at": self.at, "kind": self.kind, "entity": self.entity, "detail": dict(self.detail)}


class WorldSimulator:
    """Replays a scripted world timeline; deterministic sensor noise."""

    def __init__(self, timeline: list[SimEvent], *, seed: int = 42, noise_scale: float = 0.02) -> None:
        self.timeline = list(timeline)
        self._rng = random.Random(seed)
        self.noise_scale = noise_scale

    def play(self, observer: Callable[[SimEvent], None]) -> list[dict[str, Any]]:
        """Replay every event through the observer; returns the trace."""
        trace: list[dict[str, Any]] = []
        for event in self.timeline:
            observer(event)
            trace.append(event.snapshot())
        return trace

    def noisy(self, value: float) -> float:
        """Deterministic sensor noise (seeded, small)."""
        return value + self._rng.uniform(-self.noise_scale, self.noise_scale)

    @staticmethod
    def plan_example_timeline() -> list[SimEvent]:
        """The plan §26 example: T0 empty room … T8 Vano returns."""
        return [
            SimEvent("T0", "scene.stable", detail={"people": 0, "objects": []}),
            SimEvent("T1", "person.entered", "vano", {"identity_confidence": 0.97}),
            SimEvent("T2", "gaze", "vano", {"at_novi": True}),
            SimEvent("T3", "speech", "vano", {"text": "hey novi"}),
            SimEvent("T4", "speech", "novi", {"text": "hey vano"}),
            SimEvent("T5", "object.placed", "mug", {"location": "desk"}),
            SimEvent("T6", "person.left", "vano", {}),
            SimEvent("T7", "object.disappeared", "mug", {"last_location": "desk"}),
            SimEvent("T8", "person.entered", "vano", {"identity_confidence": 0.98}),
        ]
