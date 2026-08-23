---
name: pdf-creator
description: Create a simple PDF document from title and lines. Requires the optional fpdf2 dependency; reports dependency_missing honestly when absent.
kind: script
triggers: create-pdf, make-pdf, pdf-create
script: make_pdf.py
---

# PDF Creator

Writes a titled one-page PDF from plain lines. Fully offline once fpdf2 is installed.

## Invocation

`run("pdf-creator", ["--title", "Report", "--out", "/path/out.pdf", "--line", "first", "--line", "second"])`

## Contract

`{"ok": true, "path": ..., "lines": N}`
When fpdf2 is missing: `{"ok": false, "outcome": "dependency_missing", "dependency": "fpdf2"}`.
