# Spherecast Supply Chain Co-Pilot — Backend

FastAPI backend for wAgent. Reads supply chain data from Postgres, enriches via SearchEngine on startup, and serves an AI chat (Agnes) with keyword-triggered commands for searching materials, checking compliance, and querying the database.

---

## Architecture

```
FRONTEND
    │
    ▼
┌──────────────────────────────────────────────────────┐
│  API ROUTERS  (app/api/)          read-only          │
│                                                      │
│  GET  /companies, /products, /raw-materials,         │
│       /suppliers, /proposals, /substitutions         │
│       → repo.py → DB                                 │
│                                                      │
│  POST /agnes/ask  → AgnesAgent                        │
│                     Phase 1: keyword-triggered cmds   │
│                     Phase 2: LLM decides (TODO)       │
│                                                      │
│                     Commands:                         │
│                     "search <name>"   → enrich 1      │
│                     "search all"      → enrich all    │
│                     "compliance X Y"  → score (TODO)  │
│                     "bom <id>"        → show BOM      │
│                     "company <id>"    → show company   │
│                     anything else     → chat + RAG    │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  POSTGRESQL                                           │
│                                                      │
│  [raw tables — from SQLite migration]                │
│  companies  products  boms  bom_components           │
│  suppliers  supplier_products                        │
│                                                      │
│  [derived tables]                                    │
│  raw_material_map       ← pre-joined flat view       │
│  substitution_groups    ← embeddings + specs          │
│  substitutions          ← scored pairs from compliance│
│  proposals              ← TBD                        │
│  agnes_suggestions      ← TBD                        │
└──────────────────────────▲───────────────────────────┘
                           │ writes
┌──────────────────────────┴───────────────────────────┐
│  AGENTS                                               │
│                                                      │
│  STARTUP (pipeline.py):                              │
│    SearchEngine.run_all()                            │
│      → for each unenriched material:                 │
│        web search → new info → updated raw material  │
│        → generate embedding → store in               │
│          substitution_groups                          │
│                                                      │
│  ON-DEMAND:                                          │
│    SearchEngine.run_one(name)  ← from chat/frontend  │
│    ComplianceAgent.rank()      ← from chat/frontend  │
└──────────────────────────────────────────────────────┘
```

**Core rules:**
- Routers call `repo.py` only. Never write DB.
- Agents write to DB directly via `db.py`.
- IDs are plain integers matching Postgres `PRIMARY KEY`.
- `POST /agnes/ask` is the only endpoint that runs agents (via keyword commands).
- SearchEngine runs once on startup for all materials. Can also be called on-demand for one material.
- ComplianceAgent is on-demand only — called from Agnes chat or frontend.

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
cp .env.example .env
# edit .env — set OPENAI_API_KEY (required for Agnes + SearchEngine)

# 4. Enable git hook (once per clone)
git config core.hooksPath .githooks

# 5. Run
uvicorn app.main:app --reload --log-level info
```

On first boot: SQLite → Postgres migration, then SearchEngine processes all unenriched materials.

**Git hook:** runs `pytest tests/` before every commit if server is up. Skips silently if server is down.
```bash
sh .githooks/pre-commit   # test without committing
```

Interactive docs: `http://localhost:8000/docs`

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness probe |
| GET | `/companies`, `/companies/{id}` | Portfolio companies |
| GET | `/products`, `/products/{id}`, `/products/{id}/bom` | Finished goods + BOM |
| GET | `/raw-materials`, `/raw-materials/{id}` | Raw materials |
| GET | `/suppliers`, `/suppliers/{id}` | Suppliers |
| GET | `/proposals`, `/proposals/{id}` | Consolidation proposals (TBD) |
| GET | `/substitutions` | Scored substitution pairs |
| GET | `/agnes/suggestions?proposal_id=` | Pre-seeded chat questions (TBD) |
| POST | `/agnes/ask` | AI chat — keyword commands + RAG-backed LLM |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py
│   ├── api/                 # routers — one file per domain
│   │   ├── companies.py
│   │   ├── products.py
│   │   ├── raw_materials.py
│   │   ├── suppliers.py
│   │   ├── proposals.py
│   │   ├── substitutions.py
│   │   └── agnes.py
│   ├── data/
│   │   ├── db.py            # asyncpg pool
│   │   ├── repo.py          # all SQL reads
│   │   ├── rag.py           # embedding storage + semantic search
│   │   └── migration.py     # SQLite → Postgres
│   ├── schemas/
│   │   ├── company.py, product.py, raw_material.py, supplier.py
│   │   ├── proposal.py, substitution.py, agnes.py
│   │   └── similar_raw_material.py
│   ├── prompts/             # Jinja2 templates
│   │   ├── loader.py        # render("system/agnes")
│   │   ├── system/agnes.j2, system/compliance.j2
│   │   └── user/compliance_rank.j2
│   └── agents/
│       ├── pipeline.py      # startup: SearchEngine.run_all()
│       ├── agnes.py         # agentic chat with tools
│       ├── search_engine.py # enrichment + embeddings
│       └── compliance.py    # GPT-4o substitute scoring
├── init/01_schema.sql
├── data/db.sqlite
├── tests/
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Agents

