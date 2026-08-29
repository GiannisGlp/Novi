"""LocateAnything backends (plan Step 3.1/3.4/3.5, §19 steps 5/15).

Two implementations of the Novi-owned `SpatialPerceptionBackend` surface:

- `DeterministicLocateAnythingBackend` — scripted, model-free CI backend
  (same role as DeterministicObjectDetector): deterministic results keyed by
  (frame_id, query), zero hardware, zero downloads.
- `LocateAnythingBackend` — the thin real adapter. It owns the Novi contract
  (prompt hand-off, strict parsing, provenance, fail-closed semantics) and
  delegates model specifics to the optional runtime boundary
  (`locate_anything_runtime`), which is never imported at module load time.

Neither module-level import touches torch/transformers: `import
novi.perception.locate_anything` is safe on every machine, and a missing
LocateAnything runtime only shows up as a non-usable capability state.
"""

from __future__ import annotations

import time
from dataclasses import replace
from typing import Protocol, cast, runtime_checkable

from novi.brain.io import CameraFrame
from novi.perception.grounding import (
    BackendState,
    GroundingObservation,
    GroundingResult,
    PointObservation,
    SpatialBackendCapabilities,
    SpatialInferenceMode,
    SpatialInferencePolicy,
    SpatialQuery,
    sha256_hex,
)
from novi.perception.locate_anything_parse import ParseOutcome, parse_locate_anything_output

MODEL_ID = "nvidia/LocateAnything-3B"
MODEL_REVISION = "c32291ca5e996f5a7a485845b4f57a233936bba0"
BACKEND_VERSION = "0.1.0"

BoxSpec = tuple[str, tuple[int, int, int, int]]
PointSpec = tuple[str, tuple[int, int]]
ScriptedEntry = BoxSpec | PointSpec | str  # str == "none" marker


@runtime_checkable
class LocateAnythingRuntime(Protocol):
    """The optional runtime boundary (implemented in locate_anything_runtime).

    `infer` returns (raw model text, latency_ms). The adapter owns parsing,
    validation, and provenance — the runtime owns the model.
    """

    def probe(self) -> SpatialBackendCapabilities: ...

    def infer(
        self, image: CameraFrame, prompt: str, mode: SpatialInferenceMode
    ) -> tuple[str, float]: ...


def _norm_query(text: str) -> str:
    return " ".join(text.strip().lower().split())


