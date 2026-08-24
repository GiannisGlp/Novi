---
name: data-profile
description: Profile a CSV data file offline — row/column counts, column types, missing values, numeric summaries (mean, median, stdev, min, max), and top categorical values. Use when a message asks to inspect, summarize, or understand a dataset or CSV.
license: MIT
kind: script
triggers: dataset, csv, profile-data, data-summary, columns, missing-values
script: profile.py
metadata:
  origin: original Novi skill (stdlib-only)
---

# Data Profile

Fast, dependency-free first look at a CSV file — the "what am I looking at?"
step of any data science task.

## Invocation

`run("data-profile", ["/path/to/file.csv"])`

## Contract

Emits `{"ok": true, "rows": N, "columns": {...}, "missing_total": M}` where
each column reports inferred type, missing count, and either numeric stats
(mean/median/stdev/min/max) or the most frequent values. Stdlib only — no
pandas required.
