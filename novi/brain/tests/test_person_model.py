"""Tests for novi/brain/person_model.py — persistent person identity.

Plan 22 Phase 2 (Tasks 2.1–2.4) and the required identity test classes:
- same face repeatedly resolves to same person;
- unknown face remains unknown;
- ambiguous face remains ambiguous;
- contradictory modalities preserve contradiction;
- confidence never becomes 1.0 without evidence.
"""

from __future__ import annotations

import unittest

from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.person_model import (
    _CONFIDENCE_CEILING,
    IdentityStatus,
    PersonRegistry,
)


class PersonRegistryLifecycleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.reg = PersonRegistry()

    def observe(self, name=None, conf=0.9, modality="face", person="person-1", cycle=1, **kw):
        return self.reg.observe(
            person_id=person, name=name, confidence=conf, modality=modality,
            cycle=cycle, **kw,
        )

    def test_unknown_face_remains_unknown(self) -> None:
        model = self.observe(name=None, conf=0.35)
        self.assertEqual(model.identity_status, IdentityStatus.UNKNOWN)
        self.assertFalse(model.known)
        model = self.observe(name=None, conf=0.45, cycle=2)
        self.assertEqual(model.identity_status, IdentityStatus.UNKNOWN)

    def test_low_face_match_is_candidate_not_recognized(self) -> None:
        model = self.observe(name="vano", conf=0.61)
        self.assertEqual(model.identity_status, IdentityStatus.CANDIDATE)
        self.assertFalse(model.known)

    def test_high_face_match_with_repetition_becomes_recognized(self) -> None:
        self.observe(name="vano", conf=0.96, cycle=1)
        model = self.observe(name="vano", conf=0.97, cycle=2)
        self.assertEqual(model.identity_status, IdentityStatus.RECOGNIZED)
        self.assertTrue(model.known)
        self.assertEqual(model.canonical_name, "vano")

    def test_cross_modal_evidence_confirms(self) -> None:
        self.observe(name="vano", conf=0.9, modality="face", cycle=1)
        model = self.observe(name="vano", conf=0.94, modality="voice", cycle=2)
        self.assertEqual(model.identity_status, IdentityStatus.CONFIRMED)

    def test_same_face_repeatedly_resolves_to_same_person(self) -> None:
        for cycle in range(1, 6):
            self.observe(name="vano", conf=0.95, modality="face", cycle=cycle)
        self.assertIs(self.reg.resolve("vano"), self.reg.person("person-1"))
        self.assertEqual(self.reg.resolve("vano").person_id, "person-1")  # type: ignore[union-attr]

    def test_conflicting_modalities_preserve_contradiction(self) -> None:
        # face says Vano .96, voice says unknown .72 — contradiction retained,
        # identity confidence lowered, match never forced.
        self.observe(name="vano", conf=0.96, modality="face", cycle=1)
        model = self.observe(name="unknown", conf=0.72, modality="voice", cycle=2)
        # the voice no-match discounted the belief instead of adding a rival
        self.assertEqual(model.canonical_name, "vano")
        self.assertLess(model.confidence, 0.96)
        # contradiction blocked confirmation (needs >= 0.9)
        self.assertNotEqual(model.identity_status, IdentityStatus.CONFIRMED)
        self.assertIn("voice", model.modalities_seen)

    def test_ambiguous_face_remains_ambiguous(self) -> None:
        # balanced competing evidence stays ambiguous across cycles
        self.observe(name="vano", conf=0.7, modality="face", cycle=1)
        model = self.observe(name="davit", conf=0.68, modality="face", cycle=2)
        self.assertEqual(model.identity_status, IdentityStatus.AMBIGUOUS)
        model = self.observe(name="vano", conf=0.71, modality="face", cycle=3)
        model = self.observe(name="davit", conf=0.69, modality="face", cycle=4)
        self.assertEqual(model.identity_status, IdentityStatus.AMBIGUOUS)

    def test_confidence_never_reaches_certainty(self) -> None:
        model = None
        for cycle in range(1, 21):
            model = self.observe(name="vano", conf=0.99, modality="face", cycle=cycle)
        self.assertLessEqual(model.confidence, _CONFIDENCE_CEILING)  # type: ignore[union-attr]
        self.assertLess(model.confidence, 1.0)  # type: ignore[union-attr]

    def test_reject_emits_lost_and_sticks(self) -> None:
        self.observe(name="vano", conf=0.95, cycle=1)
        self.assertTrue(self.reg.reject("person-1"))
        self.assertEqual(self.reg.person("person-1").identity_status, IdentityStatus.REJECTED)  # type: ignore[union-attr]
        # explicit rejection survives further weak observations
        self.observe(name="vano", conf=0.3, cycle=2)
        self.assertEqual(self.reg.person("person-1").identity_status, IdentityStatus.REJECTED)  # type: ignore[union-attr]


