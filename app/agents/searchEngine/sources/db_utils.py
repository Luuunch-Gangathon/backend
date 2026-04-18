"""DB utilities for the search engine sources."""

from __future__ import annotations

from app.data import db


def parse_supplier_id(supplier_id: str) -> int:
    """Extract the raw DB ID from a prefixed supplier ID like 'sup_db_12'."""
    return int(supplier_id.replace("sup_db_", ""))


async def get_supplier_names_async(raw_ids: list[int]) -> list[str]:
    """Async lookup of supplier names from Postgres.

    Called at the async boundary in enrich_and_store() before dispatching
    to the sync enrichment engine. Do not call from sync context.
    """
    async with db.get_conn() as conn:
        rows = await conn.fetch(
            "SELECT name FROM suppliers WHERE id = ANY($1::int[])",
            raw_ids,
        )
    return [row["name"] for row in rows]
