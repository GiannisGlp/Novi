#!/usr/bin/env python3
"""Deterministic arithmetic solver for the maths skill. JSON-on-stdout contract."""
from __future__ import annotations

import ast
import json
import operator
import re
import sys

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError(f"unsupported_expression:{type(node).__name__}")


def normalize(text: str) -> str:
    t = text.strip().lower()
    pct = re.fullmatch(r"([0-9.]+)\s*%\s*of\s*([0-9.]+)", t)
    if pct:
        p, whole = float(pct.group(1)), float(pct.group(2))
        return f"({p}/100)*{whole}"
    t = t.replace("^", "**").replace(",", "").replace("×", "*").replace("÷", "/")
    t = re.sub(r"\bplus\b", "+", t)
    t = re.sub(r"\bminus\b", "-", t)
    t = re.sub(r"\btimes\b", "*", t)
    return t


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "missing_expression"}))
        return 1
    expr = normalize(sys.argv[1])
    try:
        tree = ast.parse(expr, mode="eval")
        result = _eval(tree)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        print(json.dumps({"ok": True, "expression": sys.argv[1], "result": result}))
        return 0
    except (ValueError, SyntaxError, ZeroDivisionError, OverflowError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
