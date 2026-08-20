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

from .autonomy import BoundedGoalController, Goal, GoalState, GoalStatus
from .io import Camera, MacMicrophone, MacSpeaker, VirtualBody
from .storage import DurableMemoryStore
from .models import (
    DeterministicReasoningProvider,
    DeterministicSTTProvider,
    ReasoningProvider,
    SpeechToTextProvider,
    TranscriptionResult,
)


@dataclass(frozen=True)
class MacBrainConfig:
    sensor_id: str = "mac.camera.front"
    run_id: str = ""
    memory_dir: Path = Path("MAC_BRAIN_data/memory")
    max_cycles: int = 1


class MacBrain:
    """First executable Mac embodiment of the existing Novi Brain."""

    def __init__(
        self,
        *,
        camera: Camera | None = None,
        speaker: MacSpeaker | None = None,
        body: VirtualBody | None = None,
        perception: SpecialistPerception | None = None,
        reasoning: ReasoningProvider | None = None,
        microphone: MacMicrophone | None = None,
        stt: SpeechToTextProvider | None = None,
        goals: BoundedGoalController | None = None,
        store_path: str | None = None,
        config: MacBrainConfig | None = None,
    ) -> None:
        self.config = config or MacBrainConfig()
        self.run_id = self.config.run_id or str(uuid4())
        self.camera = camera
        self.speaker = speaker or MacSpeaker()
        self.body = body or VirtualBody()
        self.microphone = microphone or MacMicrophone()
        self.brain = BrainSupervisor()
        self.perception = perception or SpecialistPerception()
        self.reasoning = reasoning or DeterministicReasoningProvider()
        self.stt = stt or DeterministicSTTProvider()
        self.world = TemporalWorldModel()
        self.memory = DurableMemoryStore(store_path) if store_path else DeterministicMemoryManager()
        self.cognition = DeterministicCognition()
        self.goals = goals or BoundedGoalController()
        self._cycle = 0
        self.events: list[dict[str, Any]] = []

    def start(self) -> None:
        self.brain.start()
        self._emit("MAC_BRAIN.started", {"run_id": self.run_id})

    def step(self) -> dict[str, Any]:
        if self.brain.lifecycle is not Lifecycle.ACTIVE:
            raise RuntimeError(f"Mac Brain must be ACTIVE, got {self.brain.lifecycle.value}")
        if self.camera is None:
            raise RuntimeError("camera provider is not configured")
        self._cycle += 1
        frame = self.camera.read()
        self._emit("sensor.camera.frame", {"frame_id": frame.frame_id, "width": frame.width, "height": frame.height, "captured_at": frame.captured_at, "metadata": frame.metadata})
        evidence = self.perception.process(sensor_id=self.config.sensor_id, frame_id=frame.frame_id, timestamp=frame.captured_at, frame=frame.payload)
        self._emit("perception.completed", {"frame_id": evidence.frame_id, "detection_count": len(evidence.detections), "provenance": dict(evidence.provenance)})
        observations = tuple(SensorObservation(cycle=self._cycle, source=f"{self.config.sensor_id}.perception", entity=detection.label, location=None, state="present", confidence=detection.confidence, captured_cycle=self._cycle) for detection in evidence.detections)
        self.world.apply_many(observations)
        self._admit_detections(evidence.detections)
        cognitive = self.cognition.cycle(self.world.state, observations, cycle=self._cycle)
        self._emit("cognition.completed", {"cycle": self._cycle, "conclusion": cognitive.reasoning.conclusion, "confidence": cognitive.reasoning.confidence, "uncertainty": list(cognitive.situation.uncertainty)})

        recall = self._recall_context(cognitive.situation, evidence.detections)
        self._emit("memory.recall", {"cycle": self._cycle, "query": " ".join(recall["query"]), "recalled": len(recall["memories"])})

        intent = self.reasoning.decide(
            conclusion=cognitive.reasoning.conclusion,
            confidence=cognitive.reasoning.confidence,
            situation=cognitive.situation,
            recall=recall["memories"],
        )
        self._emit("reasoning.completed", {"cycle": self._cycle, "action": intent.action, "rationale": intent.rationale})

        goal_was_active = self.goals.has_active
        if goal_was_active:
            step_command = self.goals.step(self.body, cycle=self._cycle)
            action = step_command.action
            parameters = step_command.parameters
            reason = "goal_pursuit"
        else:
            action = intent.action
            parameters = intent.parameters
            reason = intent.rationale

        proposal = RuntimeActionProposal(action=action, parameters=parameters, reason=reason, correlation_id=str(uuid4()))
        decision = self.brain.propose(proposal)
        if decision.authorized:
            outcome = self.brain.execute(proposal, decision)
            virtual_state = self.body.execute(action, **parameters)
        else:
            outcome = None
            virtual_state = self.body.snapshot()
        self._emit("action.completed", {"action": action, "authorized": decision.authorized, "outcome": outcome.detail if outcome else decision.reason, "virtual_body": virtual_state})
        if goal_was_active and not self.goals.has_active:
            terminal = self.goals.history[-1]
            self._emit("goal.status", {"goal_id": terminal.goal.goal_id, "kind": terminal.goal.kind, "status": terminal.status.value, "steps_taken": terminal.steps_taken})
            self._admit_goal_outcome(terminal)
            self._persist_goal(terminal)
        goal_info = None
        if self.goals.history:
            last = self.goals.history[-1]
            goal_info = {"goal_id": last.goal.goal_id, "kind": last.goal.kind, "status": last.status.value, "steps_taken": last.steps_taken}
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
            "goal": goal_info,
        }

    def set_goal(self, goal: Goal, *, cycle: int | None = None) -> GoalState:
        """Adopt a bounded goal for the autonomy layer to pursue."""
        cycle = self._cycle if cycle is None else cycle
        state = self.goals.adopt(goal)
        self._emit("goal.adopted", {"goal_id": goal.goal_id, "kind": goal.kind, "target": str(goal.target), "max_steps": goal.max_steps})
        self._persist_goal(state)
        return state

    def _persist_goal(self, state: Any) -> None:
        if isinstance(self.memory, DurableMemoryStore):
            self.memory.save_goal(
                goal_id=state.goal.goal_id,
                kind=state.goal.kind,
                target=state.goal.target,
                priority=state.goal.priority,
                max_steps=state.goal.max_steps,
                created_cycle=state.goal.created_cycle,
                status=state.status.value,
                steps_taken=state.steps_taken,
            )

    def listen(self, seconds: float = 3.0, *, output_dir: Path | None = None) -> dict[str, Any]:
        """Record from the microphone, transcribe locally, and ingest into cognition/memory."""
        output_dir = output_dir or Path("mac_test_results/STT")
        recording = self.microphone.record(seconds, output_dir)
        self._emit("audio.recording.completed", {"recording_id": recording.recording_id, "duration_s": recording.duration_s, "path": str(recording.path)})
        transcription = self.stt.transcribe(recording.path)
        self._emit("stt.completed", {"recording_id": recording.recording_id, "text": transcription.text, "language": transcription.language, "confidence": transcription.confidence, "model_id": transcription.model_id})
        ingested = self.ingest_transcript(transcription)
        return {"transcription": transcription, **ingested}

    def ingest_transcript(self, transcription: TranscriptionResult) -> dict[str, Any]:
        """Feed a transcript into memory (durable) and cognition (transient speech event)."""
        entity_refs = self._entities_in_text(transcription.text)
        admission = self.memory.admit(
            memory_type="utterance",
            content=transcription.text,
            confidence=transcription.confidence,
            verification_status="verified" if transcription.confidence >= 0.7 else "unverified",
            privacy_class="private",
            provenance={
                "source": "audio.stt",
                "provider": transcription.provider,
                "model_id": transcription.model_id,
                "audio_path": transcription.audio_path,
            },
            entity_refs=entity_refs,
        )
        self._emit("memory.admitted", {"memory_id": admission.memory_id, "memory_type": "utterance", "accepted": admission.accepted, "entity_refs": list(entity_refs)})

        speech = SensorObservation(
            cycle=self._cycle,
            source="audio.stt",
            entity=DeterministicCognition.SPEECH_ENTITY,
            location=None,
            state="heard",
            confidence=transcription.confidence,
            captured_cycle=self._cycle,
        )
        cognitive = self.cognition.cycle(self.world.state, (speech,), cycle=self._cycle)
        self._emit("cognition.completed", {"cycle": self._cycle, "conclusion": cognitive.reasoning.conclusion, "confidence": cognitive.reasoning.confidence, "source": "audio.stt"})
        self._emit("speech.ingested", {"text": transcription.text, "memory_id": admission.memory_id, "reasoning": cognitive.reasoning.conclusion})
        return {"admission": admission, "speech_observation": speech, "reasoning": cognitive.reasoning.conclusion, "confidence": cognitive.reasoning.confidence}

    def _admit_detections(self, detections: Any) -> None:
        for detection in detections:
            admission = self.memory.admit(
                memory_type="perception",
                content={"label": detection.label, "confidence": detection.confidence, "bbox": list(detection.bbox_xyxy)},
                confidence=detection.confidence,
                verification_status="verified" if detection.confidence >= 0.7 else "unverified",
                privacy_class="public",
                provenance={"source": self.config.sensor_id, "capability": "vision.object_detection"},
                entity_refs=(detection.label,),
            )
            self._emit("memory.admitted", {"memory_id": admission.memory_id, "memory_type": "perception", "accepted": admission.accepted, "entity": detection.label})

    def _entities_in_text(self, text: str) -> tuple[str, ...]:
        known = set(self.world.state.entities) | {"alice", "door", "person", "table", "room", "kitchen", "object", "window"}
        lowered = text.lower()
        return tuple(sorted(name for name in known if name in lowered))

    def _admit_goal_outcome(self, state: Any) -> None:
        admission = self.memory.admit(
            memory_type="goal_outcome",
            content={"goal_id": state.goal.goal_id, "kind": state.goal.kind, "status": state.status.value, "steps_taken": state.steps_taken, "target": str(state.goal.target)},
            confidence=1.0,
            verification_status="verified",
            privacy_class="public",
            provenance={"source": "autonomy.goals"},
        )
        self._emit("memory.admitted", {"memory_id": admission.memory_id, "memory_type": "goal_outcome", "accepted": admission.accepted, "goal_id": state.goal.goal_id})

    def _recall_context(self, situation: Any, detections: Any) -> dict[str, Any]:
        """Retrieve relevant memories (salient entities + detections) for reasoning."""
        entities: list[str] = []
        for entity in situation.salient_entities:
            if entity not in entities:
                entities.append(entity)
        for detection in detections:
            if detection.label not in entities:
                entities.append(detection.label)
        query = " ".join(entities) if entities else "memory"
        records = self.memory.retrieve(query, limit=5)
        memories = [
            {
                "memory_type": record.memory_type,
                "content": record.content,
                "confidence": record.confidence,
                "entity_refs": list(record.entity_refs),
            }
            for record in records
        ]
        return {"query": entities, "memories": memories}

    def speak(self, text: str) -> None:
        self._emit("audio.speech.requested", {"text": text})
        self.speaker.speak(text)
        self._emit("audio.speech.completed", {"text": text})

    def stop(self) -> None:
        if self.camera is not None:
            self.camera.close()
        if isinstance(self.memory, DurableMemoryStore):
            self.memory.close()
        if self.brain.lifecycle is not Lifecycle.SHUTTING_DOWN:
            self.brain.shutdown()
        self._emit("MAC_BRAIN.stopped", {"run_id": self.run_id, "cycles": self._cycle})

    def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        self.events.append({"event_type": event_type, "run_id": self.run_id, "cycle": self._cycle, "payload": payload})
