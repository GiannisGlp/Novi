# Mac Python Environment

## Objective

Create an isolated Python environment for Novi without modifying the system Python installation.

## Required pattern

```text
repository/
  .venv/
  requirements / project dependency metadata
```

Use the Python version pinned by the repository. Create the environment with `python3 -m venv .venv` when that matches the repository setup, activate it, then install only declared project/test dependencies.

## PEP 668

Do not bypass externally-managed-environment protections with global `pip` installation. The project virtual environment is the expected installation target.

## Reproducibility

Dependency changes must be captured in repository dependency metadata/lock files. A developer's local package installation is not evidence.

## Verification

Run the repository's configured import/version checks and the complete deterministic test suite after environment creation.
