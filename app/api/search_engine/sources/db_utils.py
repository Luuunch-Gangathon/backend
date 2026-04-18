"""DB utilities for the search engine sources."""

from __future__ import annotations

import asyncio

from app.data import db


def parse_supplier_id(supplier_id: str) -> int:
    """Extract the raw DB ID from a prefixed supplier ID like 'sup_db_12'."""
    return int(supplier_id.replace("sup_db_", ""))


async def _get_supplier_names_async(raw_ids: list[int]) -> list[str]:
    """Async lookup of supplier names from Postgres."""
    async with db.get_conn() as conn:
        rows = await conn.fetch(
            "SELECT name FROM suppliers WHERE id = ANY($1::int[])",
            raw_ids,
        )
    return [row["name"] for row in rows]


def get_supplier_names(supplier_ids: list[str]) -> list[str]:
    """Look up supplier names from the DB given prefixed IDs."""
    if not supplier_ids:
        return []

    raw_ids = [parse_supplier_id(sid) for sid in supplier_ids]

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, _get_supplier_names_async(raw_ids)).result()
    else:
        return asyncio.run(_get_supplier_names_async(raw_ids))
