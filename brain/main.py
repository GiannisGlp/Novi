from __future__ import annotations

import argparse
import json

from .runtime import BrainSupervisor


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Novi Brain Stage-0 runtime")
    parser.add_argument("--cycles", type=int, default=1, help="number of deterministic runtime cycles")
    args = parser.parse_args()
    if args.cycles < 1:
        parser.error("--cycles must be >= 1")

    brain = BrainSupervisor()
    outcomes = brain.run(args.cycles)
    print(json.dumps({
        "lifecycle": brain.lifecycle.value,
        "health": brain.health.status,
        "cycles": len(outcomes),
        "events": len(brain.events.events),
        "outcomes": [out.__dict__ for out in outcomes],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
