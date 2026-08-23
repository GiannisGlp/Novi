# novi/db

Durable SQLite runtime stores for Novi. Database files (`*.db`) are
gitignored runtime artifacts and live here when created by the default
launcher scripts:

- `novi_demo.db` — demo store (used by `scripts/brain-demo.sh` / `scripts/mac-brain-demo.sh`)
- `novi_web.db` — web app store (used by `scripts/brain-web.sh` / `scripts/mac-web.sh`)

Override the location per-run with `NOVI_STORE` (or `--store`).
