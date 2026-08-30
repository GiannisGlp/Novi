"""Tests for novi/brain/object_identity.py — persistent object identity.

Plan 22 Phase 3 and the required object-identity test classes:
- same object reidentified across frames;
- similar objects remain separate;
- object disappearance is emitted once;
- reacquisition links to prior instance when evidence supports it;
- the "mug moved" scenario (plan §1 Example B) surfaces as object.moved.
"""

from __future__ import annotations

import unittest

from novi.brain.object_identity import ObjectRegistry, ObjectStatus


class ObjectIdentityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.reg = ObjectRegistry()

    def observe(self, entity_id="track-1", cls="mug", conf=0.9, cycle=1, location="desk", bbox=(0, 0, 100, 80)):
        return self.reg.observe(
            entity_id=entity_id, cls=cls, confidence=conf, cycle=cycle,
            location=location, bbox=bbox,
        )

    def test_same_object_reidentified_across_frames(self) -> None:
        self.observe(cycle=1)
        self.reg.drain_events()  # the DETECTED event is legitimate
        obj = self.observe(cycle=2)
        self.assertEqual(obj.object_id, "track-1")
        self.assertEqual(obj.cls, "mug")
        self.assertEqual(obj.status, ObjectStatus.TRACKED)
        obj = self.observe(cycle=3, conf=0.95)
        self.assertEqual(obj.status, ObjectStatus.IDENTIFIED)
        self.assertEqual(self.reg.known_instances("mug"), [obj])
        self.assertEqual(len(self.reg.drain_events()), 0)  # steady state, no noise

    def test_similar_objects_remain_separate_instances(self) -> None:
        self.observe(entity_id="track-1", cycle=1)
        self.observe(entity_id="track-2", cycle=1)
        obj1 = self.reg.object("track-1")
        obj2 = self.reg.object("track-2")
        self.assertIsNot(obj1, obj2)
        self.assertEqual(len(self.reg.known_instances("mug")), 2)

    def test_disappearance_emitted_once(self) -> None:
        self.observe(cycle=1)
        self.observe(cycle=2)
        first = self.reg.expire_missing(cycle=15, max_age_cycles=10)
        self.assertEqual([e["event_type"] for e in first], ["object.disappeared"])
        self.assertEqual(self.reg.object("track-1").status, ObjectStatus.LOST)  # type: ignore[union-attr]
        second = self.reg.expire_missing(cycle=25, max_age_cycles=10)
        self.assertEqual(second, [])

    def test_reacquisition_links_to_prior_instance(self) -> None:
        self.observe(entity_id="track-1", cycle=1)
        self.observe(entity_id="track-1", cycle=2)
        self.reg.expire_missing(cycle=15, max_age_cycles=10)
        self.assertEqual(self.reg.object("track-1").status, ObjectStatus.LOST)  # type: ignore[union-attr]
        # the tracker reuses track ids across gaps; the registry must still
        # link the reappearance back to the same instance
        obj = self.observe(entity_id="track-1", cycle=20)
        self.assertEqual(obj.status, ObjectStatus.REACQUIRED)
        self.assertEqual(obj.first_seen, self.reg.object("track-1").first_seen)  # type: ignore[union-attr]
        events = [e["event_type"] for e in self.reg.drain_events()]
        self.assertIn("object.reappeared", events)

    def test_reacquisition_by_appearance_links_unknown_id(self) -> None:
        """A new track id with the same appearance re-identifies the instance:
        the registry returns the *prior instance*, linking the new sighting
        to the same object identity."""
        self.observe(entity_id="track-1", cls="mug", cycle=1, location="desk")
        self.observe(entity_id="track-1", cls="mug", cycle=2)
        self.reg.expire_missing(cycle=15, max_age_cycles=10)
        # tracker restarts numbering after the gap: track-2 is a NEW id now
        obj = self.observe(entity_id="track-2", cls="mug", cycle=20, location="desk")
        self.assertEqual(obj.object_id, "track-1")  # linked to the prior instance
        self.assertEqual(obj.status, ObjectStatus.REACQUIRED)
        events = [e["event_type"] for e in self.reg.drain_events()]
        self.assertIn("object.reappeared", events)

    def test_mug_moved_emits_moved_event_and_tracks_locations(self) -> None:
        # Example B: black mug was on the desk, now in the kitchen.
        self.observe(cycle=1, location="desk")
        self.observe(cycle=2, location="desk")
        self.observe(cycle=3, location="desk")
        obj = self.observe(cycle=4, location="kitchen")
        events = self.reg.drain_events()
        types = [e["event_type"] for e in events]
        self.assertIn("object.moved", types)
        moved = [e for e in events if e["event_type"] == "object.moved"][0]
        self.assertEqual(moved["class"], "mug")
        self.assertEqual(moved["location"], "kitchen")
        self.assertEqual(obj.current_location, "kitchen")
        self.assertEqual(obj.usual_location, "desk")  # most frequent recent location
        # the same move is not re-reported while it stays put
        self.observe(cycle=5, location="kitchen")
        self.assertEqual(self.reg.drain_events(), [])

    def test_instance_identity_confidence_stays_honest(self) -> None:
        # appearance-only re-identification is capped below certainty
        obj = self.observe(conf=0.97, cycle=1)
        self.assertLess(obj.confidence, 1.0)
        self.assertLessEqual(obj.confidence, 0.99)

    def test_snapshot_round_trip(self) -> None:
        self.observe(cycle=1, location="desk")
        self.observe(cycle=2, location="kitchen")
        restored = ObjectRegistry.from_snapshot(self.reg.snapshot())
        obj = restored.object("track-1")
        self.assertEqual(obj.current_location, "kitchen")  # type: ignore[union-attr]
        self.assertIsNotNone(obj)
        assert obj is not None
        self.assertEqual(len(obj.history), 1)  # re-observations only; creation has first_seen
        self.assertEqual(restored.known_instances("mug")[0].object_id, "track-1")

    def test_retire_removes_from_known_instances(self) -> None:
        self.observe(cycle=1)
        self.assertTrue(self.reg.retire("track-1"))
        self.assertEqual(self.reg.known_instances("mug"), [])


