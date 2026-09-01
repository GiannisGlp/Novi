"""Tests: camera loop — single JPEG decode + VisionBudget gating (plan 26, A).

The loop used to decode the JPEG 3-4x per frame and run every expensive stage
(every frame). This module drives `camera_loop.process_record` with a fake
server + injected VisionBudget (fake clock) and asserts the cadence:

- the JPEG decodes ONCE into a BGR ndarray; every stage reuses it (no re-decode);
- detection + presence always run; the gated stages (preview / face_embed /
  object_embed) follow the `every_n` counters;
- skipped face frames reuse the last embedding so identity presence stays alive;
- a popped `scene.changed` event forces one full frame via `mark_scene_change`;
- per-stage timings + processed_fps flow back into the budget telemetry.
"""

from __future__ import annotations

import threading

import numpy as np

from novi.brain.io import CameraFrame
from novi.perception.cadence import VisionBudget
from novi.web.camera_loop import build_work_frame, decode_bgr, process_record


class _Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


def _jpeg() -> bytes:
    import cv2

    ok, buf = cv2.imencode(".jpg", np.zeros((48, 64, 3), dtype="uint8"))
    assert ok
    return buf.tobytes()


class _Det:
    def __init__(self, label: str = "cup", bbox=(0, 0, 10, 10)) -> None:
        self.label = label
        self.bbox = bbox


class _Obs:
    def __init__(self, detections=None) -> None:
        self.detections = detections or []
        self.identities = []
        self.tracks = []
        self.last_frame = None
        self.face_embedding = None


class _Rec:
    def __init__(self, seq: int, payload) -> None:
        self.seq = seq
        self.frame = CameraFrame(
            frame_id=f"f{seq}", captured_at="t", width=64, height=48, payload=payload
        )


class _FaceEmb:
    def __init__(self) -> None:
        self.calls = 0
        self.received: list[np.ndarray] = []

    def embed_bgr(self, bgr):
        self.calls += 1
        self.received.append(bgr)
        return ([0.1] * 128, (1, 1, 8, 8))


class _ObjEmb:
    def __init__(self) -> None:
        self.calls = 0

    def embed(self, payload, bboxes):
        self.calls += 1
        return [[1.0, 0.0]] * len(bboxes)


class FakeRuntime:
    """Mirror of the MultimodalRuntime surface the loop touches."""

    def __init__(self, budget: VisionBudget) -> None:
        self.budget = budget
        self.current_person = ""
        self.current_person_tier = ""
        self._events: list[dict] = []
        self._results: list[_Obs] = []
        self.observed: list[_Obs] = []
        self.recognize_calls: list[tuple] = []

    def process_camera_frame(self, frame, face_embedding=None):
        obs = self._results.pop(0) if self._results else _Obs()
        obs.last_frame = frame
        obs.face_embedding = face_embedding
        self.observed.append(obs)
        return obs

    def recognize_objects(self, pairs, frame_id):
        self.recognize_calls.append((pairs, frame_id))

    def pop_pending_events(self):
        events = self._events
        self._events = []
        return events


class FakeServer:
    def __init__(self, budget=None, *, face_embedder=None, object_embedder=None) -> None:
        self.mm_runtime = FakeRuntime(budget or VisionBudget(clock=_Clock()))
        self.face_embedder = face_embedder
        self.object_embedder = object_embedder
        self.mm_last_object_embeddings: dict[str, list[float]] = {}
        self.mm_last_tracks: list[dict] = []
        self.mm_last_face: dict | None = None
        self.mm_last_face_pair: tuple | None = None
        self.mm_last_frame_bgr: np.ndarray | None = None
        self.mm_lock = threading.RLock()
        self.preview_calls = 0
        self.note_calls = 0
        self.bus_events: list[dict] = []

    def _store_preview_frame(self, rec, bgr=None):
        self.mm_last_frame_bgr = bgr
        self.preview_calls += 1
        return "data:image/jpeg;base64,xxx"

    def _note_person_holding(self, detections, face_bbox, vecs, frame_id):
        self.note_calls += 1

    def _forward_bus_events(self, events: list[dict]) -> None:
        self.bus_events.extend(events)


def _server(budget=None, *, face=True, objects=True) -> FakeServer:
    return FakeServer(
        budget,
        face_embedder=_FaceEmb() if face else None,
        object_embedder=_ObjEmb() if objects else None,
    )


