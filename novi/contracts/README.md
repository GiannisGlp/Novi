# Novi Executable Contract Registry

This directory contains implementation artifacts derived from the canonical semantics in `docs/01-system-architecture/16_CANONICAL_SYSTEM_CONTRACTS.md`.

## Authority

- Semantic authority: `docs/01-system-architecture/16_CANONICAL_SYSTEM_CONTRACTS.md`
- Implementation standard: `docs/01-system-architecture/17_CONTRACT_IMPLEMENTATION_AND_SCHEMA_STANDARD.md`
- Ownership reconciliation: `docs/01-system-architecture/24_ARCHITECTURE_CONTRACT_OWNERSHIP_RECONCILIATION.md`
- Registry: `contracts/registry.json`

Schemas are **implementations**, not semantic authorities.

## Versioning

All initial contracts are `1.0.0`. Breaking semantic changes require a new major version or an explicit migration path. Unknown major versions must be rejected by consumers.

## Required lifecycle

```text
canonical semantics
  ↓
registry
  ↓
JSON Schema
  ↓
positive fixtures
  ↓
negative fixtures
  ↓
compatibility fixtures
  ↓
consumer integration tests
  ↓
validation evidence
```

The registry is intentionally metadata-only. Domain semantics remain in their authoritative documentation.

## Current status

The registry and all 18 initial JSON Schema artifacts exist. Fixture coverage, compatibility execution and consumer validation remain open until evidence is recorded in the architecture closure register.
