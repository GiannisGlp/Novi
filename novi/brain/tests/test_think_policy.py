"""Think-policy tests: fast tiers answer directly, heavy-thinking tier keeps CoT.

The curated ollama stack (2026-08-29) has three qwen3 tiers:
  - qwen3:4b / qwen3:8b  -> think disabled INTENT, but the installed Ollama
                           build (0.33.1) does NOT honor `think:false` for
                           qwen3 — the CoT leaks into `content` and no
                           `thinking` field is returned. Fix (2026-08-30):
                           these tiers get a 2x/min-600 budget so the CoT
                           finishes and the real answer lands in `content`.
  - qwen3.8:27b (heavy think) -> think ENABLED (user's tiering decision)
Plus nemotron-3.5-lightning (CoT model) -> think:false IS honored -> direct.
"""

import unittest

from novi.brain.models.ollama_reasoning import can_disable_thinking, disable_thinking_for, num_predict_for


class ThinkPolicyTests(unittest.TestCase):
    def test_fast_tiers_disable_thinking(self) -> None:
        for model in ("qwen3:4b", "qwen3:8b", "nemotron-3.5-lightning", "nemotron-3.5-lightning:latest"):
            self.assertTrue(disable_thinking_for(model), model)

    def test_heavy_thinking_tier_keeps_thinking(self) -> None:
        self.assertFalse(disable_thinking_for("qwen3.8:27b"))

    def test_can_disable_thinking_only_where_honored(self) -> None:
        # `think:false` is only honored by nemotron on the installed Ollama
        # build; qwen3 models leak CoT into content when it is sent.
        self.assertTrue(can_disable_thinking("nemotron-3.5-lightning"))
        self.assertFalse(can_disable_thinking("qwen3:4b"))
        self.assertFalse(can_disable_thinking("qwen3:8b"))
        self.assertFalse(can_disable_thinking("qwen3.8:27b"))

    def test_budget_grows_for_qwen3_thinking(self) -> None:
        # qwen3 (4b/8b) cannot disable thinking on this Ollama build, so they
        # need the same thought+answer budget as the heavy tier (2x, min 600) —
        # with the old fast budget their CoT was cut off mid-thought and
        # content came back empty (deterministic fallback bug, fixed 2026-08-30).
        self.assertEqual(num_predict_for("qwen3:4b", 512), 1024)
        self.assertEqual(num_predict_for("qwen3:8b", 400), 800)
        self.assertEqual(num_predict_for("qwen3.8:27b", 512), 1024)
        self.assertEqual(num_predict_for("qwen3.8:27b", 400), 800)

    def test_nemotron_keeps_fast_budget(self) -> None:
        # Nemotron honors think:false -> direct answer, no thinking room needed.
        self.assertEqual(num_predict_for("nemotron-3.5-lightning", 512), 512)


if __name__ == "__main__":
    unittest.main()
