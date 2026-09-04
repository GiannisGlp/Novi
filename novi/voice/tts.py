"""TTS provider boundary: macOS `say` stub + deterministic fallback.

Doc 15 contract: synthesize(text) -> AudioOut. The deterministic provider
records utterances for CI assertions; SayTTSProvider shells out to the
macOS `say` binary as the day-one audible stub. Piper/Kokoro-class neural
providers implement the same protocol later.
"""

from __future__ import annotations

import contextlib
import os
import subprocess
from dataclasses import dataclass
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


class PiperTTSProvider:
    """Piper neural TTS via the `piper` command — the Jetson-body voice.

    Pipes text into ``piper --model <voice.onnx> -f <wav>`` then plays the
    file with an external player (``aplay`` on ALSA bodies). Same protocol
    as every provider: honest degrade when binaries are missing.
    """

    def __init__(self, *, piper_bin: str = "piper", model: str = "", player_bin: str = "aplay") -> None:
        self._piper_bin = piper_bin
        self._model = model
        self._player_bin = player_bin

    def available(self) -> bool:
        import shutil

        return (
            bool(self._model)
            and os.path.isfile(self._model)
            and shutil.which(self._piper_bin) is not None
            and shutil.which(self._player_bin) is not None
        )

    def synthesize(self, text: str) -> AudioOut:
        import shutil
        import subprocess
        import tempfile

        cleaned = (text or "").strip()
        if not cleaned:
            raise ValueError("cannot synthesize empty speech")
        if not self.available():
            missing = [p for p in (self._piper_bin, self._player_bin) if shutil.which(p) is None]
            if not self._model or not os.path.isfile(self._model):
                missing.append(f"voice-model:{self._model or '-'}")
            raise RuntimeError(
                f"Piper TTS unavailable (missing: {', '.join(missing)}); "
                "install piper + a voice model or use the say provider"
            )
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name
        try:
            subprocess.run(
                [self._piper_bin, "--model", self._model, "-f", wav_path],
                input=cleaned.encode("utf-8"),
                check=True,
                timeout=60,
            )
            subprocess.run([self._player_bin, wav_path], check=True, timeout=60)
        finally:
            with contextlib.suppress(OSError):
                os.unlink(wav_path)
        return AudioOut(text=cleaned, provider="piper", spoken=True)


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
