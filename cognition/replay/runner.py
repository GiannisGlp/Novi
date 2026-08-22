"""Replay runner for the typed cognition contracts (doc 26 §20, §21).

Replays each scenario's events through the full validation pipeline and
optionally reconstructs a world state (entities + relations) from the fixture,
proving the contracts can be consumed end-to-end without inventing semantic
fields.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cognition.replay.loader import load_all, load_scenario_events
from cognition.validation import (
    CrossContractValidation,
    ProvenanceValidation,
    SemanticContext,
    SemanticValidation,
    StructuralValidation,
    validate_cross_contract,
    validate_provenance,
    validate_semantic,
    validate_structurally,
)


class ReplayStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: int
    contract_type: str
    object_id: str | None = None
    structural_valid: bool = False
    semantic_valid: bool = False
    provenance_valid: bool = False
    cross_valid: bool = False
    issues: list[str] = Field(default_factory=list)


class ReplayResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    description: str
    expect_valid: bool
    steps: list[ReplayStep] = Field(default_factory=list)

    @property
    def all_structural_valid(self) -> bool:
        return all(step.structural_valid for step in self.steps)

    @property
    def all_semantic_valid(self) -> bool:
        return all(step.semantic_valid for step in self.steps)

    @property
    def all_provenance_valid(self) -> bool:
        return all(step.provenance_valid for step in self.steps)

    @property
    def all_cross_valid(self) -> bool:
        return all(step.cross_valid for step in self.steps)

    @property
    def passed(self) -> bool:
        return self.all_structural_valid and self.all_semantic_valid and self.all_provenance_valid and self.all_cross_valid


def replay_scenario(scenario: dict[str, Any], *, ctx: SemanticContext | None = None) -> ReplayResult:
    """Replay one scenario fixture through the validation pipeline."""
    ctx = ctx or SemanticContext()
    result = ReplayResult(
        scenario_id=scenario.get("scenario_id", "?"),
        description=scenario.get("description", ""),
        expect_valid=scenario.get("expect_valid", True),
    )
    for i, event in enumerate(load_scenario_events(scenario)):
        contract_type = event.get("contract_type", "?")
        structural: StructuralValidation = validate_structurally(contract_type, event)
        semantic: SemanticValidation = SemanticValidation(valid=True, issues=[])
        provenance: ProvenanceValidation = ProvenanceValidation(valid=True, issues=[])
        cross: CrossContractValidation = CrossContractValidation(valid=True, issues=[])

        issues: list[str] = []
        if structural.valid:
            structural = StructuralValidation(valid=True, value=structural.value, issues=[])
            semantic = validate_semantic(structural.value, ctx)
            provenance = validate_provenance(structural.value, durable=True)
            cross = validate_cross_contract(structural.value)
            for name, validation in (("semantic", semantic), ("provenance", provenance), ("cross", cross)):
                for issue in validation.issues:
                    issues.append(f"{name}:{issue.category}:{issue.message}")
        else:
            for issue in structural.issues:
                issues.append(f"structural:{issue.category}:{issue.message}")

        result.steps.append(
            ReplayStep(
                index=i,
                contract_type=contract_type,
                object_id=event.get("id"),
                structural_valid=structural.valid,
                semantic_valid=semantic.valid,
                provenance_valid=provenance.valid,
                cross_valid=cross.valid,
                issues=issues,
            )
        )
    return result


def replay_all() -> list[ReplayResult]:
    return [replay_scenario(scenario) for scenario in load_all()]


def summarize(results: list[ReplayResult]) -> dict[str, Any]:
    passed = sum(1 for r in results if r.passed)
    return {
        "scenarios": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "details": [
            {
                "scenario_id": r.scenario_id,
                "passed": r.passed,
                "steps": len(r.steps),
                "failed_steps": [s.index for s in r.steps if not (s.structural_valid and s.semantic_valid and s.provenance_valid and s.cross_valid)],
            }
            for r in results
        ],
    }