class PersonRegistryEventTest(unittest.TestCase):
    def test_recognized_event_emitted_on_transition(self) -> None:
        reg = PersonRegistry()
        reg.observe(person_id="p1", name="vano", confidence=0.6, modality="face", cycle=1)
        self.assertEqual(reg.drain_events(), [])  # CANDIDATE is not a recognition
        reg.observe(person_id="p1", name="vano", confidence=0.97, modality="face", cycle=2)
        events = reg.drain_events()
        types = [e["event_type"] for e in events]
        self.assertIn("identity.recognized", types)
        self.assertEqual(events[-1]["name"], "vano")
        self.assertGreater(events[-1]["confidence"], 0.8)

    def test_ambiguous_event_emitted(self) -> None:
        reg = PersonRegistry()
        reg.observe(person_id="p1", name="vano", confidence=0.7, modality="face", cycle=1)
        reg.drain_events()
        reg.observe(person_id="p1", name="davit", confidence=0.68, modality="face", cycle=2)
        events = reg.drain_events()
        self.assertEqual(events[-1]["event_type"], "identity.ambiguous")

    def test_reidentified_after_rejection(self) -> None:
        reg = PersonRegistry()
        reg.observe(person_id="p1", name="vano", confidence=0.95, modality="face", cycle=1)
        reg.drain_events()
        reg.reject("p1")
        reg.drain_events()
        reg.observe(person_id="p1", name="vano", confidence=0.98, modality="face", cycle=3)
        events = reg.drain_events()
        self.assertEqual(events[-1]["event_type"], "identity.reidentified")

    def test_no_spurious_events_for_steady_state(self) -> None:
        reg = PersonRegistry()
        reg.observe(person_id="p1", name="vano", confidence=0.95, modality="face", cycle=1)
        reg.drain_events()
        reg.observe(person_id="p1", name="vano", confidence=0.96, modality="face", cycle=2)
        self.assertEqual(reg.drain_events(), [])


class PersonModelFieldsTest(unittest.TestCase):
    def test_biometric_refs_are_opaque_not_embeddings(self) -> None:
        reg = PersonRegistry()
        reg.observe(
            person_id="p1", name="vano", confidence=0.95, modality="face",
            cycle=1, face_ref="face-store://enroll/vano/0001",
        )
        model = reg.person("p1")
        self.assertEqual(model.face_identity_refs, ["face-store://enroll/vano/0001"])  # type: ignore[union-attr]
        # no raw embedding/vector ever stored on the model
        snap = model.snapshot()  # type: ignore[union-attr]
        self.assertNotIn("embedding", snap)
        self.assertNotIn("vector", snap)

    def test_interactions_and_preferences_recorded(self) -> None:
        reg = PersonRegistry()
        reg.observe(person_id="p1", name="vano", confidence=0.9, modality="face", cycle=1)
        reg.note_interaction("p1", "discussed camera integration", cycle=5)
        reg.note_interaction("p1", "asked about architecture", cycle=6)
        reg.learn_preference("p1", "verbosity", "short")
        model = reg.person("p1")
        self.assertEqual(model.interaction_count, 2)  # type: ignore[union-attr]
        self.assertEqual(len(model.recent_interactions), 2)  # type: ignore[union-attr]
        self.assertEqual(model.preferences["verbosity"], "short")  # type: ignore[index]

    def test_snapshot_round_trip(self) -> None:
        reg = PersonRegistry()
        reg.observe(
            person_id="p1", name="vano", confidence=0.96, modality="face", cycle=1,
            location="office", face_ref="face-store://v1",
        )
        reg.observe(person_id="p1", name="vano", confidence=0.9, modality="voice", cycle=2)
        reg.note_interaction("p1", "hello", cycle=3)
        restored = PersonRegistry.from_snapshot(reg.snapshot())
        model = restored.person("p1")
        self.assertEqual(model.canonical_name, "vano")  # type: ignore[union-attr]
        self.assertEqual(model.identity_status, IdentityStatus.CONFIRMED)  # type: ignore[union-attr]
        self.assertEqual(model.usual_locations, ["office"])  # type: ignore[union-attr]
        self.assertEqual(model.interaction_count, 1)  # type: ignore[union-attr]
        self.assertAlmostEqual(model.confidence, reg.person("p1").confidence)  # type: ignore[union-attr]

    def test_unknown_persons_listed_separately(self) -> None:
        reg = PersonRegistry()
        reg.observe(person_id="p1", name="vano", confidence=0.95, modality="face", cycle=1)
        reg.observe(person_id="p2", name=None, confidence=0.4, modality="face", cycle=1)
        self.assertEqual([p.person_id for p in reg.recognized_persons()], ["p1"])
        self.assertEqual(len(reg.all_persons()), 2)


