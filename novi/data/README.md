# Novi Data — single canonical store

`novi.db` is THE database: one SQLite file (WAL mode) that everything reads
from and writes to, regardless of interface — web app, CLI, voice, camera,
and the future robot body.

## What lives inside

| Domain | Tables |
|---|---|
| Memory + semantic recall | `memory_records`, `memory_fts`, `vectors` |
| Conversation | `chat` |
| Identity (who is who) | `identity`, `recognition_enrollments` (face/voice/noise/place) |
| Cognition | `beliefs`, `expectations`, `temporal`, `fusion` |
| Self | `soul`, `relationships`, `lexicon`, `preferences` |
| Action | `goals`, `plans`, `body` |

## Rules

- Every component resolves the same path: `novi/data/novi.db`
  (web launcher, CLI default, future body config).
- WAL journaling stays ON (`PRAGMA journal_mode=WAL`) — concurrent readers
  (web UI, perception loop, body processes) never block the writer.
- Do NOT create second databases for new subsystems; add tables here.
- `archive/` holds retired databases (e.g. the old demo fork).

## Access

```python
from novi.brain.storage import DurableMemoryStore
store = DurableMemoryStore("novi/data/novi.db")           # brain memory
from novi.integration.recognition_store import RecognitionStore
rec = RecognitionStore("novi/data/novi.db")               # faces/voices/places
```
