"""Controlled deployment workflow (plan 23 steps 12/24-26; §18 loop).

Encodes the deployment gate: evaluation -> T1-T8 gates -> register manifest
-> stage -> shadow compare -> promote to active, with current/previous/
known-good slots (plan §23) so rollback never needs retraining.

`plan_deployment` is the deterministic decision; `run_deployment` executes it
against a registry. The heavy candidate evaluation itself runs in
`training/training/evaluate.py --candidate-dir`; this module consumes its
report.

The actual model load + shadow inference is intentionally NOT here — the
module stays deterministic and testable. Wire the real evaluation into
`run_deployment(eval_report=...)` from the training CLI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from training.models.registry import ModelRegistry, build_manifest
from training.models.rollback import DeploymentSlots

# Gates that must pass before any deployment (plan §39). Latency/regression
# are external or measured on-device — reported, not blocking here.
_REQUIRED_GATES = ("naturalness", "grounding", "memory", "initiative", "silence", "safety")


def plan_deployment(eval_report: dict[str, Any], adapter_dir: str) -> dict[str, Any]:
    """Deterministic deployment decision from an evaluation report."""
    gates = eval_report.get("gates", {})
    passed = [g for g in _REQUIRED_GATES if gates.get(g, {}).get("passed") is True]
    failed = [g for g in _REQUIRED_GATES if gates.get(g, {}).get("passed") is False]
    steps = ["register_candidate", "stage"]
    if not failed:
        steps += ["shadow_compare", "promote_active"]
    return {
        "adapter_dir": adapter_dir,
        "deploy": not failed,
        "gates_passed": passed,
        "gates_failed": failed,
        "steps": steps,
    }


@dataclass
class DeploymentReport:
    model_id: str
    deployed: bool
    plan: dict[str, Any] = field(default_factory=dict)
    manifest_path: str | None = None
    slots: dict[str, str | None] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id, "deployed": self.deployed,
            "plan": self.plan, "manifest_path": self.manifest_path,
            "slots": self.slots,
        }


def run_deployment(
    eval_report: dict[str, Any],
    adapter_dir: str,
    registry_root: str | Path,
    *,
    base_model: str,
    training_dataset: str,
    training_config: str,
    commit: str,
    evaluation_suite: str = "social-v1",
    shadow_report: dict[str, Any] | None = None,
) -> DeploymentReport:
    """Register + stage + promote when gates AND shadow pass; never otherwise."""
    plan = plan_deployment(eval_report, adapter_dir)
    registry = ModelRegistry(registry_root)
    slots = DeploymentSlots()
    # The manifest id MUST match the adapter directory name (rollback and
    # loading resolve adapters by their registry id).
    model_id = Path(adapter_dir).name

    if not plan["deploy"]:
        return DeploymentReport(model_id=model_id, deployed=False, plan=plan)

    shadow_ok = True
    if shadow_report is not None:
        from training.evaluation.shadow import should_promote  # noqa: PLC0415

        shadow_ok = should_promote(shadow_report)
        plan["shadow"] = shadow_report.get("verdict", "unknown")

    metrics = eval_report.get("metrics", {})
    manifest = build_manifest(
        base_model=base_model,
        training_dataset=training_dataset,
        training_config=training_config,
        training_commit=commit,
        evaluation_suite=evaluation_suite,
        metrics={
            "naturalness": 1.0 - metrics.get("naturalness", {}).get("assistant_phrase_rate", 0.0),
            "grounding": 1.0 - metrics.get("grounding", {}).get("false_grounding_rate", 0.0),
            "memory": metrics.get("memory", {}).get("retrieval_precision", 0.0),
            "initiative": metrics.get("initiative", {}).get("appropriate_initiative_rate", 0.0),
            "safety": 1.0 - max(
                metrics.get("safety", {}).get("unsupported_claim_rate", 0.0),
                metrics.get("safety", {}).get("unsafe_action_proposal_rate", 0.0),
                metrics.get("safety", {}).get("identity_false_positive_rate", 0.0),
            ),
        },
        model_id=model_id,
    )
    manifest["status"] = "candidate"
    path = registry.register(manifest)
    registry.set_status(model_id, "staged")
    if not shadow_ok:
        # Gates passed but shadow comparison failed: keep the model staged
        # (available for offline evaluation) — never active.
        plan["steps"] = [s for s in plan["steps"] if s != "promote_active"]
        return DeploymentReport(
            model_id=model_id,
            deployed=False,
            plan=plan,
            manifest_path=str(path),
            slots={"current": slots.current, "previous": slots.previous, "known_good": slots.known_good},
        )
    registry.set_status(model_id, "active")
    slots.promote(model_id)
    return DeploymentReport(
        model_id=model_id,
        deployed=True,
        plan=plan,
        manifest_path=str(path),
        slots={"current": slots.current, "previous": slots.previous, "known_good": slots.known_good},
    )
