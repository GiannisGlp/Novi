# Mac Toolchain

## Baseline

Use the versions declared by the repository first. Do not independently upgrade core tooling just to obtain a newer local version.

## Expected tooling

- Git for source control;
- Python for Brain/runtime/test tooling;
- pytest for Python tests;
- coverage for test coverage;
- Ruff for lint/format where configured;
- mypy or the repository's configured type checker;
- Node/npm or pnpm only where existing project components require them;
- Docker only where a repository service explicitly requires it.

## Verification

The local commands should be the same commands used by GitHub Actions wherever practical.

## Change policy

Toolchain changes must be reflected in repository configuration and CI rather than relying on undocumented Mac setup.
