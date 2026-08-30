"""Dialogue policy scorer training — fourth experiment (plan 23 §35, steps 19-21).

Learns to *rank* deterministic policy candidates, never to control directly:

    state -> deterministic candidate generation
          -> learned ranking
          -> deterministic safety/cooldown validation
          -> action

The deterministic brain policy (novi/brain/dialogue_policy.py) remains the
authority; this scorer is consulted as a recommendation (plan §12/§35).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.config import capture_provenance, load_config  # noqa: E402
from training.training.common import add_common_args, emit_report, load_jsonl  # noqa: E402

_STATE_FEATURES = (
    "user_speaking", "known_person", "new_event", "event_salience", "open_thread",
    "interruption_cost", "person_available", "social_opportunity", "last_proactive_s",
)


def _smoke_report(cfg) -> dict:
    records = load_jsonl(ROOT / cfg.dataset)
    from training.schemas import validate_example  # noqa: PLC0415

    bad = [r["example_id"] for r in records if validate_example(r, kind="policy")]
    if bad:
        raise ValueError(f"policy: {len(bad)} records fail validation, e.g. {bad[:3]}")
    acts: dict[str, int] = {}
    for r in records:
        acts[r["preferred"]] = acts.get(r["preferred"], 0) + 1
    prov = capture_provenance(cfg.base_model, cfg.dataset_version, cfg.seed, cfg.hyperparams, ROOT)
    prov.pop("captured_at", None)
    return {
        "dry_run": True,
        "task": "policy",
        "config": cfg.to_dict(),
        "records_loaded": len(records),
        "preferred_act_distribution": dict(sorted(acts.items())),
        "framework": prov.pop("framework"),
        "provenance": prov,
        "next_step": "grow policy dataset -> run without --dry-run; integrate via training/integration/policy_scorer.py",
    }


def _real_report(cfg) -> dict:
    import json  # noqa: PLC0415

    from training.training.backends.torch_linear import train_linear_ranker  # noqa: PLC0415

    records = load_jsonl(ROOT / cfg.dataset)
    # One-vs-rest linear models: one weight vector per dialogue act, so the
    # learned scorer actually discriminates between acts (the artifact is
    # consumed by training/integration/policy_scorer.py).
    acts = sorted({c for r in records for c in r["candidates"]})
    act_weights: dict[str, dict[str, float]] = {}
    act_biases: dict[str, float] = {}
    state_vecs: list[list[float]] = []
    for rec in records:
        state = rec.get("state") or {}
        vec = [float(state.get(f, 0.0)) for f in _STATE_FEATURES if f in state]
        if not vec:
            vec = [0.0] * len(_STATE_FEATURES)
        state_vecs.append(vec)
    for act in acts:
        labels = [1.0 if rec["preferred"] == act else 0.0 for rec in records]
        weights, _preds = train_linear_ranker(
            state_vecs, labels,
            epochs=int(cfg.hyperparams.get("epochs", 10)),
            lr=float(cfg.hyperparams.get("learning_rate", 1e-2)),
            seed=cfg.seed,
        )
        act_weights[act] = weights
        act_biases[act] = 0.0
    out_dir = Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact = out_dir / "policy_scorer_v1.json"
    artifact.write_text(json.dumps({
        "model": "linear-ovr",
        "state_features": _STATE_FEATURES,
        "act_weights": act_weights,
        "act_biases": act_biases,
        "provenance": capture_provenance(cfg.base_model, cfg.dataset_version, cfg.seed, cfg.hyperparams),
    }, indent=2))
    return {
        "task": "policy",
        "framework": "torch-linear",
        "artifact": str(artifact),
        "records_trained": len(records),
        "acts": acts,
        "note": "scorer ranks candidates only; deterministic guardrails stay authoritative (plan §35)",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    report = _smoke_report(cfg) if args.dry_run else _real_report(cfg)
    return emit_report(report, args.out_json)


if __name__ == "__main__":
    raise SystemExit(main())
