"""TTS provider boundary: macOS `say` stub + deterministic fallback.

Doc 15 contract: synthesize(text) -> AudioOut. The deterministic provider
records utterances for CI assertions; SayTTSProvider shells out to the
macOS `say` binary as the day-one audible stub. Piper/Kokoro-class neural
providers implement the same protocol later.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class AudioOut:
    """One synthesized utterance."""

    text: str
    provider: str
    spoken: bool = False  # True when audio actually rendered to a device


@runtime_checkable
class TTSProvider(Protocol):
    def synthesize(self, text: str) -> AudioOut: ...


class DeterministicTTSProvider:
    """Records utterances instead of speaking — CI-safe by construction."""

    def __init__(self) -> None:
        self.utterances: list[AudioOut] = []

    def synthesize(self, text: str) -> AudioOut:
        cleaned = (text or "").strip()
        if not cleaned:
            raise ValueError("cannot synthesize empty speech")
        out = AudioOut(text=cleaned, provider="deterministic", spoken=False)
        self.utterances.append(out)
        return out


class SayTTSProvider:
    """macOS `say` command stub — proves the audible path end-to-end."""

    def __init__(self, say_bin: str = "/usr/bin/say", voice: str | None = None) -> None:
        self._say_bin = say_bin
        self._voice = voice

    def available(self) -> bool:
        return os.path.isfile(self._say_bin) and os.access(self._say_bin, os.X_OK)

    def synthesize(self, text: str) -> AudioOut:
        cleaned = (text or "").strip()
        if not cleaned:
            raise ValueError("cannot synthesize empty speech")
        if not self.available():
            raise RuntimeError(
                f"TTS binary not available: {self._say_bin!r} "
                "(fall back to DeterministicTTSProvider in non-Mac/CI environments)"
            )
        cmd = [self._say_bin]
        if self._voice:
            cmd += ["-v", self._voice]
        cmd.append(cleaned)
        subprocess.run(cmd, check=True, timeout=30)
        return AudioOut(text=cleaned, provider="say", spoken=True)
