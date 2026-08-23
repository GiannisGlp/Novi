# Compatibility Fixtures

Compatibility fixtures will exercise declared schema evolution policies.

## Required cases

For each contract, the eventual fixture set must cover:

- current version accepted;
- supported backward-compatible minor evolution accepted;
- unsupported major-version evolution rejected;
- undeclared version rejected;
- incompatible field/type change rejected.

The current matrix uses `major-stable` as the baseline policy for the registered contracts. This file deliberately documents the fixture requirements without inventing historical payloads that the repository does not yet possess.