class TestDecodeBgr:
    def test_jpeg_bytes_decode_once_to_bgr(self):
        img = decode_bgr(_jpeg())
        assert img is not None and img.shape == (48, 64, 3)

    def test_ndarray_passes_through_unchanged(self):
        arr = np.zeros((48, 64, 3), dtype="uint8")
        assert decode_bgr(arr) is arr

    def test_garbage_payload_returns_none(self):
        assert decode_bgr(b"not-an-image") is None


class TestBuildWorkFrame:
    def test_wraps_bgr_with_dimensions_from_array(self):
        rec = _Rec(seq=7, payload=b"unused")
        work = build_work_frame(rec, np.zeros((480, 640, 3), dtype="uint8"))
        assert work.width == 640 and work.height == 480
        assert work.frame_id == "f7"
        assert work.payload.shape == (480, 640, 3)


class TestProcessRecordCadence:
    def test_gated_stages_follow_counter(self):
        clk = _Clock()
        budget = VisionBudget(clock=clk, face_every_n=3, object_every_n=4, preview_every_n=2)
        server = _server(budget)
        for seq in range(1, 9):
            clk.advance(0.1)
            server.mm_runtime._results.append(_Obs([_Det()]))
            process_record(server, _Rec(seq, _jpeg()))
        assert server.preview_calls == 4  # frames 1,3,5,7
        assert server.face_embedder.calls == 3  # frames 1,4,7
        assert server.object_embedder.calls == 2  # frames 1,5
        assert len(server.mm_runtime.recognize_calls) == 2
        assert server.note_calls == 2  # object stage only
        tel = budget.telemetry()
        assert tel["frames_processed"] == 8
        assert tel["runs"]["preview"] == 4
        assert tel["runs"]["face_embed"] == 3
        assert tel["runs"]["object_embed"] == 2
        assert tel["runs"]["detect"] == 8, "detection runs every frame"
        assert tel["processed_fps"] is not None and tel["processed_fps"] > 0.0

    def test_detect_every_frame_and_latest_bgr_kept(self):
        clk = _Clock()
        budget = VisionBudget(clock=clk, preview_every_n=2)
        server = _server(budget, face=False, objects=False)
        for seq in (1, 2, 3):
            clk.advance(0.1)
            server.mm_runtime._results.append(_Obs([_Det()]))
            process_record(server, _Rec(seq, _jpeg()))
        assert len(server.mm_runtime.observed) == 3, "detection + presence always run"
        assert server.mm_last_frame_bgr is not None, "latest decoded frame always kept"
        assert server.preview_calls == 2  # frames 1,3
        assert budget.telemetry()["stage_ms"]["detect"]["samples"] == 3

    def test_skipped_face_frames_reuse_last_embedding(self):
        clk = _Clock()
        budget = VisionBudget(clock=clk, face_every_n=3)
        server = _server(budget, objects=False)
        for seq in range(1, 8):
            clk.advance(0.1)
            server.mm_runtime._results.append(_Obs([_Det()]))
            process_record(server, _Rec(seq, _jpeg()))
        assert server.face_embedder.calls == 3  # frames 1,4,7
        # every processed frame still feeds a face embedding to identity matching
        assert all(o.face_embedding == [0.1] * 128 for o in server.mm_runtime.observed)

    def test_object_stages_skip_without_detections_or_embedder(self):
        clk = _Clock()
        budget = VisionBudget(clock=clk, object_every_n=1)
        server = _server(budget, face=False, objects=True)
        clk.advance(0.1)
        server.mm_runtime._results.append(_Obs())  # no detections
        process_record(server, _Rec(1, _jpeg()))
        assert server.object_embedder.calls == 0, "nothing to embed with no detections"
        assert server.note_calls == 0

    def test_scene_changed_event_forces_every_stage_next_frame(self):
        clk = _Clock()
        budget = VisionBudget(clock=clk, face_every_n=3, object_every_n=4, preview_every_n=2)
        server = _server(budget)
        server.mm_runtime._events = [{"kind": "scene.changed", "place": "kitchen"}]
        server.mm_runtime._results.append(_Obs([_Det()]))
        process_record(server, _Rec(1, _jpeg()))
        # the popped event marks the budget AND reaches the input bus
        decided = budget.decide(frame_seq=2)
        assert all(decided.values()) is True
        assert {e["kind"] for e in server.bus_events} == {"scene.changed"}