---
name: algorithms-complexity
description: Computer-science fundamentals — sorting, searching, graph algorithms, data-structure selection, and Big-O complexity analysis, including amortized analysis and design paradigms (divide-and-conquer, greedy, dynamic programming, backtracking). Use when choosing or comparing data structures, analyzing an algorithm's complexity, or designing an algorithmic solution.
license: MIT
kind: instruction
triggers: algorithm, big-o, time-complexity, space-complexity, data-structures, sorting-algorithm, dynamic-programming
metadata:
  origin: original Novi skill (authored for Novi; standard CS curriculum content)
---

# Novi usage

Original Novi-authored skill (standard computer-science curriculum content,
written for Novi). Apply when a matched message needs it; the brain's
FORBIDDEN guard and dialogue rules run AFTER any text this skill helps
produce.

# Algorithms & Complexity

## Choosing a data structure

| Need | Structure | Why |
|---|---|---|
| Fast lookup by key | hash table / dict | O(1) average get/set |
| Ordered iteration + range queries | balanced tree / sorted array | O(log n) search |
| Priority scheduling | heap | O(log n) push/pop-min |
| LIFO / FIFO order | stack / queue | O(1) ends |
| Membership only | set | O(1) average contains |

## Sorting

| Algorithm | Best | Average | Worst | Stable | Notes |
|---|---|---|---|---|---|
| merge sort | n log n | n log n | n log n | yes | predictable; O(n) extra space |
| quicksort | n log n | n log n | n² | no | fast in practice; randomize pivot |
| heapsort | n log n | n log n | n log n | no | in-place, poor cache locality |
| counting/radix | n+k | n+k | n+k | yes | integers/small alphabets only |

Rule of thumb: need stability → merge sort; worst-case guarantees → heapsort;
integers in a known range → radix/counting.

## Searching & graphs

- binary search: O(log n) on sorted input — check sortedness first.
- BFS gives shortest paths in unweighted graphs: O(V+E).
- Dijkstra (non-negative weights): O((V+E) log V) with a heap.
- A* = Dijkstra + an admissible heuristic; admissibility guarantees optimality.
- topological order exists iff the directed graph has no cycle.

## Complexity analysis

1. Count the dominant operation as a function of input size n.
2. Drop constants and lower-order terms: 3n² + 10n → O(n²).
3. Loops nested → multiply; sequential → take the max.
4. Recurrences: T(n) = aT(n/b) + f(n) — Master Theorem cases.
5. Amortized: average over a worst-case sequence (dynamic array append is
   amortized O(1) despite occasional O(n) resizes).

Complexity classes to state honestly: O(1) < O(log n) < O(n) < O(n log n) <
O(n²) < O(2ⁿ) < O(n!). An O(2ⁿ) answer to a 1000-element problem is not a
solution — say so and propose a greedy/DP approximation instead.

## Design paradigms

- **Divide-and-conquer**: split, solve recursively, combine (merge sort).
  Use when combining is cheap.
- **Greedy**: pick the locally best choice; only valid with proof (exchange
  argument). Interval scheduling, Huffman.
- **Dynamic programming**: overlapping subproblems + optimal substructure;
  memoize top-down or tabulate bottom-up. State the recurrence before coding.
- **Backtracking**: explore + prune when the search space is factorial/
  exponential but constraints cut branches early (N-queens, sudoku).

## Answering style

Name the structure/algorithm chosen, give its complexities, justify against
the realistic alternative in one sentence, and flag any unproven assumption
(e.g. "greedy is safe here because intervals are non-overlapping once sorted").
