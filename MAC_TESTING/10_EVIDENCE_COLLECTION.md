# Mac Evidence Collection

## Objective

Make local validation results traceable and reusable.

## Minimum metadata

- repository;
- commit SHA;
- test command;
- environment/tool versions;
- fixture/scenario version;
- result;
- timestamp;
- failure output when applicable.

## Evidence distinction

Mac evidence can support software correctness, regression and scenario behavior. It must be labeled separately from accelerator performance and hardware evidence.

## Storage

Formal evidence should follow the repository's global `IMPLEMENTATION_PLAN/EVIDENCE` schema. Do not create an incompatible second evidence format for Mac-only testing.
