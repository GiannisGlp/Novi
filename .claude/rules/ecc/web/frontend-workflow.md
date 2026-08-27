---
paths:
  - "novi/web/static/**"
  - "**/*.html"
  - "**/*.css"
  - "**/*.js"
---

# Frontend Workflow

When working on Novi's web UI — or any HTML/CSS/JS — delegate to the **`frontend-developer`** agent.

## Trigger

Any change touching `novi/web/static/` (index.html, preview.html, camera.html) or other `.html`/`.css`/`.js` files is frontend work.

## What to do

1. **Delegate** — spawn the `frontend-developer` agent for the implementation. It owns the frontend and applies the `frontend-design` and `canvas-design` skills.
2. **Coordinate, don't own** — the Python backend (`novi/web/server.py`, `novi/web/integration_api.py`) stays with the standard Python workflow (`python-reviewer`, `tdd-guide`). If a UI change needs a backend change, the frontend agent flags it rather than stubbing endpoints.
3. **Verify** — after the change, run `pytest novi/web/tests -q` and confirm the page renders.

## Constraints

- Plain static HTML/CSS/JS — no bundler, framework, or npm dependency unless the task explicitly requires one.
- No secrets in client-side code; sanitize any user- or model-generated content rendered into the DOM.
- Keep accessibility: semantic elements, labels, keyboard reachability, `alt` text.
