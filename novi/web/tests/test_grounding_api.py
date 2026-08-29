"""Tests: /api/grounding web endpoint (L3 — web app as another surface).

The endpoint drives the SAME PerceptionPipeline.ground_frame the body would
use; here it is served by the deterministic backend (CI — no model, no
service), and the fallback wrapper proves the never-crash rule when the
grounding service is down.
"""

from __future__ import annotations

import base64
import json
import threading
import unittest
import urllib.error
import urllib.request

from novi.perception.locate_anything import DeterministicLocateAnythingBackend
from novi.web.server import NoviWebHTTPServer, NoviWebServer, _GroundingWithFallback

FRAME_B64 = base64.b64encode(b"jpeg-bytes").decode("ascii")


def _post(port: int, path: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}", data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


class TestGroundingApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._server = NoviWebServer(
            port=0,
            store_path=None,
            auto_step=False,
            chat_llm=False,
            grounding_backend=DeterministicLocateAnythingBackend(
                scripted={("web-ground", "locate the cup"): [("cup", (100, 200, 900, 800))]}
            ),
        )
        cls._server.start()
        cls._httpd = NoviWebHTTPServer(("127.0.0.1", 0), cls._server)
        cls._port = cls._httpd.server_address[1]
        cls._thread = threading.Thread(target=cls._httpd.serve_forever, daemon=True)
        cls._thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._httpd.shutdown()
        cls._httpd.server_close()
        cls._server.stop()

    def test_grounding_returns_typed_observations(self):
        resp = _post(
            self._port,
            "/api/grounding",
            {"query": "locate the cup", "frame_b64": FRAME_B64, "width": 640, "height": 480},
        )
        self.assertTrue(resp["success"])
        self.assertEqual(resp["model_id"], "deterministic")
        self.assertEqual(len(resp["observations"]), 1)
        obs = resp["observations"][0]
        self.assertEqual(obs["kind"], "box")
        self.assertEqual(obs["label"], "cup")
        self.assertEqual(obs["pixel_box"], [64, 96, 512, 288])
        self.assertEqual(resp["frame_id"], "web-ground")
        # no tracks yet -> conservative candidate, never invented continuity
        self.assertEqual(resp["associations"][0]["status"], "candidate")
        self.assertIsNone(resp["associations"][0]["track_id"])

    def test_empty_query_rejected(self):
        body = json.dumps({"query": "   "}).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{self._port}/api/grounding", data=body, headers={"Content-Type": "application/json"}
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 400)

    def test_unscripted_query_is_valid_empty(self):
        resp = _post(self._port, "/api/grounding", {"query": "locate a unicorn", "frame_b64": FRAME_B64})
        self.assertTrue(resp["success"])
        self.assertEqual(resp["observations"], [])
        self.assertFalse(resp["no_object"])

    def test_demo_mode_without_frame_uses_demo_camera(self):
        # no frame_b64, no real feed -> DemoCamera frame (deterministic result)
        resp = _post(self._port, "/api/grounding", {"query": "locate the cup"})
        self.assertIn("frame_id", resp)


class TestGroundingWithFallback(unittest.TestCase):
    def test_service_down_falls_back_to_deterministic(self):
        # port 1: nothing listens -> client raises -> deterministic backend
        from novi.brain.io import CameraFrame
        from novi.perception.grounding import SpatialInferencePolicy, SpatialQuery

        backend = _GroundingWithFallback(service_url="http://127.0.0.1:1")
        frame = CameraFrame(frame_id="f1", captured_at="t0", width=640, height=480, payload=b"x")
        result = backend.ground(frame, SpatialQuery(text="q", frame_id="f1", timestamp="t0"), SpatialInferencePolicy())
        self.assertTrue(result.success)  # never crashes, never blocks the web app
        self.assertEqual(result.model_id, "deterministic")
        caps = backend.capabilities()
        self.assertEqual(caps.model_id, "deterministic")


if __name__ == "__main__":
    unittest.main()
