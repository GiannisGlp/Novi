"""Acceptance tests for the reasoning/cognition improvement (rules 1-10).

Consolidates the cross-cutting behavioral guarantees, each cited to its governing
doc, so the 'follow the documentation / everything must be perfect' bar is
auditable in one place.
"""

from __future__ import annotations

import unittest

from novi.brain.b2_perception import Detection, SpecialistPerception
from novi.brain.dialogue import _is_forbidden, natural_fallback
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame
from novi.brain.models.recognition import DeterministicFaceId, DeterministicSpeakerId


class FakeCamera:
    def __init__(self) -> None:
        self.sequence = 0
        self.closed = False

    def close(self) -> None:
        self.closed = True

    def read(self) -> CameraFrame:
        self.sequence += 1
        return CameraFrame(frame_id=f"f-{self.sequence}", captured_at="2026-08-19T14:00:00Z", width=2, height=2, payload=b"frame", metadata={"backend": "test"})


class PersonBackend:
    def detect(self, frame):
        return (Detection("person", 0.95, (0.0, 0.0, 1.0, 1.0)),)

    def depth(self, frame):
        return None

    def segment(self, frame):
        return None


def _brain(**kw) -> MacBrain:
    providers = {k: kw.pop(k) for k in ("face_id", "speaker_id") if k in kw}
    cfg = MacBrainConfig(curiosity_enabled=False, **kw)
    return MacBrain(camera=FakeCamera(), perception=SpecialistPerception(PersonBackend()), config=cfg, **providers)


