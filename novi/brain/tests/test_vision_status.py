"""Tests: live-vision self-awareness (plan 26 B).

The brain must be able to honestly say what it currently sees — and when it
can't. ``build_vision_status`` merges a web-provided live snapshot into a
JSON-safe dict; with NO provider (non-web builds) it returns an honest offline
report so a camera-less brain never claims sight. The web provider only READS
camera/runtime state, so the reply thread can never deadlock the camera thread.

The default brain (no provider) must stay byte-identical: the self-model gains
no ``vision`` capability and the dialogue system prompt is unchanged.
"""

from __future__ import annotations

import unittest

from novi.brain.engine import MacBrain
from novi.brain.vision_status import build_vision_status


def _live_provider(*, person: str = "Anna", tier: str = "recognized",
                   health: str = "available", camera_live: bool = True):
    def _provider():
        return {
            "camera_live": camera_live,
            "health": health,
            "recognition_available": True,
            "person": person,
            "person_tier": tier,
            "place": "kitchen",
            "objects": ["blue mug"],
            "scene_labels": ["cup", "person"],
            "last_frame_age_s": 0.05,
            "processed_fps": 12.5,
            "stage_ms": {"detect": 8.0},
            "drop_rate": 0.01,
            "associations": [{"object_ref": "object-my-mug", "label": "my-mug"}],
        }

    return _provider


class BuildVisionStatusTests(unittest.TestCase):
    def test_no_provider_is_honest_offline(self) -> None:
        s = build_vision_status(None, None)
        self.assertFalse(s["available"])
        self.assertFalse(s["camera_live"])
        self.assertFalse(s["can_see"])
        self.assertEqual(s["health"], "offline")
        self.assertEqual(s["person"], "")

    def test_no_provider_still_shows_brain_camera_failure(self) -> None:
        class _B:
            _last_health = {"status": "WARN", "checks": [{"name": "camera", "status": "FAIL"}]}

        s = build_vision_status(_B(), None)
        self.assertEqual(s["health"], "fail")
        self.assertFalse(s["can_see"], "no live frames => cannot see even with a health check")

    def test_live_provider_reports_seeing(self) -> None:
        s = build_vision_status(None, _live_provider())
        self.assertTrue(s["available"])
        self.assertTrue(s["camera_live"])
        self.assertTrue(s["can_see"])
        self.assertEqual(s["person"], "Anna")
        self.assertEqual(s["person_tier"], "recognized")
        self.assertEqual(s["place"], "kitchen")
        self.assertEqual(s["objects"], ["blue mug"])
        self.assertEqual(s["stage_ms"], {"detect": 8.0})

    def test_camera_live_but_failed_health_cannot_see(self) -> None:
        s = build_vision_status(None, _live_provider(health="failed", camera_live=True))
        self.assertFalse(s["can_see"])

    def test_offline_provider_cannot_see(self) -> None:
        s = build_vision_status(None, _live_provider(health="offline", camera_live=False))
        self.assertFalse(s["can_see"])

    def test_unknown_extra_provider_keys_are_dropped(self) -> None:
        base = _live_provider()()

        def _sneaky():
            return {**base, "arbitrary": "injection", "can_see": True}

        s = build_vision_status(None, _sneaky)
        self.assertNotIn("arbitrary", s)

    def test_can_see_is_computed_not_trusted(self) -> None:
        # provider tries to fake sight (can_see=True) on a dead camera feed
        base = _live_provider()()

        def _sneaky():
            return {**base, "camera_live": False, "can_see": True}

        s = build_vision_status(None, _sneaky)
        self.assertFalse(s["can_see"])

    def test_exceptioning_provider_degrades_gracefully(self) -> None:
        def _boom():
            raise RuntimeError("camera exploded")

        s = build_vision_status(None, _boom)
        self.assertTrue(s["available"], "stack is wired even when the feed broke")
        self.assertFalse(s["camera_live"])
        self.assertFalse(s["can_see"])
        self.assertEqual(s["health"], "offline")


class BrainVisionSeamTests(unittest.TestCase):
    def test_default_brain_vision_status_is_offline(self) -> None:
        brain = MacBrain(camera=None)
        s = brain.vision_status()
        self.assertFalse(s["available"])
        self.assertFalse(s["can_see"])

    def test_install_provider_gives_live_status(self) -> None:
        brain = MacBrain(camera=None)
        brain.set_vision_provider(_live_provider())
        s = brain.vision_status()
        self.assertTrue(s["available"])
        self.assertTrue(s["can_see"])
        self.assertEqual(s["person"], "Anna")

    def test_self_model_unchanged_without_provider(self) -> None:
        brain = MacBrain(camera=None)
        sm = brain.self_model()
        # default-brain capabilities/health stay byte-identical (no vision entry)
        self.assertEqual(sm["capabilities"], {"physical_actions": "FAIL"})
        self.assertNotIn("vision", sm["capabilities"])
        self.assertFalse(sm["live_vision"]["can_see"])
        self.assertFalse(sm["live_vision"]["available"])

    def test_self_model_vision_capability_from_provider(self) -> None:
        brain = MacBrain(camera=None)
        brain.set_vision_provider(_live_provider())
        sm = brain.self_model()
        self.assertEqual(sm["capabilities"].get("vision"), "PASS")
        self.assertTrue(sm["live_vision"]["can_see"])
        self.assertEqual(sm["live_vision"]["person"], "Anna")

    def test_degraded_provider_marks_vision_fail(self) -> None:
        brain = MacBrain(camera=None)
        brain.set_vision_provider(_live_provider(health="failed", camera_live=True))
        sm = brain.self_model()
        self.assertEqual(sm["capabilities"].get("vision"), "FAIL")

    def test_system_prompt_discloses_vision_failure(self) -> None:
        brain = MacBrain(camera=None)
        prompt = brain._dialogue_system_prompt(
            {"name": "Novi", "tone": "warm"},
            {"tier": "friend", "expression": {}},
            capabilities={"vision": "FAIL"},
        )
        self.assertIn("vision", prompt)
        self.assertIn("degraded or unavailable", prompt)

        # ... but an all-PASS capabilities set produces no degradation clause
        prompt_ok = brain._dialogue_system_prompt(
            {"name": "Novi", "tone": "warm"},
            {"tier": "friend", "expression": {}},
            capabilities={"vision": "PASS"},
        )
        self.assertNotIn("degraded or unavailable", prompt_ok)


if __name__ == "__main__":
    unittest.main()
