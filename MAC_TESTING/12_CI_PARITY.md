# Mac and CI Parity

## Objective

Make local Mac validation and GitHub Actions use the same repository-defined commands and dependency constraints wherever possible.

## Rules

- CI should not require undocumented local setup;
- local commands should be discoverable from repository documentation/scripts;
- Python and other tool versions should be pinned or explicitly bounded;
- generated artifacts should be ignored consistently;
- test ordering and environment assumptions should be minimized.

## Parity gate

A Mac test suite is ready for routine development when a clean checkout on the Mac can execute the same deterministic test command that CI executes and obtain the same result class.
