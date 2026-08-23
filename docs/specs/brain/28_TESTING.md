# Mac Brain Testing

## Test layers

1. Interface/contract tests.
2. AI provider tests with deterministic fixtures.
3. Component integration tests.
4. Multimodal scenario tests.
5. Memory/cognition tests.
6. Goal/planning tests.
7. Closed-loop tests.
8. Failure/recovery tests.
9. Stress/soak tests.
10. Regression tests.

## Real-device tests

Camera, microphone and speakers should be exercised on the actual Mac once the Mac Testing Acceptance Gate is active.

## AI validation

Where real models run locally, compare model output to task-specific expectations. Where they cannot run locally, keep the provider boundary and use deterministic fixtures until the appropriate hardware is available.

## Evidence

Every formal run records commit, configuration, scenario/model identity, environment, result and relevant measurements.
