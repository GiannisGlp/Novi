from __future__ import annotations

"""Runtime bindings for Novi's canonical contract registry.

This module intentionally does not redefine contract semantics. The registry and
versioned JSON Schemas under ``contracts/`` remain the semantic authority.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPOSITORY_ROOT / "contracts" / "registry.json"


class ContractError(ValueError):
    """Base error for contract binding/validation failures."""


class UnknownContract(ContractError):
    pass


class ContractVersionError(ContractError):
    pass


class ContractValidationError(ContractError):
    pass


@dataclass(frozen=True)
class ContractDescriptor:
    contract_id: str
    canonical_name: str
    semantic_version: str
    schema_path: Path
    validation_suite: str


class ContractRegistry:
    """Read-only view over the canonical Novi contract registry."""

    def __init__(self, registry_path: Path = REGISTRY_PATH) -> None:
        self.registry_path = registry_path
        document = json.loads(registry_path.read_text(encoding="utf-8"))
        self._contracts = {
            item["contract_id"]: ContractDescriptor(
                contract_id=item["contract_id"],
                canonical_name=item["canonical_name"],
                semantic_version=item["semantic_version"],
                schema_path=registry_path.parent / item["schema"],
                validation_suite=item["validation_suite"],
            )
            for item in document["contracts"]
        }

    def get(self, contract_id: str, version: str | None = None) -> ContractDescriptor:
        descriptor = self._contracts.get(contract_id)
        if descriptor is None:
            raise UnknownContract(contract_id)
        if version is not None and version != descriptor.semantic_version:
            raise ContractVersionError(
                f"{contract_id}: requested {version}, canonical {descriptor.semantic_version}"
            )
        return descriptor

    def schema(self, contract_id: str, version: str | None = None) -> dict[str, Any]:
        descriptor = self.get(contract_id, version)
        return json.loads(descriptor.schema_path.read_text(encoding="utf-8"))


registry = ContractRegistry()


def _matches_type(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, True)


def validate_contract(contract_id: str, payload: dict[str, Any], *, version: str | None = None) -> dict[str, Any]:
    """Validate the structural JSON-Schema constraints needed by Stage 0.

    The repository intentionally keeps the canonical JSON Schema as the source
    of truth. This lightweight validator avoids introducing a third-party
    dependency before the runtime dependency policy is finalized.
    """
    schema = registry.schema(contract_id, version)
    if not isinstance(payload, dict):
        raise ContractValidationError(f"{contract_id}: payload must be an object")

    required = schema.get("required", [])
    missing = [key for key in required if key not in payload]
    if missing:
        raise ContractValidationError(f"{contract_id}: missing required fields: {', '.join(missing)}")

    properties = schema.get("properties", {})
    if schema.get("additionalProperties") is False:
        unknown = sorted(set(payload) - set(properties))
        if unknown:
            raise ContractValidationError(f"{contract_id}: unknown fields: {', '.join(unknown)}")

    for name, definition in properties.items():
        if name not in payload:
            continue
        expected = definition.get("type")
        if expected and not _matches_type(payload[name], expected):
            raise ContractValidationError(
                f"{contract_id}: field '{name}' must be {expected}"
            )
        if definition.get("format") == "date-time":
            try:
                parsed = datetime.fromisoformat(payload[name].replace("Z", "+00:00"))
            except (TypeError, ValueError) as exc:
                raise ContractValidationError(
                    f"{contract_id}: field '{name}' must be an ISO-8601 date-time"
                ) from exc
            if parsed.tzinfo is None:
                raise ContractValidationError(
                    f"{contract_id}: field '{name}' must include a timezone"
                )

    return payload


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
