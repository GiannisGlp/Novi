"""Face identity: embeddings -> PersonIdentity tiers (doc 02 §2).

Closes gap G4's face half: the injection boundary exists in the brain;
this module is the concrete provider. ArcFace-class embedding backends
plug in later; CI uses plain float vectors and cosine similarity.

Rules:
- enrollment is explicit (conversational upstream); never a silent write;
- ambiguous similarity never best-guesses an identity;
- cross-modal: voiceprint agreement escalates recognized -> verified,
  disagreement never escalates;
- privacy gate: camera privacy off refuses all biometric processing and
  audits the transition.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass


class IdentityTier(enum.Enum):
    UNKNOWN = "unknown"
    RECOGNIZED = "recognized"
    VERIFIED = "verified"


@dataclass(frozen=True)
class FaceObservation:
    """One detected face ready for identity resolution."""

    embedding: tuple[float, ...]
    frame_id: str
    captured_at: str = ""
    bbox: tuple[int, int, int, int] | None = None


@dataclass(frozen=True)
class IdentityDecision:
    tier: IdentityTier
    person_id: str | None
    reason: str
    similarity: float = 0.0
    frame_id: str = ""
    new_person_proposal: bool = False


def _cosine(a: tuple[float, ...] | list[float], b: tuple[float, ...] | list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


@dataclass
class _Enrolled:
    person_id: str
    display_name: str
    embedding: list[float]
    enrolled_frame_id: str
    quality: float


class FaceIdentifier:
    """Embedding-match identity with tiered trust and a privacy gate."""

    def __init__(
        self,
        *,
        tau_match: float = 0.90,
        tau_ambig: float = 0.75,
        privacy_enabled: bool = True,
    ) -> None:
        self.tau_match = tau_match
        self.tau_ambig = tau_ambig
        self._privacy = privacy_enabled
        self._people: dict[str, _Enrolled] = {}
        self.audit_log: list[dict] = []

    # -- privacy -------------------------------------------------------------

    @property
    def privacy_enabled(self) -> bool:
        return self._privacy

    def set_privacy(self, enabled: bool, *, reason: str) -> None:
        self._privacy = enabled
        self.audit_log.append(
            {
                "kind": "privacy-enabled" if enabled else "privacy-disabled",
                "reason": reason,
            }
        )

    # -- enrollment -------------------------------------------------------------

    def enroll(
        self,
        display_name: str,
        embedding: list[float],
        *,
        frame_id: str,
        quality: float = 1.0,
    ) -> str:
        self._require_privacy("enroll")
        person_id = f"person-{len(self._people) + 1:04d}"
        self._people[person_id] = _Enrolled(
            person_id=person_id,
            display_name=display_name,
            embedding=list(embedding),
            enrolled_frame_id=frame_id,
            quality=quality,
        )
        return person_id

    # -- observation ---------------------------------------------------------------

    def observe(
        self,
        embedding: list[float],
        *,
        frame_id: str,
        speaker_person_id: str | None = None,
    ) -> IdentityDecision:
        return self.observe_observation(
            FaceObservation(embedding=tuple(embedding), frame_id=frame_id),
            speaker_person_id=speaker_person_id,
        )

    def observe_observation(
        self,
        obs: FaceObservation,
        *,
        speaker_person_id: str | None = None,
    ) -> IdentityDecision:
        self._require_privacy("observe")

        best_id, best_sim = None, -1.0
        for pid, p in self._people.items():
            sim = _cosine(obs.embedding, p.embedding)
            if sim > best_sim:
                best_id, best_sim = pid, sim

        def _dec(tier: IdentityTier, reason: str, pid: str | None = None, proposal: bool = False):
            return IdentityDecision(
                tier=tier,
                person_id=pid,
                reason=reason,
                similarity=max(0.0, best_sim),
                frame_id=obs.frame_id,
                new_person_proposal=proposal,
            )

        if best_id is None or best_sim < self.tau_ambig:
            return _dec(IdentityTier.UNKNOWN, "no-match", None, proposal=True)
        if best_sim < self.tau_match:
            return _dec(IdentityTier.UNKNOWN, "ambiguous")

        # recognized — cross-modal check may escalate or hold
        if speaker_person_id is not None and speaker_person_id != best_id:
            return _dec(IdentityTier.RECOGNIZED, "speaker-disagreement", best_id)

        tier = (
            IdentityTier.VERIFIED
            if speaker_person_id == best_id
            else IdentityTier.RECOGNIZED
        )
        return _dec(tier, "face+voice-agree" if tier is IdentityTier.VERIFIED else "face-match", best_id)

    # -- internals ----------------------------------------------------------------------

    def _require_privacy(self, op: str) -> None:
        if not self._privacy:
            raise PermissionError(
                f"face {op} refused: camera privacy state disables biometric processing"
            )
