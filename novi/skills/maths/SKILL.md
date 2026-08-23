---
name: maths
description: Solve arithmetic and percentage expressions deterministically, offline. Use when a message asks to calculate, evaluate, or convert numbers.
kind: script
triggers: calculate, compute, solve, math, plus, minus, times, percent
script: solve.py
---

# Maths

Evaluates arithmetic expressions with exact fraction semantics where possible.

## Invocation

`run("maths", ["<expression>"])` — the expression is one argument, e.g. `"12*(3+4)"` or `"15% of 240"`.

## Contract

Emits `{"ok": true, "expression": ..., "result": ...}` on stdout, or
`{"ok": false, "error": "..."}` for malformed input. No network, no file access.
