"""Repository layer: async PostgreSQL queries with fixture fallback.

Each public function here corresponds to one read path used by a router.
Fixtures still work as before — useful for tests and local dev without a DB.
DB rows are namespaced (e.g. `rm_db_<n>`) so they never collide with fixture IDs.
"""
from __future__ import annotations

import re
from typing import Optional

from app.schemas import RawMaterial, SimilarRawMaterial

from . import db, fixtures

SIMILARITY_THRESHOLD: float = 0.75  # cosine similarity cutoff (-1..1)


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


_DB_ID_RE = re.compile(r"^rm_db_(\d+)$")


async def find_similar_raw_materials(
    raw_material_id: str,
) -> list[SimilarRawMaterial]:
    """Return raw materials whose embedding is above SIMILARITY_THRESHOLD
    cosine-similar to the source id's embedding.

    DB-backed ids only (rm_db_<n>). Fixture ids and malformed ids return [].
    Source id is excluded from results.
    """
    m = _DB_ID_RE.match(raw_material_id)
    if not m:
        return []
    db_id = int(m.group(1))

    try:
        async with db.get_conn() as conn:
            rows = await conn.fetch(
                """
                WITH source AS (
                    SELECT sg.raw_material_name, sg.embedding
                    FROM raw_material_map rmm
                    JOIN substitution_groups sg
                      ON sg.raw_material_name = rmm.raw_material_name
                    WHERE rmm.raw_material_id = $1
                    LIMIT 1
                )
                SELECT rmm.raw_material_id,
                       1 - (sg.embedding <=> (SELECT embedding FROM source)) AS score
                FROM   substitution_groups sg
                JOIN   raw_material_map    rmm ON rmm.raw_material_name = sg.raw_material_name
                WHERE  sg.raw_material_name <> (SELECT raw_material_name FROM source)
                  AND  1 - (sg.embedding <=> (SELECT embedding FROM source)) >= $2
                ORDER  BY score DESC
                """,
                db_id,
                SIMILARITY_THRESHOLD,
            )
    except Exception:
        return []

    return [
        SimilarRawMaterial(
            raw_material_id=f"rm_db_{row['raw_material_id']}",
            similarity_score=float(row["score"]),
        )
        for row in rows
    ]
