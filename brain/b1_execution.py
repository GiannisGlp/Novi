from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

from .b1_autonomy import ActionProposal


@dataclass(frozen=True)
class SimulatedExecution:
    execution_id: str
    proposal_ref: str
    authorization_ref: str
    safety_ref: str
    capability: str
    started_at: str
    execution_attempt: int
    status: str
    operation_id: str
    runtime_version: str
    hardware_target: Any
    provenance: Any

    def as_contract(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "proposal_ref": self.proposal_ref,
            "authorization_ref": self.authorization_ref,
            "safety_ref": self.safety_ref,
            "capability": self.capability,
            "started_at": self.started_at,
            "execution_attempt": self.execution_attempt,
            "status": self.status,
            "operation_id": self.operation_id,
            "runtime_version": self.runtime_version,
            "hardware_target": self.hardware_target,
            "provenance": self.provenance,
        }


class SimulatedCapabilityGateway:
    """B1.8 execution boundary. It simulates capability execution and never drives hardware."""

    def execute(
        self,
        proposal: ActionProposal,
        *,
        authorization_ref: str,
        safety_ref: str,
        allowed: bool,
        hardware_target: str = "simulated-body",
    ) -> SimulatedExecution:
        if not allowed:
            raise PermissionError("execution requires explicit authorization and safety approval")
        if not proposal.constraints.get("requires_safety_authorization", True):
            raise PermissionError("proposal does not carry the required safety boundary")

        operation_id = sha256(
            json.dumps(
                {"proposal": proposal.proposal_id, "authorization": authorization_ref, "safety": safety_ref},
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()[:24]
        execution_id = f"execution-{operation_id}"
        return SimulatedExecution(
            execution_id=execution_id,
            proposal_ref=proposal.proposal_id,
            authorization_ref=authorization_ref,
            safety_ref=safety_ref,
            capability=proposal.capability,
            started_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            execution_attempt=1,
            status="SIMULATED_ACCEPTED",
            operation_id=operation_id,
            runtime_version="brain-b1.8",
            hardware_target=hardware_target,
            provenance={"boundary": "simulated_capability_gateway", "direct_hardware_control": False},
        )
