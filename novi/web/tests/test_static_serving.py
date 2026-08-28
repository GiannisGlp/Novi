"""HTTP-level tests for the React SPA static serving added to the web server.

The server serves the built SPA (novi/web/ui/dist) for page routes and assets,
returns a 503 build hint when the UI is not built, and never lets the SPA
fallback swallow /api/* routes.
"""

import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from novi.web.server import NoviWebHTTPServer, NoviWebServer, _resolve_ui_asset

SPA_SHELL = '<!DOCTYPE html><html><head><title>Novi</title></head><body><div id="root"></div></body></html>'


class StaticServingTests(unittest.TestCase):
    """Real HTTP requests against a server on an ephemeral port."""

    def setUp(self) -> None:
        self.novi = NoviWebServer(port=0, store_path=None, auto_step=False, chat_llm=False)
        self.novi.start()
        self.httpd = NoviWebHTTPServer(("127.0.0.1", 0), self.novi)
        self.port = self.httpd.server_address[1]
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self._thread.start()

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.novi.stop()

    def _get(self, path: str) -> tuple[int, str, bytes]:
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}") as resp:
            return resp.status, resp.headers.get("Content-Type", ""), resp.read()

    def _dist(self) -> Path:
        d = Path(tempfile.mkdtemp())
        (d / "index.html").write_text(SPA_SHELL, encoding="utf-8")
        (d / "assets").mkdir()
        (d / "assets" / "app.js").write_text("console.log('novi')", encoding="utf-8")
        (d / "assets" / "app.css").write_text("body{}", encoding="utf-8")
        return d

    # ── SPA shell serving ─────────────────────────────────────────

    def test_root_serves_spa_shell_when_dist_present(self) -> None:
        with patch("novi.web.server._UI_DIST", self._dist()):
            status, ctype, body = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", ctype)
        self.assertIn(b'id="root"', body)

    def test_camera_and_preview_serve_spa_shell(self) -> None:
        with patch("novi.web.server._UI_DIST", self._dist()):
            for route in ("/camera", "/preview", "/live"):
                status, _, body = self._get(route)
                self.assertEqual(status, 200, route)
                self.assertIn(b'id="root"', body, route)

    def test_spa_fallback_serves_shell_for_client_route(self) -> None:
        with patch("novi.web.server._UI_DIST", self._dist()):
            status, _, body = self._get("/overview")
        self.assertEqual(status, 200)
        self.assertIn(b'id="root"', body)

    # ── built assets ───────────────────────────────────────────────

    def test_serves_asset_with_mime_type(self) -> None:
        with patch("novi.web.server._UI_DIST", self._dist()):
            status, ctype, body = self._get("/assets/app.js")
        self.assertEqual(status, 200)
        self.assertIn("javascript", ctype)
        self.assertIn(b"console.log", body)

    def test_missing_asset_returns_404(self) -> None:
        with patch("novi.web.server._UI_DIST", self._dist()), self.assertRaises(urllib.error.HTTPError) as ctx:
            self._get("/assets/nope.js")
        self.assertEqual(ctx.exception.code, 404)

    # ── unbuilt UI (dist missing) ──────────────────────────────────

    def test_serves_build_hint_when_dist_missing(self) -> None:
        with patch("novi.web.server._UI_DIST", Path("/nonexistent/ui/dist")):
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                self._get("/")
        self.assertEqual(ctx.exception.code, 503)
        self.assertIn(b"npm run build", ctx.exception.read())

    # ── API routes are never swallowed by the SPA fallback ─────────

    def test_api_route_not_swallowed_by_fallback(self) -> None:
        with patch("novi.web.server._UI_DIST", self._dist()):
            status, ctype, _ = self._get("/api/state")
        self.assertEqual(status, 200)
        self.assertIn("application/json", ctype)

    # ── path traversal guard (pure function) ───────────────────────

    def test_resolve_ui_asset_rejects_traversal(self) -> None:
        with patch("novi.web.server._UI_DIST", Path("/tmp/fake-dist")):
            self.assertIsNone(_resolve_ui_asset("../server.py"))
            self.assertIsNone(_resolve_ui_asset("assets/../../server.py"))
            self.assertIsNone(_resolve_ui_asset("..%2fserver.py"))

    def test_resolve_ui_asset_accepts_in_dist_file(self) -> None:
        d = self._dist()
        with patch("novi.web.server._UI_DIST", d):
            self.assertEqual(_resolve_ui_asset("assets/app.js"), (d / "assets" / "app.js").resolve())
            self.assertIsNone(_resolve_ui_asset("assets/missing.js"))


if __name__ == "__main__":
    unittest.main()
