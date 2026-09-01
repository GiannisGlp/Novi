"""Tests: web vision provider + brain install (plan 26 B).

The web server installs a read-only provider on the brain that reports what
Novi currently sees (person/tier/place/objects/cadence) from MultimodalRuntime
+ the camera feed — honestly offline until a real camera is enabled.
"""

from __future__ import annotations

import unittest

from novi.perception.camera import CameraHealth
from novi.web.server import NoviWebServer
from novi.web.vision_provider import build_vision_provider


class _FakeRuntime:
    _last_scene_labels = {"person", "cup"}

    def snapshot(self) -> dict:
        return {
            "person": "Anna",
            "tier": "recognized",
            "place": "kitchen",
            "objects": ["blue mug", "cup"],
            "cadence": {"processed_fps": 12.5, "stage_ms": {"detect": 8.0}},
            "associations": [{"object_ref": "object-my-mug", "label": "my-mug"}],
        }


class _FakeFeed:
    captured = 5
    dropped = 1

    def __init__(self, health: CameraHealth = CameraHealth.AVAILABLE) -> None:
        self.health = health

    def last_frame_age_s(self) -> float:
        return 0.2


def _server(*, runtime=None, feed=None, store=True):
    class _S:
        pass

    s = _S()
    s.mm_runtime = runtime if runtime is not None else _FakeRuntime()
    s.mm_camera_feed = feed
    s.mm_store = object() if store else None
    return s


class BuildVisionProviderTests(unittest.TestCase):
    def test_live_feed_snapshot_shape(self) -> None:
        p = build_vision_provider(_server(feed=_FakeFeed()))()
        self.assertTrue(p["camera_live"])
        self.assertEqual(p["health"], "available")
        self.assertEqual(p["person"], "Anna")
        self.assertEqual(p["person_tier"], "recognized")
        self.assertEqual(p["place"], "kitchen")
        self.assertEqual(p["objects"], ["blue mug", "cup"])
        self.assertIn("person", p["scene_labels"])
        self.assertEqual(p["processed_fps"], 12.5)
        self.assertEqual(p["stage_ms"], {"detect": 8.0})
        self.assertAlmostEqual(p["drop_rate"], 1 / 6)
        self.assertEqual(len(p["associations"]), 1)
        self.assertEqual(p["last_frame_age_s"], 0.2)
        self.assertTrue(p["recognition_available"])

    def test_objects_bounded_to_eight(self) -> None:
        class _Many:
            _last_scene_labels = set()

            def snapshot(self) -> dict:
                return {
                    "person": "",
                    "tier": "",
                    "place": "",
                    "objects": [f"o{i}" for i in range(12)],
                    "cadence": {},
                    "associations": [],
                }

        p = build_vision_provider(_server(runtime=_Many(), feed=_FakeFeed()))()
        self.assertEqual(len(p["objects"]), 8)

    def test_no_feed_is_honestly_offline(self) -> None:
        p = build_vision_provider(_server(feed=None))()
        self.assertFalse(p["camera_live"])
        self.assertEqual(p["health"], "offline")

    def test_failed_feed_is_not_live(self) -> None:
        p = build_vision_provider(_server(feed=_FakeFeed(CameraHealth.FAILED)))()
        self.assertFalse(p["camera_live"])
        self.assertEqual(p["health"], "failed")

    def test_no_runtime_is_offline(self) -> None:
        p = build_vision_provider(_server(runtime=None, feed=None))()
        self.assertEqual(p["health"], "offline")
        self.assertFalse(p["camera_live"])


class BrainInstallTests(unittest.TestCase):
    def test_integration_init_installs_provider(self) -> None:
        s = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        try:
            brain = s.brain
            self.assertIsNotNone(brain._vision_provider)
            vs = brain.vision_status()
            self.assertTrue(vs["available"], "the provider is wired")
            # demo camera: no real frames yet, so Novi must NOT claim sight
            self.assertFalse(vs["can_see"])
            sm = brain.self_model()
            self.assertEqual(sm["capabilities"].get("vision"), "FAIL")
            self.assertFalse(sm["live_vision"]["can_see"])
        finally:
            s.stop()


if __name__ == "__main__":
    unittest.main()
