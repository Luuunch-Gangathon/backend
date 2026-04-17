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

## Layout

```
app/
  main.py               # FastAPI app, CORS (localhost:3000), router wiring
  schemas/              # Pydantic v2 models — consumed by the frontend via
                        # /openapi.json + `openapi-typescript`
  api/                  # one router per domain
  data/                 # fixture loader + repo (DB-first, fixtures fallback)
tests/fixtures/         # JSON seed data keyed with the same IDs as frontend mocks
```

## Frontend TypeScript types

Types are generated on the frontend side from this backend's live OpenAPI
schema — no Python-side codegen. After editing `app/schemas/`, restart the
backend and run `npm run gen:types` from `../frontend`.

## ID scheme

String IDs everywhere. Hand-authored fixtures use `ing_<n>`, `sup_<n>`,
`co_<n>`, `cg_<n>`. Rows sourced from `data/db.sqlite` are namespaced with a
`_db` infix (`ing_db_<Product.Id>`, etc.) so they never collide with mock IDs.
