"""Tests: face identity — embeddings, tiers, ambiguity refusal,
cross-modal verification, privacy gating (doc 02 §2).

Contract:
- observe(face_embedding) -> IdentityDecision{tier: unknown|recognized|verified};
- enrolled match within tau -> recognized; between tau_match and tau_ambig
  stays unknown (ambiguous never best-guesses);
- no-match below tau_ambig -> new-person proposal (enrollment is
  conversational upstream, never a silent write here);
- voiceprint agreement escalates recognized -> verified;
- camera privacy off => processing refused outright.
"""

from __future__ import annotations

import pytest

from novi.perception.faces import FaceIdentifier, FaceObservation, IdentityTier


def _emb(base: list[float], jitter: float = 0.0) -> list[float]:
    return [v + jitter for v in base]


def _at_cos(c: float) -> list[float]:
    """Unit vector whose cosine to [1,0,0,0] is exactly c."""
    s = (1.0 - c * c) ** 0.5
    return [c, s, 0.0, 0.0]


ANNA = [1.0, 0.0, 0.0, 0.0]
BOB = [0.0, 1.0, 0.0, 0.0]


class TestEnrollmentAndRecognition:
    def test_unenrolled_face_is_unknown_new_person(self):
        fid = FaceIdentifier()
        d = fid.observe(_emb(ANNA), frame_id="f1")
        assert d.tier is IdentityTier.UNKNOWN
        assert d.new_person_proposal is True
        assert d.person_id is None

    def test_enroll_then_recognize(self):
        fid = FaceIdentifier()
        anna = fid.enroll("Anna", _emb(ANNA), frame_id="f0", quality=0.95)
        d = fid.observe(_emb(ANNA), frame_id="f1")
        assert d.tier is IdentityTier.RECOGNIZED
        assert d.person_id == anna

    def test_other_person_still_unknown(self):
        fid = FaceIdentifier()
        fid.enroll("Anna", _emb(ANNA), frame_id="f0")
        d = fid.observe(_emb(BOB), frame_id="f1")
        assert d.tier is IdentityTier.UNKNOWN
        assert d.person_id is None


class TestAmbiguityRefusal:
    def test_between_thresholds_stays_unknown(self):
        fid = FaceIdentifier(tau_match=0.90, tau_ambig=0.75)
        fid.enroll("Anna", _emb(ANNA), frame_id="f0")
        # similarity exactly 0.86: above ambiguity floor, below match bar
        d = fid.observe(_at_cos(0.86), frame_id="f1")
        assert d.tier is IdentityTier.UNKNOWN
        assert d.reason == "ambiguous"
        assert d.similarity == pytest.approx(0.86, abs=1e-6)

    def test_below_ambiguity_floor_is_proposal_not_guess(self):
        fid = FaceIdentifier(tau_match=0.90, tau_ambig=0.75)
        fid.enroll("Anna", _emb(ANNA), frame_id="f0")
        # similarity exactly 0.66: not plausibly Anna
        d = fid.observe(_at_cos(0.66), frame_id="f1")
        assert d.tier is IdentityTier.UNKNOWN
        assert d.reason == "no-match"
        assert d.new_person_proposal is True


class TestCrossModalVerification:
    def test_voiceprint_agreement_escalates_to_verified(self):
        fid = FaceIdentifier()
        anna = fid.enroll("Anna", _emb(ANNA), frame_id="f0")
        d = fid.observe(_emb(ANNA), frame_id="f1", speaker_person_id=anna)
        assert d.tier is IdentityTier.VERIFIED

    def test_voiceprint_disagreement_keeps_recognized(self):
        fid = FaceIdentifier()
        anna = fid.enroll("Anna", _emb(ANNA), frame_id="f0")
        bob = fid.enroll("Bob", _emb(BOB), frame_id="f0")
        d = fid.observe(_emb(ANNA), frame_id="f1", speaker_person_id=bob)
        assert d.tier is IdentityTier.RECOGNIZED
        assert d.reason == "speaker-disagreement"

    def test_verified_requires_face_match_first(self):
        fid = FaceIdentifier()
        fid.enroll("Anna", _emb(ANNA), frame_id="f0")
        # stranger face claims to be Anna's speaker id: face gate wins
        d = fid.observe(_emb(BOB), frame_id="f1", speaker_person_id="anna-id")
        assert d.tier is IdentityTier.UNKNOWN


class TestPrivacyGate:
    def test_privacy_off_refuses_processing(self):
        fid = FaceIdentifier(privacy_enabled=False)
        with pytest.raises(PermissionError):
            fid.observe(_emb(ANNA), frame_id="f1")
        with pytest.raises(PermissionError):
            fid.enroll("X", _emb(BOB), frame_id="f0")

    def test_privacy_transitions_audited(self):
        fid = FaceIdentifier()
        fid.set_privacy(False, reason="owner request")
        fid.set_privacy(True, reason="owner restored")
        kinds = [(e["kind"], e["reason"]) for e in fid.audit_log]
        assert ("privacy-disabled", "owner request") in kinds
        assert ("privacy-enabled", "owner restored") in kinds


class TestProvenance:
    def test_observation_records_frame_and_similarity(self):
        fid = FaceIdentifier()
        anna = fid.enroll("Anna", _emb(ANNA), frame_id="f0")
        obs = FaceObservation(embedding=_emb(ANNA), frame_id="f7", captured_at="t7")
        d = fid.observe_observation(obs)
        assert d.person_id == anna
        assert d.similarity == pytest.approx(1.0)
        assert d.frame_id == "f7"
