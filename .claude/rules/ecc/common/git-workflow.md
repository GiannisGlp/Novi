# Git Workflow (Novi)

> **Novi override.** This replaces ECC's default branch/PR workflow. Novi commits
> directly to `main`; there are no feature branches or pull requests, and the agent
> never pushes.

## Branching

- **Commit directly to `main`.** No feature branches, no pull requests.
- This is a solo/small-team project; branch/PR overhead does not apply. Keep the
  history linear on `main`.

## Pushing

- **Never push.** `git push` is a human decision, not an agent action.
- The user reviews the local commits and pushes when they see fit. Do not run
  `git push` (or `git push --force`) under any circumstances.

## Commit Message Format

```
<type>: <description>

<optional body>
```

Types: feat, fix, refactor, docs, test, chore, perf, ci

- One coherent change set per commit (matches `AGENTS.md` rule 3: step-by-step
  patches, humans review and commit).
- Keep the description short; put detail in the body when needed.

> For the full development process (planning, TDD, code review) before git operations,
> see [development-workflow.md](./development-workflow.md).
