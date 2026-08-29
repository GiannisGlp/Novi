"""Grounding service client (L2 bridge consumer).

HTTP implementation of SpatialPerceptionBackend over urllib (stdlib) — the
web server, CLI, and future body all use this to reach the local (or later,
Jetson-hosted) grounding service. When the service is unreachable the client
raises ConnectionError; callers fall back to the deterministic backend
(Novi's never-crash rule).
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request

from novi.brain.io import CameraFrame
from novi.perception.grounding import (
    GroundingResult,
    SpatialBackendCapabilities,
    SpatialInferencePolicy,
    SpatialPerceptionBackend,
    SpatialQuery,
)
from novi.perception.grounding_rpc import (
    CAPABILITIES_PATH,
    GROUND_PATH,
    HEALTH_PATH,
    capabilities_from_dict,
    result_from_dict,
)


class GroundingClient:
    """SpatialPerceptionBackend speaking the grounding RPC wire format."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def capabilities(self) -> SpatialBackendCapabilities:
        return capabilities_from_dict(self._get(CAPABILITIES_PATH))

    def health(self) -> bool:
        try:
            return bool(self._get(HEALTH_PATH).get("ok"))
        except ConnectionError:
            return False

    def ground(
        self,
        image: CameraFrame,
        query: SpatialQuery,
        policy: SpatialInferencePolicy,
    ) -> GroundingResult:
        return self._ground(image, query, policy, requested_output=query.requested_output)

    def point(
        self,
        image: CameraFrame,
        query: SpatialQuery,
        policy: SpatialInferencePolicy,
    ) -> GroundingResult:
        return self._ground(image, query, policy, requested_output="point")

    def detect(
        self,
        image: CameraFrame,
        labels: tuple[str, ...],
        policy: SpatialInferencePolicy,
    ) -> GroundingResult:
        from dataclasses import replace

        query = SpatialQuery(
            text=", ".join(labels),
            frame_id=image.frame_id,
            timestamp=image.captured_at,
            requested_output="box",
        )
        return self._ground(image, query, policy, requested_output="box")

    # -- internals ---------------------------------------------------------

    def _get(self, path: str) -> dict:
        try:
            with urllib.request.urlopen(f"{self.base_url}{path}", timeout=10) as resp:
                return json.loads(resp.read())
        except urllib.error.URLError as exc:
            raise ConnectionError(f"grounding service unreachable at {self.base_url}: {exc}") from exc

    def _ground(
        self, image: CameraFrame, query: SpatialQuery, policy: SpatialInferencePolicy, *, requested_output: str
    ) -> GroundingResult:
        payload = {
            "query": query.text,
            "frame_id": query.frame_id,
            "timestamp": query.timestamp,
            "requested_output": requested_output,
            "max_results": policy.max_results,
            "mode": policy.mode.value,
            "risk_class": policy.risk_class,
            "width": image.width,
            "height": image.height,
            "frame_b64": base64.b64encode(image.payload).decode("ascii"),
        }
        body = json.dumps(payload).encode("utf-8")
        try:
            req = urllib.request.Request(
                f"{self.base_url}{GROUND_PATH}", data=body, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                return result_from_dict(json.loads(resp.read()))
        except urllib.error.URLError as exc:
            raise ConnectionError(f"grounding service unreachable at {self.base_url}: {exc}") from exc