class DeterministicLocateAnythingBackend:
    """Scripted language-grounding backend for CI and deterministic tests.

    Script table: {(frame_id, query_text): [("label", box4) | ("label", pt2) | "none"]}.
    Query matching is exact after normalization (strip/lower/collapse-space);
    an unscripted (frame, query) pair yields a valid empty result — the same
    convention as DeterministicObjectDetector's unplanned frames.
    """

    def __init__(self, scripted: dict[tuple[str, str], list[ScriptedEntry]]) -> None:
        self._scripted = {(fid, _norm_query(q)): entries for (fid, q), entries in scripted.items()}

    def capabilities(self) -> SpatialBackendCapabilities:
        return SpatialBackendCapabilities(
            state=BackendState.AVAILABLE,
            model_id="deterministic",
            model_revision="local",
            device="none",
            modes=(SpatialInferenceMode.FAST, SpatialInferenceMode.SLOW, SpatialInferenceMode.HYBRID),
        )

    def _entries(self, frame_id: str, query_text: str) -> list[ScriptedEntry]:
        return self._scripted.get((frame_id, _norm_query(query_text)), [])

    def ground(
        self,
        image: CameraFrame,
        query: SpatialQuery,
        policy: SpatialInferencePolicy,
    ) -> GroundingResult:
        entries = self._entries(query.frame_id, query.text)
        observations: list[GroundingObservation | PointObservation] = []
        no_object = False
        for idx, entry in enumerate(entries):
            if entry == "none":
                no_object = True
                continue
            label, coords = cast(tuple[str, tuple[int, ...]], entry)
            if len(coords) == 4 and query.requested_output in ("box", "both"):
                x1, y1, x2, y2 = coords
                observations.append(
                    GroundingObservation(
                        observation_id=f"det-{query.frame_id}-{idx}",
                        query=query.text,
                        label=label,
                        source_box=(x1, y1, x2, y2),
                        image_width=image.width,
                        image_height=image.height,
                        model_id="deterministic",
                        model_revision="local",
                        backend_version=BACKEND_VERSION,
                        inference_mode=policy.mode,
                        frame_id=query.frame_id,
                        timestamp=query.timestamp,
                        latency_ms=0.0,
                        provenance="deterministic",
                    )
                )
            elif len(coords) == 2 and query.requested_output in ("point", "both"):
                x, y = coords
                observations.append(
                    PointObservation(
                        observation_id=f"det-{query.frame_id}-{idx}",
                        query=query.text,
                        label=label,
                        source_point=(x, y),
                        image_width=image.width,
                        image_height=image.height,
                        model_id="deterministic",
                        model_revision="local",
                        backend_version=BACKEND_VERSION,
                        inference_mode=policy.mode,
                        frame_id=query.frame_id,
                        timestamp=query.timestamp,
                        latency_ms=0.0,
                        provenance="deterministic",
                    )
                )
        return GroundingResult(
            query=query.text,
            observations=tuple(observations),
            backend_status="available",
            model_id="deterministic",
            model_revision="local",
            backend_version=BACKEND_VERSION,
            inference_mode=policy.mode,
            frame_id=query.frame_id,
            timestamp=query.timestamp,
            latency_ms=0.0,
            success=True,
            no_object=no_object and not observations,
        )

    def point(
        self,
        image: CameraFrame,
        query: SpatialQuery,
        policy: SpatialInferencePolicy,
    ) -> GroundingResult:
        return self.ground(image, replace(query, requested_output="point"), policy)

    def detect(
        self,
        image: CameraFrame,
        labels: tuple[str, ...],
        policy: SpatialInferencePolicy,
    ) -> GroundingResult:
        query = SpatialQuery(
            text=", ".join(labels),
            frame_id=image.frame_id,
            timestamp=image.captured_at,
            requested_output="box",
        )
        return self.ground(image, query, policy)


