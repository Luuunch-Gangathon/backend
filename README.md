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
# edit .env — set OPENAI_API_KEY (embeddings + Agnes chat)
#             set ANTHROPIC_API_KEY (SearchEngine LLM enrichment)

# 4. Enable git hook (once per clone)
git config core.hooksPath .githooks

# 5. Run
uvicorn app.main:app --reload --log-level info
```

On first boot: SQLite → Postgres migration → name-only embeddings seeded for all materials → SearchEngine enrichment scheduler started.

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
| POST | `/raw-materials/{id}/enrich` | Trigger on-demand enrichment for one material |
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
│       ├── pipeline.py      # startup scheduler: calls search_engine.run_all() hourly
│       ├── agnes.py         # agentic chat with tools
│       ├── search_engine.py # orchestrates enrichment waterfall → rag.store_embedding()
│       ├── searchEngine/    # waterfall engine + per-source handlers
│       │   ├── engine.py    # property-by-property waterfall loop
│       │   ├── config.py    # active sources + trust tiers
│       │   ├── handlers.py  # source fn registry
│       │   ├── models.py    # EnrichmentResult, PropertyResult
│       │   └── sources/     # supplier_website, llm_knowledge, llm_general_fallback, ...
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
| `search_engine.py` | Startup + on-demand | Runs `searchEngine` waterfall → `rag.store_embedding()` → rich vectors in `substitution_groups` |
| `compliance.py` | On-demand | Scores substitute candidates 0-100 via GPT-4o structured output |
| `agnes.py` | Live (POST /agnes/ask) | Keyword-triggered commands + RAG chat. Phase 2: agentic tool use. |

### SearchEngine flow

```
Startup (main.py lifespan)
  → rag.seed_name_only_embeddings()   — name-only baseline vectors for ALL materials
                                         batched into 1–2 OpenAI calls (256 names/call)
  → pipeline.start_scheduler()        — runs SearchEngine.run_all() hourly

SearchEngine.run_all() / run_one(name)
  → rag.get_unenriched_names()          — materials with embedding but spec IS NULL
  → for each name: searchEngine waterfall
      verified:    supplier_website, ChEBI, FooDB, NIH DSLD, OpenFDA, EFSA
      probable:    retail pages
      inferred:    llm_knowledge (Claude Haiku — no web, from training data)
      speculative: llm_general_fallback (Claude Haiku — best-effort inference)
  → rag.store_embedding(enriched_result)
      builds embedding text from spec (functional role, origin, dietary flags,
      allergens, certs, GRAS status, recalls, form/grade)
      → OpenAI text-embedding-3-small → stored in substitution_groups
      ON CONFLICT DO UPDATE — overwrites name-only baseline with spec-based vector
```

**Two-phase embedding strategy:**
- Phase 1 (startup): `seed_name_only_embeddings()` gives every material a cheap name-only vector so similarity search works immediately.
- Phase 2 (scheduled/on-demand): `run_all()` / `run_one()` upgrades to spec-based vectors as enrichment completes. `store_embedding()` always overwrites; `store_name_only_embedding()` never does.

**Requires** `ANTHROPIC_API_KEY` for LLM handlers. If unset, a `WARNING` is logged and properties stay null (name-only embedding is kept).

Entry points:
- `run_all()` — scheduled hourly, processes up to 10 materials (testing cap, see `search_engine.py`)
- `run_one(name)` — on-demand, single material; called by `POST /raw-materials/{id}/enrich` and Agnes `search <name>` command

### Agnes — keyword commands + RAG chat

**Phase 1 (current):** user types explicit commands. No LLM reasoning over tool selection.
**Phase 2 (next):** swap keyword matching for LangChain `bind_tools()` — LLM decides which tools to call.

Commands:
| Command | What it does | Status |
|---------|-------------|--------|
| `search <name>` | Enrich single material via SearchEngine waterfall | Working |
| `search all` | Enrich all unenriched materials | Working |
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
