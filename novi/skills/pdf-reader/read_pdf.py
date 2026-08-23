#!/usr/bin/env python3
"""PDF text extraction for the pdf-reader skill (optional pypdf dependency)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from pypdf import PdfReader  # type: ignore[import-not-found]
except ImportError:
    print(json.dumps({"ok": False, "outcome": "dependency_missing", "dependency": "pypdf"}))
    raise SystemExit(0) from None


def _page_span(arg: str | None, total: int) -> range:
    if not arg:
        return range(total)
    m = arg.replace("--pages", "").strip()
    if "-" in m:
        lo, _, hi = m.partition("-")
        return range(max(1, int(lo)), min(total, int(hi)) + 1)
    page = int(m)
    return range(page - 1, page) if page >= 1 else range(total)


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "missing_path"}))
        return 1
    path = Path(sys.argv[1])
    pages_arg = sys.argv[2] if len(sys.argv) > 2 else None
    if not path.is_file():
        print(json.dumps({"ok": False, "error": "file_not_found", "path": str(path)}))
        return 1
    reader = PdfReader(str(path))
    chunks = []
    for i in _page_span(pages_arg, len(reader.pages)):
        chunks.append(reader.pages[i].extract_text() or "")
    text = "\n".join(chunks).strip()
    print(json.dumps({"ok": True, "pages": len(reader.pages), "text": text[:20000]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
