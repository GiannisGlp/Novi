"""Tests for the interactive evaluation CLI (plan 23 §37 human eval tooling).

The full model-loading path (base + both adapters side by side) is verified
live rather than in the unit suite — each subprocess holds 16-24GB, which is
memory-fragile under pytest. The pure logic is unit-tested here; the heavy
smoke run is documented in the module docstring of evaluate_chat.py.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from training.evaluate_chat import _strip_think

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve().parents[1] / "evaluate_chat.py"


class TestStripThink:
    def test_removes_cot_block(self):
        assert _strip_think("<think>Let me reason...</think>Hey.") == "Hey."

    def test_multiline_cot(self):
        text = "<think>\nline one\nline two\n</think>\nThe mug is on the desk."
        assert _strip_think(text) == "The mug is on the desk."

    def test_no_think_block_untouched(self):
        assert _strip_think("Hey.") == "Hey."

    def test_empty_input(self):
        assert _strip_think("") == ""


class TestArgValidation:
    def test_empty_prompt_rejected(self):
        out = subprocess.run([sys.executable, str(SCRIPT), "--prompt", ""],
                             capture_output=True, text=True, cwd=ROOT)
        assert out.returncode != 0

    def test_help_prints(self):
        out = subprocess.run([sys.executable, str(SCRIPT), "--help"],
                             capture_output=True, text=True, cwd=ROOT)
        assert out.returncode == 0
        assert "--adapter" in out.stdout
