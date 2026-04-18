# Spherecast Supply Chain Co-Pilot — Backend

FastAPI backend for wAgent. Reads supply chain data from Postgres, runs background agent pipeline to generate consolidation proposals, and serves everything via REST API.

---

## Architecture

```
REQUEST
   │
   ▼
┌──────────────────────────────────┐
│  API ROUTERS  (app/api/)         │  ← thin HTTP layer, read-only
│  companies / products /          │
│  raw-materials / suppliers /     │
│  proposals / substitutions /     │
│  agnes (POST /ask is exception)  │
└──────────────┬───────────────────┘
               │ calls
               ▼
┌──────────────────────────────────┐
│  REPO  (app/data/repo.py)        │  ← SQL only, no logic, int IDs
└──────────────┬───────────────────┘
               │ reads
               ▼
┌─────────────────────────────────────────────────────┐
│  POSTGRESQL                                          │
│                                                     │
│  [raw tables — migrated from SQLite on first boot]  │
│  companies  products  boms  bom_components          │
│  suppliers  supplier_products                       │
│                                                     │
│  [derived tables — agents write, routers read]      │
│  raw_material_map     proposals                     │
│  substitution_groups  substitutions                 │
│  recommendations      agnes_suggestions             │
└───────────────────────▲─────────────────────────────┘
                        │ writes directly (bypass repo)
┌───────────────────────┴─────────────────────────────┐
│  AGENTS  (app/agents/)    background pipeline        │
│                                                     │
│  pipeline.py orchestrates on startup:               │
│    SubstitutionAgent  → substitution_groups         │
│    SearchEngine       → enrichment data (stub)      │
│    ProposalAgent      → proposals + suggestions     │
│    ComplianceAgent    → compliance fields (stub)    │
│    AuditorAgent       → confidence scoring (stub)   │
│                                                     │
│  AgnesAgent → live LLM, only called by POST /ask    │
└─────────────────────────────────────────────────────┘
```

**Core rules:**
- Routers call `repo.py` only. Never touch agents or write DB.
- Repo is SQL-only. No business logic. Returns Pydantic models.
- Agents call `db.py` directly for writes. Skip repo. Own their tables.
- IDs are plain integers matching Postgres `PRIMARY KEY`. No string prefixes.
- `POST /agnes/ask` is the only endpoint that runs a live agent.

---

## Setup

**Requirements:** Docker, Python 3.11+

```bash
# 1. Start Postgres
docker-compose up -d

# 2. Virtualenv + deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Env vars
cp .env.example .env   # default DATABASE_URL works with docker-compose

# 4. Run
uvicorn app.main:app --reload
```

On first boot: SQLite → Postgres migration runs automatically, then pipeline runs (all agents currently stubbed — no-op).

Interactive docs: `http://localhost:8000/docs`
OpenAPI schema: `http://localhost:8000/openapi.json`

