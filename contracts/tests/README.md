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

## Execution

The suite is a set of standalone executable validators plus a pytest shim:

```text
python -m pytest contracts/tests -q          # CI-runnable entry point
python contracts/tests/generate_fixtures.py  # regenerate fixtures (run before validation)
```

`test_executable_suite.py` runs the fixture generator and then executes every
validator as a subprocess, failing the pytest run on any non-zero exit. All 25
registry contracts validated (schemas, fixtures, compatibility policy,
integration, persistence, semantic) — 18 original domains + 7 cognition
contracts (SituationState, PersonContext, AttentionCandidate, IntentHypothesis,
Prediction, CognitiveDecisionRecord, CognitiveEvent).

## Current status

Fixtures are generated deterministically from the registry schemas
(`generate_fixtures.py`), then validated by `fixture_validation.py`
(18/18 positive, 36 negative cases) and `validate_registry.py`. Requires
`jsonschema` (declared in the `dev` extra of `pyproject.toml`).
