"""Runtime-prompt SFT v3 builder (trained-model fix, iteration 3).

v2 trained on an APPROXIMATION of the runtime prompt (a short persona +
bullet context) and therefore still ignored the real system/user the
brain sends — the v1 echo-template survived under the actual prompt.
This builder uses the EXACT prompts captured at runtime
(NOVI_CAPTURE_PROMPTS hook in chat.py): each captured row is the real
(system, user_json) the model saw, and the gold target is the reply of
the same scenario turn from a PASSING acceptance evidence run
(empirically validated, never invented). Rows without a gold are
skipped: we do not train on failures.

Output rows (jsonl): {"system": ..., "user": ..., "gold": ...} ->
mlx training text = <|im_start|>system\\n{S}<|im_end|>\\n<|im_start|>user\\n{U}<|im_end|>\\n<|im_start|>assistant\\n{G}<|im_end|>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_evidence_pass_replies(dirs: list[Path]) -> dict[tuple[str, int], str]:
    """Map (scenario_id, turn_index) -> PASS dialogue reply across evidence dirs."""
    out: dict[tuple[str, int], str] = {}
    for d in dirs:
        for p in sorted(Path(d).glob("scenarios/*.json")):
            try:
                env = json.loads(p.read_text())
            except json.JSONDecodeError:
                continue
            if env.get("result") != "PASS":
                continue
            sid = env.get("scenario")
            for t in env.get("conversation") or []:
                if t.get("reply_source") == "dialogue" and (t.get("response_text") or "").strip():
                    out[(sid, int(t.get("turn_index", -1)))] = str(t["response_text"]).strip()
    return out


def main() -> int:
    from novi.brain.conversation_scenarios import SCENARIOS

    parser = argparse.ArgumentParser()
    parser.add_argument("--captures", required=True)
    parser.add_argument("--evidence-dirs", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    gold = _load_evidence_pass_replies([Path(d) for d in args.evidence_dirs])
    turn_to_sid: dict[str, str] = {}
    for s in SCENARIOS:
        for i, text in enumerate(s.turns):
            key = str(text).strip().lower()
            if key not in turn_to_sid:
                turn_to_sid[key] = s.scenario_id

    rows = []
    skipped = {"no_gold": 0, "unmatched": 0}
    seen = set()
    for line in Path(args.captures).read_text().splitlines():
        if not line.strip():
            continue
        cap = json.loads(line)
        system = str(cap.get("system", ""))
        user = str(cap.get("user", ""))
        says = str(cap.get("user_says", "")).strip()
        if not system or not user or not says:
            continue
        sid = turn_to_sid.get(says.lower())
        if not sid:
            skipped["unmatched"] += 1
            continue
        # turn index inside the scenario's scored turns
        scenario = next(s for s in SCENARIOS if s.scenario_id == sid)
        tidx = next((i for i, t in enumerate(scenario.turns) if t.strip().lower() == says.lower()), -1)
        if tidx < 0 or (sid, tidx) not in gold:
            skipped["no_gold"] += 1
            continue
        text = f"<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n{gold[(sid, tidx)]}<|im_end|>"
        if text in seen:
            continue
        seen.add(text)
        rows.append({"text": text, "system": system, "user": user,
                     "gold": gold[(sid, tidx)], "scenario": sid, "turn": tidx})
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    print(f"rows={len(rows)} skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
