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
    # Language-conditioned spatial grounding (LocateAnything workstream)
    "BackendState": (".grounding", "BackendState"),
    "SpatialInferenceMode": (".grounding", "SpatialInferenceMode"),
    "SpatialInferencePolicy": (".grounding", "SpatialInferencePolicy"),
    "SpatialQuery": (".grounding", "SpatialQuery"),
    "GroundingObservation": (".grounding", "GroundingObservation"),
    "PointObservation": (".grounding", "PointObservation"),
    "GroundingResult": (".grounding", "GroundingResult"),
    "SpatialBackendCapabilities": (".grounding", "SpatialBackendCapabilities"),
    "SpatialPerceptionBackend": (".grounding", "SpatialPerceptionBackend"),
    "parse_locate_anything_output": (".locate_anything_parse", "parse_locate_anything_output"),
    "LocateAnythingBackend": (".locate_anything", "LocateAnythingBackend"),
    "DeterministicLocateAnythingBackend": (".locate_anything", "DeterministicLocateAnythingBackend"),
    "LocateAnythingRuntime": (".locate_anything_runtime", "LocateAnythingRuntime"),
    # Grounding benchmark (plan Phase 10)
    "BenchmarkCorpus": (".benchmark_corpus", "BenchmarkCorpus"),
    "run_grounding_benchmark": (".benchmark", "run_grounding_benchmark"),
    "compare_baseline_vs_grounding": (".benchmark_compare", "compare_baseline_vs_grounding"),
    # Re-observation verification (plan Step 9.2)
    "VerificationOutcome": (".grounding_verification", "VerificationOutcome"),
    "verify_grounding_agreement": (".grounding_verification", "verify_grounding_agreement"),
    # Brain-zone seams (plan steps 18/21/22/24 — perception side)
    "admit_grounding_outcome": (".world_state_adapter", "admit_grounding_outcome"),
    "verify_predicted_presence": (".prediction_verification", "verify_predicted_presence"),
    "build_deliberation_record": (".deliberation_record", "build_deliberation_record"),
    "promotion_candidate": (".spatial_memory_promotion", "promotion_candidate"),
    # L2 bridge: local grounding service + HTTP client (web/CLI/body consumer)
    "GroundingServer": (".grounding_service", "GroundingServer"),
    "GroundingClient": (".grounding_client", "GroundingClient"),
}

__all__ = list(_LAZY)


def __getattr__(name: str):
    if name in _LAZY:
        from importlib import import_module

        mod_name, attr = _LAZY[name]
        return getattr(import_module(mod_name, __name__), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
