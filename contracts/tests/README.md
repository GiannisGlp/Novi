# Contract Validation Suite

**Status:** P0 validation baseline

This directory contains executable validation artifacts for the canonical Novi contract registry.

## Scope

The suite validates:

1. registry completeness and schema mapping;
2. JSON Schema structural validity;
3. positive fixtures;
4. negative fixtures;
5. compatibility/version behavior;
6. rejection of undeclared properties;
7. required-field enforcement;
8. basic format and numeric constraints.

Semantic validation remains domain-owned and is not replaced by JSON Schema.

## Required fixture layout

```text
fixtures/
  positive/<contract-id>.json
  negative/<contract-id>__missing-required.json
  negative/<contract-id>__wrong-type.json
  negative/<contract-id>__extra-property.json
```

The suite must eventually be executed in CI and its evidence recorded in the architecture closure register.

## Current limitation

Fixtures are being introduced incrementally. Until all 18 contracts have positive and negative coverage and the validator has executed successfully, ARCH-CLOSE-001 remains open.
