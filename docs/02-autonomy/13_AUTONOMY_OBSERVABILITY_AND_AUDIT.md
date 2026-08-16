# 13 — Autonomy Observability and Audit

## Status

**DESIGN**

## Purpose

Novi must make autonomous behavior diagnosable. Observability records system state and decision metadata without exposing or storing unnecessary private data or hidden model chain-of-thought.

## Decision Trace

A consequential action should be traceable through:

```text
trigger event
→ relevant context references
→ goal
→ selected strategy
→ capability request
→ policy result
→ safety result
→ execution
→ outcome
```

## Required Metadata

- correlation ID;
- goal ID;
- plan ID;
- action ID;
- model/runtime version;
- capability version;
- timestamps;
- confidence metadata;
- policy result;
- safety result;
- outcome.

## Metrics

Track:

- perception-to-event latency;
- event-to-decision latency;
- model time-to-first-token;
- planning latency;
- action latency;
- success/failure rates;
- replanning frequency;
- false interaction rate;
- missed important-event rate;
- memory retrieval quality;
- resource utilization;
- thermal behavior;
- service availability.

## Audit vs Logs

Operational logs are short-lived debugging information. Audit records are structured records of consequential decisions and actions with retention controls.

## Privacy

Do not store raw audio/video in audit records unless explicitly required and authorized. Prefer references, summaries, hashes, or structured observations.

## Reproducibility

A trace should provide enough information to reconstruct the software/runtime conditions and event sequence needed to reproduce a behavior in simulation, subject to privacy controls.

## User Audit

The control application should eventually allow authorized users to inspect:

- what Novi observed at a high level;
- what action occurred;
- why the action was requested at a structured level;
- which capability executed it;
- result/failure;
- what data was created or changed.

## Acceptance Criteria

- consequential actions have trace IDs;
- policy/safety outcomes are visible;
- privacy-sensitive raw media is not copied unnecessarily;
- metrics identify latency and behavioral regressions;
- traces can drive simulation replay.
