#!/usr/bin/env python3
"""Grounding service launcher (L2 bridge — run in the HEAVY venv).

Starts the LocateAnything grounding service on 127.0.0.1:8721 so the web
server / CLI / future body (all stdlib, main venv) can reach the real model
through GroundingClient. The capability probe reports honestly when the
model cannot load; consumers fall back to the deterministic backend.

Usage:
    HF_HOME=~/.cache/novi/models/locateanything-hf \
    .venv-locateanything/bin/python scripts/mac-locateanything-service.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
os.environ.setdefault("HF_HOME", os.path.expanduser("~/.cache/novi/models/locateanything-hf"))

from novi.perception.grounding_service import GroundingServer  # noqa: E402
from novi.perception.locate_anything import LocateAnythingBackend  # noqa: E402
from novi.perception.locate_anything_runtime import LocateAnythingRuntime  # noqa: E402


def main() -> int:
    backend = LocateAnythingBackend()
    backend.attach_runtime(LocateAnythingRuntime())
    caps = backend.capabilities()
    print(f"[grounding-service] state={caps.state.value} device={caps.device}")
    if not caps.usable:
        print("[grounding-service] model not usable; serving fail-closed (consumers fall back)")
    server = GroundingServer(backend, host="127.0.0.1", port=8721)
    port = server.start()
    print(f"[grounding-service] listening on 127.0.0.1:{port} (Ctrl-C to stop)")
    try:
        import time

        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