Frontend generates TypeScript types from `/openapi.json` via `yarn gen:types`.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness probe → `{"status": "ok"}` |
| GET | `/companies` | All 61 portfolio companies |
| GET | `/companies/{id}` | Single company |
| GET | `/products` | All finished goods (`?company_id=` filter available) |
| GET | `/products/{id}` | Single product |
| GET | `/products/{id}/bom` | Bill of materials (list of raw-material IDs) |
| GET | `/raw-materials` | All 876 raw materials |
| GET | `/raw-materials/{id}` | Single raw material |
| GET | `/suppliers` | All 40 suppliers |
| GET | `/suppliers/{id}` | Single supplier |
| GET | `/proposals` | AI-generated proposals, sorted by `fragmentation_score` desc |
| GET | `/proposals/{id}` | Single proposal with evidence trail + tradeoffs |
| GET | `/substitutions` | Known raw-material substitution pairs |
| GET | `/agnes/suggestions?proposal_id=` | Pre-seeded questions for a proposal |
| POST | `/agnes/ask` | Ask Agnes a free-form question about a proposal |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app — lifespan, CORS, router wiring
│   ├── api/                 # HTTP routers — one file per domain, read-only
│   │   ├── companies.py
│   │   ├── products.py
│   │   ├── raw_materials.py
│   │   ├── suppliers.py
│   │   ├── proposals.py
│   │   ├── substitutions.py
│   │   └── agnes.py
│   ├── data/
│   │   ├── db.py            # asyncpg connection pool (do not modify)
│   │   ├── repo.py          # all SQL reads — add new queries here
│   │   └── migration.py     # SQLite → Postgres migration (runs on first boot)
│   ├── schemas/             # Pydantic models — source of truth for wire format
│   │   ├── company.py
│   │   ├── product.py       # Product, BOM
│   │   ├── raw_material.py
│   │   ├── supplier.py
│   │   ├── proposal.py      # Proposal, EvidenceItem, ComplianceRequirement, Tradeoffs
│   │   ├── substitution.py
│   │   └── agnes.py         # AgnesAskRequest/Response, AgnesMessage
│   └── agents/
│       ├── pipeline.py      # orchestrator — uncomment lines to activate agents
│       ├── agnes.py         # live LLM agent — wire Claude API here
│       ├── substitution.py  # DB heuristic — writes substitution_groups + substitutions
│       ├── proposal.py      # rule-based stub — upgrade to LLM
│       ├── compliance.py    # stub
│       ├── search_engine.py # stub — web scraping goes here
│       └── auditor.py       # stub — hallucination checking goes here
├── init/
│   └── 01_schema.sql        # full Postgres schema with derived tables + pgvector
├── data/
│   └── db.sqlite            # source data, migrated to Postgres on boot
├── tests/                   # integration tests (server must be running)
│   ├── conftest.py          # requests session fixture
│   ├── test_health.py
│   ├── test_companies.py
│   ├── test_products.py
│   ├── test_raw_materials.py
│   └── test_suppliers.py
├── docker-compose.yml       # pgvector/pgvector:pg16
├── requirements.txt
└── .env.example
```

---

## Agents

Agents live in `app/agents/`. They write to DB directly and are called by `pipeline.py` on startup (or on demand).

| Agent | Status | Writes to | Notes |
|-------|--------|-----------|-------|
| `substitution.py` | Working | `substitution_groups`, `substitutions` | DB heuristic: same canonical name = substitutable |
| `proposal.py` | Stub | `proposals`, `agnes_suggestions` | Replace with LLM reasoning |
| `compliance.py` | Stub | `proposals` (compliance fields) | REACH/RoHS/allergen checks |
| `search_engine.py` | Stub | enrichment columns | Web scraping + PDF parsing |
| `auditor.py` | Stub | `proposals` (confidence) | Hallucination detection |
| `agnes.py` | Stub | — (live response) | Wire Claude API to activate |

**To activate an agent:**
```python
# app/agents/pipeline.py — uncomment the relevant line
await _step("ProposalAgent", proposal.run)
```

**To wire Agnes (Claude API):**
```bash
pip install anthropic
# add ANTHROPIC_API_KEY to .env
# implement app/agents/agnes.py — replace stub with Claude API call
```

---

## Tests

Sync integration tests using `requests`. No async, no mocking — tests hit the real server.

```bash
# Terminal 1 — server must be running
uvicorn app.main:app --reload

# Terminal 2
pytest tests/ -v
```

Tests cover only stable endpoints (companies, products, raw-materials, suppliers). Agnes/proposals/substitutions excluded — those shapes are still being finalized.

**21 tests covering:**
- HTTP status codes (200, 404)
- Exact counts from DB (61 companies, 149 products, 876 raw materials, 40 suppliers)
- Exact known values (company 1 = "21st Century", supplier 1 = "ADM", etc.)
- Schema shapes (correct field names and types)
- Query param filtering (`?company_id=`)

**Adding a test:**
```python
# tests/test_<domain>.py
from tests.conftest import get

def test_something(api):
    r = get(api, "/companies/1")
    assert r.status_code == 200
    assert r.json()["name"] == "21st Century"
```

---

## Database

Full schema in `init/01_schema.sql`. Uses pgvector extension for future semantic similarity search.

**Derived tables** (agents write, routers read):
- `raw_material_map` — flattened BOM view per company+ingredient+supplier. Rebuilt by `refresh_raw_material_map()` SQL function.
- `substitution_groups` — functional equivalence groups with pgvector embedding slot
- `proposals` — consolidation recommendations with evidence, tradeoffs, rollout plans
- `substitutions` — raw substitution pairs (from_rm → to_rm + reason)
- `agnes_suggestions` — pre-seeded chat questions per proposal

**Reset DB and re-run migration:**
```bash
docker-compose down -v && docker-compose up -d
uvicorn app.main:app --reload
```
