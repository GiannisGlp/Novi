"""Real speaker recognition: Resemblyzer d-vector voiceprints (doc 17 §8).

Closes the "recognize voices" gap: enroll a person's voice once, then
match every incoming audio clip to the closest enrolled speaker.

- RealVoiceEmbedder: wav -> L2-normalized 256-d embedding (CPU);
- RealSpeakerRecognizer: enroll/match over those embeddings; optionally
  persists every enrollment into RecognitionStore (VOICE kind) so
  speaker identity survives restarts.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import numpy as np


class RealVoiceEmbedder:
    """Resemblyzer VoiceEncoder wrapper: wav file -> embedding vector."""

    def __init__(self) -> None:
        from resemblyzer import VoiceEncoder

        self._encoder = VoiceEncoder()

    def embed_wav(self, path: str | Path) -> np.ndarray:
        """Load 16k mono wav and return an L2-normalized 256-d embedding."""
        from resemblyzer import preprocess_wav

        wav = preprocess_wav(Path(path))
        emb = self._encoder.embed_utterance(wav)
        norm = float(np.linalg.norm(emb))
        return emb / norm if norm > 0 else emb


class RealSpeakerRecognizer:
    """Enroll voices, match incoming clips to the closest speaker."""

    def __init__(
        self,
        *,
        store: Any | None = None,
        embedder: RealVoiceEmbedder | None = None,
        default_min_similarity: float = 0.75,
    ) -> None:
        self._embedder = embedder or RealVoiceEmbedder()
        self._store = store
        self._lock = threading.RLock()
        # label -> embedding (in-memory cache of enrolled voiceprints)
        self._voices: dict[str, np.ndarray] = {}
        self.default_min_similarity = default_min_similarity

    # -- enrollment -----------------------------------------------------------

    def enroll(self, label: str, wav_path: str | Path) -> str:
        """Embed a voice sample and remember it under this person's label."""
        emb = self._embedder.embed_wav(wav_path)
        with self._lock:
            self._voices[label] = emb
        if self._store is not None:
            pid = self._store.enroll(
                kind=self._voice_kind(),
                label=label,
                embedding=[float(x) for x in emb],
                provenance={"source": "resemblyzer", "wav": str(wav_path)},
            )
        else:
            pid = f"voice-{label.lower().replace(' ', '-')}"
        return pid

    @staticmethod
    def _voice_kind():
        from novi.integration.recognition_store import RecognitionKind

        return RecognitionKind.VOICE

    # -- matching -----------------------------------------------------------------

    def match(
        self,
        wav_path: str | Path,
        *,
        min_similarity: float | None = None,
    ):
        """Return the best Match above threshold, else None."""
        floor = min_similarity if min_similarity is not None else self.default_min_similarity
        probe = self._embedder.embed_wav(wav_path)
        best_label, best_sim = None, -1.0
        with self._lock:
            items = list(self._voices.items())
        for label, emb in items:
            sim = float(np.dot(probe, emb))  # both normalized => cosine
            if sim > best_sim:
                best_label, best_sim = label, sim
        if best_label is None or best_sim < floor:
            return None

        from novi.integration.recognition_store import Match, RecognitionKind

        pid = f"voice-{best_label.lower().replace(' ', '-')}"
        if self._store is not None:
            m = self._store.match(RecognitionKind.VOICE, [float(x) for x in probe], min_similarity=floor)
            if m is not None and m.label == best_label:
                pid = m.person_id
        return Match(kind=RecognitionKind.VOICE, label=best_label, person_id=pid, similarity=best_sim, enrollment_id=-1)

    # -- introspection ---------------------------------------------------------------

    @property
    def labels(self) -> list[str]:
        with self._lock:
            return list(self._voices)
