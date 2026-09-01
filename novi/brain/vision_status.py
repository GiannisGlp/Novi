"""Live-vision self-awareness for the brain (plan 26 B).

Novi must be able to honestly say what it currently sees — and when it can't.
The web layer installs a provider that *reads* ``MultimodalRuntime`` + feed
state; ``build_vision_status`` merges that snapshot into a JSON-safe dict.
With NO provider (non-web builds) it returns an honest offline report, so a
brain with no camera wired never claims sight.

Read-only by design: the provider only reads camera/runtime state and never
calls brain methods, so the reply thread (which may hold the brain lock) can
never deadlock against the camera thread.
"""

from __future__ import annotations

from typing import Any

# Every key ``build_vision_status`` emits. A provider may only contribute
# these keys — anything extra is dropped, so a stale or hostile provider can't
# grow the payload or inject a fake ``can_see``.
_KEYS: tuple[str, ...] = (
    "camera_live",
    "health",
    "recognition_available",
    "person",
    "person_tier",
    "place",
    "objects",
    "scene_labels",
    "last_frame_age_s",
    "processed_fps",
    "stage_ms",
    "drop_rate",
    "associations",
)

# Hardware health values that mean "no frames you can trust right now".
_OFFLINE_HEALTH: frozenset[str] = frozenset({"offline", "failed"})

# Health-check names on the brain's own engine that describe vision hardware.
_BRAIN_HEALTH_NAMES: frozenset[str] = frozenset({"camera", "perception", "vision"})


def _default_status() -> dict[str, Any]:
    return {
        "camera_live": False,
        "health": "offline",
        "recognition_available": False,
        "person": "",
        "person_tier": "",
        "place": "",
        "objects": [],
        "scene_labels": [],
        "last_frame_age_s": None,
        "processed_fps": 0.0,
        "stage_ms": {},
        "drop_rate": 0.0,
        "associations": [],
        "can_see": False,
        "available": False,
    }


def _brain_camera_health(brain: Any) -> str | None:
    """Camera/vision status from the brain's own health checks, if any."""
    health = getattr(brain, "_last_health", None) or {}
    for check in health.get("checks", []) or []:
        name = str(check.get("name") or check.get("check") or "").lower()
        if name in _BRAIN_HEALTH_NAMES:
            return str(check.get("status", "unknown")).lower()
    return None


def build_vision_status(brain: Any, provider: Any | None = None) -> dict[str, Any]:
    """Assemble the JSON-safe vision state for ``brain``.

    ``provider`` is a zero-arg callable returning a dict of the known keys
    (or raising — the stack is still wired, just broken). Without a provider
    the status is honestly offline. ``can_see`` is True only when frames are
    live AND the hardware health isn't offline/failed.
    """
    status = _default_status()
    if provider is None:
        health = _brain_camera_health(brain)
        if health is not None:
            status["health"] = health
        return status

    data: dict[str, Any] = {}
    try:
        data = dict(provider() or {})
    except Exception:  # noqa: BLE001 - a failing provider degrades to offline
        data = {}

    for key in _KEYS:
        if key in data:
            status[key] = data[key]

    status["available"] = True  # a provider answered: the vision stack is wired
    health = str(status.get("health", "")).lower()
    status["can_see"] = bool(
        status.get("camera_live") and health not in _OFFLINE_HEALTH
    )
    return status
