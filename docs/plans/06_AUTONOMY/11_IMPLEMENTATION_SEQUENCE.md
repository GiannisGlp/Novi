# 11 — Dependency-Ordered Implementation Sequence

## Purpose

This is the execution order for the entire autonomy workstream. Do not implement phases out of order unless a dependency is explicitly documented.

## Phase 0 — Freeze the autonomy contract

1. Review current `novi.brain`, perception, memory, planning and governance interfaces.
2. Create the autonomy state machine.
3. Define goal/plan/action/verification contracts.
4. Define authority levels.
5. Define event/evidence schema.
6. Add serialization and version fields.
7. Add contract tests.

**Exit:** all autonomy primitives exist without physical hardware dependencies.

## Phase 1 — Deterministic supervisor

1. Implement `AutonomySupervisor`.
2. Implement one-tick execution.
3. Add cancellation tokens.
4. Add deadlines/timeouts.
5. Add health checks.
6. Add event logging.
7. Add safe-stop state.
8. Add replayable simulated clock.

**Exit:** 10,000 simulated ticks complete without unauthorized execution.

## Phase 2 — Goal management

1. Implement goal lifecycle.
2. Implement priority/urgency scoring.
3. Implement arbitration.
4. Implement conflict handling.
5. Implement resource budgets.
6. Implement persistence.
7. Revalidate goals after restart.
8. Add background-goal limits.

**Exit:** deterministic goal selection under competing goals.

## Phase 3 — Grounded world state

1. Normalize observation provenance.
2. Add freshness/TTL.
3. Add contradiction representation.
4. Add belief revision.
5. Add spatial observation contracts.
6. Connect tracker state.
7. Add temporal prediction error.
8. Improve memory retrieval scoring.

**Exit:** simulated moving-world tests maintain correct beliefs and provenance.

## Phase 4 — Active perception

1. Define `PerceptionQuery`.
2. Keep SSDLite continuous.
3. Add optional LocateAnything adapter.
4. Implement strict parser.
5. Add model availability/timeout handling.
6. Fuse VLM results with tracks.
7. Add query budgets.
8. Add active search.
9. Add information-gain scoring.
10. Add future depth/3D fusion interface.

**Exit:** object-search scenario succeeds without false-positive claims after budget exhaustion.

## Phase 5 — Planning and skill execution

1. Audit existing SkillRegistry.
2. Define complete skill contracts.
3. Separate planning and execution.
4. Implement behavior-tree/task-graph semantics.
5. Add precondition checking.
6. Add postcondition verification.
7. Add recovery handlers.
8. Add outcome memory.
9. Implement virtual `NavigateTo` first.
10. Implement virtual `SearchForObject`.

**Exit:** 100 simulated tasks execute, recover or safely stop.

## Phase 6 — Navigation and spatial autonomy

1. Define `PoseProvider`.
2. Define `MapProvider`.
3. Choose SLAM/localization backend after benchmark.
4. Implement map representation.
5. Implement coordinate transforms.
6. Add global path planning.
7. Add local obstacle handling.
8. Add dynamic obstacle detection.
9. Add replanning.
10. Add navigation verification.

**Exit:** simulated navigation succeeds with dynamic obstacles and no collisions.

## Phase 7 — Safety and governance hardening

1. Define risk classes.
2. Implement safety monitor.
3. Implement action veto.
4. Add runtime safety monitoring.
5. Add emergency stop.
6. Add human approval.
7. Add policy versioning.
8. Add adversarial tests.

**Exit:** zero bypasses in safety/fault-injection suite.

## Phase 8 — Recovery and metacognition

1. Implement failure taxonomy.
2. Implement retry budgets.
3. Implement recovery selection.
4. Add replanning after world changes.
5. Add confidence decomposition.
6. Add health-aware authority reduction.
7. Add counterfactual failure records.
8. Add regression-memory generation.

**Exit:** 500 injected failures produce bounded recovery behavior.

## Phase 9 — Simulation-first embodied evaluation

1. Create deterministic lightweight simulation.
2. Import the robot into Isaac Sim when hardware geometry is available.
3. Add sensors and physics.
4. Connect ROS2 adapters.
5. Build scenario library.
6. Add synthetic perturbations.
7. Run SIL.
8. Collect evidence artifacts.
9. Run repeated seeds.
10. Promote only passing scenarios to HIL.

NVIDIA's current Isaac Sim workflow explicitly supports robot/scene import, physics and sensors, synthetic data, ROS2 and SIL/HIL validation. citeturn0search0turn0search4

**Exit:** full scenario suite passes with zero safety violations.

## Phase 10 — Curiosity and autonomous background behavior

Only after directed autonomy is reliable:

1. implement novelty detection;
2. calculate information value;
3. generate bounded exploration goals;
4. add exploration budgets;
5. add safe viewpoint changes;
6. promote verified discoveries;
7. learn exploration usefulness.

**Exit:** curiosity improves information coverage without unsafe or endless behavior.

## Phase 11 — Continual learning

1. Capture verified experiences.
2. Generate candidate lessons.
3. Aggregate evidence.
4. Validate candidate knowledge.
5. Promote with versioning.
6. Generate regression tests.
7. Provide rollback.
8. Measure whether learning improves future task outcomes.

**Exit:** learning improves benchmark performance without increasing false knowledge.

## Phase 12 — Physical robot ladder

1. Sensor-only.
2. Motor-disabled simulation bridge.
3. HIL.
4. Supervised physical motion.
5. Single bounded skill.
6. Multi-step bounded task.
7. Dynamic obstacle scenario.
8. Recovery scenario.
9. Longer supervised autonomy.
10. Expanded authority only after evidence review.

## What must NOT happen

- Do not give the LLM direct motor access.
- Do not make LocateAnything mandatory for the brain.
- Do not introduce ROS2 into core cognition before provider contracts exist.
- Do not train policies on real hardware before simulation/HIL evidence exists.
- Do not promote unverified model outputs to permanent knowledge.
- Do not let curiosity create unrestricted goals.
- Do not resume physical actions after restart without revalidation.
- Do not use a single confidence value as a substitute for uncertainty modeling.

## Final autonomy milestone

Novi earns the autonomy milestone only when it can receive a high-level goal, build and execute a bounded multi-step plan, actively gather missing information, adapt to changed conditions, verify outcomes, recover from expected failures, remain within authority/safety limits, persist useful experience, and reproduce the complete episode as evidence.
