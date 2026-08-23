#!/usr/bin/env python3
"""Symbolic math operations for the symbolic-math skill (sympy, JSON-on-stdout).

Usage: solve.py <op> <expression> [variable]
  ops: solve | diff | integrate | simplify | expand | factor | limit
Examples:
  solve.py solve "x**2 - 4" x          -> [-2, 2]
  solve.py diff "sin(x)*x" x           -> x*cos(x) + sin(x)
  solve.py integrate "1/x" x           -> log(x)
  solve.py limit "sin(x)/x" x          -> 1  (x -> 0)
"""
from __future__ import annotations

import json
import sys

try:
    import sympy as sp
except ImportError:  # pragma: no cover - exercised only without sympy
    print(json.dumps({"ok": False, "outcome": "dependency_missing", "dependency": "sympy"}))
    raise SystemExit(0) from None


def _to_equation(expr: str):
    """'x**2 = 9' becomes Eq-form difference; bare expr means expr == 0."""
    if "=" in expr:
        lhs, _, rhs = expr.partition("=")
        return sp.sympify(f"({lhs}) - ({rhs})")
    return sp.sympify(expr)


def main() -> int:
    if len(sys.argv) < 3:
        print(json.dumps({"ok": False, "error": "usage: solve.py <op> <expr> [var]"}))
        return 1
    op, expression = sys.argv[1], sys.argv[2]
    var_name = sys.argv[3] if len(sys.argv) > 3 else "x"
    try:
        var = sp.Symbol(var_name)
        if op == "solve":
            result = sp.solve(_to_equation(expression), var)
            pretty = [sp.sstr(r) for r in result]
        elif op == "diff":
            result = sp.diff(sp.sympify(expression), var)
            pretty = sp.sstr(result)
        elif op == "integrate":
            result = sp.integrate(sp.sympify(expression), var)
            pretty = sp.sstr(result)
        elif op == "simplify":
            pretty = sp.sstr(sp.simplify(sp.sympify(expression)))
        elif op == "expand":
            pretty = sp.sstr(sp.expand(sp.sympify(expression)))
        elif op == "factor":
            pretty = sp.sstr(sp.factor(sp.sympify(expression)))
        elif op == "limit":
            pretty = sp.sstr(sp.limit(sp.sympify(expression), var, 0))
        else:
            print(json.dumps({"ok": False, "error": f"unknown_op:{op}"}))
            return 1
        print(json.dumps({"ok": True, "op": op, "expression": expression, "result": pretty}))
        return 0
    except Exception as exc:  # sympy raises many types; report honestly
        print(json.dumps({"ok": False, "error": str(exc)[:300]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
