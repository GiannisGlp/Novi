"""Novi perception: camera acquisition, object detection, tracking-lite,
and face identity on the Mac body.

Self-contained capability package implementing
docs/plans/02_PERCEPTION/01_CAMERA_ACQUISITION.md and
docs/plans/02_PERCEPTION/02_FACE_AND_OBJECT_RECOGNITION.md.

Reuses brain contracts (CameraFrame) read-only; nothing in novi.brain
depends on this package. Exports resolve lazily so the package can be
imported while implementation lands module by module.
"""

_LAZY = {
    "CameraHealth": (".camera", "CameraHealth"),
    "FrameRecord": (".camera", "FrameRecord"),
    "CameraFeed": (".camera", "CameraFeed"),
    "Detection": (".detection", "Detection"),
    "ObjectDetector": (".detection", "ObjectDetector"),
    "DeterministicObjectDetector": (".detection", "DeterministicObjectDetector"),
    "Track": (".tracking", "Track"),
    "ObjectTracker": (".tracking", "ObjectTracker"),
    "FaceObservation": (".faces", "FaceObservation"),
    "IdentityTier": (".faces", "IdentityTier"),
    "IdentityDecision": (".faces", "IdentityDecision"),
    "FaceIdentifier": (".faces", "FaceIdentifier"),
    "PerceptionPipeline": (".pipeline", "PerceptionPipeline"),
}

__all__ = list(_LAZY)


def __getattr__(name: str):
    if name in _LAZY:
        from importlib import import_module

        mod_name, attr = _LAZY[name]
        return getattr(import_module(mod_name, __name__), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
