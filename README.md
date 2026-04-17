# Backend — Spherecast Supply Chain Co-Pilot

FastAPI service. Paired with a Next.js frontend (sibling repo: clone it next to this one as `../frontend`).

- **Contract (source of truth):** [`../frontend/knowledge/api-contract.md`](../frontend/knowledge/api-contract.md)
- **Agent-facing notes:** [`CLAUDE.md`](./CLAUDE.md)
- **Frontend repo:** `../frontend` — see its README for startup.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive docs: http://localhost:8000/docs
OpenAPI schema: http://localhost:8000/openapi.json

## What's here

Only one template endpoint (`GET /ingredients`) is implemented. It demonstrates
the full layering pattern — schema, fixture, repo, router — that every new
endpoint should follow. See `CLAUDE.md` for the recipe.

```
app/
  main.py               — FastAPI app, CORS, router wiring, /health
  schemas/
    ingredient.py       — Pydantic model (template)
  api/
    ingredients.py      — router (template)
  data/
    db.py               — SQLite connection helper (optional DB-backed rows)
    fixtures.py         — JSON fixtures loaded into Pydantic
    repo.py             — domain queries (template)
tests/fixtures/
  ingredients.json      — seed data
```

## Frontend TypeScript types

Types are generated on the frontend side from this backend's live OpenAPI
schema — no Python-side codegen. After editing `app/schemas/`, restart the
backend and run `yarn gen:types` from `../frontend`.
