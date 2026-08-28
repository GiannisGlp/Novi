# Novi Web UI

React 19 + TypeScript SPA for the Novi brain console — chat, cognition, memory,
knowledge, perception, camera/voice, preview, and event feeds. Built with Vite to
`dist/` (gitignored); the web server (`novi/web/server.py`) serves only the built
bundle, so run `npm run build` before starting the server.

## Commands

```bash
npm install       # first time only
npm run dev       # Vite dev server (HMR) — API calls hit the running server
npm run build     # → dist/ (the bundle the server serves)
npm run preview   # serve the built dist locally
npx vitest run    # test suite (Vitest + React Testing Library)
npx tsc --noEmit  # type check
```

## Structure

- `src/App.tsx` — route table (react-router BrowserRouter) + app-level hook mounting
- `src/pages/` — one component per route (Overview, Cognition, Memory, Knowledge, Perception, Camera, Preview, Events)
- `src/components/` — shared UI (RailNav, TopBar, ChatDrawer, camera/preview pages, `shared/` primitives)
- `src/hooks/` — polling hooks matching the legacy console cadence (`useChat`, `useBrainState`, `useEvents`, `useAttention`, `useIdentity`, `useTheme`, …); no Redux
- `src/canvas/` — pure `CanvasRenderingContext2D` draw functions; React wrappers handle DPR scaling and `requestAnimationFrame` loops
- `src/api/` — typed API client (`client.ts`) + response types (`types.ts`), one front door for all `/api/*` calls
- `src/styles/app.css` — design tokens (CSS custom properties) + component styles

## Conventions

- Custom hooks for all data fetching; polling intervals mirror the legacy static pages.
- Canvas visuals are hand-rolled (no chart library) — keep draw functions pure and resolve CSS theme vars at draw time.
- Never render user- or model-generated content via `dangerouslySetInnerHTML`; React's default escaping applies.
- Tests live beside the code (`src/hooks/useChat.test.ts`, etc.).
