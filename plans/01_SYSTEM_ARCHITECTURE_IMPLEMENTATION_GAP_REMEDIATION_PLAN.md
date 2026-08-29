# NOVI — 01 System Architecture & Implementation Gap Remediation Plan

Date: 2026-08-29
Scope: docs/01-system-architecture and related implementation
Target: main

## Purpose

Audit the documented NOVI architecture against actual repository implementation. Every item must be classified as IMPLEMENTED, PARTIALLY_IMPLEMENTED, DESIGN_ONLY, MISSING, or UNKNOWN. Documentation alone is not implementation evidence.

## Verified architecture areas

The repository contains a substantial system-architecture set, including:
- docs/01-system-architecture/22_ARCHITECTURE_CLOSURE_AND_BASELINE.md
- docs/01-system-architecture/21_ARCHITECTURE_COMPLETION_GATE.md
- docs/01-system-architecture/16_SOLUTION_SELECTION_POLICY.md
- docs/01-system-architecture/15_ARCHITECTURE_FILE_AUDIT.md
- docs/01-system-architecture/38_ARCH_CLOSE_010_DEPENDENCY_NUMBERING_INTEGRITY_AUDIT.md
- novi/contracts/README.md
- docs/02-novi-brain/20_TEMPORAL_COGNITION.md
- docs/04-memory-and-knowledge/README.md

## P0 gaps

### 1. Architecture-to-code truth matrix
Create docs/01-system-architecture/ARCHITECTURE_IMPLEMENTATION_MATRIX.md. Map every documented component, interface, state and dependency to exact implementation paths, symbols and tests. Mark unsupported claims explicitly.

### 2. End-to-end contracts
Inventory novi/contracts and define versioned schemas for observation, perception, world state, cognition request/result, routing, memory read/write, tools, action proposal, authorization, actuator command, execution result, safety override and health/fault events. Add boundary validation and contract tests.

### 3. Physical authority boundary
Enforce: cognition proposal -> policy -> authority -> safety -> capability validation -> command compilation -> actuator. AI components must never have unrestricted physical authority. Add allow-lists, bounds, expiry, rate limits, rejection codes and audit events.

### 4. Safety/autonomy state machine
Implement deterministic states: BOOT, SELF_TEST, SAFE_IDLE, READY, AUTONOMOUS, DEGRADED, FAULT, EMERGENCY_STOP, RECOVERY. Define ownership and transitions for actuator, battery/thermal, localization, perception, communication, cognition and resource failures. Test every transition.

### 5. Canonical world state
Define current robot state, pose, localization confidence, tracked entities, semantic scene state, task state, sensor health, uncertainty, timestamps, provenance, coordinate frames and versions. Keep current state separate from long-term memory.

### 6. Memory separation and retrieval correctness
Separate working, episodic, semantic, procedural, preference, environmental, routing telemetry and audit memory. Define retention, write authority, confidence, provenance, temporal validity, contradiction handling and deletion. Retrieval must filter and rank by time/provenance/confidence rather than vector similarity alone.

### 7. Routing contract
Make route decisions capability-oriented and versioned. Each route requires reason, confidence, required capability, safety class, latency budget, fallback, expiry and trace ID. Invalid routes fail closed.

### 8. Degraded modes
Define deterministic behavior when models, sensors, navigation, tools, communications or other subsystems fail. Fault injection must prove the robot reaches an explicitly safe reduced mode.

### 9. Action/tool semantics
Every side-effecting capability needs risk class, authorization, schema, preconditions, postconditions, timeout, idempotency and compensation/rollback where possible. Duplicate/retry tests are mandatory.

### 10. Decision observability
Record trace ID, observation IDs, world-state version, route, model/runtime version, memory references, tool calls, policy/safety decisions, action ID, execution result, confidence, degradation state and stage latency. Provide replay fixtures without retaining sensitive media by default.

### 11. Autonomy evaluation
Create repeatable tests for perception, localization, navigation, intent, routing, memory, tools, safety, interruption, recovery, long-duration autonomy and resource exhaustion. Track task success, unsafe-action rate, route accuracy, memory precision/recall, p50/p95/p99 latency and recovery success.

### 12. Simulation release gate
Create deterministic scenarios for normal navigation, obstacles, people, blocked routes, localization loss, sensor failure, model failure, emergency stop, ambiguity and contradictory observations. Simulation/evaluation results must gate physical deployment.

### 13. Security/threat model
Model threats across user input, speech/text, vision, memory, tools, models, network, physical access, firmware and supply chain. Every high-risk threat needs prevention, detection, containment and recovery.

## P1 gaps

14. Separate capability selection from model selection and maintain model/runtime provenance.
15. Define end-to-end latency budgets and timeout/fallback behavior for every critical stage.
16. Propagate perception uncertainty, timestamps, source, tracking confidence and coordinate frame into cognition.
17. Define deterministic source precedence for contradictory sensor, memory, user and model information.
18. Version prompts, policies, routing rules, schemas, memory formats, tool definitions, calibration, firmware, runtime, simulation worlds and evaluation datasets.
19. Establish CI checks for formatting, unit/contract tests, static analysis, dependency/security scanning, secret scanning and architecture consistency.

## P2 gaps

