#!/usr/bin/env python3
"""CSV profiling for the data-profile skill. Stdlib only; JSON-on-stdout."""
from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

MAX_TOP = 5


def _is_number(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False


def _column_report(values: list[str]) -> dict:
    missing = sum(1 for v in values if v == "")
    present = [v for v in values if v != ""]
    report: dict = {"missing": missing}
    if present and all(_is_number(v) for v in present):
        nums = [float(v) for v in present]
        report["type"] = "numeric"
        report["mean"] = round(statistics.fmean(nums), 6)
        report["median"] = round(statistics.median(nums), 6)
        report["stdev"] = round(statistics.stdev(nums), 6) if len(nums) > 1 else 0.0
        report["min"] = min(nums)
        report["max"] = max(nums)
    else:
        report["type"] = "categorical"
        report["distinct"] = len(set(present))
        report["top_values"] = [[v, c] for v, c in Counter(present).most_common(MAX_TOP)]
    return report


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "missing_path"}))
        return 1
    path = Path(sys.argv[1])
    if not path.is_file():
        print(json.dumps({"ok": False, "error": "file_not_found", "path": str(path)}))
        return 1
    try:
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            rows = list(reader)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        print(json.dumps({"ok": False, "error": str(exc)[:200]}))
        return 1
    if not header:
        print(json.dumps({"ok": False, "error": "empty_csv"}))
        return 1
    columns = {}
    for i, name in enumerate(header):
        values = [row[i] if i < len(row) else "" for row in rows]
        columns[name] = _column_report(values)
    missing_total = sum(c.get("missing", 0) for c in columns.values())
    print(json.dumps({"ok": True, "rows": len(rows), "columns": columns, "missing_total": missing_total}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
