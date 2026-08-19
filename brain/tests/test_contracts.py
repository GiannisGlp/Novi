import unittest
from datetime import datetime, timezone

from brain.contracts import (
    ContractValidationError,
    ContractVersionError,
    registry,
    utc_now,
    validate_contract,
)


class ContractBindingTests(unittest.TestCase):
    def test_registry_resolves_canonical_model_invocation(self) -> None:
        descriptor = registry.get("novi.model-invocation", "1.0.0")
        self.assertEqual(descriptor.canonical_name, "ModelInvocation")
        self.assertEqual(descriptor.semantic_version, "1.0.0")

    def test_version_mismatch_is_rejected(self) -> None:
        with self.assertRaises(ContractVersionError):
            registry.get("novi.model-invocation", "2.0.0")

    def test_required_fields_are_enforced(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_contract("novi.model-invocation", {})

    def test_unknown_fields_are_rejected(self) -> None:
        payload = {
            "invocation_id": "inv-1",
            "model_id": "model",
            "model_version": "1.0.0",
            "artifact_digest": "sha256:test",
            "runtime": "test",
            "runtime_version": "1",
            "hardware": {},
            "input_schema_version": "1.0.0",
            "output_schema_version": "1.0.0",
            "started_at": utc_now(),
            "completed_at": utc_now(),
            "latency": {"milliseconds": 1},
            "provenance": {},
            "not_in_contract": True,
        }
        with self.assertRaises(ContractValidationError):
            validate_contract("novi.model-invocation", payload)

    def test_datetime_requires_timezone(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "invocation_id": "inv-1",
            "model_id": "model",
            "model_version": "1.0.0",
            "artifact_digest": "sha256:test",
            "runtime": "test",
            "runtime_version": "1",
            "hardware": {},
            "input_schema_version": "1.0.0",
            "output_schema_version": "1.0.0",
            "started_at": now,
            "completed_at": now,
            "latency": {"milliseconds": 1},
            "provenance": {},
        }
        self.assertEqual(validate_contract("novi.model-invocation", payload), payload)


if __name__ == "__main__":
    unittest.main()
