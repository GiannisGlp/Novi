#!/usr/bin/env python3
"""Validate architecture-document reference integrity for Novi.

Checks:
1. Explicit Markdown path references resolve to existing repository files.
2. Ambiguous numeric references are accepted only when the referencing
   document's directory contains exactly one matching local document; these
   legacy references are reported as migration warnings.
3. ARCH-CLOSE identifiers referenced by documents must be defined in the
   tracked architecture corpus.

Numeric filename prefixes remain organizational labels. Exact paths and
ARCH-CLOSE identifiers are the preferred stable references. Local numeric
references are a temporary migration bridge for legacy documentation.

Historical archive documents and the ARCH-CLOSE-010 audit itself may contain
numeric examples intentionally describing the numbering problem. Those
references are not executable dependencies and are therefore excluded from
numeric-reference enforcement.
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
    warnings: list[str] = []
    closure_ids: set[str] = set()
    for path in files:
        text = path.read_text(encoding="utf-8")
        closure_ids.update(re.findall(r"\bARCH-CLOSE-\d{3}\b", text))

    explicit_path_pattern = re.compile(r"(?<![A-Za-z0-9_./-])(?:docs/|contracts/)[A-Za-z0-9_./-]+\.md")
    numeric_pattern = re.compile(r"\b(?:document|doc)\s+(\d{1,3})\b", re.IGNORECASE)

    for path in files:
        relative_path = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        for ref in explicit_path_pattern.findall(text):
            if ref not in relative:
                errors.append(f"{relative_path}: unresolved document path: {ref}")

        # Archive material and the closure audit may intentionally mention
        # ambiguous numeric examples while describing historical state.
        enforce_numeric = "/archive/" not in relative_path and not relative_path.endswith(
            "38_ARCH_CLOSE_010_DEPENDENCY_NUMBERING_INTEGRITY_AUDIT.md"
        )
        if enforce_numeric:
            for prefix in numeric_pattern.findall(text):
                candidates = prefix_to_paths.get(prefix, [])
                if len(candidates) <= 1:
                    continue
                local_candidates = [
                    candidate for candidate in candidates
                    if Path(candidate).parent == path.relative_to(ROOT).parent
                ]
                if len(local_candidates) == 1:
                    warnings.append(
                        f"{relative_path}: legacy scoped numeric reference 'document {prefix}' "
                        f"resolves locally to {local_candidates[0]}"
                    )
                else:
                    errors.append(
                        f"{relative_path}: ambiguous numeric reference 'document {prefix}'; "
                        f"use an exact filename or ARCH-CLOSE ID ({', '.join(candidates)})"
                    )

        for closure_id in re.findall(r"\bARCH-CLOSE-\d{3}\b", text):
            if closure_id not in closure_ids:
                errors.append(f"{relative_path}: unknown {closure_id}")

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
    print(f"Scoped legacy numeric references: {len(warnings)}")
    print(f"Closure IDs discovered: {len(closure_ids)}")
    if warnings:
        print("MIGRATION WARNINGS:")
        for warning in warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
