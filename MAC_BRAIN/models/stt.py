from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

# Default location for downloaded Whisper weights. Kept under the git-ignored
# mac_test_results/ tree so model weights are never committed to Git.
DEFAULT_WHISPER_CACHE = Path(__file__).resolve().parents[2] / "mac_test_results" / "STT" / "models"


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str
    confidence: float
    audio_path: str
    provider: str
    model_id: str


class SpeechToTextProvider(Protocol):
    """Capability boundary for local speech-to-text providers."""

    def transcribe(self, audio_path: str | Path) -> TranscriptionResult: ...


class WhisperSTTProvider:
    """Real local speech-to-text using faster-whisper.

    Runs fully offline after a one-time model download into the git-ignored
    workspace cache. CPU/int8 is the safe default; MPS/CUDA can be enabled by
    passing a different ``device``/``compute_type``.
    """

    model_id_prefix = "faster-whisper"

    def __init__(
        self,
        *,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        model_cache: str | Path | None = None,
    ) -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "WhisperSTTProvider requires faster-whisper. Install with "
                "`.venv/bin/pip install faster-whisper`."
            ) from exc
        cache = Path(model_cache) if model_cache else DEFAULT_WHISPER_CACHE
        cache.mkdir(parents=True, exist_ok=True)
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model = WhisperModel(model_size, device=device, compute_type=compute_type, download_root=str(cache))

    @property
    def model_id(self) -> str:
        return f"{self.model_id_prefix}:{self._model_size}"

    def transcribe(self, audio_path: str | Path) -> TranscriptionResult:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"audio file not found: {path}")
        segments, info = self._model.transcribe(str(path))
        text = " ".join(segment.text.strip() for segment in segments).strip()
        return TranscriptionResult(
            text=text,
            language=info.language,
            confidence=float(info.language_probability),
            audio_path=str(path),
            provider="whisper",
            model_id=self.model_id,
        )


class DeterministicSTTProvider:
    """Contract-test STT provider that does not run learned inference.

    Used by CI and deterministic Mac tests to exercise the STT capability
    boundary without a model download.
    """

    def __init__(self, text: str = "hello from novi") -> None:
        self._text = text

    def transcribe(self, audio_path: str | Path) -> TranscriptionResult:
        return TranscriptionResult(
            text=self._text,
            language="en",
            confidence=1.0,
            audio_path=str(Path(audio_path)),
            provider="deterministic",
            model_id="deterministic:test",
        )
