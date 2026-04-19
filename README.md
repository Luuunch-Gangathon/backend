# Spherecast Supply Chain Co-Pilot — Backend

AI decision-support system for CPG sourcing: ingest BOM + supplier data, identify interchangeable ingredients via semantic similarity, score substitutes with a quantifiable 5-dimension compliance rubric, and reason about it through an autonomous chat agent with visible evidence trails.

---

## General Approach

Three-layer architecture:

**Layer 1 — Data Ingestion + Enrichment.** On startup, the system migrates the provided SQLite database into PostgreSQL, builds a flattened BOM view (`raw_material_map`), and seeds vector embeddings for all 876 raw materials. The SearchEngine then enriches each material through a waterfall of external sources (supplier websites, scientific databases, LLM knowledge), attaching structured specs with provenance metadata (source URL, confidence tier, raw excerpt).

**Layer 2 — Intelligence Engines.** Two engines work together. The *SearchEngine* converts enriched specs into 1536-dim vectors (OpenAI text-embedding-3-small), enabling pgvector cosine similarity search — "find ingredients that function like soy lecithin." The *Compliance Engine* takes those candidates and scores them via GPT-4o structured output against a 5-dimension rubric (functional equivalence, spec compatibility, regulatory fit, dietary compliance, certification match), each dimension 0–20, total 0–100. Every score is auditable.

**Layer 3 — Agnes, the Autonomous Agent.** An LLM-driven chat agent (GPT-4o-mini via LangChain) with 5 tools it calls autonomously — no hardcoded routing. Agnes decides which tools to invoke, chains them together, and returns a response with a visible reasoning trace (which tools called, what they returned).

---

## Requirements & Status

| # | Requirement | Type | Status |
|---|------------|------|--------|
| R1 | Ingest BOM and supplier data | FR | Done |
| R2 | Enrich materials with external knowledge | FR | Done |
| R3 | Identify interchangeable components | FR | Done |
| R4 | Infer compliance/quality bar per substitute | FR | Done |
| R5 | Score substitutes with explainable reasoning | FR | Done |
| R6 | Preserve evidence trails | FR | Done |
| R7 | Surface fragmentation across portfolio | FR | Done (data layer) |
| R8 | Consolidated sourcing proposals | FR | Partial (schema ready, agent pending) |
| R9 | Conversational reasoning interface | FR | Done |

---

## Architecture

```
Frontend (React)
    |
    |--- POST /agnes/ask ---------> Agnes Agent (GPT-4o-mini, LangChain)
    |                                   |-- tool: search_material --> SearchEngine waterfall
    |                                   |-- tool: check_compliance -> Compliance Agent (GPT-4o)
    |                                   |-- tool: show_bom --------> repo.get_bom()
    |                                   |-- tool: show_company ----> repo.get_company()
    |                                   |-- tool: search_all ------> SearchEngine.run_all()
    |                                   |-- RAG context (auto-injected into system prompt)
    |
    |--- GET /products, /raw-materials, /companies, /suppliers --> repo.py --> DB
    |--- POST /compliance/{product_id}/{rm_id}/candidates ------> Compliance Agent
    |--- GET /raw-materials/{id}/substitutes -------------------> pgvector search
    |--- POST /raw-materials/{id}/enrich -----------------------> SearchEngine.run_one()
    |
    v
PostgreSQL + pgvector
    |-- companies, products, boms, bom_components, suppliers (migrated from SQLite)
    |-- raw_material_map (flattened BOM: material x company x supplier)
    |-- substitution_groups (enriched specs + 1536-dim embeddings)
    |-- substitutions, proposals (scored pairs, sourcing recommendations)

Enrichment Sources (waterfall, trust-tiered):
    verified:    supplier_website (crawl4ai + Claude Haiku)
    inferred:    llm_knowledge (Claude Haiku, training data only)
    speculative: llm_general_fallback (Claude Haiku, best-effort)
    [disabled]:  chebi, openfda, open_food_facts, nih_dsld, foodb, web_search
```

---

## What Worked

**Enrichment waterfall with trust tiers.** Config-driven: add a source by editing one file (`config.py`). Each property value carries provenance (source name, URL, excerpt, confidence). The engine calls each handler at most once and caches results across properties.

