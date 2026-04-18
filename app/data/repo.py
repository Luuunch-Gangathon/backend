"""Repository layer: async PostgreSQL queries with fixture fallback.

Each public function here corresponds to one read path used by a router.
Fixtures still work as before — useful for tests and local dev without a DB.
DB rows are namespaced (e.g. `rm_db_<n>`) so they never collide with fixture IDs.
"""
from __future__ import annotations

from typing import Optional

from app.schemas import RawMaterial

from . import db, fixtures


async def _db_raw_materials() -> list[RawMaterial]:
    try:
        async with db.get_conn() as conn:
            rows = await conn.fetch(
                "SELECT id, sku, company_id FROM products WHERE type = 'raw-material'"
            )
    except Exception:
        return []
    return [
        RawMaterial(
            id=f"rm_db_{row['id']}",
            name=row["sku"],
            canonical_name=None,
            company_id=f"co_db_{row['company_id']}",
            sku=row["sku"],
        )
        for row in rows
    ]


async def list_raw_materials(
    name: Optional[str] = None, company_id: Optional[str] = None
) -> list[RawMaterial]:
    merged = list(fixtures.RAW_MATERIALS) + await _db_raw_materials()
    if name:
        needle = name.lower()
        merged = [
            i
            for i in merged
            if needle in i.name.lower()
            or (i.canonical_name and needle in i.canonical_name.lower())
        ]
    if company_id:
        merged = [i for i in merged if i.company_id == company_id]
    return merged
