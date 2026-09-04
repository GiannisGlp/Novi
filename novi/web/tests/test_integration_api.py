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

    def test_place_auto_enroll_wired_to_camera_mode(self) -> None:
        """GAP-2: real cameras auto-enroll places; demo cameras do not."""
        from unittest import mock

        with mock.patch.object(NoviWebServer, "real_enable", return_value={}):
            s = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False, camera="real")
            try:
                self.assertTrue(s.mm_runtime._place_auto_enroll)
            finally:
                s.stop()
        s2 = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False, camera="demo")
        try:
            self.assertFalse(s2.mm_runtime._place_auto_enroll)
        finally:
            s2.stop()

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

    def test_bus_event_filter_includes_recognition_kinds(self) -> None:
        """GAP-1b: the camera loop must forward recognition events to the bus."""
        from novi.web.integration_api import _is_bus_event

        for kind in (
            "presence.entered",
            "presence.left",
            "scene.changed",
            "identity.auto_enrolled",
            "identity.recognized",
            "object.recognized",
            "person.holding",
            "object.novel",
        ):
            self.assertTrue(_is_bus_event(kind), f"{kind} must reach the input bus")
        self.assertFalse(_is_bus_event("perception.frame"))
        self.assertFalse(_is_bus_event("identity.ambiguous"))

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

    def _with_speaker(self, speaker):
        """Temporarily attach a fake speaker to the shared server."""
        old_speaker, old_flag = self.s._real_speaker, self.s.speak_back_enabled
        self.s._real_speaker = speaker
        self.s.speak_back_enabled = True
        self.addCleanup(setattr, self.s, "_real_speaker", old_speaker)
        self.addCleanup(setattr, self.s, "speak_back_enabled", old_flag)
        return speaker

    def test_voice_turn_speaks_through_mac_voice(self) -> None:
        class FakeSpeaker:
            def __init__(self) -> None:
                self.spoken: list[str] = []

            def speak(self, text: str):
                self.spoken.append(text)
                return {"spoken": True}

        speaker = self._with_speaker(FakeSpeaker())
        res = self.s.voice_turn({"text": "hello novi"})
        self.assertTrue(res.get("reply"))
        self.assertEqual(speaker.spoken, [res["reply"]])
        self.assertEqual(res.get("spoken"), {"spoken": True})

    def test_voice_turn_silent_when_speakback_off(self) -> None:
        class FakeSpeaker:
            def __init__(self) -> None:
                self.spoken: list[str] = []

            def speak(self, text: str):
                self.spoken.append(text)
                return {"spoken": True}

        speaker = self._with_speaker(FakeSpeaker())
        self.s.speak_back_enabled = False
        res = self.s.voice_turn({"text": "hello novi"})
        self.assertEqual(speaker.spoken, [])
        self.assertFalse(res.get("spoken", {}).get("spoken", False))

    def test_speak_back_never_raises(self) -> None:
        class ExplodingSpeaker:
            def speak(self, text: str):
                raise RuntimeError("no audio device")

        self._with_speaker(ExplodingSpeaker())
        res = self.s._speak_back("hello novi")
        self.assertFalse(res.get("spoken", False))
        self.assertEqual(self.s._speak_back("   "), {"spoken": False})

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

    def test_name_proposal_uses_last_seen_embedding(self) -> None:
        """GAP-3: naming a proposal without an embedding uses the last-seen one."""
        s = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        try:
            s.mm_runtime.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")
            s.mm_last_object_embeddings["cup"] = [1.0, 0.0]
            r = s.name_proposal_object({"category": "cup", "name": "my-mug", "frame_id": "f2"})
            self.assertTrue(r["ok"])
            self.assertEqual(r["object_id"], "object-my-mug")
        finally:
            s.stop()

    def test_preview_payload_shape(self) -> None:
        p = self.s.preview_frame()
        for key in ("camera_health", "stale", "person", "tier", "place", "detections"):
            self.assertIn(key, p)

    # ---- H1/H2: enrollment must source the FULL-RES frame, not the preview ----

    def test_store_preview_frame_keeps_decoded_bgr_for_enrollment(self) -> None:
        import numpy as np

        from novi.brain.io import CameraFrame

        bgr = np.zeros((720, 1280, 3), dtype="uint8")
        rec = type("Rec", (), {"frame": CameraFrame(
            frame_id="f1", captured_at="t", width=1280, height=720, payload=bgr,
        )})()
        self.s._store_preview_frame(rec, bgr)
        # the decoded array is preserved for enrollment cropping (no per-frame
        # full-res JPEG re-encode); the preview slot is a separate data URL.
        self.assertIs(self.s.mm_last_frame_bgr, bgr)
        self.assertTrue(
            isinstance(self.s.mm_last_frame_b64, str)
            and self.s.mm_last_frame_b64.startswith("data:image/jpeg;base64,")
        )

    def test_enroll_face_prefers_decoded_bgr(self) -> None:
        import numpy as np

        s = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        try:
            class _FakeEmbedder:
                def __init__(self) -> None:
                    self.received = None

                def embed_bgr(self, bgr):
                    self.received = bgr
                    return ([1.0, 0.0], (0, 0, 10, 10))

                def embed(self, jpeg):
                    raise AssertionError("embed_bgr path must be preferred")

            fake = _FakeEmbedder()
            s.face_embedder = fake
            bgr = np.zeros((48, 64, 3), dtype="uint8")
            s.mm_last_frame_bgr = bgr
            r = s.enroll_face_from_camera("Alice")
            self.assertTrue(r["ok"])
            self.assertIs(fake.received, bgr)
        finally:
            s.stop()

    def test_enroll_face_falls_back_to_encoded_jpeg(self) -> None:
        import numpy as np

        s = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        try:
            class _FakeEmbedder:
                def __init__(self) -> None:
                    self.received = None

                def embed(self, jpeg):
                    self.received = jpeg
                    return ([1.0, 0.0], (0, 0, 10, 10))

            fake = _FakeEmbedder()
            s.face_embedder = fake
            s.mm_last_frame_bgr = np.zeros((48, 64, 3), dtype="uint8")
            r = s.enroll_face_from_camera("Alice")
            self.assertTrue(r["ok"])
            # legacy embedder receives a JPEG encoded on demand from the bgr
            self.assertIsInstance(fake.received, bytes)
            self.assertEqual(fake.received[:2], b"\xff\xd8")
        finally:
            s.stop()

    def test_enroll_object_uses_decoded_bgr_and_bbox(self) -> None:
        import numpy as np

        s = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        try:
            class _FakeEmbedder:
                def __init__(self) -> None:
                    self.received = None

                def embed(self, payload, bboxes):
                    self.received = (payload, bboxes)
                    return [[1.0, 0.0]]

            fake = _FakeEmbedder()
            s.object_embedder = fake
            bgr = np.zeros((48, 64, 3), dtype="uint8")
            s.mm_last_frame_bgr = bgr
            s.mm_last_tracks = [{"label": "cup", "bbox": [10, 20, 30, 40], "is_person": False}]
            r = s.enroll_object_from_camera("mug")
            self.assertTrue(r["ok"])
            # the decoded array + the full-res bbox (no coordinate mismatch)
            self.assertIs(fake.received[0], bgr)
            self.assertEqual(fake.received[1], [(10, 20, 30, 40)])
        finally:
            s.stop()


