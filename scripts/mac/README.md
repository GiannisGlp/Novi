# Novi Mac Test Scripts

All commands are intended to be run from the repository root. Use `bash` explicitly unless executable permissions have been enabled in a local checkout.

## Standard workflow

```bash
bash scripts/mac/setup.sh
source .venv/bin/activate
bash scripts/mac/doctor.sh
bash scripts/mac/test.sh
bash scripts/mac/collect-evidence.sh
```

## Commands

- `setup.sh` — create/update the project-local Python environment and install declared dependencies.
- `doctor.sh` — inspect the Mac/toolchain/repository state and save environment metadata through the collector.
- `test.sh` — run the complete available deterministic suite and collect logs, JUnit, coverage and environment metadata.
- `test-brain.sh` — run the Brain test suite and collect the same evidence.
- `benchmark.sh` — run the deterministic Brain benchmark entrypoint; this is not NVIDIA performance evidence.
- `collect-evidence.sh` — snapshot the latest run into `IMPLEMENTATION_PLAN/EVIDENCE/mac/<timestamp>/`.
- `runner.py` — underlying Python orchestrator.

## Result location

Every run is stored in:

```text
mac_test_results/<UTC-run-id>/
├── environment.json
├── summary.json
├── *.log
├── *.xml
└── *_coverage.json
```

`mac_test_results/latest/` points to the latest run where the filesystem supports symlinks; otherwise `LATEST_RUN.txt` is written.

## Important

A Mac result proves local software/test behavior. It does not prove Jetson TensorRT performance, GPU power/thermal behavior, or the Orin-vs-Thor hardware decision.
