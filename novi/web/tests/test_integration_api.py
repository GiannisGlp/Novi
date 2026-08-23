"""Tests: web integration endpoints for voice/perception/recognition.

Exercises the additive API surface through NoviWebServer methods
(the same methods the HTTP handlers call), plus the preview payload.
"""

from __future__ import annotations

import unittest

from novi.web.server import NoviWebServer


class IntegrationApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.s = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)

    def test_runtime_initialized(self) -> None:
        self.assertIsNotNone(self.s.mm_runtime)
        self.assertIsNotNone(self.s.mm_store)

    def test_perception_frame_endpoint_payload(self) -> None:
        res = self.s.perception_frame({
            "frame_id": "web-f1",
            "captured_at": "t1",
            "payload": b"",
        })
        self.assertIn("detections", res)
        self.assertIn("tracks", res)
        self.assertIn("identities", res)

    def test_voice_turn_replies_and_mirrors_chat(self) -> None:
        res = self.s.voice_turn({"text": "hello novi"})
        self.assertTrue(res.get("ok"))
        self.assertTrue(res.get("reply"))
        # mirrored into the shared chat log
        texts = [c.get("text", "") for c in getattr(self.s, "_chat", [])]
        self.assertTrue(any("[voice] hello novi" in t for t in texts))

    def test_recognize_person_then_preview_shows_them(self) -> None:
        r = self.s.recognize_person({
            "name": "Preview Person",
            "face_embedding": [1.0, 0.0],
            "frame_id": "f-enroll",
        })
        self.assertTrue(r["ok"])
        out = self.s.mm_runtime.process_camera_frame(
            __import__("novi.brain.io", fromlist=["CameraFrame"]).CameraFrame(
                frame_id="f-prev", captured_at="t", width=4, height=4, payload=b""
            ),
            face_embedding=[1.0, 0.0],
        )
        self.assertEqual(out.identities[0].tier.value, "recognized")
        prev = self.s.preview_frame()
        self.assertEqual(prev["person"], "Preview Person")

    def test_enroll_place_and_landmark_lookup(self) -> None:
        r = self.s.enroll_place_or_noise({
            "kind": "place",
            "label": "studio",
            "descriptor": {"landmarks": ["lamp"]},
        })
        self.assertTrue(r["ok"])
        listed = self.s.recognition_list("place")
        labels = [e["label"] for e in listed["enrollments"]]
        self.assertIn("studio", labels)

    def test_privacy_toggle_blocks_biometrics(self) -> None:
        self.s.recognition_privacy({"enabled": False, "reason": "test"})
        with self.assertRaises(PermissionError):
            self.s.recognize_person({"name": "X", "face_embedding": [1.0], "frame_id": "f"})
        self.s.recognition_privacy({"enabled": True, "reason": "restore"})

    def test_preview_payload_shape(self) -> None:
        p = self.s.preview_frame()
        for key in ("camera_health", "stale", "person", "tier", "place", "detections"):
            self.assertIn(key, p)


if __name__ == "__main__":
    unittest.main()
