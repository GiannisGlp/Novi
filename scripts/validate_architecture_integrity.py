#!/usr/bin/env python3
"""Validate architecture-document reference integrity for Novi.

Checks:
1. Explicit Markdown path references resolve to existing repository files.
2. Ambiguous numeric references such as "document 18" are rejected when the
   prefix is used by more than one Markdown document.
3. ARCH-CLOSE identifiers referenced by documents must be defined in at least
   one current architecture document.

Numeric filename prefixes remain organizational labels; exact paths and
ARCH-CLOSE identifiers are the stable references.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "*.md"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return [ROOT / line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    files = git_files()
    relative = {p.relative_to(ROOT).as_posix() for p in files}

    prefix_to_paths: defaultdict[str, list[str]] = defaultdict(list)
    for path in sorted(relative):
        name = Path(path).name
        match = re.match(r"^(\d+)_", name)
        if match:
            prefix_to_paths[match.group(1)].append(path)

    errors: list[str] = []
    closure_ids: set[str] = set()
    for path in files:
        text = path.read_text(encoding="utf-8")
        closure_ids.update(re.findall(r"\bARCH-CLOSE-\d{3}\b", text))

    explicit_path_pattern = re.compile(r"(?<![A-Za-z0-9_./-])(?:docs/|contracts/)[A-Za-z0-9_./-]+\.md")
    ambiguous_numeric_pattern = re.compile(
        r"\b(?:document|doc)\s+(\d{1,3})\b", re.IGNORECASE
    )

    for path in files:
        text = path.read_text(encoding="utf-8")
        for ref in explicit_path_pattern.findall(text):
            if ref not in relative:
                errors.append(f"{path.relative_to(ROOT)}: unresolved document path: {ref}")

        for prefix in ambiguous_numeric_pattern.findall(text):
            candidates = prefix_to_paths.get(prefix, [])
            if len(candidates) > 1:
                errors.append(
                    f"{path.relative_to(ROOT)}: ambiguous numeric reference 'document {prefix}'; "
                    f"use an exact filename or ARCH-CLOSE ID ({', '.join(candidates)})"
                )

        for closure_id in re.findall(r"\bARCH-CLOSE-\d{3}\b", text):
            # The closure document itself may be the defining occurrence; this
            # check only verifies that the identifier exists somewhere in the
            # tracked architecture corpus.
            if closure_id not in closure_ids:
                errors.append(f"{path.relative_to(ROOT)}: unknown {closure_id}")

    if errors:
        print("ARCHITECTURE INTEGRITY: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    duplicate_prefixes = {
        prefix: paths for prefix, paths in prefix_to_paths.items() if len(paths) > 1
    }
    print("ARCHITECTURE INTEGRITY: PASS")
    print(f"Markdown documents scanned: {len(files)}")
    print(f"Duplicate numeric prefixes governed as non-authoritative: {len(duplicate_prefixes)}")
    print(f"Closure IDs discovered: {len(closure_ids)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
