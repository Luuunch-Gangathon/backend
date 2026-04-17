"""Repository layer: DB-first with fixture fallback.

Template pattern for domain queries. Each public function here corresponds to
one read path used by a router. If a SQLite DB is present at
`data/db.sqlite`, merge rows from there with the hand-authored fixtures.
DB-derived rows are namespaced (e.g. `ing_db_<n>`) so they never collide
with fixture IDs.
"""

from __future__ import annotations

import sqlite3
from typing import Optional

from app.schemas import Ingredient

from . import db, fixtures


def _db_ingredients() -> list[Ingredient]:
    if not db.is_available():
        return []
    try:
        with db.get_conn() as conn:
            rows = conn.execute(
                "SELECT Id, SKU, CompanyId FROM Product WHERE Type = 'raw-material'"
            ).fetchall()
    except sqlite3.Error:
        return []
    return [
        Ingredient(
            id=f"ing_db_{row['Id']}",
            name=row["SKU"],
            canonical_name=None,
            company_id=f"co_db_{row['CompanyId']}",
            sku=row["SKU"],
        )
        for row in rows
    ]


def list_ingredients(
    name: Optional[str] = None, company_id: Optional[str] = None
) -> list[Ingredient]:
    merged = list(fixtures.INGREDIENTS) + _db_ingredients()
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
