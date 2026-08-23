# Mac Repository Setup

## Steps

1. Clone the Novi repository.
2. Checkout the intended development branch.
3. Inspect repository documentation and implementation-plan status.
4. Create the project-local Python environment.
5. Install declared dependencies.
6. Verify Git working tree state.
7. Run the same baseline tests used by CI.

## Expected result

A clean checkout can run the deterministic test suite without untracked generated artifacts or machine-specific edits.

## Local configuration

Keep developer-only configuration outside tracked files or in explicitly ignored files. Never store credentials in the repository.