20. Improve ownership metadata, README/setup documentation, architecture change records and module responsibility documentation.
21. Profile inference, memory and state-update paths before adding infrastructure or scaling mechanisms.
22. Audit third-party dependencies and project licensing based on the actual repository inventory.

# Execution plan

## Task 01 — Truth inventory
1. Enumerate all files under docs/01-system-architecture.
2. Extract every component, interface, state, dependency and completion claim.
3. Search the full repository for each item.
4. Inspect actual call sites and imports.
5. Inspect tests and runtime wiring.
6. Classify implementation status.
7. Record exact evidence paths.
8. Identify undocumented implementation behavior.
9. Produce the implementation matrix.
10. Freeze the baseline before architecture-changing work.

## Task 02 — Authority and safety
1. Enumerate all action-producing components.
2. Enumerate actuator interfaces.
3. Trace every action path.
4. Identify bypasses.
5. Define trust boundaries.
6. Define capability permissions and risk classes.
7. Define physical parameter limits.
8. Define command expiry and watchdog behavior.
9. Implement deterministic validation outside the model.
10. Add bypass and malformed-command tests.

## Task 03 — Safety state machine
1. Specify states and transitions.
2. Specify transition authority.
3. Implement startup/self-test.
4. Implement health checks.
5. Implement timeout handling.
6. Implement degraded/fault/emergency behavior.
7. Implement recovery authorization.
8. Add transition tests.
9. Add fault-injection tests.
10. Add audit events.

## Task 04 — Contracts
1. Inventory novi/contracts.
2. Compare every contract with architecture documents.
3. Remove duplicates.
4. Add schema versions.
5. Add boundary validation.
6. Add compatibility rules.
7. Add serialization tests.
8. Add invalid-message tests.
9. Add contract fixtures.

## Task 05 — World state
1. Define entities and ownership.
2. Define timestamps and validity.
3. Define confidence and provenance.
4. Define coordinate frames.
5. Define versioning.
6. Define conflict resolution.
7. Implement read/update APIs.
8. Test stale state.
9. Test conflicting sources.
10. Test restart/recovery.

## Task 06 — Memory
1. Inventory current memory implementation.
2. Map uses to memory types.
3. Define schemas and metadata.
4. Define read/write authority.
5. Define retention/deletion.
6. Implement temporal/provenance/confidence filtering.
7. Implement contradiction handling.
8. Add retrieval regression tests.
9. Add persistence/restart tests.

## Task 07 — Routing and models
1. Inventory current routing decisions.
2. Define capability routes.
3. Define route schema/version.
4. Define confidence/expiry/fallback.
5. Separate capability from model identity.
6. Record model metadata.
7. Add route telemetry.
8. Test invalid routes.
9. Benchmark route latency.

## Task 08 — Tools/actions
1. Inventory tools.
2. Classify side effects and risk.
3. Define authorization.
4. Define schemas/preconditions/postconditions.
5. Add idempotency.
6. Add timeout handling.
7. Add compensation where possible.
8. Audit side effects.
9. Test duplicate/retry behavior.
10. Test authorization failures.

## Task 09 — Observability
1. Define event taxonomy.
2. Add correlation IDs.
3. Instrument perception, state, routing, retrieval, models, tools, safety and actuation.
4. Record stage latency.
5. Redact sensitive data.
6. Define replay format.
7. Verify an end-to-end run can be reconstructed.

## Task 10 — Evaluation/simulation
1. Define scenario manifest.
2. Capture deterministic configuration.
3. Add normal scenarios.
4. Add ambiguity scenarios.
5. Add sensor/localization faults.
6. Add model/tool faults.
7. Add emergency-stop scenarios.
8. Add contradiction scenarios.
9. Define thresholds.
10. Gate promotion on results.

## Task 11 — CI and provenance
1. Inventory current CI.
2. Add lint/format checks.
3. Add unit and contract tests.
4. Add static/security/dependency/secret scanning.
5. Add architecture consistency checks.
6. Add evaluation jobs where practical.
7. Store provenance artifacts.
8. Require green checks before main changes.

## Task 12 — Security closure
1. Enumerate trust boundaries.
2. Threat-model every external input.
3. Threat-model memory and tools.
4. Threat-model models and runtime.
5. Threat-model network/firmware/physical access.
6. Define mitigations.
7. Add adversarial tests.
8. Define recovery procedures.
9. Record residual risk.

# Dependency order

01 Truth inventory -> 02 Authority/safety -> 03 Safety state -> 04 Contracts -> 05 World state -> 06 Memory -> 07 Routing/models -> 08 Tools/actions -> 09 Observability -> 10 Evaluation/simulation -> 11 CI/provenance -> 12 Security closure

# Definition of Done

The architecture phase is complete only when every architecture component has an evidence-backed status; all cross-boundary interfaces are versioned; physical actuation has a deterministic safety boundary; safety states are executable and tested; world state is separate from long-term memory; retrieval respects time/provenance/confidence; actions have authority/risk/idempotency semantics; decisions are observable/replayable; autonomy evaluation and simulation gate releases; all behavior-critical versions are recorded; high-risk threats have mitigations and tests; and documentation matches implementation.

## Immediate next action

Start with Task 01. Do not implement new architecture components until the repository-wide architecture-to-code truth matrix is complete. This prevents duplicate systems, conflicting contracts and unnecessary rewrites.
