"""Tests: grounding service + client round-trip (L2 bridge).

The service hosts ANY SpatialPerceptionBackend (here: the deterministic one
— no model, no torch); the client is the stdlib HTTP consumer the web app,
CLI, and future body will use. Proves the wire format end-to-end and the
never-crash behavior when the service is down.
"""

from __future__ import annotations

from typing import Iterator

import pytest

from novi.brain.io import CameraFrame
from novi.perception.grounding import (
    GroundingObservation,
    PointObservation,
    SpatialInferenceMode,
    SpatialInferencePolicy,
    SpatialQuery,
)
from novi.perception.grounding_client import GroundingClient
from novi.perception.grounding_service import GroundingServer
from novi.perception.locate_anything import DeterministicLocateAnythingBackend

W, H = 640, 480


def _frame(fid: str = "f1") -> CameraFrame:
    return CameraFrame(frame_id=fid, captured_at="t0", width=W, height=H, payload=b"jpeg-bytes")


def _backend() -> DeterministicLocateAnythingBackend:
    return DeterministicLocateAnythingBackend(
        scripted={
            ("f1", "locate the cup"): [("cup", (100, 200, 900, 800)), ("handle", (500, 500))],
            ("f1", "locate a unicorn"): ["none"],
        }
    )


@pytest.fixture()
def server() -> Iterator[GroundingServer]:
    s = GroundingServer(_backend(), port=0)
    s.start()
    yield s
    s.stop()


class TestService:
    def test_health_and_capabilities(self, server):
        import urllib.request

        with urllib.request.urlopen(f"http://127.0.0.1:{server.port}/health", timeout=5) as resp:
            assert resp.status == 200

        client = GroundingClient(f"http://127.0.0.1:{server.port}")
        caps = client.capabilities()
        assert caps.usable
        assert caps.model_id == "deterministic"
        assert caps.state.value == "available"


class TestClientRoundTrip:
    def test_ground_returns_typed_result(self, server):
        client = GroundingClient(f"http://127.0.0.1:{server.port}")
        query = SpatialQuery(text="locate the cup", frame_id="f1", timestamp="t0")
        result = client.ground(_frame(), query, SpatialInferencePolicy())
        assert result.success
        assert len(result.observations) == 2
        box = result.observations[0]
        assert isinstance(box, GroundingObservation)
        assert box.pixel_box == (64, 96, 512, 288)
        assert box.model_revision == "local"
        point = result.observations[1]
        assert isinstance(point, PointObservation)
        assert point.pixel_point == (320, 240)

    def test_no_object_round_trip(self, server):
        client = GroundingClient(f"http://127.0.0.1:{server.port}")
        query = SpatialQuery(text="locate a unicorn", frame_id="f1", timestamp="t0")
        result = client.ground(_frame(), query, SpatialInferencePolicy())
        assert result.success
        assert result.no_object

    def test_point_request_filters_boxes(self, server):
        client = GroundingClient(f"http://127.0.0.1:{server.port}")
        query = SpatialQuery(text="locate the cup", frame_id="f1", timestamp="t0")
        result = client.point(_frame(), query, SpatialInferencePolicy())
        assert all(isinstance(o, PointObservation) for o in result.observations)

    def test_client_is_spatial_perception_backend_compatible(self, server):
        # the web layer can use the client wherever a backend is expected
        from novi.perception.grounding import SpatialPerceptionBackend

        client = GroundingClient(f"http://127.0.0.1:{server.port}")
        assert isinstance(client, SpatialPerceptionBackend)


class TestServiceDown:
    def test_health_false_when_down(self):
        client = GroundingClient("http://127.0.0.1:1")  # nothing listens on port 1
        assert client.health() is False

    def test_ground_raises_connection_error_when_down(self):
        client = GroundingClient("http://127.0.0.1:1")
        query = SpatialQuery(text="locate the cup", frame_id="f1", timestamp="t0")
        with pytest.raises(ConnectionError):
            client.ground(_frame(), query, SpatialInferencePolicy())
