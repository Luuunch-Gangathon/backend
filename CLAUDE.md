# Backend — Spherecast Supply Chain Co-Pilot

FastAPI service implementing the contract in `../frontend/knowledge/api-contract.md`.

## Type generation flow

Pydantic models in `app/schemas/` are the source of truth for REST types.
The frontend consumes them via FastAPI's built-in `/openapi.json`, generated
into TypeScript by [`openapi-typescript`](https://www.npmjs.com/package/openapi-typescript).

**After any change under `app/schemas/`**, restart the backend, then from the
frontend:
```bash
cd ../frontend
npm run gen:types   # reads http://localhost:8000/openapi.json
```

### SSE events are hand-mirrored
`ChatEvent` and its variants live in `app/schemas/chat.py` as a Pydantic
`Annotated[Union[...], Field(discriminator="type")]`. OpenAPI does not describe
SSE payload shapes, so the TS equivalent is hand-written in
`../frontend/lib/types.ts` (the SSE block at the bottom of the file). **If you
add or rename a ChatEvent variant here, mirror the change in the frontend's
`lib/types.ts`.**

### Contract quirks to preserve
- `ComplianceResult.passed: bool = Field(alias="pass")` — `pass` is a Python
  keyword. The router MUST return `JSONResponse(result.model_dump(by_alias=True))`
  so the wire key is `pass`, not `passed`. See `app/api/enrichment.py`.
- `/chat` is SSE: `data: <json>\n\n` frames, headers `Cache-Control: no-cache`,
  `Connection: keep-alive`, `X-Accel-Buffering: no`, terminated by
  `{"type":"done"}`.
- CORS allows `http://localhost:3000` only (`app/main.py`).
- IDs are strings: `ing_*`, `sup_*`, `cg_*`, `co_*`. Never raw ints on the wire.

## Run locally
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
