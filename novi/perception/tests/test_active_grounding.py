"""Tests: active grounding policy + budgets + dedup + short-term cache
(plan Phase 6, Steps 6.1/6.3/6.4/6.5).

Perception owns budgeted execution of semantic queries; cognition owns query
generation. These primitives are the perception-side half: when to escalate,
with what budget, without re-spending expensive inference on the same
frame/query pair.
"""

from __future__ import annotations

import pytest

from novi.perception.active_grounding import (
    EscalationSignal,
    GroundingBudget,
    GroundingCache,
    GroundingEscalationPolicy,
    GroundingRequest,
    GroundingRequestDeduplicator,
)
from novi.perception.grounding import (
    GroundingObservation,
    GroundingResult,
    SpatialInferenceMode,
)

W, H = 640, 480


class TestGroundingBudget:
    def test_defaults(self):
        b = GroundingBudget()
        assert b.time_budget_ms == 5000
        assert b.max_retries == 1
        assert b.max_frames == 1
        assert b.risk_class == "routine"

    def test_zero_time_budget_rejected(self):
        with pytest.raises(ValueError, match="time_budget"):
            GroundingBudget(time_budget_ms=0)

    def test_negative_retries_rejected(self):
        with pytest.raises(ValueError, match="retries"):
            GroundingBudget(max_retries=-1)

    def test_zero_frames_rejected(self):
        with pytest.raises(ValueError, match="frames"):
            GroundingBudget(max_frames=0)


class TestGroundingRequest:
    def test_defaults_and_validation(self):
        r = GroundingRequest(query="locate the cup", frame_id="f1", reason="low_conf")
        assert r.requester == "active_perception"
        assert r.budget.max_retries == 1
        with pytest.raises(ValueError, match="query"):
            GroundingRequest(query="", frame_id="f1", reason="low_conf")
        with pytest.raises(ValueError, match="reason"):
            GroundingRequest(query="q", frame_id="f1", reason="")


class TestEscalationPolicy:
    def _policy(self, **kw) -> GroundingEscalationPolicy:
        return GroundingEscalationPolicy(**kw)

    def test_low_confidence_label_escalates(self):
        signal = EscalationSignal(frame_id="f1", low_confidence_labels=("cup",))
        requests = self._policy().evaluate(signal)
        assert len(requests) == 1
        r = requests[0]
        assert r.query == "locate the cup"
        assert r.reason == "ssdlite_low_confidence"
        assert r.frame_id == "f1"

    def test_expected_but_missing_triggers_active_search(self):
        signal = EscalationSignal(frame_id="f1", expected_labels=("keys",))
        requests = self._policy().evaluate(signal)
        assert len(requests) == 1
        assert requests[0].query == "find the keys"
        assert requests[0].reason == "expected_but_missing"

    def test_prediction_violation_regrounds_scene(self):
        signal = EscalationSignal(frame_id="f1", prediction_violated=True)
        requests = self._policy().evaluate(signal)
        assert any(r.query == "locate all objects visible in the image" and r.reason == "prediction_violated" for r in requests)

    def test_ambiguous_label_escalates(self):
        signal = EscalationSignal(frame_id="f1", ambiguous_labels=("vase",))
        requests = self._policy().evaluate(signal)
        assert any(r.reason == "ambiguous_description" for r in requests)

    def test_planner_queries_pass_through(self):
        signal = EscalationSignal(frame_id="f1", planner_queries=("the blue cup beside the laptop",))
        requests = self._policy().evaluate(signal)
        assert requests[0].query == "the blue cup beside the laptop"
        assert requests[0].requester == "planner"

    def test_duplicate_label_across_signals_deduped(self):
        signal = EscalationSignal(
            frame_id="f1",
            low_confidence_labels=("cup",),
            ambiguous_labels=("cup",),
        )
        requests = self._policy().evaluate(signal)
        assert len([r for r in requests if "cup" in r.query]) == 1

    def test_request_cap_enforced(self):
        signal = EscalationSignal(
            frame_id="f1",
            low_confidence_labels=("a", "b", "c", "d", "e"),
        )
        requests = self._policy(max_requests_per_signal=3).evaluate(signal)
        assert len(requests) == 3

    def test_empty_signal_yields_no_requests(self):
        assert self._policy().evaluate(EscalationSignal(frame_id="f1")) == ()


class TestDeduplicator:
    def test_duplicate_detection(self):
        d = GroundingRequestDeduplicator()
        assert not d.is_duplicate("f1", "locate the cup")
        d.remember("f1", "locate the cup")
        assert d.is_duplicate("f1", "locate the cup")

    def test_query_normalization(self):
        d = GroundingRequestDeduplicator()
        d.remember("f1", "  Locate   The Cup ")
        assert d.is_duplicate("f1", "locate the cup")

    def test_frame_id_scoped(self):
        d = GroundingRequestDeduplicator()
        d.remember("f1", "q")
        assert not d.is_duplicate("f2", "q")

    def test_eviction(self):
        d = GroundingRequestDeduplicator(max_entries=2)
        d.remember("f1", "q1")
        d.remember("f2", "q2")
        d.remember("f3", "q3")  # evicts f1/q1
        assert not d.is_duplicate("f1", "q1")
        assert d.is_duplicate("f3", "q3")


class TestGroundingCache:
    def _result(self, frame_id: str = "f1", query: str = "q") -> GroundingResult:
        obs = GroundingObservation(
            observation_id="o",
            query=query,
            label="cup",
            source_box=(100, 100, 500, 500),
            image_width=W,
            image_height=H,
            model_id="deterministic",
            model_revision="local",
            backend_version="0.1.0",
            inference_mode=SpatialInferenceMode.HYBRID,
            frame_id=frame_id,
            timestamp="t0",
        )
        return GroundingResult(
            query=query,
            observations=(obs,),
            backend_status="available",
            model_id="deterministic",
            model_revision="local",
            backend_version="0.1.0",
            inference_mode=SpatialInferenceMode.HYBRID,
            frame_id=frame_id,
            timestamp="t0",
            latency_ms=1.0,
            success=True,
        )

    def test_put_get_roundtrip(self):
        c = GroundingCache()
        r = self._result()
        assert c.get("f1", "q", SpatialInferenceMode.HYBRID) is None
        c.put(r)
        assert c.get("f1", "q", SpatialInferenceMode.HYBRID) is r

    def test_query_and_mode_are_part_of_key(self):
        c = GroundingCache()
        r = self._result()
        c.put(r)
        assert c.get("f1", "other", SpatialInferenceMode.HYBRID) is None
        assert c.get("f1", "q", SpatialInferenceMode.FAST) is None

    def test_lru_eviction(self):
        c = GroundingCache(maxsize=2)
        c.put(self._result("f1", "q1"))
        c.put(self._result("f2", "q2"))
        c.put(self._result("f3", "q3"))
        assert c.get("f1", "q1", SpatialInferenceMode.HYBRID) is None
        assert c.get("f3", "q3", SpatialInferenceMode.HYBRID) is not None

    def test_stats_and_clear(self):
        c = GroundingCache()
        r = self._result()
        c.put(r)
        c.get("f1", "q", SpatialInferenceMode.HYBRID)
        c.get("f1", "miss", SpatialInferenceMode.HYBRID)
        assert c.stats()["hits"] == 1
        assert c.stats()["misses"] == 1
        c.clear()
        assert c.stats()["hits"] == 0
