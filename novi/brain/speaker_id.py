"""Speaker identity provider for the Mac Brain (gap-audit plan Phase B2).

A dependency-light voice-fingerprint provider behind the engine's
``speaker_id`` boundary (``identify(audio_features={"audio_path": ...})``).

Design boundaries:
  - Local/offline only; no cloud, no heavy model download. numpy is used when
    importable (it ships with the neural extra) and the provider reports
    unavailable otherwise — the brain loop never depends on it.
  - Recognition is evidence, not identity: results are fed to PersonIdentity
    which tiers them (detected/probable/verified) under governance.
  - Deterministic: same waveform ⇒ same print ⇒ same match.
"""

from __future__ import annotations

import math
import wave

from .identity import IdentityMatch


def _cosine(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b, strict=False))
    da = math.sqrt(sum(x * x for x in a)) or 1.0
    db = math.sqrt(sum(y * y for y in b)) or 1.0
    return num / (da * db)


def _l2(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


class VoiceprintSpeakerID:
    """Enrolls speaker voiceprints from WAV files and matches utterances.

    The feature vector is a deterministic spectral/energy summary: mean
    log-spaced magnitude spectrum + zero-crossing rate + energy statistics,
    L2-normalized. It is deliberately simple — a stable baseline that a
    stronger model (e.g. ECAPA-TDNN) can replace behind the same boundary.
    """

    def __init__(self, *, threshold: float = 0.82, frame_size: int = 1024, bins: int = 24) -> None:
        self.threshold = float(threshold)
        self.frame_size = int(frame_size)
        self.bins = int(bins)
        self._prints: dict[str, list[list[float]]] = {}  # name -> enrolled prints
        try:
            import numpy as _np  # noqa: F401
            self._np = _np
        except Exception:  # noqa: BLE001 - optional acceleration
            self._np = None

    @property
    def available(self) -> bool:
        return self._np is not None

    # ---- features ----

    def features(self, audio_path: str) -> list[float] | None:
        """Deterministic voiceprint of a WAV file, or None when unreadable."""
        if self._np is None:
            return None
        np = self._np
        try:
            with wave.open(str(audio_path), "rb") as w:
                n_channels = w.getnchannels()
                width = w.getsampwidth()
                raw = w.readframes(w.getnframes())
        except Exception:  # noqa: BLE001 - unreadable audio is just "no evidence"
            return None
        if width != 2 or not raw:
            return None
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        if n_channels > 1:
            samples = samples.reshape(-1, n_channels).mean(axis=1)
        if samples.size < self.frame_size:
            return None
        # Mean magnitude spectrum over frames (log-spaced bin pooling).
        hop = self.frame_size // 2
        frames = [samples[i : i + self.frame_size] for i in range(0, samples.size - self.frame_size + 1, hop)][:64]
        spec = np.zeros(self.bins, dtype=np.float64)
        edges = np.logspace(0, math.log10(self.frame_size // 2), self.bins + 1).astype(int)
        for fr in frames:
            mag = np.abs(np.fft.rfft(fr * np.hanning(self.frame_size)))
            for b in range(self.bins):
                lo, hi = edges[b], max(edges[b + 1], edges[b] + 1)
                spec[b] += float(mag[lo:hi].mean()) if hi <= mag.size else 0.0
        spec /= max(1, len(frames))
        zcr = float(np.mean(np.abs(np.diff(np.sign(samples))) > 0))
        energy = float(np.sqrt(np.mean(samples**2)))
        vec = spec.tolist() + [zcr * 10.0, energy * 10.0]
        return _l2(vec)

    # ---- enrollment / recognition ----

    def enroll(self, name: str, audio_path: str) -> bool:
        """Enroll (or reinforce) a speaker print. Returns True on success."""
        f = self.features(audio_path)
        if f is None:
            return False
        self._prints.setdefault(name, []).append(f)
        return True

    def identify(self, audio_features: dict) -> IdentityMatch | None:
        """Match an utterance against enrolled prints (engine contract)."""
        path = (audio_features or {}).get("audio_path")
        if not path:
            return None
        f = self.features(path)
        if f is None:
            return None
        best_name, best_score = "", -1.0
        for name, prints in self._prints.items():
            score = max(_cosine(f, p) for p in prints)
            if score > best_score:
                best_name, best_score = name, score
        if not best_name or best_score < self.threshold:
            return None
        return IdentityMatch(name=best_name, confidence=min(1.0, best_score), modality="voice")

    def known_speakers(self) -> list[str]:
        return sorted(self._prints)
