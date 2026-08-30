"""Router tests (plan 12, §17 Phase 17, §22, §23 Phase 18, §46 Phase 46)."""

from __future__ import annotations

import unittest

from novi.brain.inference.errors import ModelUnavailableError
from novi.brain.inference.registry import ModelRegistry, ModelSpec
from novi.brain.inference.router import ModelRouter, RoutingContext


class ModelRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = ModelRegistry()
        self.router = ModelRouter(self.registry)

    def _approve(self, model_id: str, backend_preferences: tuple[str, ...]) -> None:
        spec = self.registry.get(model_id)
        self.registry.register(
            ModelSpec(
                id=spec.id,
                family=spec.family,
                role_candidates=spec.role_candidates,
                backend_preferences=backend_preferences,
                source_type=spec.source_type,
                source_id=spec.source_id,
                local_aliases=spec.local_aliases,
                status="approved",
            )
        )

    def test_no_approved_model_raises(self) -> None:
        # Step 10: no routing enabled automatically.
        with self.assertRaises(ModelUnavailableError):
            self.router.route(RoutingContext(reasoning_complexity="NORMAL"))

    def test_deliberation_hypothesis_maps_to_model(self) -> None:
        self._approve("qwen3-8b", ("existing",))
        self._approve("qwen3-4b", ("existing",))
        decision = self.router.route(RoutingContext(reasoning_complexity="NORMAL"))
        self.assertEqual(decision.model, "qwen3-8b")
        self.assertIn("deliberation:NORMAL", decision.reason)

    def test_deep_deliberation_prefers_qwen38_27b_hypothesis(self) -> None:
        self._approve("qwen3.8-27b", ("existing",))
        self._approve("qwen3-8b", ("existing",))
        decision = self.router.route(RoutingContext(reasoning_complexity="DEEP"))
        self.assertEqual(decision.model, "qwen3.8-27b")
        self.assertEqual(decision.execution_mode, "background")
        self.assertEqual(decision.deliberation_level, "DEEP")

    def test_airllm_backend_not_selected_until_artifact_resolved(self) -> None:
        # qwen3.8-27b prefers airllm but has no resolved artifact: the router
        # must not select airllm (Step 33 eligibility rules).
        self._approve("qwen3.8-27b", ("airllm", "existing"))
        self._approve("qwen3-8b", ("existing",))
        decision = self.router.route(RoutingContext(reasoning_complexity="DEEP"))
        self.assertEqual(decision.backend, "existing")

    def test_decision_is_observable(self) -> None:
        self._approve("qwen3-8b", ("existing",))
        self.router.route(RoutingContext(reasoning_complexity="NORMAL"))
        decisions = self.router.recent_decisions()
        self.assertEqual(len(decisions), 1)
        self.assertIn("model", decisions[0])
        self.assertIn("reason", decisions[0])
        self.assertIn("backend", decisions[0])

    def test_fallback_chain_is_smaller_model(self) -> None:
        self._approve("qwen3.8-27b", ("existing",))
        decision = self.router.route(RoutingContext(reasoning_complexity="DEEP"))
        self.assertEqual(decision.fallback, "nemotron-3.5-lightning")

    def test_snapshot_exposes_hypotheses(self) -> None:
        snapshot = self.router.snapshot()
        self.assertEqual(snapshot["deliberation_hypotheses"]["DEEP"], "qwen3.8-27b")


if __name__ == "__main__":
    unittest.main()