**Quantifiable compliance scoring.** The 5-dimension rubric (functional equivalence, spec compatibility, regulatory fit, dietary compliance, certification match) makes every score auditable. Judges can see *why* 72 and not 85: "dietary_compliance: 12/20 — introduces soy allergen not present in original." GPT-4o structured output enforces the schema.

**Autonomous agent loop.** Agnes uses LangChain `bind_tools()` — the LLM decides which tools to call, not hardcoded routing. Multi-step reasoning works: LLM calls `show_bom`, then `check_compliance`, then synthesizes. Reasoning trace is returned to frontend.

**Two-phase embedding strategy.** Name-only vectors seeded on startup (fast, cheap) so similarity search works immediately. Enrichment upgrades vectors with spec-based embeddings later. `store_embedding` always overwrites; `store_name_only_embedding` never does.

**Evidence trails everywhere.** Every enriched property is wrapped in `PropertyResult{value, confidence, source_name, source_url, raw_excerpt}`. Confidence maps to trust tiers. URLs are clickable (FDA pages, ChEBI terms, supplier product pages).

---

## What Did Not Work / Known Gaps

**ProposalAgent not implemented.** R8 (consolidated sourcing proposals) is partially realized: the `proposals` table with all fields (headline, tradeoffs, rollout plans, evidence, compliance requirements) is defined, Pydantic schemas exist, but no agent populates the table. API endpoints return empty results.

**Most enrichment sources disabled.** Due to API reliability and relevance tuning, only `supplier_website`, `llm_knowledge`, and `llm_general_fallback` are active. ChEBI, OpenFDA, Open Food Facts, NIH DSLD, FooDB, and web_search are implemented but commented out in `config.py`. This means specs are thinner than intended — many properties filled by LLM inference rather than authoritative databases.

**Substitution group clustering not implemented.** `substitution_groups.group_name` and `reasoning` columns exist but are never written. Materials are found by vector similarity, not by pre-computed groups.

**In-memory session storage.** Agnes chat history is stored in a Python dict — lost on server restart. No persistence to DB.

**Dependency conflict.** `crawl4ai` requires `openai>=2.x` via `litellm`, but `langchain-openai` caps at `<2.0.0`. Current state works (openai 1.x installed), but crawl4ai's litellm features may break at runtime.

---

## How We Would Improve

1. **Enable all enrichment sources** — uncomment chebi, openfda, open_food_facts in `config.py`. Adds authoritative data for functional roles, allergens, regulatory status. Requires tuning for API reliability.

2. **Implement ProposalAgent** — combine fragmentation data (`raw_material_map` queries: "same ingredient, multiple suppliers across companies") with compliance scores to generate written proposals with tradeoffs and rollout plans. Table schema is ready.

3. **Persist chat sessions** — move from `_sessions` dict to Postgres. Table already exists (`agnes_suggestions`), just needs a `chat_history` table.

4. **Populate benchmark dataset** — `knowledge/benchmark/compliance_cases.json` has the template. Need 10–15 real cases with known-good substitutes to measure precision/recall/F1.

5. **Streaming responses** — Agnes currently waits for the full agent loop to complete. SSE streaming would show tool calls in real-time.

6. **Scoring rubric refinement** — current 5-dimension rubric is a first pass. With real benchmark data, weights could be tuned (e.g., regulatory_fit may matter more than certification_match for food products).

7. **Resolve dependency conflict** — upgrade `langchain-openai` to 0.4.x to support `openai>=2.x` and eliminate the crawl4ai/litellm conflict.

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
# edit .env:
#   OPENAI_API_KEY      — embeddings + Agnes chat + compliance scoring
#   ANTHROPIC_API_KEY   — SearchEngine LLM enrichment (supplier_website, llm_knowledge)
#   SKIP_SEARCH_ENGINE=true  — skip enrichment on startup (faster local dev)

