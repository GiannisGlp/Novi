#!/usr/bin/env python3
"""Novi Mac test orchestrator.

Runs repository-local validation commands when their corresponding tooling/configuration
exists, captures stdout/stderr, exit codes and timing, and writes a self-contained
run directory under mac_test_results/. It intentionally does not require NVIDIA hardware.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "mac_test_results"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def git_value(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unknown"


def environment() -> dict:
    return {
        "timestamp_utc": utc_now(),
        "repository": "GiannisGlp/Novi",
        "commit_sha": git_value(["rev-parse", "HEAD"]),
        "branch": git_value(["branch", "--show-current"]),
        "working_tree": git_value(["status", "--porcelain"]),
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "system": platform.system(),
        "release": platform.release(),
        "processor": platform.processor(),
        "tools": {name: shutil.which(name) for name in ["git", "python3", "pytest", "coverage", "ruff", "mypy", "node", "npm", "docker"]},
    }


def command_for(name: str) -> list[str] | None:
    pytest = shutil.which("pytest")
    python = sys.executable
    if name == "brain":
        if pytest and (ROOT / "brain/tests").exists():
            return [pytest, "brain/tests", "--junitxml={JUNIT}", "--cov=brain", "--cov-report=term-missing", "--cov-report=json:{COV}"]
    if name == "unit":
        if pytest:
            return [pytest, "brain/tests", "--junitxml={JUNIT}", "--cov=brain", "--cov-report=term-missing", "--cov-report=json:{COV}"]
    if name == "full":
        if pytest:
            return [pytest, "--junitxml={JUNIT}", "--cov=brain", "--cov-report=term-missing", "--cov-report=json:{COV}"]
    if name == "lint" and command_exists("ruff"):
        return ["ruff", "check", "."]
    if name == "typecheck" and command_exists("mypy"):
        return ["mypy", "brain"]
    return None


def execute(name: str, cmd: list[str], out_dir: Path) -> dict:
    safe_name = name.replace("/", "_")
    junit = out_dir / f"{safe_name}.xml"
    cov = out_dir / f"{safe_name}_coverage.json"
    rendered = [x.replace("{JUNIT}", str(junit)).replace("{COV}", str(cov)) for x in cmd]
    log = out_dir / f"{safe_name}.log"
    start = time.monotonic()
    started = utc_now()
    print(f"\n=== {name} ===")
    print("$", " ".join(rendered))
    proc = subprocess.run(rendered, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    duration = time.monotonic() - start
    log.write_text(proc.stdout, encoding="utf-8")
    print(proc.stdout, end="")
    return {"name": name, "command": rendered, "started_utc": started, "duration_seconds": round(duration, 3), "exit_code": proc.returncode, "status": "PASS" if proc.returncode == 0 else "FAIL", "log": str(log.relative_to(ROOT))}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Novi Mac test runner")
    parser.add_argument("--suite", choices=["doctor", "brain", "unit", "full", "lint", "typecheck", "all"], default="all")
    args = parser.parse_args()

    run = run_id()
    out_dir = RESULTS / run
    out_dir.mkdir(parents=True, exist_ok=True)
    env = environment()
    (out_dir / "environment.json").write_text(json.dumps(env, indent=2), encoding="utf-8")

    results: list[dict] = []
    if args.suite == "doctor":
        print(json.dumps(env, indent=2))
        return 0

    suites = [args.suite] if args.suite != "all" else ["lint", "typecheck", "brain", "full"]
    for suite in suites:
        cmd = command_for(suite)
        if cmd is None:
            results.append({"name": suite, "status": "SKIP", "reason": "required tool/configuration not present"})
            print(f"\n=== {suite} ===\nSKIP: required tool/configuration not present")
            continue
        results.append(execute(suite, cmd, out_dir))

    summary = {
        "run_id": run,
        "started_utc": utc_now(),
        "repository": "GiannisGlp/Novi",
        "commit_sha": env["commit_sha"],
        "environment_file": str((out_dir / "environment.json").relative_to(ROOT)),
        "results": results,
        "failed": any(r.get("status") == "FAIL" for r in results),
        "completed_utc": utc_now(),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    latest = RESULTS / "latest"
    if latest.exists() or latest.is_symlink():
        if latest.is_dir() and not latest.is_symlink():
            shutil.rmtree(latest)
        else:
            latest.unlink()
    try:
        latest.symlink_to(out_dir.name, target_is_directory=True)
    except OSError:
        (RESULTS / "LATEST_RUN.txt").write_text(str(out_dir.relative_to(ROOT)), encoding="utf-8")

    print("\n========================================")
    print(f"Novi Mac Test Run: {run}")
    for result in results:
        print(f"{result['name']:12} {result['status']}")
    print(f"Results: {out_dir.relative_to(ROOT)}")
    print("========================================")
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
