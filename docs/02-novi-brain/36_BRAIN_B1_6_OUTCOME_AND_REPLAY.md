# B1.6 — Outcome and Replay Validation

## Status

IMPLEMENTED — deterministic baseline.

## Purpose

B1.6 closes the first bounded autonomy loop by evaluating an action proposal against observed effects and recording the result for deterministic replay.

```text
Cognition
  ↓
ActionProposal
  ↓
[external execution boundary]
  ↓
Observed effects
  ↓
Outcome evaluator
  ↓
SUCCEEDED / DIVERGED
  ↓
Replay ledger
```

## Boundary

B1.6 does not execute hardware actions. It consumes a proposal and an externally supplied result. This keeps proposal, authorization, execution, and outcome responsibilities separate.

## Outcome semantics

- `SUCCEEDED`: every expected effect was observed.
- `DIVERGED`: at least one expected effect was absent.

The evaluator preserves observed effects and discrepancies so later stages can distinguish successful execution from environmental divergence.

## Replay

The deterministic replay ledger records cycle, proposal identity, and outcome status. It is intentionally an in-process baseline; durable persistence remains a later architectural decision.

## Acceptance criteria

- matching expected/observed effects produce `SUCCEEDED`;
- missing expected effects produce `DIVERGED`;
- outcomes retain proposal identity;
- replay records are append-only and deterministic;
- no execution or motor-control path is introduced.

## Next

B1.7 should introduce explicit execution-boundary semantics and safety/authorization decisions around a proposal, while preserving the invariant that the reasoning layer cannot directly command hardware.
