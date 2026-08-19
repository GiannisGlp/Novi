from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any

from .b1_cognition import CognitiveState
from .contracts import validate_contract


@dataclass(frozen=True)
class ActionProposal:
    proposal_id: str
    capability: str
    semantic_intent: Any
    parameters: Any
    constraints: Any
    expected_effects: Any
    risks: Any
    requester_id: str
    authorization_context: Any
    expires_at: str
    idempotency_key: str
    provenance: Any
    target_refs: tuple[str, ...] = ()
    goal_ref: str | None = None
    plan_ref: str | None = None

    def as_contract(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["target_refs"] = list(self.target_refs)
        return {key: value for key, value in payload.items() if value is not None}


class DeterministicAutonomy:
    """B1 autonomy baseline: construct proposals, never execute them."""

    def propose(self, cognitive: CognitiveState, *, requester_id: str = "brain.b1") -> ActionProposal:
        intent = cognitive.reasoning.conclusion
        target_refs = tuple(cognitive.situation.salient_entities[:1])
        capability = "observe.relevant_entity" if target_refs else "observe.environment"
        parameters = {"targets": list(target_refs)}
        constraints = {
            "requires_safety_authorization": True,
            "max_duration_ms": 1000,
            "no_direct_motor_control": True,
        }
        expected_effects = {"type": "observation_update", "target_refs": list(target_refs)}
        risks = {"risk_class": "low", "uncertainty": list(cognitive.situation.uncertainty)}
        authorization_context = {"source": "deterministic_b1_autonomy", "safety_authority": "external"}
        provenance = {
            "cognition_cycle": cognitive.situation.cycle,
            "reasoning_conclusion": intent,
            "reasoning_confidence": cognitive.reasoning.confidence,
            "evidence_count": len(cognitive.reasoning.provenance),
        }
        canonical = json.dumps({"intent": intent, "targets": target_refs, "cycle": cognitive.situation.cycle}, sort_keys=True, separators=(",", ":"))
        proposal_id = "proposal-" + sha256(canonical.encode("utf-8")).hexdigest()[:24]
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=5)).isoformat().replace("+00:00", "Z")
        proposal = ActionProposal(proposal_id, capability, intent, parameters, constraints, expected_effects, risks, requester_id, authorization_context, expires_at, proposal_id, provenance, target_refs)
        validate_contract("novi.action-proposal", proposal.as_contract())
        return proposal
