from __future__ import annotations

import argparse
import json
from pathlib import Path

from .io import CameraFrame, MacCamera
from .runtime import MacBrain


class DemoCamera:
    """No-hardware camera used for CI and first runtime smoke tests."""

    def __init__(self) -> None:
        self.sequence = 0

    def read(self) -> CameraFrame:
        self.sequence += 1
        return CameraFrame(
            frame_id=f"demo-{self.sequence}",
            captured_at="2026-08-19T00:00:00Z",
            width=1,
            height=1,
            payload=b"demo-frame",
            metadata={"backend": "deterministic-demo"},
        )

    def close(self) -> None:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Novi Mac Brain runtime")
    parser.add_argument("--live-camera", action="store_true", help="use the Mac camera instead of the deterministic camera")
    parser.add_argument("--deterministic", action="store_true", help="explicitly select the deterministic camera mode")
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--speak", type=str, default=None)
    parser.add_argument("--evidence", type=Path, default=Path("mac_brain_evidence.json"), help="write JSON evidence to this path")
    args = parser.parse_args()

    if args.live_camera and args.deterministic:
        parser.error("--live-camera and --deterministic are mutually exclusive")
    if args.cycles <= 0:
        parser.error("--cycles must be > 0")

    camera = MacCamera() if args.live_camera else DemoCamera()
    brain = MacBrain(camera=camera)
    results = []
    brain.start()
    try:
        for _ in range(args.cycles):
            results.append(brain.step())
        if args.speak:
            brain.speak(args.speak)
    finally:
        brain.stop()

    evidence = {
        "run_id": brain.run_id,
        "mode": "live_camera" if args.live_camera else "deterministic_demo",
        "results": results,
        "events": brain.events,
    }
    encoded = json.dumps(evidence, indent=2, sort_keys=True, default=str)
    print(encoded)
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(encoded + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
