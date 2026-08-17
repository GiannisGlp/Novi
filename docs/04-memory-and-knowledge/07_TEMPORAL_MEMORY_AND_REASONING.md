# 07 — Temporal Memory and Reasoning

**Status:** CANONICAL — CONSOLIDATED V1.1

## Purpose
Define how Novi represents time, temporal validity, event order, intervals, change and historical truth without collapsing observation time into storage time.

## Core principle

```text
WHEN OBSERVED ≠ WHEN IT HAPPENED ≠ WHEN IT BECAME KNOWN ≠ WHEN IT WAS STORED
```

All four timestamps may matter.

## Temporal primitives

Novi supports instants, intervals, durations, recurring intervals, temporal relations, event sequences and validity windows. Temporal claims carry precision and uncertainty where exact time is unavailable.

## Temporal relation vocabulary

Where interval reasoning is required, use an explicit relation vocabulary:

```text
BEFORE
AFTER
MEETS
OVERLAPS
DURING
STARTS
FINISHES
EQUALS
CONTAINS
```

Relations must be evaluated against the relevant interval semantics and uncertainty rather than inferred from string labels.

## Required timestamps

Where applicable:

- `occurred_at` — event time;
- `observed_at` — observation time;
- `captured_at` — acquisition time;
- `ingested_at` — system ingestion;
- `asserted_at` — claim creation;
- `valid_from` / `valid_until` — semantic validity;
- `superseded_at` — replacement time.

## Temporal uncertainty

Represent:

```text
EXACT
BOUNDED_INTERVAL
APPROXIMATE
UNKNOWN
RECURRING_PATTERN
CONFLICTED
```

An interval must not be made artificially precise merely because storage uses a timestamp. Preserve bounds, precision, source and confidence where applicable.

## Historical truth

A claim can be true for a historical interval and false now. Novi must never rewrite historical state merely because current state changed.

```text
HISTORICAL FACT
      ↓
CURRENT VIEW
```

Views may be updated; provenance-bearing history remains immutable subject to privacy policy.

## Ordering

Novi distinguishes physical timestamps from logical ordering. Clock skew must not be treated as proof of causal order. Event identifiers, logical clocks and explicit causal links may be required.

```text
timestamp order ≠ causal order
```

## Recurrence

Recurring routines are represented as patterns plus observed instances. A predicted recurrence must not be treated as an observed event. Missed occurrences and exceptions remain explicit.

## Temporal conflicts

Conflicts are classified as:

- source disagreement;
- clock uncertainty;
- stale observation;
- true state change;
- duplicate event;
- impossible ordering;
- schema interpretation conflict.

Resolution uses provenance and evidence, not arbitrary last-write-wins.

## Temporal queries

The canonical query layer must support `before`, `after`, `during`, `overlaps`, `contains`, `starts`, `ends`, `since`, `until`, recurrence and “as-of” queries.

Queries must state whether they seek historical truth, current state or a reconstruction as-of a time.

## Time-dependent identity and knowledge

Identity, relationships, skills, permissions, locations and causal claims may all be temporally scoped. A current identity or authorization must not retroactively alter historical events.

## Clock and synchronization

Distributed components may use system-level consistency and synchronization mechanisms. Physical-clock uncertainty is explicitly represented; synchronized clocks improve ordering but do not establish causality by themselves.

## Evaluation

Temporal reasoning must be tested with boundary intervals, overlapping intervals, missing timestamps, clock skew, delayed ingestion, recurring events, historical/current divergence and contradictory timestamps. Metrics should include temporal relation accuracy, interval-boundary error, stale-current-state errors and false causal-order inference.

## Safety invariants

1. Preserve event time separately from storage time.
2. Never infer causality solely from timestamps.
3. Never overwrite historical truth with current truth.
4. Preserve uncertainty and precision.
5. Expired authorization cannot become current through historical memory.
6. Temporal corrections remain auditable.
7. “Unknown time” is valid state.
8. Temporal relations must respect uncertainty and scope.

## Integration

`03` supplies temporal provenance. `05` uses temporal validity for beliefs. `06` uses temporal identity. `08` combines time with space. `09` uses temporal ordering in causal models. `12` governs schema migration of temporal fields. Distributed ordering and consistency belong to system architecture.