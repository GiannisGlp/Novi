"""Grounding RPC payload schema (L2 bridge: service <-> clients).

JSON wire format shared by the local grounding service (heavy venv) and its
clients (web server, CLI, future body — all stdlib, no heavy deps).
Encode/decode GroundingResult <-> dict. Deterministic, no imports beyond
the perception package.
"""

from __future__ import annotations

from novi.brain.io import CameraFrame
from novi.perception.grounding import (
    BackendState,
    GroundingObservation,
    GroundingResult,
    PointObservation,
    SpatialBackendCapabilities,
    SpatialInferenceMode,
)

GROUND_PATH = "/ground"
CAPABILITIES_PATH = "/capabilities"
HEALTH_PATH = "/health"


def observation_to_dict(obs: GroundingObservation | PointObservation) -> dict:
    if isinstance(obs, GroundingObservation):
        return {
            "kind": "box",
            "observation_id": obs.observation_id,
            "query": obs.query,
            "label": obs.label,
            "image_width": obs.image_width,
            "image_height": obs.image_height,
            "source_box": list(obs.source_box),
            "pixel_box": list(obs.pixel_box),
            "source_point": list(obs.source_point) if obs.source_point else None,
            "pixel_point": list(obs.pixel_point) if obs.pixel_point else None,
            "model_id": obs.model_id,
            "model_revision": obs.model_revision,
            "backend_version": obs.backend_version,
            "inference_mode": obs.inference_mode.value,
            "frame_id": obs.frame_id,
            "timestamp": obs.timestamp,
            "confidence": obs.confidence,
            "fallback": obs.fallback,
            "provenance": obs.provenance,
            "latency_ms": obs.latency_ms,
        }
    return {
        "kind": "point",
        "observation_id": obs.observation_id,
        "query": obs.query,
        "label": obs.label,
        "image_width": obs.image_width,
        "image_height": obs.image_height,
        "source_point": list(obs.source_point),
        "pixel_point": list(obs.pixel_point),
        "model_id": obs.model_id,
        "model_revision": obs.model_revision,
        "backend_version": obs.backend_version,
        "inference_mode": obs.inference_mode.value,
        "frame_id": obs.frame_id,
        "timestamp": obs.timestamp,
        "confidence": obs.confidence,
        "fallback": obs.fallback,
        "provenance": obs.provenance,
        "latency_ms": obs.latency_ms,
    }


def _s(d: dict, key: str) -> str:
    v = d[key]
    assert isinstance(v, str), f"{key} must be str"
    return v


def _i(d: dict, key: str) -> int:
    v = d[key]
    assert isinstance(v, int), f"{key} must be int"
    return v


def _b(d: dict, key: str, default: bool = False) -> bool:
    v = d.get(key, default)
    assert isinstance(v, bool), f"{key} must be bool"
    return v


def _f_opt(d: dict, key: str) -> float | None:
    v = d.get(key)
    assert v is None or isinstance(v, (int, float)), f"{key} must be float|None"
    return v


def observation_from_dict(d: dict) -> GroundingObservation | PointObservation:
    mode = SpatialInferenceMode(_s(d, "inference_mode"))
    if d["kind"] == "box":
        x1, y1, x2, y2 = d["source_box"]
        sp = d.get("source_point")
        return GroundingObservation(
            observation_id=_s(d, "observation_id"),
            query=_s(d, "query"),
            label=_s(d, "label"),
            source_box=(x1, y1, x2, y2),
            source_point=tuple(sp) if sp else None,
            image_width=_i(d, "image_width"),
            image_height=_i(d, "image_height"),
            model_id=_s(d, "model_id"),
            model_revision=_s(d, "model_revision"),
            backend_version=_s(d, "backend_version"),
            inference_mode=mode,
            frame_id=_s(d, "frame_id"),
            timestamp=_s(d, "timestamp"),
            confidence=_f_opt(d, "confidence"),
            fallback=_b(d, "fallback"),
            provenance=_s(d, "provenance"),
            latency_ms=_f_opt(d, "latency_ms"),
        )
    sp = d["source_point"]
    return PointObservation(
        observation_id=_s(d, "observation_id"),
        query=_s(d, "query"),
        label=_s(d, "label"),
        source_point=tuple(sp),
        image_width=_i(d, "image_width"),
        image_height=_i(d, "image_height"),
        model_id=_s(d, "model_id"),
        model_revision=_s(d, "model_revision"),
        backend_version=_s(d, "backend_version"),
        inference_mode=mode,
        frame_id=_s(d, "frame_id"),
        timestamp=_s(d, "timestamp"),
        confidence=_f_opt(d, "confidence"),
        fallback=_b(d, "fallback"),
        provenance=_s(d, "provenance"),
        latency_ms=_f_opt(d, "latency_ms"),
    )


