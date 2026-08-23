"""Phase C3 (gap-audit plan 13): spatial/temporal context on every admit.

Pins:
  - every engine admission carries temporal_context={"cycle": N} and
    spatial_context={"x_m","y_m","place"};
  - the place comes from SpatialMap.region_at over the body pose;
  - retrieve(place=...) filters records by that tag across store backends;
  - temporal context is cycle-only (no wall clock) so duplicate admission at
    one cycle stays idempotent.
"""

import unittest

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.spatial_map import default_home_map
from novi.brain.tests.test_mac_brain import FakeCamera


class CupBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)


def _brain() -> MacBrain:
    brain = MacBrain(
        camera=FakeCamera(),
        perception=SpecialistPerception(CupBackend()),
        config=MacBrainConfig(curiosity_enabled=False),
    )
    brain.start()
    return brain


def _records(brain: MacBrain) -> list:
    mem = brain.memory
    if hasattr(mem, "active_rows"):
        return [item["record"] for item in mem.active_rows()]
    return list(getattr(mem, "_records", {}).values())


class RegionAtTests(unittest.TestCase):
    def test_point_in_kitchen_resolves(self):
        m = default_home_map()
        self.assertEqual(m.region_at(1.0, 1.0), "kitchen")
        self.assertEqual(m.region_at(6.0, 2.0), "living_room")
        self.assertIsNone(m.region_at(50.0, 50.0))


class AdmitContextTests(unittest.TestCase):
    def test_perception_records_carry_spatial_and_temporal_context(self):
        brain = _brain()
        try:
            # Put the body inside the kitchen region of the default map.
            brain.body.x_m = 1.0
            brain.body.y_m = 1.0
            brain.step()
            perceptions = [r for r in _records(brain) if r.memory_type == "perception"]
            self.assertTrue(perceptions)
            rec = perceptions[-1]
            self.assertEqual(rec.temporal_context.get("cycle"), brain._cycle)
            sc = rec.spatial_context or {}
            self.assertEqual(sc.get("place"), "kitchen")
            self.assertEqual(sc.get("x_m"), 1.0)
            self.assertEqual(sc.get("y_m"), 1.0)
        finally:
            brain.stop()

    def test_utterance_records_carry_context(self):
        brain = _brain()
        try:
            brain.body.x_m = 5.0
            brain.body.y_m = 1.0

            class T:
                text = "hello there"
                confidence = 0.9
                provider = "test"
                model_id = "m"
                audio_path = ""

            brain.ingest_transcript(T())
            utt = [r for r in _records(brain) if r.memory_type == "utterance"]
            self.assertTrue(utt)
            self.assertEqual((utt[-1].spatial_context or {}).get("place"), "living_room")
            self.assertIn("cycle", utt[-1].temporal_context)
            self.assertNotIn("wall_time", utt[-1].temporal_context)
        finally:
            brain.stop()


class RetrievePlaceTests(unittest.TestCase):
    def test_retrieve_place_filters_across_backends(self):
        for make_brain_kwargs in ({}, {"store_path": ":memory:"}):
            with self.subTest(store=make_brain_kwargs):
                brain = MacBrain(
                    camera=FakeCamera(),
                    perception=SpecialistPerception(CupBackend()),
                    config=MacBrainConfig(curiosity_enabled=False),
                    **make_brain_kwargs,
                )
                brain.start()
                try:
                    brain.body.x_m = 1.0
                    brain.body.y_m = 1.0

                    class T:
                        text = "the cup is on the table"
                        confidence = 0.9
                        provider = "test"
                        model_id = "m"
                        audio_path = ""

                    brain.ingest_transcript(T())
                    hits_kitchen = brain.memory.retrieve("cup", place="kitchen", limit=10)
                    hits_living = brain.memory.retrieve("cup", place="living_room", limit=10)
                    places_seen = {(r.spatial_context or {}).get("place") for r in hits_kitchen}
                    self.assertNotIn("living_room", places_seen)
                    if hits_living:
                        self.assertTrue(all((r.spatial_context or {}).get("place") == "living_room" for r in hits_living))
                finally:
                    brain.stop()

    def test_no_place_filter_returns_everything(self):
        brain = _brain()
        try:
            brain.step()
            unfiltered = brain.memory.retrieve("cup", limit=50)
            self.assertTrue(unfiltered)
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
