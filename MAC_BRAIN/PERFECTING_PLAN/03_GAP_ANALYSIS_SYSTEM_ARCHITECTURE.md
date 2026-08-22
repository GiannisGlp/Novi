# 03 — Gap Analysis: System Architecture

## Docs mandate (01-system-architecture)
- Authority hierarchy + architecture invariants (ARCH-001..020) mapped to executable tests.
- Canonical contracts (EventEnvelope, Observation, Evidence, WorldStateChange, Entity,
  Relationship, MemoryRecord, KnowledgeRecord, Goal, Plan, ActionProposal, Authorization,
  SafetyDecision, ActionExecution/Outcome, ModelInvocation, HardwareHealth, DeploymentManifest).
- Durable state/event log; transactions/concurrency; replication; recovery/checkpointing;
  privacy/erasure; observability; resource governance; time sync; deployment manifest.
- Evidence classes E0-E5; "document exists" is not completion.
- Global completion gate: no new phase until all 12 domains COMPLETE (currently CLOSED).

## Exists today
- Contract registry + JSON Schemas; contract/validation scripts; observability;
  resource-budget baseline; time semantics; stage-1 SQLite (Mac) storage with a benchmark
  evidence record (ARCH-CLOSE-003) — RocksDB/Postgres adapters not reproducible yet.

## Delta (what is missing)
- Real event store + transaction/recovery/erasure engines beyond the Mac SQLite path.
- Executable canonical schemas for the full contract set (some are schemas only, not
  enforced end-to-end).
- Resource/power/thermal empirical measurement (provisional Mac numbers only; no
  Jetson/Thor data — hardware not purchased, correct for brain phase but must be flagged).
- A living traceability map requirement - decision - contract - implementation - test - evidence.
- Deployment-manifest executable/rollback validation.

## Next action
- Keep system-architecture workstreams as gated campaigns (ARCH-CLOSE-003/004/006/007/008)
  but do not expand scope in the brain phase; fold only the contracts the cognitive core
  needs (world-state, evidence, memory-record, governance) into roadmap Steps 1-3. Re-open
  the hardware-dependent gates when prototype hardware arrives.