def result_to_dict(result: GroundingResult) -> dict:
    return {
        "query": result.query,
        "observations": [observation_to_dict(o) for o in result.observations],
        "backend_status": result.backend_status,
        "model_id": result.model_id,
        "model_revision": result.model_revision,
        "backend_version": result.backend_version,
        "inference_mode": result.inference_mode.value,
        "frame_id": result.frame_id,
        "timestamp": result.timestamp,
        "latency_ms": result.latency_ms,
        "success": result.success,
        "validation_errors": list(result.validation_errors),
        "fallback_count": result.fallback_count,
        "raw_hash": result.raw_hash,
        "no_object": result.no_object,
    }


def result_from_dict(d: dict) -> GroundingResult:
    return GroundingResult(
        query=_s(d, "query"),
        observations=tuple(observation_from_dict(o) for o in d["observations"]),
        backend_status=_s(d, "backend_status"),
        model_id=_s(d, "model_id"),
        model_revision=_s(d, "model_revision"),
        backend_version=_s(d, "backend_version"),
        inference_mode=SpatialInferenceMode(_s(d, "inference_mode")),
        frame_id=_s(d, "frame_id"),
        timestamp=_s(d, "timestamp"),
        latency_ms=_f_opt(d, "latency_ms"),
        success=_b(d, "success"),
        validation_errors=tuple(d.get("validation_errors", [])),
        fallback_count=d.get("fallback_count", 0),
        raw_hash=d.get("raw_hash"),
        no_object=_b(d, "no_object"),
    )


def request_to_dict(query, policy) -> dict:
    return {
        "query": query.text,
        "frame_id": query.frame_id,
        "timestamp": query.timestamp,
        "requested_output": query.requested_output,
        "max_results": query.max_results,
        "mode": policy.mode.value,
        "risk_class": policy.risk_class,
    }


def capabilities_to_dict(caps: SpatialBackendCapabilities) -> dict:
    return {
        "state": caps.state.value,
        "model_id": caps.model_id,
        "model_revision": caps.model_revision,
        "device": caps.device,
        "modes": [m.value for m in caps.modes],
        "details": list(caps.details),
    }


def capabilities_from_dict(d: dict) -> SpatialBackendCapabilities:
    return SpatialBackendCapabilities(
        state=BackendState(d["state"]),
        model_id=d.get("model_id"),
        model_revision=d.get("model_revision"),
        device=d.get("device"),
        modes=tuple(SpatialInferenceMode(m) for m in d.get("modes", [])),
        details=tuple(tuple(x) for x in d.get("details", [])),
    )


def frame_to_dict(frame: CameraFrame) -> dict:
    import base64

    return {
        "width": frame.width,
        "height": frame.height,
        "frame_b64": base64.b64encode(frame.payload).decode("ascii"),
    }


def frame_from_dict(d: dict) -> CameraFrame:
    import base64

    return CameraFrame(
        frame_id=d["frame_id"],
        captured_at=d.get("timestamp", ""),
        width=d["width"],
        height=d["height"],
        payload=base64.b64decode(d["frame_b64"]),
    )
