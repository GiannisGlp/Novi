"""Web vision provider for the brain (plan 26 B/C).

Builds the read-only callable installed on the brain via
``brain.set_vision_provider(...)``. It reads ``MultimodalRuntime`` + camera
feed state and returns the bounded JSON-safe dict ``build_vision_status``
merges.

Deadlock rule: the provider only READS ``mm_runtime``/feed — it never calls
brain methods. The reply thread can hold the brain lock while the camera
thread holds ``mm_lock``; a provider that called back into the brain would
risk a cross-lock deadlock, so it never does. A failure degrades to ``{}``,
which ``build_vision_status`` turns into an honest offline report.
"""

from __future__ import annotations

from typing import Any

from novi.perception.camera import CameraHealth

_MAX_OBJECTS = 8
_LIVE_HEALTHS = frozenset({CameraHealth.AVAILABLE.value, CameraHealth.DEGRADED.value})


def build_vision_provider(server: Any) -> Any:
    """Return a zero-arg provider callable reading ``server``'s perception state."""

    def _provider() -> dict[str, Any]:
        runtime = getattr(server, "mm_runtime", None)
        if runtime is None:
            return {"camera_live": False, "health": "offline"}

        snap = runtime.snapshot()
        feed = getattr(server, "mm_camera_feed", None)

        health = "offline"
        camera_live = False
        last_frame_age_s: float | None = None
        drop_rate = 0.0
        if feed is not None:
            health = feed.health.value
            camera_live = health in _LIVE_HEALTHS
            try:
                last_frame_age_s = feed.last_frame_age_s()
            except Exception:  # noqa: BLE001 - telemetry is best-effort
                last_frame_age_s = None
            total = feed.captured + feed.dropped
            drop_rate = (feed.dropped / total) if total else 0.0

        cadence = snap.get("cadence") or {}
        return {
            "camera_live": camera_live,
            "health": health,
            "recognition_available": getattr(server, "mm_store", None) is not None,
            "person": str(snap.get("person", "") or ""),
            "person_tier": str(snap.get("tier", "") or ""),
            "place": str(snap.get("place", "") or ""),
            "objects": [str(o) for o in (snap.get("objects") or [])][:_MAX_OBJECTS],
            "scene_labels": sorted(getattr(runtime, "_last_scene_labels", set()) or set()),
            "last_frame_age_s": last_frame_age_s,
            "processed_fps": cadence.get("processed_fps", 0.0),
            "stage_ms": cadence.get("stage_ms", {}),
            "drop_rate": drop_rate,
            "associations": list(snap.get("associations") or []),
        }

    return _provider
