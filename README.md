# Backend — Spherecast Supply Chain Co-Pilot

FastAPI service matching the contract in `frontend/knowledge/api-contract.md`.

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

## Layout

```
app/
  main.py               # FastAPI app, CORS (localhost:3000), router wiring
  schemas/              # Pydantic v2 models, 1:1 with frontend/lib/types.ts
  api/                  # one router per domain
  data/                 # fixture loader + repo (DB-first, fixtures fallback)
tests/fixtures/         # JSON seed data keyed with the same IDs as frontend mocks
scripts/
  generate_ts_types.py  # regenerate ../frontend/lib/types.ts from Pydantic
```

## Regenerate TypeScript types

```bash
python scripts/generate_ts_types.py
```

Overwrites `../frontend/lib/types.ts` with an auto-generated header.

## ID scheme

String IDs everywhere. Hand-authored fixtures use `ing_<n>`, `sup_<n>`,
`co_<n>`, `cg_<n>`. Rows sourced from `data/db.sqlite` are namespaced with a
`_db` infix (`ing_db_<Product.Id>`, etc.) so they never collide with mock IDs.
