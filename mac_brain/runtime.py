from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from brain.b1_cognition import DeterministicCognition
from brain.b1_memory import DeterministicMemoryManager
from brain.b1_world import SensorObservation, TemporalWorldModel
from brain.b2_perception import SpecialistPerception
from brain.runtime import ActionProposal as RuntimeActionProposal
from brain.runtime import BrainSupervisor, Lifecycle

from .io import Camera, MacSpeaker, VirtualBody


@dataclass(frozen=True)
class MacBrainConfig:
    sensor_id: str = "mac.camera.front"
    run_id: str = ""
    memory_dir: Path = Path("mac_brain_data/memory")
    max_cycles: int = 1


class MacBrain:
    """First executable Mac embodiment of the existing Novi Brain.

    This class deliberately composes existing B1/B2 Brain components instead of
    creating a second cognitive architecture. Camera/model providers remain
    replaceable, while the deterministic runtime and safety boundary remain the
    authority for action execution.
    """

    def __init__(
        self,
        *,
        camera: Camera | None = None,
        speaker: MacSpeaker | None = None,
        body: VirtualBody | None = None,
        perception: SpecialistPerception | None = None,
        config: MacBrainConfig | None = None,
    ) -> None:
        self.config = config or MacBrainConfig()
        self.run_id = self.config.run_id or str(uuid4())
        self.camera = camera
        self.speaker = speaker or MacSpeaker()
        self.body = body or VirtualBody()
        self.brain = BrainSupervisor()
        self.perception = perception or SpecialistPerception()
        self.world = TemporalWorldModel()
        self.memory = DeterministicMemoryManager()
        self.cognition = DeterministicCognition()
        self._cycle = 0
        self.events: list[dict[str, Any]] = []

    def start(self) -> None:
        self.brain.start()
        self._emit("mac_brain.started", {"run_id": self.run_id})

    def step(self) -> dict[str, Any]:
        if self.brain.lifecycle is not Lifecycle.ACTIVE:
            raise RuntimeError(f"Mac Brain must be ACTIVE, got {self.brain.lifecycle.value}")
        if self.camera is None:
            raise RuntimeError("camera provider is not configured")

        self._cycle += 1
        frame = self.camera.read()
        self._emit("sensor.camera.frame", {
            "frame_id": frame.frame_id,
            "width": frame.width,
            "height": frame.height,
            "captured_at": frame.captured_at,
            "metadata": frame.metadata,
        })

        evidence = self.perception.process(
            sensor_id=self.config.sensor_id,
            frame_id=frame.frame_id,
            timestamp=frame.captured_at,
            frame=frame.payload,
        )
        self._emit("perception.completed", {
            "frame_id": evidence.frame_id,
            "detection_count": len(evidence.detections),
            "provenance": dict(evidence.provenance),
        })

        observations = tuple(
            SensorObservation(
                cycle=self._cycle,
                source=f"{self.config.sensor_id}.perception",
                entity=detection.label,
                location=None,
                state="present",
                confidence=detection.confidence,
                captured_cycle=self._cycle,
            )
            for detection in evidence.detections
        )
        self.world.apply_many(observations)
        cognitive = self.cognition.cycle(self.world.state, observations, cycle=self._cycle)
        self._emit("cognition.completed", {
            "cycle": self._cycle,
            "conclusion": cognitive.reasoning.conclusion,
            "confidence": cognitive.reasoning.confidence,
            "uncertainty": list(cognitive.situation.uncertainty),
        })

        action = self._action_from_cognition(cognitive.reasoning.conclusion)
        proposal = RuntimeActionProposal(
            action=action,
            parameters={},
            reason="Mac Brain v0 runtime bounded virtual action",
            correlation_id=str(uuid4()),
        )
        decision = self.brain.propose(proposal)
        if decision.authorized:
            outcome = self.brain.execute(proposal, decision)
            virtual_state = self.body.execute(action)
        else:
            outcome = None
            virtual_state = self.body.snapshot()

        self._emit("action.completed", {
            "action": action,
            "authorized": decision.authorized,
            "outcome": outcome.detail if outcome else decision.reason,
            "virtual_body": virtual_state,
        })
        return {
            "run_id": self.run_id,
            "cycle": self._cycle,
            "frame_id": frame.frame_id,
            "detections": [d.label for d in evidence.detections],
            "reasoning": cognitive.reasoning.conclusion,
            "reasoning_confidence": cognitive.reasoning.confidence,
            "action": action,
            "authorized": decision.authorized,
            "virtual_body": virtual_state,
        }

    def speak(self, text: str) -> None:
        self._emit("audio.speech.requested", {"text": text})
        self.speaker.speak(text)
        self._emit("audio.speech.completed", {"text": text})

    def stop(self) -> None:
        if self.camera is not None:
            self.camera.close()
        if self.brain.lifecycle is not Lifecycle.SHUTTING_DOWN:
            self.brain.shutdown()
        self._emit("mac_brain.stopped", {"run_id": self.run_id, "cycles": self._cycle})

    def _action_from_cognition(self, conclusion: str) -> str:
        # The Mac prototype starts with observation-only autonomy. Movement is
        # deliberately not inferred from model text until a future policy gate.
        if conclusion == "person_alice_is_relevant_to_current_situation":
            return "observe"
        return "observe"

    def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        self.events.append({
            "event_type": event_type,
            "run_id": self.run_id,
            "cycle": self._cycle,
            "payload": payload,
        })