class ObjectRegistryEngineWiringTest(unittest.TestCase):
    """Phase 3 Task 3.4: object events flow through the brain's event bus and
    the registry persists on the consolidation cadence."""

    def _brain(self, store_path=None):
        from novi.brain.b2_perception import DeterministicPerceptionBackend, SpecialistPerception
        from novi.brain.engine import MacBrain, MacBrainConfig
        from novi.brain.io import CameraFrame
        from novi.brain.tests.test_mac_brain import FakeCamera
        from novi.perception.detection import DeterministicObjectDetector
        from novi.perception.pipeline import PerceptionPipeline

        class ScriptedCamera(FakeCamera):
            def read(self):
                self.sequence += 1
                return CameraFrame(
                    frame_id=f"f-{self.sequence}",
                    captured_at="2026-08-30T12:00:00Z",
                    width=640, height=480, payload=b"frame",
                    metadata={"backend": "test"},
                )

        detector = DeterministicObjectDetector(
            scripted={"f-1": [("mug", 0.85, (10, 10, 300, 300))]}
        )
        pipeline = PerceptionPipeline(detector=detector)
        brain = MacBrain(
            camera=ScriptedCamera(),
            perception=SpecialistPerception(DeterministicPerceptionBackend()),
            config=MacBrainConfig(curiosity_enabled=False, perception_every_n_cycles=1),
            store_path=store_path,
        )
        brain.perception_pipeline = pipeline
        return brain

    def test_step_feeds_object_registry_and_emits_detected(self) -> None:
        brain = self._brain()
        brain.start()
        try:
            brain.step()
            obj = brain.object_registry.object("track-1")
            self.assertIsNotNone(obj)
            assert obj is not None
            self.assertEqual(obj.cls, "mug")
            event_types = [e["event_type"] for e in brain.events]
            self.assertIn("object.detected", event_types)
        finally:
            brain.stop()

    def test_registry_persists_through_durable_store(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            store_path = str(Path(tmp) / "brain.db")
            brain = self._brain(store_path=store_path)
            brain.start()
            brain.step()
            brain.consolidate()
            brain.stop()
            brain2 = self._brain(store_path=store_path)
            obj = brain2.object_registry.object("track-1")
            self.assertIsNotNone(obj)
            assert obj is not None
            self.assertEqual(obj.cls, "mug")


if __name__ == "__main__":
    unittest.main()
