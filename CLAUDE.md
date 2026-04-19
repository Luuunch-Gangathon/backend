# Backend — Spherecast Supply Chain Co-Pilot

FastAPI service implementing the contract in `../frontend/knowledge/api-contract.md`.

Every new endpoint follows this layering: schema → repo → router → main.

## Template pattern

1. **Schema** — `app/schemas/<domain>.py` defines a Pydantic `BaseModel`. Add the class to `app/schemas/__init__.py` so it's importable as `from app.schemas import <Name>`.
2. **Repo** — `app/data/repo.py` exposes a plain function (e.g. `list_raw_materials(...)`) that reads from Postgres via SQL queries.
3. **Router** — `app/api/<domain>.py` declares an `APIRouter` with `response_model=` on every route (required so the schema lands in `/openapi.json`).
4. **Wire** — `app.include_router(...)` in `app/main.py`.

Then the frontend runs `yarn gen:types` against `/openapi.json` and consumes the new type immediately.

## Type generation flow

Pydantic models in `app/schemas/` are the source of truth for REST types. The frontend consumes them via FastAPI's built-in `/openapi.json`, generated into TypeScript by [`openapi-typescript`](https://www.npmjs.com/package/openapi-typescript).

**After any change under `app/schemas/`**, restart the backend, then from the frontend:
```bash
cd ../frontend
yarn gen:types   # reads http://localhost:8000/openapi.json
```

## Conventions to preserve
- CORS allows `http://localhost:3000` only (`app/main.py`).
- IDs are plain Postgres integer PKs — emitted as `int` on the wire.
- `response_model=` is not optional — it's how schemas reach OpenAPI.
- For fields whose JSON key is a Python reserved word (e.g. `pass`), use
  `Field(alias="pass")` + `response_model_by_alias=True` on the route.

## Compliance scoring rubric

Compliance agent scores substitutes on 5 dimensions (0–20 each, total 0–100):

| Dimension | What it measures |
|-----------|-----------------|
| `functional_equivalence` | Same functional role in the formulation |
| `spec_compatibility` | Physical/chemical overlap (form, grade, origin) |
| `regulatory_fit` | GRAS, recalls, regulatory pathway alignment |
| `dietary_compliance` | Preserves dietary claims (vegan, halal, allergens) |
| `certification_match` | Retains certifications (organic, non-GMO, etc.) |

Response includes `score_breakdown` with per-dimension scores so every number is auditable.
Prompt: `app/prompts/system/compliance.j2`. Schema: `app/schemas/compliance.py`.

## Agnes chat agent

Fully autonomous tool-calling agent (LangChain bind_tools, GPT-4o-mini).
LLM decides which tools to call — no hardcoded routing.
Returns `reasoning_steps[]` showing which tools were called and their results.

Tools: `search_all_materials`, `search_material`, `show_bom`, `show_company`, `check_product_compliance`.

## Benchmark

```bash
python scripts/benchmark.py          # default K=3
python scripts/benchmark.py --k 5    # override K
```

Dataset: `knowledge/benchmark/compliance_cases.json`
Results: `knowledge/benchmark/results.json` + `results.md`

## Run locally
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
