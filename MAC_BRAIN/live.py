"""Interactive live brain demo.

Ties the Mac Brain's real local senses together into one loop:
  - a camera stream (real Mac camera, or a static image / deterministic fallback);
  - periodic speech-to-text from the microphone (local Whisper, or a deterministic
    transcript injection for offline/test runs);
  - reasoning (local LLM via Ollama when available, else the deterministic
    reasoning provider);
  - soul-based tone expression;
  - text-to-speech via the macOS ``say`` command (gracefully skipped if absent).

Everything degrades gracefully: a missing camera, microphone, model, or voice
simply falls back rather than aborting, so the demo runs fully offline and is
testable with fakes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol


class Speaker(Protocol):
    def available(self) -> bool: ...
    def speak(self, text: str) -> None: ...


@dataclass
class LiveSession:
    brain: Any  # MacBrain
    rounds: int = 1
    per_round_steps: int = 1
    listen_seconds: float = 3.0
    demo_hear: str | None = None  # inject a deterministic transcript (no microphone)
    speaker: Speaker | None = None
    on_round: Callable[[int, dict[str, Any]], None] | None = None

    def _compose_reply(self, steps: list[dict[str, Any]], heard: str | None, tone: dict[str, Any]) -> str:
        last = steps[-1] if steps else {}
        reasoning = str(last.get("reasoning", "") or "")
        seen = []
        for step in steps:
            for label in step.get("detections", []):
                if label not in seen:
                    seen.append(label)
        parts = []
        if seen:
            parts.append("I can see " + ", ".join(seen) + ".")
        if heard:
            parts.append(f"You said: {heard!r}.")
        parts.append(reasoning if reasoning else "I'm here and paying attention.")
        opening = {
            "curious": "That's interesting —",
            "satisfied": "Lovely —",
            "cautious": "Noted —",
            "warm": "Hi —",
        }.get(tone.get("tone", "warm"), "")
        base = " ".join(parts)
        return (opening + " " + base).strip() if opening else base

    def run(self) -> dict[str, Any]:
        summary: dict[str, Any] = {"rounds": []}
        try:
            for round_index in range(self.rounds):
                round_out: dict[str, Any] = {"index": round_index}
                steps = [self.brain.step() for _ in range(self.per_round_steps)]
                round_out["steps"] = steps

                heard = None
                if self.demo_hear is not None:
                    heard = self.demo_hear
                elif self.listen_seconds > 0 and self.brain.microphone is not None and self.brain.stt is not None:
                    try:
                        heard = self.brain.listen(self.listen_seconds)["transcription"].text
                    except Exception as exc:  # microphone/STT unavailable -> degrade
                        round_out["hear_error"] = str(exc)
                if heard is not None:
                    round_out["heard"] = heard
                    round_out["heard_reasoning"] = self._ingest_heard(heard)

                tone = self.brain.soul.tone({"heard": bool(heard)})
                round_out["tone"] = tone
                reply = self._compose_reply(steps, heard, tone)
                round_out["reply"] = reply

                if self.speaker is not None and self.speaker.available():
                    try:
                        self.speaker.speak(reply)
                        round_out["spoke"] = True
                    except Exception as exc:
                        round_out["speak_error"] = str(exc)

                self.brain._emit("live.round_completed", {"round": round_index, "heard": heard, "reply": reply, "tone": tone.get("tone")})
                if self.on_round is not None:
                    self.on_round(round_index, round_out)
                summary["rounds"].append(round_out)
        finally:
            self.brain.stop()
        summary["events"] = self.brain.events
        return summary

    def _ingest_heard(self, heard: str) -> str | None:
        from .models import TranscriptionResult

        result = TranscriptionResult(text=heard, language="en", confidence=1.0, audio_path="", provider="live-inject", model_id="live-inject")
        return self.brain.ingest_transcript(result).get("reasoning")
