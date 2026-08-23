# Mac Test Execution

## Test layers

```text
contract → unit → integration → scenario → failure → regression
```

## Rules

Run focused tests while developing, then the complete deterministic suite before declaring a work unit complete.

Prefer repository-provided scripts/commands when they exist. Do not invent a second local test path that diverges from CI.

## Brain

Brain tests must cover runtime contracts, model adapters, evidence validation, scenario behavior, failure handling and regression fixtures.

## Reporting

Record command, environment, commit SHA, result and relevant failure output for formal validation runs.