| Agent | Mode | What it does |
|-------|------|-------------|
| `search_engine.py` | Startup + on-demand | Enriches materials → generates embeddings → stores in `substitution_groups` |
| `compliance.py` | On-demand | Scores substitute candidates 0-100 via GPT-4o structured output |
| `agnes.py` | Live (POST /agnes/ask) | Keyword-triggered commands + RAG chat. Phase 2: agentic tool use. |

### SearchEngine flow

```
Raw Material name
  → Web Search (TODO: teammate implements)
  → New Information (specs, certs, allergens)
  → Updated Raw Material (stored in substitution_groups.spec)
  → Generate Embedding (rag.store_embedding())
  → Available for similarity search (pgvector)
```

Two entry points:
- `run_all()` — startup, processes all unenriched materials
- `run_one(name)` — on-demand, single material (from Agnes chat or frontend)

### Agnes — keyword commands + RAG chat

**Phase 1 (current):** user types explicit commands. No LLM reasoning over tool selection.
**Phase 2 (next):** swap keyword matching for LangChain `bind_tools()` — LLM decides which tools to call.

Commands:
| Command | What it does | Status |
|---------|-------------|--------|
| `search <name>` | Enrich single material via SearchEngine | Working (name-only fallback) |
| `search all` | Enrich all unenriched materials | Working (name-only fallback) |
| `compliance <rm_id> <product_id>` | Score substitutes via ComplianceAgent | TODO — teammate implements |
| `bom <product_id>` | Show BOM ingredients | Working |
| `company <company_id>` | Show company + products | Working |
| anything else | RAG-backed LLM chat | Working |

Example:
```
user: "search whey-protein-isolate"     → enriches + embeds that material
user: "bom 90"                          → shows ingredients for product 90
user: "tell me about lecithin"          → RAG search + LLM answers with DB context
```

**Session flow:**
```
POST /agnes/ask {message, session_id: null}  → new session
POST /agnes/ask {message, session_id: "..."}  → resume session
```

Server stores history in memory. Session cleared on restart.

---

## Prompts

Jinja2 templates in `app/prompts/`. Edit without touching Python.

```python
from app.prompts.loader import render
prompt = render("system/agnes")                    # static
prompt = render("user/compliance_rank", **kwargs)  # with variables
```

---

## Tests

```bash
# server must be running
uvicorn app.main:app --reload
pytest tests/ -v
```

21 integration tests on stable endpoints. Agnes/proposals/substitutions excluded.

---

## Database

Schema: `init/01_schema.sql`. pgvector extension enabled.

Key tables:
- `raw_material_map` — pre-joined BOM view. Rebuilt by `refresh_raw_material_map()`.
- `substitution_groups` — specs + pgvector embeddings. Written by SearchEngine.
- `substitutions` — scored from→to pairs. Written by ComplianceAgent.

Reset: `docker-compose down -v && docker-compose up -d`
