"""End-to-end integration scenario (doc 16 §5): the multimodal loop.

Enroll Anna -> she appears on camera (recognized -> person context)
-> place recognized from landmarks -> Anna speaks via voice_turn and is
answered with person context attached -> owner sends a chat message in
parallel -> recognition state persists to disk and survives reopen.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from novi.brain.io import CameraFrame
from novi.integration.recognition_store import RecognitionKind, RecognitionStore
from novi.web.server import NoviWebServer

ANNA_FACE = [1.0, 0.0]


def _frame(fid: str) -> CameraFrame:
    return CameraFrame(frame_id=fid, captured_at=f"t-{fid}", width=64, height=48, payload=b"")


class EndToEndScenarioTests(unittest.TestCase):
    def test_annas_visit_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store_path = str(Path(tmp) / "novi-e2e.db")
            s = NoviWebServer(port=0, store_path=store_path, auto_step=False, chat_llm=False)

            # 1. enroll Anna (conversationally upstream; here via API)
            r = s.recognize_person({"name": "Anna", "face_embedding": ANNA_FACE, "frame_id": "f0"})
            self.assertTrue(r["ok"])

            # 2. enroll the kitchen by its landmarks
            r = s.enroll_place_or_noise({
                "kind": "place", "label": "kitchen",
                "descriptor": {"landmarks": ["cup", "book"]},
            })
            self.assertTrue(r["ok"])

            # 3. Anna appears; a frame flows through perception
            res = s.perception_frame({"frame_id": "f-anna", "captured_at": "t-a", "face_embedding": ANNA_FACE})
            self.assertEqual(res["identities"][0]["tier"], "recognized")
            self.assertTrue(res["proposal"] is False or res["proposal"] is True)  # shape check

            # 4. kitchen landmark (cup) was scripted? no detector entries yet,
            #    so place stays unset until detection provides landmarks.
            #    Swap in a detector with the kitchen landmark scripted:
            from novi.perception.detection import DeterministicObjectDetector

            s.mm_runtime.perception.detector = DeterministicObjectDetector(
                scripted={"f-kitchen": [("cup", 0.9, (10, 10, 8, 12))]}
            )
            s.perception_frame({"frame_id": "f-kitchen"})
            self.assertEqual(s.mm_runtime.current_place, "kitchen")

            # 5. Anna speaks; brain answers with her as addressee
            turn = s.voice_turn({"text": "hello novi, it's anna", "speaker_label": "Anna"})
            self.assertTrue(turn["ok"])
            self.assertTrue(turn["reply"])
            self.assertEqual(turn["person"], "Anna")

            # 6. owner chats from work in parallel — same brain, separate channel
            hear = s.hear("what did anna say?")
            self.assertIn("reasoning", hear)

            # 7. preview reflects live state
            prev = s.preview_frame()
            self.assertEqual(prev["person"], "Anna")
            self.assertIn(prev["camera_health"], ("offline", "unknown"))

            # 8. persistence: recognition survives server restart
            mm_path = Path(store_path)
            self.assertTrue(mm_path.exists(), "recognition store must persist to disk")
            s.stop()
            store2 = RecognitionStore(mm_path)
            faces = [e for e in store2.all(RecognitionKind.FACE) if e["label"] == "Anna"]
            places = [e for e in store2.all(RecognitionKind.PLACE) if e["label"] == "kitchen"]
            self.assertEqual(len(faces), 1)
            self.assertEqual(len(places), 1)
            store2.close()


if __name__ == "__main__":
    unittest.main()
