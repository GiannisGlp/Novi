#!/usr/bin/env python3
"""Numpy-backed linear algebra ops for the linear-algebra skill (JSON-on-stdout)."""
from __future__ import annotations

import json
import sys

try:
    import numpy as np
except ImportError:  # pragma: no cover - exercised only without numpy
    print(json.dumps({"ok": False, "outcome": "dependency_missing", "dependency": "numpy"}))
    raise SystemExit(0) from None

_OPS_1 = ("det", "rank", "inverse", "eig")
_OPS_2 = ("solve", "mul", "add")


def main() -> int:
    if len(sys.argv) < 3:
        print(json.dumps({"ok": False, "error": "usage: linalg.py <op> <matrix-json> [second-json]"}))
        return 1
    op, m1_raw = sys.argv[1], sys.argv[1 + 1]
    try:
        m1 = np.array(json.loads(m1_raw), dtype=float)
    except (ValueError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": f"bad_matrix:{exc}"}))
        return 1

    def _clean(value):
        arr = np.asarray(value)
        if arr.ndim == 0:
            v = float(arr)
            return int(v) if v.is_integer() else round(v, 6)
        if arr.ndim == 1:
            return [int(x) if float(x).is_integer() else round(float(x), 6) for x in arr]
        return [[int(x) if float(x).is_integer() else round(float(x), 6) for x in row] for row in arr]

    try:
        if op == "det":
            result = {"result": _clean(np.linalg.det(m1))}
        elif op == "rank":
            result = {"result": int(np.linalg.matrix_rank(m1))}
        elif op == "inverse":
            result = {"result": _clean(np.linalg.inv(m1))}
        elif op == "eig":
            values, vectors = np.linalg.eig(m1)

            def _num(x):
                c = complex(x)
                return round(c.real, 6) if abs(c.imag) < 1e-9 else [round(c.real, 6), round(c.imag, 6)]

            result = {
                "eigenvalues": [_num(v) for v in values],
                "eigenvectors": [_clean([float(z.real) for z in vectors[:, i]]) for i in range(vectors.shape[1])],
            }
        elif op in ("solve", "mul", "add"):
            if len(sys.argv) < 4:
                print(json.dumps({"ok": False, "error": f"{op}_needs_second_argument"}))
                return 1
            m2 = np.array(json.loads(sys.argv[3]), dtype=float)
            if op == "solve":
                result = {"result": _clean(np.linalg.solve(m1, m2))}
            elif op == "mul":
                result = {"result": _clean(m1 @ m2)}
            else:
                result = {"result": _clean(m1 + m2)}
        else:
            print(json.dumps({"ok": False, "error": f"unknown_op:{op}"}))
            return 1
    except Exception as exc:  # numpy raises LinAlgError etc.
        print(json.dumps({"ok": False, "error": str(exc)[:300]}))
        return 1
    result.update({"op": op})
    print(json.dumps({"ok": True, **result}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
