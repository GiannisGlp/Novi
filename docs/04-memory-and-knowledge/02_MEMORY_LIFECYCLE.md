# 02 — Memory Lifecycle

## Status

**DESIGN**

## Lifecycle

```text
captured
  ↓
classified
  ↓
admitted / discarded
  ↓
indexed
  ↓
retrieved
  ↓
reinforced / corrected
  ↓
consolidated
  ↓
stale / superseded
  ↓
archived / deleted
```

## Capture

Raw observations remain owned by perception/data ingestion. Memory receives normalized events or references rather than arbitrary sensor streams.

## Classification

The Memory Manager determines likely memory class, privacy level, importance and retention requirements.

## Admission

A candidate is admitted when expected future value justifies storage and privacy/retention policy permits it.

## Reinforcement

Repeated independent evidence can increase confidence or importance. Repetition alone must not convert a false claim into truth.

## Correction

Corrections should preserve provenance. For important claims, create a replacement/superseding relation instead of erasing the historical record.

## Consolidation

Background processing can:

- merge duplicate episodes;
- summarize repeated experiences;
- promote stable patterns;
- create semantic knowledge candidates;
- update routine hypotheses;
- compress old interactions;
- expire low-value details.

## Staleness

Memory can become stale when its validity interval expires or environmental state changes. Stale memory may remain historically useful but must not be presented as current state without qualification.

## Deletion

Deletion supports user requests, retention policy, privacy requirements and storage management. Deletion must not silently leave active indexes pointing to removed content.

## Immutable Data

Some audit/safety records may have stronger retention rules. The Memory Manager must distinguish ordinary mutable memory from protected records.
