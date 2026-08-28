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

    def test_event_autonomy_defaults_on(self) -> None:
        self.assertTrue(self.s.event_autonomy)
        self.assertTrue(self.s.brain.config.event_autonomy_enabled)

    def test_event_autonomy_can_be_disabled(self) -> None:
        s = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False, event_autonomy=False)
        try:
            self.assertFalse(s.event_autonomy)
            self.assertFalse(s.brain.config.event_autonomy_enabled)
        finally:
            s.stop()

    def test_overlaps_reads_contained_object_as_held(self) -> None:
        from novi.web.integration_api import _overlaps

        # object fully inside the person box → held
        self.assertTrue(_overlaps((60, 40, 20, 20), (50, 30, 100, 150)))
        # object barely brushing the box edge → not held
        self.assertFalse(_overlaps((149, 30, 10, 10), (50, 30, 100, 150)))

    def test_note_person_holding_ignores_unknown_person(self) -> None:
        class _Det:
            def __init__(self, label, bbox):
                self.label = label
                self.bbox = bbox

        rt = self.s.mm_runtime
        rt.current_person = "new-person-1"
        self.s._note_person_holding(
            [_Det("cup", (60, 40, 20, 20))],
            (50, 30, 100, 150),
            [[1.0, 0.0]],
            "web-f1",
        )
        self.assertEqual(rt.current_person, "new-person-1")
        self.assertFalse(any(e["kind"] in ("person.holding", "object.novel") for e in rt.events))

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

    def test_observation_last_sighting_roundtrip(self) -> None:
        # enroll + recognize an object so a durable sighting is written
        self.s.mm_runtime.recognize_object("mug", embedding=[1.0, 0.0], frame_id="f0")
        self.s.mm_runtime.current_place = "kitchen"
        self.s.mm_runtime.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")
        r = self.s.observation_last_sighting({"kind": "object", "entity_ref": "object-mug"})
        self.assertIsNotNone(r["sighting"])
        self.assertEqual(r["sighting"]["place"], "kitchen")
        self.assertEqual(r["sighting"]["label"], "mug")

    def test_observation_last_sighting_none_for_unknown(self) -> None:
        r = self.s.observation_last_sighting({"kind": "object", "entity_ref": "object-nope"})
        self.assertIsNone(r["sighting"])

    def test_observation_in_place_returns_objects(self) -> None:
        self.s.mm_runtime.current_place = "kitchen"
        self.s.mm_runtime.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")
        r = self.s.observation_in_place({"place": "kitchen", "kind": "object"})
        refs = {o["entity_ref"] for o in r["observations"]}
        self.assertEqual(refs, {"object-unresolved-cup"})

    def test_observation_search_ranks_by_cosine(self) -> None:
        self.s.mm_runtime.recognize_objects([("book", [0.0, 1.0])], frame_id="f1")
        r = self.s.observation_search({"query_vector": [0.95, 0.1]})
        self.assertIn("matches", r)
        # a distant cosine still ranks the single object highest
        self.assertTrue(r["matches"])

    def test_proposal_list_and_name_object(self) -> None:
        # a novel object appears -> proposal ledger lists it
        self.s.mm_runtime.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")
        pl = self.s.proposal_list()
        refs = {p["entity_ref"] for p in pl["proposals"]}
        self.assertIn("object-unresolved-cup", refs)

        # name it -> history rebinds to the canonical id
        r = self.s.name_proposal_object(
            {"category": "cup", "name": "my-mug", "embedding": [1.0, 0.0], "frame_id": "f2"}
        )
        self.assertTrue(r["ok"])
        self.assertEqual(r["object_id"], "object-my-mug")
        self.assertGreaterEqual(r["rebound"], 1)
        named = self.s.observation_last_sighting({"kind": "object", "entity_ref": "object-my-mug"})
        self.assertIsNotNone(named["sighting"])

    def test_name_proposal_requires_embedding(self) -> None:
        r = self.s.name_proposal_object({"category": "cup", "name": "x", "embedding": []})
        self.assertIn("error", r)

    def test_preview_payload_shape(self) -> None:
        p = self.s.preview_frame()
        for key in ("camera_health", "stale", "person", "tier", "place", "detections"):
            self.assertIn(key, p)


if __name__ == "__main__":
    unittest.main()
