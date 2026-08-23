# Mac Datasets and Fixtures

## Objective

Provide small, versioned fixtures for deterministic local and CI testing.

## Structure

```text
fixtures/
  brain/
    scenarios/
    sensor_frames/
    expected/
```

## Rules

- fixtures are versioned and reproducible;
- each scenario has an identifier;
- expected outputs are explicit where deterministic comparison is possible;
- large/private datasets are not committed blindly;
- dataset metadata records source, license and version.

## Regression principle

A bug discovered in a testable deterministic path should become a permanent regression fixture unless there is a documented reason not to retain it.
