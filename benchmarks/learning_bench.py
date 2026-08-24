"""Learning benchmark for the B2 gate (doc 14).

Demonstration target: **spatial-context recall precision** — the contract's
primary candidate. The brain is quizzed on where objects are before and
after an experience window (observing object placements), with no code
changes between runs. Improvement must come from persisted memory.

Protocol:
  1. baseline: fresh in-memory brain answers placement questions -> score
  2. experience: a durable-store brain observes N placements (admissions
     tagged with spatial context)
  3. after: same questions again -> score must improve
  4. restart_survival: a NEW brain over the same durable store retains it
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BENCHMARK_NAME = "spatial-context-recall"


def _score(brain, questions: list[tuple[str, str]]) -> float:
    """Fraction of 'where is X' questions answered with the right place."""
    if not questions:
        return 0.0
    correct = 0
    for obj, place in questions:
        hits = brain.memory.retrieve(f"where is the {obj}", place=place)
        # precise: the record naming this object exists under THIS place
        if any(obj in str(h.content).lower() for h in hits):
            correct += 1
    return correct / len(questions)


def _observe_placements(brain, placements: list[tuple[str, str]], region_id: str) -> None:
    """Admit placement observations tagged with spatial context."""
    x = float(getattr(brain.body, "x_m", 0.0))
    y = float(getattr(brain.body, "y_m", 0.0))
    for obj, place in placements:
        brain.memory.admit(
            memory_type="observation",
            content=f"the {obj} is in the {place}",
            confidence=0.9,
            verification_status="verified",
            privacy_class="personal",
            provenance={"source": "learning-bench"},
            spatial_context={"place": region_id, "x_m": x, "y_m": y},
        )


def _register_kitchen(brain) -> None:
    from novi.brain.spatial_map import Region

    x = float(getattr(brain.body, "x_m", 0.0))
    y = float(getattr(brain.body, "y_m", 0.0))
    brain.spatial.register_region(
        Region(region_id="kitchen", frame="map", kind="room",
               bounds_x=(x - 5.0, x + 5.0), bounds_y=(y - 5.0, y + 5.0))
    )


PLACEMENTS = [
    ("kettle", "kitchen"),
    ("cup", "kitchen"),
    ("book", "kitchen"),
]
QUESTIONS = [(obj, rid) for obj, rid in PLACEMENTS]


def run_learning_benchmark() -> dict:
    from novi.brain.engine import MacBrain, MacBrainConfig
    from novi.brain.tests.test_mac_brain import FakeCamera

    report: dict = {"benchmark": BENCHMARK_NAME}

    # -- baseline: brand-new in-memory brain knows nothing -------------------
    baseline_brain = MacBrain(camera=FakeCamera(),
                              config=MacBrainConfig(curiosity_enabled=False))
    _register_kitchen(baseline_brain)
    baseline_score = _score(baseline_brain, QUESTIONS)
    report["baseline"] = {"score": baseline_score, "questions": len(QUESTIONS)}

    # -- durable brain: baseline -> experience -> after ----------------------
    with tempfile.TemporaryDirectory() as tmp:
        store_path = Path(tmp) / "learn.db"
        learner = MacBrain(camera=FakeCamera(), store_path=str(store_path),
                           config=MacBrainConfig(curiosity_enabled=False))
        _register_kitchen(learner)
        pre = _score(learner, QUESTIONS)

        # experience window: observe placements (no code changes, no teaching)
        _observe_placements(learner, PLACEMENTS, "kitchen")

        post = _score(learner, QUESTIONS)
        report["after"] = {"score": post, "questions": len(QUESTIONS)}
        report["pre_experience"] = {"score": pre}
        report["improved"] = post > pre

        # restart survival: new brain instance over the same durable store
        try:
            learner.stop()
        except Exception:  # noqa: BLE001 - lifecycle may not be ACTIVE; flush is best-effort
            pass
        survivor = MacBrain(camera=FakeCamera(), store_path=str(store_path),
                            config=MacBrainConfig(curiosity_enabled=False))
        _register_kitchen(survivor)
        survived_score = _score(survivor, QUESTIONS)
        report["restart_survival"] = bool(
            survived_score >= post and post > 0
        ), float(survived_score)
        report["restart_survival"] = bool(survived_score >= post and post > 0)
        report["restart_score"] = survived_score

    # regression wall: deterministic subset of the suite (fast, CI-safe).
    # Full wall runs separately via `pytest` before gate closure.
    import subprocess

    r = subprocess.run(
        [str(ROOT_VENV_PY()), "-m", "pytest",
         "novi/brain/tests/test_spatial_map.py",
         "novi/brain/tests/test_memory_class_gate.py",
         "-q", "--no-header"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=600,
    )
    tail = (r.stdout or "").strip().splitlines()[-1:] or [""]
    report["regression_wall"] = "pass" if ("passed" in tail[0] and "failed" not in tail[0]) else f"fail: {tail[0][:120]}"

    return report


def ROOT_VENV_PY() -> Path:
    return Path(__file__).resolve().parents[1] / ".venv" / "bin" / "python"


if __name__ == "__main__":
    import json

    print(json.dumps(run_learning_benchmark(), indent=2))
