"""Source-agnostic unified agent facade for the Novi Brain.

The ``MacBrain`` (engine.py) is the single brain: it integrates cognition,
soul, personality, knowledge, memory, reasoning, autonomy, relationships,
learning and governance into one continuous cognitive loop. This facade makes
that brain *source-agnostic*: chat text, a CLI command, a vision frame or a
sound/STT transcript are all normalised into one ``AgentInput`` and driven
through the same ``MacBrain`` step. The source never changes how the brain
thinks — it only changes which modality fed the loop (docs/02-autonomy/01).

It also exposes the autonomous capabilities the docs require:

  * multitasking          -> enqueue/pursue multiple bounded goals
  * context-aware action  -> ``drive()`` returns a reasoned action proposal
                             (text / speech / movement / wait) grounded in the
                             current world, memory, knowledge and self-state
  * learning              -> learn new facts (knowledge promotion), correct
                             knowledge, add user rules/preferences, meet &
                             remember people, and understand relationships

It is deliberately a thin facade over ``MacBrain`` — it adds no second
cognitive loop and no duplicate state. Callers (web, CLI, voice, vision
sources) share one brain instance.
"""

from __future__ import annotations

import contextlib
import threading
from dataclasses import dataclass, field
from typing import Any, Literal

from .audio import AudioFrame
from .engine import Brain as MacBrain
from .engine import MacBrainConfig
from .io import CameraFrame
from .models import DeterministicSTTProvider, TranscriptionResult

InputModality = Literal["chat", "cli", "voice", "vision", "audio", "none"]


@dataclass(frozen=True)
class AgentInput:
    """A normalised input from any source, ready to be driven through the brain.

    Exactly one source field is typically populated; the brain normalises it
    into the shared cognitive loop regardless of where it came from.
    """

    modality: InputModality = "none"
    text: str = ""
    confidence: float = 0.9
    person: str = ""
    audio: AudioFrame | None = None
    frame: CameraFrame | None = None

    @classmethod
    def chat(cls, text: str, *, person: str = "", confidence: float = 0.9) -> "AgentInput":
        return cls(modality="chat", text=text, person=person, confidence=confidence)

    @classmethod
    def command(cls, text: str, *, person: str = "", confidence: float = 1.0) -> "AgentInput":
        return cls(modality="cli", text=text, person=person, confidence=confidence)

    @classmethod
    def voice(cls, text: str, *, confidence: float = 0.9, person: str = "") -> "AgentInput":
        return cls(modality="voice", text=text, person=person, confidence=confidence)

    @classmethod
    def vision(cls, frame: CameraFrame) -> "AgentInput":
        return cls(modality="vision", frame=frame, confidence=0.9)

    @classmethod
    def audio_event(cls, frame: AudioFrame) -> "AgentInput":
        return cls(modality="audio", audio=frame, confidence=0.0)

    @classmethod
    def idle(cls) -> "AgentInput":
        return cls(modality="none")


@dataclass
class AgentOutcome:
    """The outcome of driving one input through the brain."""

    cycle: int
    modality: InputModality
    reasoning: str
    confidence: float
    action: str = "none"
    authorized: bool = False
    reply: str | None = None
    reply_source: str = "none"
    trace: dict[str, Any] = field(default_factory=dict)
    learned: list[tuple[str, str]] = field(default_factory=list)
    person: str = ""
    relationship: str = "unknown"
    suggestions: list[str] = field(default_factory=list)
    detections: list[str] = field(default_factory=list)


class DemoCamera:
    """Deterministic no-hardware camera (matches the CLI/web demo)."""

    def __init__(self) -> None:
        self.sequence = 0

    def read(self) -> CameraFrame:
        self.sequence += 1
        return CameraFrame(
            frame_id=f"agent-{self.sequence}",
            captured_at="2026-08-19T00:00:00Z",
            width=1,
            height=1,
            payload=b"agent-frame",
            metadata={"backend": "deterministic-agent"},
        )

    def close(self) -> None:
        return None