class AssociationApiTests(unittest.TestCase):
    """Person-object association endpoint (plan 26 D).

    A FRESH server per test: these tests enroll object instances whose
    embeddings collide with the shared-class observations tests, and their
    coalescing counts depend on a clean store — so no mutable state may be
    shared between them.
    """

    def setUp(self) -> None:
        self.a = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)

    def tearDown(self) -> None:
        self.a.stop()

    def _record(self) -> None:
        self.a.mm_runtime.recognize_object("my-mug", embedding=[1.0, 0.0], frame_id="f0")
        self.a.mm_runtime.current_person = "Anna"
        self.a.mm_runtime.current_person_tier = "recognized"
        self.a.mm_runtime.current_place = "kitchen"
        self.a.mm_runtime.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")

    def test_association_objects_with_recognized_person(self) -> None:
        self._record()
        r = self.a.association_query({"action": "objects_with", "person": "Anna"})
        self.assertEqual(len(r["associations"]), 1)
        self.assertEqual(r["associations"][0]["object_ref"], "object-my-mug")
        self.assertEqual(r["associations"][0]["places"], ["kitchen"])

    def test_association_objects_with_defaults_to_current_person(self) -> None:
        self.a.mm_runtime.recognize_object("my-mug", embedding=[1.0, 0.0], frame_id="f0")
        self.a.mm_runtime.current_person = "Anna"
        self.a.mm_runtime.current_person_tier = "verified"
        self.a.mm_runtime.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")
        # no person supplied -> the recognized person in view is used
        r = self.a.association_query({"action": "objects_with"})
        self.assertEqual(r["associations"][0]["object_ref"], "object-my-mug")

    def test_association_seen_with_true_and_false(self) -> None:
        self.a.mm_runtime.recognize_object("my-mug", embedding=[1.0, 0.0], frame_id="f0")
        self.a.mm_runtime.current_person = "Anna"
        self.a.mm_runtime.current_person_tier = "recognized"
        self.a.mm_runtime.recognize_objects([("cup", [1.0, 0.0])], frame_id="f1")

        hit = self.a.association_query({
            "action": "seen_with", "person": "Anna", "object": "object-my-mug",
        })
        self.assertTrue(hit["seen"]["seen"])
        miss = self.a.association_query({
            "action": "seen_with", "person": "Anna", "object": "object-lamp",
        })
        self.assertFalse(miss["seen"]["seen"])

    def test_association_recent_summary_lines(self) -> None:
        self._record()
        r = self.a.association_query({"action": "recent_summary", "person": "person-anna"})
        self.assertEqual(r["summary"], ["my-mug in kitchen (1x)"])

    def test_association_requires_person_when_none_recognized(self) -> None:
        self.a.mm_runtime.current_person = ""
        self.a.mm_runtime.current_person_tier = ""
        r = self.a.association_query({"action": "objects_with"})
        self.assertIn("error", r)


if __name__ == "__main__":
    unittest.main()
