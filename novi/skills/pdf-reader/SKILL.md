---
name: pdf-reader
description: Extract text from PDF files, page-ranged. Requires the optional pypdf dependency; reports dependency_missing honestly when absent.
kind: script
triggers: pdf, read-pdf
script: read_pdf.py
---

# PDF Reader

Reads text out of a local PDF file. Runs fully offline once pypdf is installed.

## Invocation

`run("pdf-reader", ["/path/to/file.pdf", "--pages 1-3"])`

## Contract

`{"ok": true, "pages": N, "text": "..."}`
When pypdf is missing: `{"ok": false, "outcome": "dependency_missing", "dependency": "pypdf"}` —
Novi states plainly that it cannot read the file yet and what would enable it.