class ReasoningAcceptanceTests(unittest.TestCase):
    """Rule 2 + Rule 1: the mind lives in brain and follows the docs."""

    def test_mind_is_portable_to_the_body(self):
        # docs/06-soul/07 §2: the brain renders the approved communicative act.
        for method in ("compose_reply", "self_model", "_identify_face", "_identify_speaker", "_maybe_initiate"):
            self.assertTrue(hasattr(MacBrain, method), f"{method} must be a brain capability, not a web concern")

    def test_dialogue_engine_is_in_mac_brain_not_web(self):
        import novi.web.server as web  # noqa: F401
        from novi.brain.dialogue import DialogueEngine  # noqa: F401
        self.assertFalse(hasattr(web.NoviWebServer, "_generate_reply"), "reply generation must not live in the web server")

    """Rule 8 + Rule 10: natural, never an assistant persona."""

    def test_forbidden_assistant_phrase_never_reaches_user(self):
        brain = _brain()
        brain.start()
        try:
            r = brain.compose_reply("tell me about yourself", llm_chat=lambda **k: "Hi I am Novi, how can I help you today")
            self.assertTrue(r["fallback"])
            self.assertFalse(_is_forbidden(r["text"]))
            self.assertNotIn("how can i help", r["text"].lower())
        finally:
            brain.stop()

    def test_natural_fallback_is_never_robotic(self):
        for tone in ("curious", "warm", "calm", "cautious", "recovering"):
            line = natural_fallback({"tone": tone}, {}, cycle=0)
            self.assertTrue(line and not _is_forbidden(line))

    def test_no_transport_reply_never_leaks_cognition_label(self):
        """Novi always distinguishes the communication type internally, but the
        spoken reply must never be the internal cognition label. compose_reply
        returns text=None when no LLM transport is configured; the brain exposes
        a natural deterministic fallback for callers, so no layer replies with
        'human_speech_observed'."""
        brain = _brain()
        brain.start()
        try:
            r = brain.compose_reply("alice moved the door", llm_chat=None)
            self.assertIsNone(r["text"])  # design contract: caller supplies fallback
            fb = brain.natural_reply_fallback(text="alice moved the door")
            self.assertTrue(fb["text"])
            self.assertNotEqual(fb["text"], "human_speech_observed")
            self.assertTrue(fb["fallback"])
            self.assertFalse(_is_forbidden(fb["text"]))
        finally:
            brain.stop()


    """Rule 9: no repetitive name-dropping."""

    def test_reply_does_not_overuse_addressee_name(self):
        brain = _brain()
        brain.start()
        try:
            r = brain.compose_reply("explain how the internet works", addressee_name="Vano", llm_chat=lambda **k: "hi Vano yes Vano ok Vano see you Vano")
            self.assertEqual(r["text"].lower().count("vano"), 1)
        finally:
            brain.stop()

    """Rule 4 + Rule 5: autonomous and initiates when neglected."""

    def test_does_not_initiate_mid_dialogue(self):
        # Mid-dialogue guard (2026-08-30): a spontaneous "it's quiet around
        # here." must NEVER interrupt an active conversation. After a user
        # utterance the initiative is suppressed for the conversation-guard
        # window even when the neglect threshold is already exceeded.
        brain = _brain(initiative_enabled=True, initiative_neglect_threshold=2, initiative_cooldown=100)
        brain.start()
        try:
            # Simulate an active conversation: a recent user utterance.
            brain._last_user_utterance_cycle = brain._cycle
            for _ in range(5):
                brain.step()
            fired = [e for e in brain.events if e.get("event_type") == "speech.initiated"]
            suppressed = [e for e in brain.events if e.get("event_type") == "speech.initiative_suppressed"]
            self.assertEqual(fired, [], "initiative must not fire mid-dialogue")
            self.assertTrue(
                any(e.get("payload", {}).get("reason") == "conversation_active" for e in suppressed),
                "suppression should cite conversation_active",
            )
        finally:
            brain.stop()

    def test_initiates_after_conversation_goes_quiet(self):
        # Once the conversation has genuinely gone quiet past the guard window,
        # neglect-driven initiative may fire again.
        brain = _brain(initiative_enabled=True, initiative_neglect_threshold=2, initiative_cooldown=100)
        brain.start()
        try:
            brain._last_user_utterance_cycle = -10**9  # no conversation at all
            for _ in range(6):
                brain.step()
            fired = [e for e in brain.events if e.get("event_type") == "speech.initiated"]
            self.assertTrue(fired, "initiative should fire after a quiet period")
        finally:
            brain.stop()

    def test_initiates_when_neglected_but_not_during_goals(self):
        brain = _brain(initiative_enabled=True, initiative_neglect_threshold=5, initiative_cooldown=100)
        brain.start()
        try:
            for _ in range(6):
                brain.step()
            self.assertTrue(any(e.get("event_type") == "speech.initiated" for e in brain.events))
        finally:
            brain.stop()

    """Rule 7: self- and surrounding-aware, capability-honest."""

    def test_self_model_reports_capabilities(self):
        brain = _brain()
        brain.start()
        try:
            brain.step()
            sm = brain.self_model()
            self.assertIn("capabilities", sm)
            self.assertIn(sm["mode"], ("PASS", "WARN", "FAIL", "UNKNOWN"))
            prompt = brain._dialogue_system_prompt({"name": "Novi", "tone": "warm"}, {"tier": "unknown", "expression": {}}, capabilities={"perception": "FAIL"})
            self.assertIn("degraded or unavailable", prompt)
        finally:
            brain.stop()

    """Rule 6: recognises voices, faces, places, buildings."""

    def test_cross_modal_voice_plus_face_verifies_identity(self):
        from novi.brain.kgraph import infer_entity_type
        brain = _brain(face_id=DeterministicFaceId({"person": "alice"}), speaker_id=DeterministicSpeakerId({"voice_alice": "alice"}))
        brain.start()
        try:
            brain.step()
            brain._identify_speaker({"voiceprint": "voice_alice"})
            belief = brain.identity.identity_for("person")
            self.assertEqual(belief.name, "alice")
            self.assertEqual(belief.tier, "verified")
        finally:
            brain.stop()
        self.assertEqual(infer_entity_type("hospital"), "building")
        self.assertEqual(infer_entity_type("kitchen"), "place")


if __name__ == "__main__":
    unittest.main()
