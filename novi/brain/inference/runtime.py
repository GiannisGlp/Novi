"""Inference runtime (plan 12, §18 Phase 13, §30 Phase 25, §44 Phase 43).

``InferenceRuntime`` is the Novi-owned orchestrator that cognition talks to:

    request -> router (model/backend decision) -> scheduler (priority queue)
            -> backend (load/generate) -> telemetry -> response

Fallback policy (plan 12, §30) is deterministic: on primary failure, try the
approved fallback model on the existing backend, then a deterministic mock
(representing structured deterministic behavior). A fallback never silently
changes a high-risk action's authority — the response warnings and the
telemetry record which path was used, and the router decision is observable.

``MacBrain`` must never instantiate a backend directly: it receives the
runtime (or a provider) via dependency injection (plan 12, §43).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, AsyncIterator, Iterable

from .capabilities import probe_hardware
from .contracts import InferenceBackend
from .errors import BackendUnavailableError, DeadlineExceededError, InferenceError, classify_backend_exception
from .health import InferenceHealth, ModelHealthEntry
from .lifecycle import ModelLifecycle, ModelResidency
from .registry import ModelRegistry
from .request import InferenceRequest
from .response import FinishReason, InferenceResponse
from .router import ModelRouter, RoutingContext, RoutingDecision
from .scheduler import InferenceScheduler, ScheduledRequest
from .telemetry import InferenceTelemetry


class BackendManager:
    """Owns registered backends; selection is observable."""

    def __init__(self, backends: Iterable[InferenceBackend] | None = None) -> None:
        self._backends: dict[str, InferenceBackend] = {}
        self._order: list[str] = []
        for backend in backends or ():
            self.register(backend)

    def register(self, backend: InferenceBackend) -> None:
        self._backends[backend.backend_id] = backend
        if backend.backend_id not in self._order:
            self._order.append(backend.backend_id)

    def get(self, backend_id: str) -> InferenceBackend:
        backend = self._backends.get(backend_id)
        if backend is None:
            raise BackendUnavailableError(f"unknown backend: {backend_id}", context={"backend": backend_id})
        return backend

    def get_or_none(self, backend_id: str) -> InferenceBackend | None:
        return self._backends.get(backend_id)

    def all(self) -> tuple[InferenceBackend, ...]:
        return tuple(self._backends[bid] for bid in self._order)

    def ids(self) -> tuple[str, ...]:
        return tuple(self._order)

    def shutdown(self) -> None:
        import contextlib

        for backend in self.all():
            with contextlib.suppress(Exception):
                backend.shutdown()


@dataclass(frozen=True)
class RuntimeConfig:
    default_backend: str = "existing"
    fallback_backend: str = "existing"
    deterministic_fallback: bool = True  # structured deterministic behavior allowed
    max_concurrent: int = 1
    arrival_policy: str = "queue"
    hardware_profile_id: str = "default"
    # Plan 12 §34/Step 34: AirLLM is enabled ONLY for explicitly validated
    # model/hardware combinations. ``validated_airllm_combinations`` holds
    # (model_id, compute_backend) pairs proven by execution evidence; empty by
    # default, so the router never selects AirLLM until a combo is validated.
    airllm_enabled: bool = False
    validated_airllm_combinations: tuple[tuple[str, str], ...] = ()

    @classmethod
    def rollback_to_existing(cls, **overrides: Any) -> "RuntimeConfig":
        """Rollback configuration (plan 12, §55): one config change disables
        AirLLM while preserving the same inference contract.

        ``backend = existing`` + ``airllm_enabled = False`` — no source rewrite
        required to disable the AirLLM backend.
        """
        base: dict[str, Any] = {
            "default_backend": "existing",
            "fallback_backend": "existing",
            "airllm_enabled": False,
            "validated_airllm_combinations": (),
        }
        base.update(overrides)
        return cls(**base)


class InferenceRuntime:
    """The Novi inference runtime orchestrator."""

    def __init__(
        self,
        *,
        registry: ModelRegistry | None = None,
        backends: Iterable[InferenceBackend] | None = None,
        router: ModelRouter | None = None,
        scheduler: InferenceScheduler | None = None,
        telemetry: InferenceTelemetry | None = None,
        health: InferenceHealth | None = None,
        config: RuntimeConfig | None = None,
    ) -> None:
        self.registry = registry or ModelRegistry()
        self.backends = BackendManager(backends)
        self.config = config or RuntimeConfig()
        self.router = router or ModelRouter(self.registry, airllm_validator=self._airllm_validator)
        self.scheduler = scheduler or InferenceScheduler(
            max_concurrent=self.config.max_concurrent,
            arrival_policy=self.config.arrival_policy,
        )
        self.telemetry = telemetry or InferenceTelemetry()
        self.health = health or InferenceHealth()
        self.hardware = probe_hardware(self.config.hardware_profile_id)
        #: model_id -> backend_id for currently loaded models
        self._loaded_models: dict[str, str] = {}
        self._last_decision: RoutingDecision | None = None
        self._last_error: str = ""
        self._fallback_used = False

    def _airllm_validator(self, spec: Any) -> bool:
        """Eligibility gate (plan 12 Step 33-34 + user directive 2026-08-30):
        AirLLM is a GENERIC backend — routable when enabled, artifact-resolved,
        per-platform architecture-compatible (Mac MLX verified set), AND the
        exact (model, compute backend) combination carries execution evidence."""
        if not self.config.airllm_enabled:
            return False
        if not spec.is_airllm_eligible():
            return False
        from .capabilities import CapabilityState

        backend = self.backends.get_or_none("airllm")
        if backend is not None:
            state = backend.check_model_compatibility(spec)
            if state is CapabilityState.UNSUPPORTED:
                return False
        combo = (spec.id, self.hardware.compute_backend.value)
        return combo in self.config.validated_airllm_combinations

    # ---------------------------------------------------------------- requests
    def generate(
        self,
        request: InferenceRequest,
        *,
        context: RoutingContext | None = None,
    ) -> InferenceResponse:
        """Route, schedule, execute, and record telemetry for one request."""
        start = time.monotonic()
        routing_context = context or self._default_routing_context(request)
        decision = self.router.route(routing_context)
        self._last_decision = decision
        sched = self.scheduler.submit(
            request,
            estimated_memory_bytes=_estimate_request_memory(request),
            estimated_duration_ms=routing_context.latency_budget_ms or 0.0,
        )
        queue_time_ms = (time.monotonic() - start) * 1000.0
        acquired = self.scheduler.wait_for_slot(
            timeout=max(1.0, sched.deadline_monotonic - time.monotonic()) if sched.deadline_monotonic else 30.0
        )
        if acquired is None:
            from .errors import DeadlineExceededError

            raise DeadlineExceededError(
                "request timed out waiting for scheduler slot",
                context={"request_id": request.request_id},
            )
        try:
            response = self._execute(decision, request, sched)
            fallback_used = ""
            failure_class = ""
        except InferenceError as exc:
            self._last_error = exc.code
            response = self._fallback(decision, request, exc)
            fallback_used = exc.code
            failure_class = exc.code
        finally:
            self.scheduler.release(request.request_id, success=getattr(locals().get("response"), "ok", False))

        end = time.monotonic()
        self.telemetry.record_request(
            request=request,
            response=response,
            start_time=start,
            end_time=end,
            queue_time_ms=queue_time_ms,
            failure_class=failure_class,
            fallback_used=fallback_used,
        )
        self.health.update_telemetry(self.telemetry.summary())
        self.health.update_scheduler(self.scheduler.snapshot())
        return response

    async def stream(
        self, request: InferenceRequest, *, context: RoutingContext | None = None
    ) -> AsyncIterator[InferenceResponse]:
        """Streaming path; backend streaming is optional (plan 12, §21)."""
        routing_context = context or self._default_routing_context(request)
        decision = self.router.route(routing_context)
        backend = self._ensure_model(request, decision)
        backend_stream = backend.stream(request)
        try:
            async for chunk in backend_stream:
                yield chunk
        except InferenceError:
            raise
        except Exception as exc:
            raise classify_backend_exception(exc) from exc

    # ------------------------------------------------------------- execution
    def _execute(
        self, decision: RoutingDecision, request: InferenceRequest, sched: ScheduledRequest
    ) -> InferenceResponse:
        if request.is_expired:
            raise DeadlineExceededError(
                "request expired before dispatch",
                context={"request_id": request.request_id},
            )
        backend = self._ensure_model(request, decision)
        sched.backend_id = decision.backend
        response = backend.generate(request)
        if response.model_id != decision.model:
            response = InferenceResponse(**{**response.__dict__, "model_id": decision.model})
        # Plan 12 §21: a deadline miss is represented explicitly, never treated
        # as silent success.
        if request.is_expired:
            response = InferenceResponse(
                **{
                    **response.__dict__,
                    "finish_reason": FinishReason.DEADLINE,
                    "warnings": list(response.warnings) + ["deadline_missed"],
                }
            )
        return response

    def _ensure_model(self, request: InferenceRequest, decision: RoutingDecision) -> InferenceBackend:
        backend = self.backends.get(decision.backend)
        model_id = decision.model
        loaded_backend = self._loaded_models.get(model_id)
        if loaded_backend is None or loaded_backend != decision.backend:
            spec = self.registry.get(model_id)
            backend.validate_model(spec)
            backend.load(spec)
            self._loaded_models[model_id] = decision.backend
            self.telemetry.record_model_switch()
        self._update_health_entry(model_id, decision.backend, ModelLifecycle.RUNNING, ModelResidency.ACTIVE)
        return backend

    def _fallback(self, decision: RoutingDecision, request: InferenceRequest, exc: InferenceError) -> InferenceResponse:
        """Deterministic fallback chain (plan 12, §30)."""
        self._fallback_used = True
        warnings = [f"primary route failed: {exc.code} ({exc.message})"]

        # 1) fallback model on the existing backend (approved local path)
        fallback_model = decision.fallback
        existing = self.backends.get_or_none(self.config.fallback_backend)
        if fallback_model and existing is not None:
            try:
                spec = self.registry.get(fallback_model)
                existing.validate_model(spec)
                existing.load(spec)
                fallback_request = InferenceRequest(
                    request_id=request.request_id,
                    trace_id=request.trace_id,
                    caller=request.caller,
                    purpose=request.purpose,
                    model_hint=fallback_model,
                    messages=request.messages,
                    system=request.system,
                    max_output_tokens=request.max_output_tokens,
                    temperature=request.temperature,
                )
                response = existing.generate(fallback_request)
                self._fallback_used = True
                return InferenceResponse(
                    **{
                        **response.__dict__,
                        "model_id": fallback_model,
                        "warnings": warnings + list(response.warnings),
                        "provider_metadata": {"fallback_from": decision.model, "fallback_reason": exc.code},
                    }
                )
            except (InferenceError, Exception):
                pass

        # 2) structured deterministic behavior (mock) — CI-safe final fallback
        if self.config.deterministic_fallback:
            mock = self.backends.get_or_none("mock")
            if mock is not None:
                try:
                    from .backends.mock import MockBackend

                    if not isinstance(mock, MockBackend):
                        mock = MockBackend()
                    response = mock.generate(request)
                    return InferenceResponse(
                        **{
                            **response.__dict__,
                            "warnings": warnings + list(response.warnings),
                            "provider_metadata": {
                                "fallback_from": decision.model,
                                "fallback_reason": exc.code,
                                "deterministic": True,
                            },
                        }
                    )
                except Exception:
                    pass

        # 3) ask for help / defer — represent the failure explicitly
        return InferenceResponse(
            request_id=request.request_id,
            model_id=decision.model,
            backend_id=decision.backend,
            trace_id=request.trace_id,
            text="",
            finish_reason=FinishReason.ERROR,
            warnings=warnings,
            provider_metadata={"error": exc.code, "message": exc.message},
        )

    # ------------------------------------------------------------ lifecycle API
    def load_model(self, model_id: str, backend_id: str | None = None) -> None:
        spec = self.registry.get(model_id)
        backend_id = backend_id or (
            spec.backend_preferences[0] if spec.backend_preferences else self.config.default_backend
        )
        backend = self.backends.get(backend_id)
        backend.validate_model(spec)
        backend.load(spec)
        self._loaded_models[model_id] = backend_id

    def unload_model(self, model_id: str) -> None:
        backend_id = self._loaded_models.pop(model_id, None)
        if backend_id is None:
            return
        backend = self.backends.get_or_none(backend_id)
        if backend is not None:
            try:
                spec = self.registry.get(model_id)
                backend.unload(spec)
            except Exception:
                pass
        self._update_health_entry(model_id, backend_id or "", ModelLifecycle.UNLOADED, ModelResidency.COLD)

    def shutdown(self) -> None:
        self.backends.shutdown()

    # ------------------------------------------------------------- observability
    def _update_health_entry(
        self, model_id: str, backend_id: str, lifecycle: ModelLifecycle, residency: ModelResidency
    ) -> None:
        entry = self.health.get(model_id)
        detail = dict(entry.detail) if entry else {}
        detail["loaded_backend"] = backend_id
        self.health.upsert_model(
            ModelHealthEntry(
                model_id=model_id,
                lifecycle=lifecycle,
                residency=residency,
                backend_id=backend_id,
                last_error=self._last_error,
                detail=detail,
            )
        )

    def _default_routing_context(self, request: InferenceRequest) -> RoutingContext:
        return RoutingContext(
            task_type=request.purpose or "reason",
            reasoning_complexity=request.reasoning_budget,
            context_length=request.max_input_tokens,
            required_modality="vision" if request.backend_options.get("modality") == "vision" else "text",
            latency_budget_ms=request.latency_budget_ms,
            available_ram_bytes=self.hardware.ram_available_bytes,
            available_vram_bytes=self.hardware.vram_available_bytes,
            compute_backend=self.hardware.compute_backend.value,
            current_residency={
                mid: self.health.get(mid).residency.value for mid in self._loaded_models if self.health.get(mid)
            },
            model_hint=request.model_hint,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "hardware": self.hardware.as_dict(),
            "registry": self.registry.snapshot(),
            "router": self.router.snapshot(),
            "scheduler": self.scheduler.snapshot(),
            "telemetry": self.telemetry.summary(),
            "health": self.health.snapshot(),
            "loaded_models": dict(self._loaded_models),
            "last_decision": self._last_decision.as_dict() if self._last_decision else None,
        }


def _estimate_request_memory(request: InferenceRequest) -> int:
    """Rough memory estimate: chars * 4 bytes for the bounded context."""
    chars = sum(len(str(m.get("content", ""))) for m in request.messages) + len(request.system)
    return chars * 4
