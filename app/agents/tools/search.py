"""search tool — semantic ingredient search backed by pgvector + DB context."""

from __future__ import annotations
import json
import logging

from app.data import rag, repo
from app.schemas import SearchHit

logger = logging.getLogger(__name__)


async def search(query: str, top_k: int = 8) -> list[SearchHit]:
    """Search for ingredients similar to query. Returns top_k hits with company/supplier context."""
    # Semantic search via embeddings
    results = await rag.search(query, top_k=top_k)

    # Name-exact fallback: also try matching query directly in raw_material_map
    if not results:
        context_rows = await repo.get_material_context([query])
        if context_rows:
            results = [{"raw_material_name": query, "similarity": 1.0, "spec": None}]

    if not results:
        return []

    names = [r["raw_material_name"] for r in results]
    context_rows = await repo.get_material_context(names)

    # Group context by material name
    by_name: dict[str, list[dict]] = {}
    for row in context_rows:
        by_name.setdefault(row["raw_material_name"], []).append(row)

    # Resolve raw_material_ids from DB
    hits: list[SearchHit] = []
    for result in results:
        name = result["raw_material_name"]
        rows = by_name.get(name, [])
        companies = sorted({r["company_name"] for r in rows if r.get("company_name")})
        suppliers = sorted({r["supplier_name"] for r in rows if r.get("supplier_name")})

        spec = result.get("spec")
        if isinstance(spec, str):
            try:
                spec = json.loads(spec)
            except (json.JSONDecodeError, TypeError):
                spec = None

        # Try to resolve the DB product ID for this name
        rm = await repo.get_raw_material_by_name(name)

        hits.append(SearchHit(
            raw_material_name=name,
            raw_material_id=rm.id if rm else None,
            similarity=float(result.get("similarity") or 0),
            spec=spec,
            companies=companies,
            suppliers=suppliers,
        ))

    logger.info("search tool: %r → %d hits", query[:60], len(hits))
    return hits
