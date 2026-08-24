---
name: linear-algebra
description: Solve linear-algebra problems exactly and numerically with numpy — systems of equations, determinants, eigenvalues/eigenvectors, matrix rank, inverse, and matrix products. Use when a message involves matrices, vectors, solving Ax=b, eigenvalues, or linear transformations.
license: MIT
kind: hybrid
triggers: matrix, matrices, eigenvalue, eigenvector, determinant, linear-system, vector-space, dot-product
script: linalg.py
metadata:
  origin: original Novi skill (numpy-backed)
---

# Linear Algebra

Novi computes real numerical linear algebra offline through numpy (bundled
`linalg.py`, JSON-on-stdout contract).

## Invocation

- `run("linear-algebra", ["solve", "[[2,1],[1,3]]", "[5,10]"])` → x for Ax=b
- `run("linear-algebra", ["det", "[[1,2],[3,4]]"])`
- `run("linear-algebra", ["eig", "[[4,1],[2,3]]"])`
- `run("linear-algebra", ["rank"|"inverse"|"mul"|"add", M1(, M2)])`

Matrices are JSON nested lists; vectors are flat lists.

## Guidance when reasoning

State the system in matrix form first; check the determinant/rank before
claiming uniqueness of solutions; prefer exact fractions for small integer
systems (pair with `symbolic-math`), numpy numerics for large ones.
