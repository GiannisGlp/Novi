# Mac Testing Acceptance Gate

## Objective

Determine whether the Mac environment is ready to serve as Novi's standard development and deterministic validation environment.

## Gate criteria

1. Repository can be cloned cleanly.
2. Required toolchain versions are documented and reproducible.
3. Project-local Python environment works without global package installation.
4. Core deterministic tests run locally.
5. Brain tests run locally.
6. Scenario/replay fixtures can execute locally.
7. Evidence metadata can be generated.
8. Local commands align with GitHub CI.
9. No NVIDIA hardware is required for deterministic validation.
10. Developer credentials remain outside tracked source.

## Status

**OPEN — requires execution on the user's Mac.**

This document is a gate definition, not a claim that the Mac environment has already been verified.
