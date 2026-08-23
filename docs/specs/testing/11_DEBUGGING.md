# Mac Debugging

## Debug order

1. Reproduce locally.
2. Capture exact command and commit SHA.
3. Reduce to the smallest failing test/scenario.
4. Inspect logs and structured error output.
5. Fix the implementation, not the test, unless the test is demonstrably incorrect.
6. Add or update a regression test.
7. Run focused tests.
8. Run the full deterministic suite.
9. Verify CI.

## CI failures

When local and CI disagree, compare Python/tool versions, environment variables, filesystem assumptions, dependency resolution and test ordering before changing behavior.
