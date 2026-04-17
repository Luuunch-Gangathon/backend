# API Contract — pointer

The canonical contract between this FastAPI backend and the Next.js frontend lives in the **frontend repo**:

- File: [`../../frontend/knowledge/api-contract.md`](../../frontend/knowledge/api-contract.md)
- URL (if browsing the frontend repo directly): `frontend/knowledge/api-contract.md`

This pointer exists so agents working in the backend repo find a `knowledge/` folder in the same place they'd expect it in the frontend. Read the linked file for endpoint shapes, the template pattern for adding endpoints, conventions, and resolved decisions.

## Why one canonical copy

Duplicating the contract across both repos invites drift. The frontend owns the file because that's where Pydantic-derived TypeScript types land (via `openapi-typescript` against `/openapi.json`) and where the contract is most often edited during UI work.

## Update flow

When you change something in `backend/app/schemas/` or add a new route that affects the wire format:

1. Edit the Pydantic model / router, restart uvicorn.
2. Update the description + examples in `../../frontend/knowledge/api-contract.md` if shapes, semantics, or IDs changed.
3. Frontend team runs `yarn gen:types` to regenerate `frontend/lib/types.generated.ts`.