# 4. Run
uvicorn app.main:app --reload --log-level info
```

On first boot: SQLite migration -> name-only embeddings seeded -> SearchEngine enrichment runs.

Interactive docs: `http://localhost:8000/docs`

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness probe |
| GET | `/companies`, `/companies/{id}` | Portfolio companies |
| GET | `/products`, `/products/{id}`, `/products/{id}/bom` | Finished goods + BOM |
| GET | `/raw-materials`, `/raw-materials/{id}` | Raw materials with supplier/product counts |
| GET | `/raw-materials/{id}/substitutes` | pgvector similarity candidates |
| GET | `/raw-materials/{id}/suppliers` | Suppliers for a material |
| GET | `/raw-materials/{id}/companies` | Companies using a material |
| GET | `/raw-materials/{id}/finished-goods` | Products containing a material |
| POST | `/raw-materials/{id}/enrich` | Trigger on-demand enrichment |
| GET | `/suppliers`, `/suppliers/{id}` | Suppliers |
| POST | `/compliance/{product_id}/{rm_id}/candidates` | Score specific candidates |
| GET | `/compliance/{product_id}/{rm_id}` | Score all substitutes for a material in a product |
| GET | `/compliance/{product_id}` | Score all materials in a product's BOM |
| GET | `/proposals`, `/proposals/{id}` | Sourcing proposals (stub) |
| GET | `/substitutions` | Scored substitution pairs |
| POST | `/agnes/ask` | Autonomous AI chat with tool calling |
| GET | `/agnes/suggestions` | Pre-seeded chat questions |

---

## Compliance Scoring Rubric

Each substitute is scored across 5 dimensions (0-20 each, total 0-100):

| Dimension | What it measures |
|-----------|-----------------|
| `functional_equivalence` | Same functional role in the formulation |
| `spec_compatibility` | Physical/chemical overlap (form, grade, origin) |
| `regulatory_fit` | GRAS, recalls, regulatory pathway alignment |
| `dietary_compliance` | Preserves dietary claims (vegan, halal, allergens) |
| `certification_match` | Retains certifications (organic, non-GMO, etc.) |

Response includes `score_breakdown` so every number is traceable.

---

## Benchmark

```bash
python scripts/benchmark.py          # default K=3
python scripts/benchmark.py --k 5    # override K
```

- Dataset: `knowledge/benchmark/compliance_cases.json`
- Results: `knowledge/benchmark/results.json` + `results.md`
- Metrics: Precision@K, Recall@K, F1@K, MRR, NDCG@K
- Docs: `knowledge/benchmark/README.md`

---

## Tests

```bash
# Search engine tests (no server needed)
pytest tests/search_engine/ -q

# Integration tests (server + DB must be running)
uvicorn app.main:app --reload
pytest tests/ -q
```

Pre-commit hook: `git config core.hooksPath .githooks`

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app + lifespan (startup pipeline)
│   ├── api/                     # Routers (one file per domain)
│   │   ├── companies.py, products.py, raw_materials.py, suppliers.py
│   │   ├── compliance.py        # Compliance scoring endpoints
│   │   ├── proposals.py         # Stub
│   │   ├── substitutions.py     # Stub
│   │   └── agnes.py             # Chat endpoint
│   ├── data/
│   │   ├── db.py                # asyncpg connection pool
│   │   ├── repo.py              # All SQL reads
│   │   ├── rag.py               # Embedding storage + semantic search
│   │   └── migration.py         # SQLite -> Postgres on first boot
│   ├── schemas/                 # Pydantic models (source of truth for API types)
│   │   ├── compliance.py        # SubstituteProposal + ScoreBreakdown
│   │   └── ...
│   ├── prompts/                 # Jinja2 templates
│   │   ├── system/agnes.j2      # Agnes system prompt
│   │   ├── system/compliance.j2 # 5-dimension scoring rubric
│   │   └── user/compliance_rank.j2
│   └── agents/
│       ├── pipeline.py          # Startup: runs SearchEngine
│       ├── agnes.py             # Autonomous chat agent (LangChain + tools)
│       ├── search_engine.py     # Orchestrates enrichment + embedding
│       ├── searchEngine/        # Waterfall engine + source handlers
│       │   ├── engine.py        # Property-by-property waterfall loop
│       │   ├── config.py        # Active sources + trust tiers
│       │   └── sources/         # supplier_website, llm_knowledge, etc.
│       └── compliance.py        # GPT-4o substitute scoring with rubric
├── knowledge/
│   └── benchmark/               # Evaluation suite
│       ├── compliance_cases.json
│       ├── results.json, results.md
│       └── README.md
├── scripts/benchmark.py         # Benchmark runner
├── init/01_schema.sql           # Full Postgres schema
├── database/db.sqlite           # Provided data
├── tests/
├── docker-compose.yml
└── requirements.txt
```