class BrainDriver:
    """A source-agnostic driver for one ``MacBrain`` instance.

    Multiple input sources share one driver (and therefore one brain, one
    memory, one soul, one knowledge graph, one set of relationships).
    """

    def __init__(
        self,
        brain: MacBrain | None = None,
        *,
        lock: threading.RLock | None = None,
        llm_chat: Any | None = None,
    ) -> None:
        self.brain = brain or self._build_default()
        self.lock = lock or threading.RLock()
        self.llm_chat = llm_chat

    # ---- construction -----------------------------------------------------

    def _build_default(self) -> MacBrain:
        """Build a brain with deterministic (no-hardware) sensing."""
        return MacBrain(camera=DemoCamera(), stt=DeterministicSTTProvider(), config=MacBrainConfig(curiosity_enabled=True))

    # ---- unified drive ----------------------------------------------------

    def drive(self, inp: AgentInput) -> AgentOutcome:
        """Drive one normalised input through the shared brain.

        Every source (chat / CLI / voice / vision / audio / idle) converges here.
        The brain decides a context-aware action and, when a communicative act
        is warranted, the natural reply grounded in soul / relationships /
        memory / knowledge / self-state (docs/06-soul/07 §2).
        """
        self._ensure_active()
        with self.lock:
            return self._drive_locked(inp)

    def _ensure_active(self) -> None:
        from .runtime import Lifecycle
        if self.brain.brain.lifecycle is not Lifecycle.ACTIVE:
            self.brain.start()

    def _drive_locked(self, inp: AgentInput) -> AgentOutcome:
        # Feed non-text modalities into the shared loop first.
        if inp.audio is not None:
            with contextlib.suppress(Exception):
                self.brain.ingest_audio_frame(inp.audio)
        # One full cognitive cycle on the shared brain.
        step = self.brain.step()
        trace = dict(self.brain._last_reasoning_trace or {})
        person = self._addressee(inp)
        outcome = AgentOutcome(
            cycle=self.brain._cycle,
            modality=inp.modality,
            reasoning=str(step.get("reasoning", "")),
            confidence=float(step.get("reasoning_confidence", 0.0)),
            action=str(step.get("action", "none")),
            authorized=bool(step.get("authorized", False)),
            trace=trace,
            person=person,
            relationship=self._relationship_for(person),
            suggestions=self._suggestions(),
            detections=[str(d) for d in step.get("detections", [])],
        )
        # A text/voice/command input warrants a reply from the brain itself.
        if inp.text:
            outcome.learned = self._learn_from_input(inp)
            outcome.reply, outcome.reply_source = self._compose(inp, person)
        else:
            initiative = self._initiate()
            if initiative is not None:
                outcome.reply = initiative.get("text")
                outcome.reply_source = "initiative"
        return outcome

    # ---- reply composition (brain-owned, consolidated via respond) -----------

    def _compose(self, inp: AgentInput, person: str) -> tuple[str | None, str]:
        """Compose the brain's own natural reply for a text input.

        Delegates to the brain's source-agnostic ``respond()`` so reply
        orchestration stays in the brain (docs/06-soul/07 §2), not the driver.
        """
        try:
            reply_obj = self.brain.respond(
                inp.text,
                person=person,
                history=[],
                llm_chat=self.llm_chat,
                last_novi_text="",
                recent_novi=[],
                learn=True,
            )
            text = reply_obj.get("text")
            if text is not None:
                return text, reply_obj.get("reply_source", "dialogue")
        except Exception:  # noqa: BLE001
            pass
        fb = self.brain.natural_reply_fallback(text=inp.text, cycle=self.brain._cycle)
        return fb.get("text"), "fallback"

    def _addressee(self, inp: AgentInput) -> str:
        if inp.person:
            return inp.person
        try:
            refs = self.brain._entities_in_text(inp.text)
            return next((r for r in refs if self.brain._is_person_name(r)), "")
        except Exception:  # noqa: BLE001
            return ""

    def _relationship_for(self, person: str) -> str:
        if not person:
            return "unknown"
        try:
            return self.brain.relationships.category_for(person).value
        except Exception:  # noqa: BLE001
            return "unknown"

    def _suggestions(self) -> list[str]:
        try:
            return [c.get("suggested_action", "") for c in getattr(self.brain, "_last_attention_candidates", []) if c.get("suggested_action")][:4]
        except Exception:  # noqa: BLE001
            return []

    def _initiate(self) -> dict[str, Any] | None:
        """Surface a spontaneous initiative the brain proposed (docs/06-soul/00 §11)."""
        if not self.brain.config.initiative_enabled:
            return None
        try:
            detections = (self.brain._last_reasoning_trace or {}).get("detections", [])
            person = self.brain._person_label(detections)
            return self.brain._maybe_initiate(person, has_active_goal=self.brain.goals.has_active)
        except Exception:  # noqa: BLE001
            return None

    # ---- source helpers ------------------------------------------------------

    def hear(self, text: str, *, person: str = "", source: InputModality = "chat") -> AgentOutcome:
        """Hear text from any of chat/CLI/voice — the brain behaves the same."""
        return self.drive(AgentInput(modality=source, text=text, person=person))

    def command(self, text: str) -> AgentOutcome:
        """Treat a CLI command / instruction as an input to the same brain."""
        return self.drive(AgentInput.command(text))

    def transcribe_and_drive(self, transcription: TranscriptionResult) -> AgentOutcome:
        """Feed a real STT transcript into the brain (voice modality)."""
        if transcription is None or not (transcription.text or "").strip():
            return self.drive(AgentInput.idle())
        with contextlib.suppress(Exception):
            self.brain.ingest_transcript(transcription)
        return self.drive(AgentInput.voice(transcription.text, confidence=transcription.confidence))

    def hear_audio(self, frame: AudioFrame) -> AgentOutcome:
        """Feed a non-speech acoustic event into the brain."""
        return self.drive(AgentInput.audio_event(frame))

    # ---- multitasking (autonomy goals) ---------------------------------------

    def set_goal(self, goal: Any) -> Any:
        """Adopt a bounded goal the brain pursues autonomously."""
        return self.brain.set_goal(goal)

    def enqueue_goal(self, goal: Any) -> Any:
        """Queue a bounded goal behind the current one (multitask backlog)."""
        return self.brain.enqueue_goal(goal)

    def active_goals(self) -> list[dict[str, Any]]:
        try:
            return [{"goal_id": s.goal.goal_id, "kind": s.goal.kind, "status": s.status.value, "steps_taken": s.steps_taken} for s in self.brain.goals.history[-8:]]
        except Exception:  # noqa: BLE001
            return []

    # ---- learning: new facts, rules, people & relations ---------------------

    def _learn_from_input(self, inp: AgentInput) -> list[tuple[str, str]]:
        """Learn preferences/reminders/people from what the user says."""
        learned: list[tuple[str, str]] = []
        with contextlib.suppress(Exception):
            self.brain._learn_from_chat(inp.text, person=inp.person)
        # Meet + remember anyone named in the message.
        if inp.person:
            self.meet_person(inp.person)
            learned.append(("met_person", inp.person))
        return learned

    def learn_preference(self, person: str, kind: str, value: str, *, explicit: bool = True) -> None:
        """Record a durable preference about a person (experience learning)."""
        self.brain.learn_preference(person or "", kind, value, explicit=explicit)

    def learn_fact(self, subject: str, predicate: str, object: str, *, confidence: float = 0.9) -> bool:
        """Add a knowledge triple via the promotion pipeline (learn new things)."""
        return self.brain.observe_knowledge(subject, predicate, object, confidence=confidence)

    def correct_fact(self, subject: str, predicate: str, new_object: str, *, person: str = "") -> bool:
        """Correct a known fact with provenance (belief revision)."""
        return self.brain.correct_knowledge(subject, predicate, new_object, person=person)

    def add_rule(self, rule: str, *, person: str = "") -> None:
        """Persist a user rule / preference (learn new rules)."""
        self.brain._learn_from_chat(rule, person=person)

    def meet_person(self, name: str, *, confidence: float = 0.9) -> None:
        """Introduce Novi to a person and remember them (identity + relation)."""
        if not name:
            return
        try:
            self.brain.identity.observe("person", name=name, confidence=confidence, modality="social", cycle=self.brain._cycle)
            if hasattr(self.brain, "_persist_identity"):
                self.brain._persist_identity()
            self.brain.relationships.note_interaction(name, positive=True)
        except Exception:  # noqa: BLE001
            pass

    def remember_relation(self, subject: str, relation: str, object: str, *, confidence: float = 0.8) -> None:
        """Add a relationship / association triple to the knowledge graph."""
        self.brain.knowledge.add(subject, relation, object, confidence=confidence, source="agent", cycle=self.brain._cycle)
        if hasattr(self.brain, "_persist_knowledge"):
            self.brain._persist_knowledge()

    def known_persons(self) -> list[str]:
        return self.brain._chat_known_persons()

    def relationship_for(self, person: str) -> str:
        return self._relationship_for(person)

    def soul_state(self) -> dict[str, Any]:
        return {
            "identity": self.brain.soul.identity.name,
            "persona": self.brain.soul.identity.persona,
            "tone": self.brain.soul.tone({}).get("tone"),
            "affect": dict(self.brain.soul.affect.dimensions),
            "traits": dict(self.brain.soul.personality.traits),
            "values": dict(self.brain.soul.personality.values),
        }

    def knowledge_counts(self) -> dict[str, int]:
        return self.brain.knowledge.counts()

    # ---- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        self.brain.start()

    def stop(self) -> None:
        with contextlib.suppress(Exception):
            self.brain.stop()
