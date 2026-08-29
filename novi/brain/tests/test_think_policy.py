"""Think-policy tests: fast tiers answer directly, heavy-thinking tier keeps CoT.

The curated ollama stack (2026-08-29) has three qwen3 tiers:
  - qwen3:4b   (default)      -> think disabled (fast replies)
  - qwen3:8b   (heavy)        -> think disabled
  - qwen3.8:27b (heavy think) -> think ENABLED (user's tiering decision)
Plus nemotron-3.5-lightning (CoT model) -> think disabled.
"""

import unittest

from novi.brain.models.ollama_reasoning import disable_thinking_for, num_predict_for


class ThinkPolicyTests(unittest.TestCase):
    def test_fast_tiers_disable_thinking(self) -> None:
        for model in ("qwen3:4b", "qwen3:8b", "nemotron-3.5-lightning", "nemotron-3.5-lightning:latest"):
            self.assertTrue(disable_thinking_for(model), model)

    def test_heavy_thinking_tier_keeps_thinking(self) -> None:
        self.assertFalse(disable_thinking_for("qwen3.8:27b"))

    def test_budget_is_fast_for_fast_tiers(self) -> None:
        self.assertEqual(num_predict_for("qwen3:4b", 512), 512)
        self.assertEqual(num_predict_for("qwen3:8b", 400), 400)

    def test_budget_grows_for_thinking_tier(self) -> None:
        # The 27b tier needs room to think AND answer (2x, min 600 — 3x/min-1200
        # took 6+ minutes at ~3 tok/s on MPS).
        self.assertEqual(num_predict_for("qwen3.8:27b", 512), 1024)
        self.assertEqual(num_predict_for("qwen3.8:27b", 400), 800)


if __name__ == "__main__":
    unittest.main()
