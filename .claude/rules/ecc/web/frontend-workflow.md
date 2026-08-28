---
paths:
  - "novi/web/ui/**"
  - "**/*.html"
  - "**/*.css"
  - "**/*.js"
  - "**/*.ts"
  - "**/*.tsx"
---

# Frontend Workflow

When working on Novi's web UI — React SPA under `novi/web/ui/` — delegate to the **`frontend-developer`** agent.

## Trigger

Any change touching `novi/web/ui/` (React/TypeScript SPA), or other `.html`/`.css`/`.js`/`.ts`/`.tsx` files, is frontend work.

## What to do

1. **Delegate** — spawn the `frontend-developer` agent for the implementation. It owns the frontend and applies the `frontend-design` and `canvas-design` skills.
2. **Coordinate, don't own** — the Python backend (`novi/web/server.py`, `novi/web/integration_api.py`) stays with the standard Python workflow (`python-reviewer`, `tdd-guide`). If a UI change needs a backend change, the frontend agent flags it rather than stubbing endpoints.
3. **Build + verify** — after the change, run `npm run build` in `novi/web/ui` (the server serves the built `ui/dist`), run the Vitest suite (`npx vitest run` in `novi/web/ui`), and confirm the page renders.

## Constraints

- React + TypeScript SPA via Vite in `novi/web/ui`, built to `novi/web/ui/dist` (gitignored). The server serves only the built bundle.
- No secrets in client-side code; never render user- or model-generated content via `dangerouslySetInnerHTML` — React's default escaping applies.
- Keep accessibility: semantic elements, labels, keyboard reachability, `alt` text.
