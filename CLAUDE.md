# Backend — Spherecast Supply Chain Co-Pilot

FastAPI service implementing the contract in `../frontend/knowledge/api-contract.md`.

## Type generation flow

The backend is the **source of truth for shared types**. Pydantic models in `app/schemas/` are mirrored 1:1 into the frontend's `lib/types.ts` by `scripts/generate_ts_types.py`.

**Run it after any change under `app/schemas/`:**
```bash
source .venv/bin/activate
python scripts/generate_ts_types.py
```
It overwrites `../frontend/lib/types.ts`. Commit the regenerated file in the frontend repo.

### What the generator emits
- Literal aliases: `SourceType`, `MessageRole`
- Models (in declared order): `Ingredient`, `Supplier`, `ConsolidationGroup`, `EvidenceItem`, `EvidenceBundle`, `Message`, `ComplianceInput`, `ComplianceResult`, `ChatRequest`
- A hand-written `CHAT_EVENTS_BLOCK` constant (in the generator itself) appending the SSE event union: `TextEvent`, `ToolCallEvent`, `ToolResultEvent`, `EvidenceEvent`, `TraceEvent`, `DoneEvent`, and the `ChatEvent` discriminated union

### Why ChatEvent is a static block, not generated
Backend models the union as a Pydantic `Annotated[Union[...], Field(discriminator="type")]` (`app/schemas/chat.py`). The generator's model walker doesn't render discriminated unions, so the TS equivalent is hard-coded in `CHAT_EVENTS_BLOCK` inside `scripts/generate_ts_types.py`. **If you add/rename a ChatEvent variant in `app/schemas/chat.py`, update `CHAT_EVENTS_BLOCK` in the generator too** — they must stay in sync by hand.

### Contract quirks to preserve
- `ComplianceResult.passed: bool = Field(alias="pass")` — `pass` is a Python keyword. The router MUST return `JSONResponse(result.model_dump(by_alias=True))` so the wire key is `pass`, not `passed`. See `app/api/enrichment.py`.
- `/chat` is SSE: `data: <json>\n\n` frames, headers `Cache-Control: no-cache`, `Connection: keep-alive`, `X-Accel-Buffering: no`, terminated by `{"type":"done"}`.
- CORS allows `http://localhost:3000` only (`app/main.py`).
- IDs are strings: `ing_*`, `sup_*`, `cg_*`, `co_*`. Never raw ints on the wire.

## Run locally
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
