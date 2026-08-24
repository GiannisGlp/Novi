"""Context-resolution benchmark (doc 14, B3 evidence).

Scripted scenario families run live against the deterministic brain:

- anaphora:       DiscourseState resolves "is it still there?" to the
                  ongoing topic ("kettle") — gap G3.
- addressee:      identity-based addressee resolution; lowercase known
                  person resolves, arbitrary capitalized non-persons do
                  not — gap G2.
- spatial_recall: a memory admitted while the body stands in a registered
                  "kitchen" region is retrievable by place=kitchen — gap G7.

Each scenario returns pass/fail; the gate needs all families green.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _make_brain():
    from novi.brain.engine import MacBrain, MacBrainConfig
    from novi.brain.tests.test_mac_brain import FakeCamera

    return MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))


def _start(brain) -> None:
    from novi.brain.runtime import Lifecycle

    if brain.brain.lifecycle is not Lifecycle.ACTIVE:
        brain.start()


# -- scenario families -----------------------------------------------------------


def scenario_anaphora() -> bool:
    """Discourse resolves 'it' to the ongoing topic via note_user_message."""
    brain = _make_brain()
    _start(brain)

    first = brain.note_user_message("where is the kettle?")
    second = brain.note_user_message("is it still there?")

    return (
        first.get("status") in ("NONE", "RESOLVED")
        and second.get("status") == "RESOLVED"
        and second.get("resolved_topic") == "kettle"
    )


def scenario_addressee() -> bool:
    """Identity-first addressee resolution via resolve_addressee (G2).

    1. self-introduction binds a name ("i am Maya" -> addressee maya);
    2. the bound name is then preferred on later messages;
    3. third-party mentions return a candidate but never rebind identity.
    """
    brain = _make_brain()
    _start(brain)

    # self-introduction binds and returns the name
    intro = brain.resolve_addressee("hi, i am Maya")
    if intro.lower() != "maya":
        return False

    # subsequent message: bound name is preferred as addressee
    follow = brain.resolve_addressee("Maya here again, did you notice?")
    if follow.lower() != "maya":
        return False

    # third-party mention: legacy fallback may surface a candidate name,
    # but the speaker's bound identity must not be overwritten
    brain.resolve_addressee("is Zoe coming over later?")
    belief = getattr(brain.identity, "identity_for", lambda _: None)("person")
    bound = (belief.name if belief is not None else "") or ""
    return bound.lower() == "maya"


def scenario_spatial_recall() -> bool:
    """Memory admitted inside the kitchen region is retrievable by place."""
    from novi.brain.spatial_map import Region

    brain = _make_brain()
    _start(brain)

    # register a kitchen region covering the body's current pose
    x = float(getattr(brain.body, "x_m", 0.0))
    y = float(getattr(brain.body, "y_m", 0.0))
    brain.spatial.register_region(
        Region(
            region_id="kitchen",
            frame="map",
            kind="room",
            bounds_x=(x - 5.0, x + 5.0),
            bounds_y=(y - 5.0, y + 5.0),
        )
    )
    place = brain.spatial.region_at(x, y)
    if place != "kitchen":
        return False

    store = getattr(brain, "memory", None)
    if store is None or not hasattr(store, "admit"):
        return False

    admission = store.admit(
        memory_type="observation",
        content="the cup is on the counter next to the sink",
        confidence=0.9,
        verification_status="verified",
        privacy_class="personal",
        provenance={"source": "context-bench"},
        spatial_context={"place": "kitchen", "x_m": x, "y_m": y},
    )
    if not getattr(admission, "accepted", False):
        return False

    hits = store.retrieve("cup counter", place="kitchen")
    return any("cup" in str(h.content).lower() for h in hits)


REGISTRY: dict[str, tuple[Callable[[], bool], str]] = {
    "anaphora": (scenario_anaphora, "G3 discourse/anaphora resolution"),
    "addressee": (scenario_addressee, "G2 identity-based addressee resolution"),
    "spatial_recall": (scenario_spatial_recall, "G7 place-tagged memory retrieval"),
}


def run_context_scenarios(brain_factory: Callable[[], Any] | None = None) -> tuple[dict[str, Any], int, int]:
    """Run all scenario families. Returns (by_name, total, passed)."""
    by_name: dict[str, Any] = {}
    total = passed = 0
    for name, (fn, why) in REGISTRY.items():
        total += 1
        try:
            ok = bool(fn())
        except Exception as exc:  # noqa: BLE001 - a crash is a fail with detail
            by_name[name] = {"pass": False, "error": f"{type(exc).__name__}: {exc}"[:200], "closes": why}
            continue
        passed += 1 if ok else 0
        by_name[name] = {"pass": ok, "closes": why}
    return by_name, total, passed


if __name__ == "__main__":
    by_name, total, passed = run_context_scenarios()
    print(f"context scenarios: {passed}/{total}")
    for k, v in by_name.items():
        print(f"  {k}: {'PASS' if v['pass'] else 'FAIL'}{'' if v['pass'] else ' ' + str(v)}")
