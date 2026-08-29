"""Local grounding service (L2 bridge).

Serves ANY SpatialPerceptionBackend over localhost HTTP so the heavy
LocateAnything runtime can live in the isolated venv while the web server,
CLI, and future body talk to it through the SAME interface. Stdlib only
(ThreadingHTTPServer) — the service runs where the model lives.

Endpoints:
  GET  /capabilities -> 7-state capability report
  GET  /health       -> {"ok": true}
  POST /ground       -> {query, frame_id, timestamp, requested_output,
                          max_results, mode, risk_class, width, height,
                          frame_b64} -> GroundingResult JSON

Wire schema lives in grounding_rpc.py (shared with clients).
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from novi.brain.io import CameraFrame
from novi.perception.grounding import (
    SpatialInferenceMode,
    SpatialInferencePolicy,
    SpatialPerceptionBackend,
    SpatialQuery,
)
from novi.perception.grounding_rpc import (
    CAPABILITIES_PATH,
    GROUND_PATH,
    HEALTH_PATH,
    capabilities_to_dict,
    result_to_dict,
)

_PORT = 8721  # novi grounding service default


class _Handler(BaseHTTPRequestHandler):
    server: "GroundingServer"  # type: ignore[assignment]

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 — keep stdout clean
        pass

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == HEALTH_PATH:
            self._json(200, {"ok": True})
        elif self.path == CAPABILITIES_PATH:
            self._json(200, capabilities_to_dict(self.server.backend.capabilities()))
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != GROUND_PATH:
            self._json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": f"bad request: {exc}"})
            return

        frame = CameraFrame(
            frame_id=payload.get("frame_id") or "grounding-service",
            captured_at=payload.get("timestamp", ""),
            width=int(payload["width"]),
            height=int(payload["height"]),
            payload=__import__("base64").b64decode(payload["frame_b64"]),
        )
        query = SpatialQuery(
            text=payload["query"],
            frame_id=frame.frame_id,
            timestamp=frame.captured_at,
            requested_output=payload.get("requested_output", "both"),
            max_results=int(payload.get("max_results", 5)),
        )
        policy = SpatialInferencePolicy(
            mode=SpatialInferenceMode(payload.get("mode", "hybrid")),
            max_results=int(payload.get("max_results", 5)),
            risk_class=payload.get("risk_class", "routine"),
        )
        result = self.server.backend.ground(frame, query, policy)
        self._json(200, result_to_dict(result))


class GroundingServer:
    """Lifecycle wrapper around the ThreadingHTTPServer."""

    def __init__(self, backend: SpatialPerceptionBackend, *, host: str = "127.0.0.1", port: int = _PORT) -> None:
        self.backend = backend
        self.host = host
        self.port = port
        self._httpd: ThreadingHTTPServer | None = None

    def start(self) -> int:
        """Bind + serve in a daemon thread. Returns the bound port."""
        self._httpd = ThreadingHTTPServer((self.host, self.port), _Handler)
        self._httpd.backend = self.backend  # type: ignore[attr-defined]
        self.port = self._httpd.server_address[1]
        import threading

        threading.Thread(target=self._httpd.serve_forever, daemon=True).start()
        return self.port

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None

    def __enter__(self) -> "GroundingServer":
        self.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.stop()


def run_grounding_service(backend: SpatialPerceptionBackend, *, host: str = "127.0.0.1", port: int = _PORT) -> GroundingServer:
    """Convenience: start the service and return the server handle."""
    return GroundingServer(backend, host=host, port=port)