class PersonRegistryEngineWiringTest(unittest.TestCase):
    """Phase 2 Task 2.4: recognition events flow through the brain's event bus
    and the registry persists into the durable store."""

    def setUp(self):
        try:
            import cv2  # noqa: F401
            import numpy as np
        except Exception:
            self.skipTest("opencv not available")
        self.np = np

    def test_face_recognition_feeds_registry_and_emits_event(self) -> None:
        import dataclasses

        from novi.brain.b2_perception import SpecialistPerception
        from novi.brain.face_id import OpenCVFaceID
        from novi.brain.tests.test_identity_providers import _FaceBackend
        from novi.brain.tests.test_mac_brain import FakeCamera

        payload = self.np.random.default_rng(9).integers(0, 255, size=(96, 96, 3), dtype=self.np.uint8)

        class PixelCamera(FakeCamera):
            def read(self):
                return dataclasses.replace(super().read(), payload=payload)

        fid = OpenCVFaceID(threshold=0.9)
        fid.enroll("vano", payload)
        brain = MacBrain(
            camera=PixelCamera(),
            perception=SpecialistPerception(_FaceBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
            face_id=fid,
        )
        brain.start()
        try:
            brain.step()
            model = brain.person_registry.person("person")
            self.assertIsNotNone(model)
            assert model is not None
            self.assertEqual(model.canonical_name, "vano")
            self.assertIn("face", model.modalities_seen)
            self.assertEqual(model.face_identity_refs, ["face:vano"])
            event_types = [e["event_type"] for e in brain.events]
            self.assertIn("identity.recognized", event_types)
        finally:
            brain.stop()

    def test_registry_persists_through_durable_store(self) -> None:
        import tempfile
        from pathlib import Path

        from novi.brain.b2_perception import DeterministicPerceptionBackend, SpecialistPerception
        from novi.brain.models import TranscriptionResult
        from novi.brain.tests.test_identity_providers import _FaceBackend
        from novi.brain.tests.test_mac_brain import FakeCamera

        with tempfile.TemporaryDirectory() as tmp:
            store_path = str(Path(tmp) / "brain.db")
            brain = MacBrain(
                camera=FakeCamera(),
                perception=SpecialistPerception(_FaceBackend()),
                config=MacBrainConfig(curiosity_enabled=False),
                store_path=store_path,
            )
            brain.start()
            # speech self-introduction binds the current speaker's name
            brain.ingest_transcript(
                TranscriptionResult(
                    text="i am vano", confidence=0.9, language="en",
                    audio_path="test.wav", provider="test", model_id="test",
                )
            )
            self.assertIsNotNone(brain.person_registry.person("person"))
            brain.stop()
            # a fresh brain on the same store restores the registry
            brain2 = MacBrain(
                camera=FakeCamera(),
                perception=SpecialistPerception(DeterministicPerceptionBackend()),
                config=MacBrainConfig(curiosity_enabled=False),
                store_path=store_path,
            )
            model = brain2.person_registry.person("person")
            self.assertIsNotNone(model)
            assert model is not None
            self.assertEqual(model.canonical_name, "vano")
            # brain2 never started — nothing to stop; registry was restored in __init__


if __name__ == "__main__":
    unittest.main()
