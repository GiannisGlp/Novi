#!/usr/bin/env python3
"""Minimal titled PDF writer for the pdf-creator skill (optional fpdf2 dependency)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from fpdf import FPDF  # type: ignore[import-not-found]
except ImportError:
    print(json.dumps({"ok": False, "outcome": "dependency_missing", "dependency": "fpdf2"}))
    raise SystemExit(0) from None


def main() -> int:
    args = sys.argv[1:]
    title = "Document"
    out = None
    lines: list[str] = []
    i = 0
    while i < len(args):
        if args[i] == "--title" and i + 1 < len(args):
            title = args[i + 1]
            i += 2
        elif args[i] == "--out" and i + 1 < len(args):
            out = Path(args[i + 1])
            i += 2
        elif args[i] == "--line" and i + 1 < len(args):
            lines.append(args[i + 1])
            i += 2
        else:
            i += 1
    if out is None:
        print(json.dumps({"ok": False, "error": "missing_out_path"}))
        return 1
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=16)
        pdf.cell(0, 10, title[:80], ln=True)
        pdf.set_font("Helvetica", size=11)
        for line in lines[:200]:
            pdf.multi_cell(0, 6, line[:500])
        pdf.output(str(out))
    except OSError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps({"ok": True, "path": str(out), "lines": len(lines[:200])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
