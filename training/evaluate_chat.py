"""Interactive evaluation CLI (plan 23 §37 human-eval tooling).

Chat with the base model and/or the trained adapters side by side:

    # one-shot (JSON): base model
    python training/evaluate_chat.py --prompt "Person: person:owner_001
    Communicative act: GREETING"

    # one-shot: SFT adapter
    python training/evaluate_chat.py --prompt "..." \
        --adapter training/models/adapters/novi-qwen3-8b-dialogue-v1

    # compare SFT vs DPO on the same situation (pairwise, §37)
    python training/evaluate_chat.py --prompt "..." \
        --adapter training/models/adapters/novi-qwen3-8b-dialogue-v1 \
        --adapter training/models/adapters/novi-qwen3-8b-dialogue-dpo-v1

    # interactive REPL (base + SFT side by side)
    python training/evaluate_chat.py --adapter .../novi-qwen3-8b-dialogue-v1

Prompt format is the training format (situation lines + Communicative act),
see training/training/common.py::situation_to_prompt.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load(adapter_dir: str | None):
    import torch  # noqa: PLC0415
    from peft import PeftModel  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: PLC0415

    base = "Qwen/Qwen3-8B"
    if adapter_dir:
        cfg = json.loads((Path(adapter_dir) / "adapter_config.json").read_text())
        base = cfg.get("base_model_name_or_path", base)
    tokenizer = AutoTokenizer.from_pretrained(base)
    model = AutoModelForCausalLM.from_pretrained(base, torch_dtype=torch.float16).to("mps")
    if adapter_dir:
        model = PeftModel.from_pretrained(model, adapter_dir)
    model.eval()
    return model, tokenizer


_THINK_RE = None


def _strip_think(text: str) -> str:
    """Remove Qwen3 <think>...</think> CoT blocks (the base model narrates
    reasoning; the fine-tuned adapters should not). Keeps comparisons fair."""
    global _THINK_RE
    if _THINK_RE is None:
        import re  # noqa: PLC0415

        _THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
    out = _THINK_RE.sub("", text).strip()
    return out


def _respond(model, tokenizer, prompt: str, max_new_tokens: int = 64) -> str:
    import torch  # noqa: PLC0415

    # Match training format: prompt + assistant marker.
    text = f"{prompt}\n<|im_start|>assistant\n"
    inp = tokenizer(text, return_tensors="pt").to("mps")
    with torch.no_grad():
        out = model.generate(**inp, max_new_tokens=max_new_tokens, temperature=0.7,
                             do_sample=True, pad_token_id=tokenizer.eos_token_id)
    raw = tokenizer.decode(out[0][inp["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    return _strip_think(raw)


def _model_id(adapter_dir: str | None) -> str:
    return Path(adapter_dir).name if adapter_dir else "base"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", default=None, help="one-shot prompt (JSON out); omit for REPL")
    parser.add_argument("--adapter", action="append", default=[],
                        help="adapter dir (repeatable for side-by-side comparison)")
    parser.add_argument("--max-new-tokens", type=int, default=64)
    args = parser.parse_args(argv)

    if not args.prompt and not sys.stdin.isatty():
        parser.error("REPL mode needs a TTY; use --prompt for scripting")

    # base model always included for comparison, then each requested adapter.
    models = {mid: _load(adapter) for mid, adapter in
              ((_model_id(a), a) for a in [None, *args.adapter])}

    if args.prompt:
        responses = {mid: _respond(m, tok, args.prompt, args.max_new_tokens)
                     for mid, (m, tok) in models.items()}
        print(json.dumps({"model_ids": list(models), "responses": responses}, ensure_ascii=False, indent=1))
        return 0

    print("REPL — type a situation prompt (empty line quits). Models: " + ", ".join(models))
    while True:
        try:
            prompt = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not prompt:
            break
        for mid, (m, tok) in models.items():
            print(f"  [{mid}] {_respond(m, tok, prompt, args.max_new_tokens)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
