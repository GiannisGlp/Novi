"""Voice turn session with barge-in (plan 22, Phase 17, Tasks 17.2–17.3).

Turn-taking verbs: start / pause / interrupt / resume / backchannel / finish.
Barge-in: if the user starts speaking while Novi speaks, stop/attenuate TTS,
preserve the unfinished communicative state, listen, replan (plan §17.3).

Deterministic and hardware-free: the session is pure state; audio transport
is injected elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

IDLE = "idle"
SPEAKING = "speaking"
PAUSED = "paused"
INTERRUPTED = "interrupted"


@dataclass
class TurnSession:
    """One Novi speech turn with full barge-in handling."""

    state: str = IDLE
    text: str = ""
    act: str = "RESPOND"
    spoken_chars: int = 0
    unfinished: dict[str, Any] = field(default_factory=dict)
    barge_in_count: int = 0

    # ---- verbs (Task 17.2) ----

    def start(self, text: str, *, act: str = "RESPOND") -> str:
        if self.state in (SPEAKING, PAUSED):
            return self.state  # already active — no-op
        self.state = SPEAKING
        self.text = text
        self.act = act
        self.spoken_chars = 0
        self.unfinished = {}
        return self.state

    def pause(self) -> str:
        if self.state == SPEAKING:
            self.state = PAUSED
        return self.state

    def interrupt(self, *, user_speaking: bool = True) -> str:
        """Barge-in: the user started speaking mid-turn (Task 17.3).

        Preserves the unfinished communicative state for replanning and
        marks the TTS as attenuated (stop/attenuate step).
        """
        if self.state != SPEAKING:
            return self.state
        self.unfinished = {
            "text": self.text,
            "act": self.act,
            "spoken_chars": self.spoken_chars,
            "attenuate_tts": bool(user_speaking),
        }
        self.state = INTERRUPTED
        self.barge_in_count += 1
        return self.state

    def resume(self) -> str:
        """Replan: continue the preserved act from where it was cut."""
        if self.state == INTERRUPTED and self.unfinished:
            self.state = SPEAKING
            self.unfinished = {}
        elif self.state == PAUSED:
            self.state = SPEAKING
        return self.state

    def backchannel(self, text: str = "mhm") -> str:
        """A short listener acknowledgment during the user's turn."""
        return text

    def finish(self) -> dict[str, Any]:
        text, act, spoken = self.text, self.act, self.spoken_chars
        barge = self.barge_in_count
        self.state = IDLE
        self.text = ""
        self.act = "RESPOND"
        self.spoken_chars = 0
        self.unfinished = {}
        return {
            "state": self.state,  # terminal state is idle
            "text": text,
            "act": act,
            "spoken_chars": spoken,
            "barge_in_count": barge,
        }

    # ---- helpers ----

    def note_progress(self, chars: int) -> None:
        if self.state == SPEAKING:
            self.spoken_chars = max(self.spoken_chars, chars)

    def snapshot(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "act": self.act,
            "spoken_chars": self.spoken_chars,
            "unfinished_preserved": bool(self.unfinished),
            "barge_in_count": self.barge_in_count,
        }