class LocateAnythingBackend:
    """Thin Novi adapter over a LocateAnythingRuntime (real or injected).

    Owns: capability state, prompt hand-off, strict parsing, provenance,
    fail-closed results. Never imports the heavy runtime at module scope.
    """

    def __init__(
        self,
        runtime: LocateAnythingRuntime | None = None,
        *,
        model_id: str = MODEL_ID,
        model_revision: str = MODEL_REVISION,
        backend_version: str = BACKEND_VERSION,
    ) -> None:
        self._runtime = runtime
        self._model_id = model_id
        self._model_revision = model_revision
        self._backend_version = backend_version

    # -- capability state -------------------------------------------------
    def capabilities(self) -> SpatialBackendCapabilities:
        if self._runtime is None:
            return SpatialBackendCapabilities(
                state=BackendState.DEPENDENCY_MISSING,
                model_id=self._model_id,
                model_revision=self._model_revision,
            )
        probe = getattr(self._runtime, "probe", None)
        if probe is not None:
            return probe()
        return SpatialBackendCapabilities(
            state=BackendState.AVAILABLE,
            model_id=self._model_id,
            model_revision=self._model_revision,
            device="unknown",
        )

    def attach_runtime(self, runtime: LocateAnythingRuntime) -> None:
        """Late runtime attachment (used by the web/brain seam after probing)."""
        self._runtime = runtime

    # -- spatial surface --------------------------------------------------
    def ground(
        self,
        image: CameraFrame,
        query: SpatialQuery,
        policy: SpatialInferencePolicy,
    ) -> GroundingResult:
        return self._run(image, query, policy)

    def point(
        self,
        image: CameraFrame,
        query: SpatialQuery,
        policy: SpatialInferencePolicy,
    ) -> GroundingResult:
        return self._run(image, replace(query, requested_output="point"), policy)

    def detect(
        self,
        image: CameraFrame,
        labels: tuple[str, ...],
        policy: SpatialInferencePolicy,
    ) -> GroundingResult:
        query = SpatialQuery(
            text=", ".join(labels),
            frame_id=image.frame_id,
            timestamp=image.captured_at,
            requested_output="box",
        )
        return self._run(image, query, policy)

    # -- internals --------------------------------------------------------
    def _run(
        self,
        image: CameraFrame,
        query: SpatialQuery,
        policy: SpatialInferencePolicy,
    ) -> GroundingResult:
        caps = self.capabilities()
        if not caps.usable:
            return GroundingResult(
                query=query.text,
                observations=(),
                backend_status=caps.state.value,
                model_id=self._model_id,
                model_revision=self._model_revision,
                backend_version=self._backend_version,
                inference_mode=policy.mode,
                frame_id=query.frame_id,
                timestamp=query.timestamp,
                latency_ms=None,
                success=False,
                validation_errors=(f"backend not usable (state={caps.state.value})",),
            )
        assert self._runtime is not None
        started = time.perf_counter()
        try:
            raw_text, latency_ms = self._runtime.infer(image, query.text, policy.mode)
        except Exception as exc:  # runtime failure -> fail-closed, never guess
            elapsed = (time.perf_counter() - started) * 1000.0
            return GroundingResult(
                query=query.text,
                observations=(),
                backend_status="available",
                model_id=self._model_id,
                model_revision=self._model_revision,
                backend_version=self._backend_version,
                inference_mode=policy.mode,
                frame_id=query.frame_id,
                timestamp=query.timestamp,
                latency_ms=elapsed,
                success=False,
                validation_errors=(f"runtime inference failed: {exc}",),
            )

        outcome = parse_locate_anything_output(raw_text, max_results=policy.max_results)
        observations = self._build_observations(outcome, image, query, policy, latency_ms)
        return GroundingResult(
            query=query.text,
            observations=observations,
            backend_status="available",
            model_id=self._model_id,
            model_revision=self._model_revision,
            backend_version=self._backend_version,
            inference_mode=policy.mode,
            frame_id=query.frame_id,
            timestamp=query.timestamp,
            latency_ms=latency_ms,
            success=outcome.valid,
            validation_errors=outcome.errors,
            raw_hash=sha256_hex(raw_text),
            no_object=outcome.none_seen and not observations,
        )

    def _build_observations(
        self,
        outcome: ParseOutcome,
        image: CameraFrame,
        query: SpatialQuery,
        policy: SpatialInferencePolicy,
        latency_ms: float,
    ) -> tuple[GroundingObservation | PointObservation, ...]:
        observations: list[GroundingObservation | PointObservation] = []
        if query.requested_output in ("box", "both"):
            for idx, b in enumerate(outcome.boxes):
                observations.append(
                    GroundingObservation(
                        observation_id=f"la-{query.frame_id}-{idx}",
                        query=query.text,
                        label=b.label,
                        source_box=(b.x1, b.y1, b.x2, b.y2),
                        image_width=image.width,
                        image_height=image.height,
                        model_id=self._model_id,
                        model_revision=self._model_revision,
                        backend_version=self._backend_version,
                        inference_mode=policy.mode,
                        frame_id=query.frame_id,
                        timestamp=query.timestamp,
                        latency_ms=latency_ms,
                        provenance="locate_anything",
                    )
                )
        if query.requested_output in ("point", "both"):
            for idx, p in enumerate(outcome.points):
                observations.append(
                    PointObservation(
                        observation_id=f"la-{query.frame_id}-{idx}",
                        query=query.text,
                        label=p.label,
                        source_point=(p.x, p.y),
                        image_width=image.width,
                        image_height=image.height,
                        model_id=self._model_id,
                        model_revision=self._model_revision,
                        backend_version=self._backend_version,
                        inference_mode=policy.mode,
                        frame_id=query.frame_id,
                        timestamp=query.timestamp,
                        latency_ms=latency_ms,
                        provenance="locate_anything",
                    )
                )
        return tuple(observations)
