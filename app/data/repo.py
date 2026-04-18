"""Repository layer — all DB reads. No business logic. No agent calls.

All IDs are plain integers matching Postgres PRIMARY KEY.
"""

from __future__ import annotations

import re
from typing import Optional

from app.schemas import (
    Company,
    Product,
    BOM,
    RawMaterial,
    SimilarRawMaterial,
    Supplier,
)

from . import db

SIMILARITY_THRESHOLD: float = 0.75  # cosine similarity cutoff (-1..1)


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------

async def list_companies() -> list[Company]:
    async with db.get_conn() as conn:
        rows = await conn.fetch("SELECT id, name FROM companies ORDER BY name")
    return [Company(id=r["id"], name=r["name"]) for r in rows]


async def get_company(company_id: int) -> Optional[Company]:
    async with db.get_conn() as conn:
        row = await conn.fetchrow("SELECT id, name FROM companies WHERE id = $1", company_id)
    return Company(id=row["id"], name=row["name"]) if row else None


# ---------------------------------------------------------------------------
# Products (finished goods)
# ---------------------------------------------------------------------------

async def list_products(company_id: Optional[int] = None) -> list[Product]:
    async with db.get_conn() as conn:
        if company_id is not None:
            rows = await conn.fetch(
                "SELECT id, sku, company_id FROM products WHERE type = 'finished-good' AND company_id = $1 ORDER BY sku",
                company_id,
            )
        else:
            rows = await conn.fetch(
                "SELECT id, sku, company_id FROM products WHERE type = 'finished-good' ORDER BY sku"
            )
    return [Product(id=r["id"], sku=r["sku"], company_id=r["company_id"]) for r in rows]


async def get_product(product_id: int) -> Optional[Product]:
    async with db.get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT id, sku, company_id FROM products WHERE id = $1 AND type = 'finished-good'",
            product_id,
        )
    return Product(id=row["id"], sku=row["sku"], company_id=row["company_id"]) if row else None


async def get_product_by_sku(sku: str) -> Optional[Product]:
    """Look up a finished-good product by partial SKU match."""
    async with db.get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT id, sku, company_id FROM products WHERE type = 'finished-good' AND sku ILIKE $1 LIMIT 1",
            f"%{sku}%",
        )
    return Product(id=row["id"], sku=row["sku"], company_id=row["company_id"]) if row else None


async def get_bom(product_id: int) -> Optional[BOM]:
    async with db.get_conn() as conn:
        bom_row = await conn.fetchrow(
            "SELECT id FROM boms WHERE produced_product_id = $1", product_id
        )
        if bom_row is None:
            return None
        rm_rows = await conn.fetch(
            """
            SELECT p.id
            FROM bom_components bc
            JOIN products p ON p.id = bc.consumed_product_id
            WHERE bc.bom_id = $1
            """,
            bom_row["id"],
        )
    return BOM(
        id=bom_row["id"],
        produced_product_id=product_id,
        consumed_raw_material_ids=[r["id"] for r in rm_rows],
    )


# ---------------------------------------------------------------------------
# Raw materials
# ---------------------------------------------------------------------------

async def list_raw_materials() -> list[RawMaterial]:
    async with db.get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT
                p.id,
                p.sku,
                COALESCE(sup.cnt, 0) AS suppliers_count,
                COALESCE(used.cnt, 0) AS used_products_count
            FROM products p
            LEFT JOIN (
                SELECT product_id, COUNT(DISTINCT supplier_id) AS cnt
                FROM supplier_products
                GROUP BY product_id
            ) sup ON sup.product_id = p.id
            LEFT JOIN (
                SELECT bc.consumed_product_id AS product_id,
                       COUNT(DISTINCT b.produced_product_id) AS cnt
                FROM bom_components bc
                JOIN boms b ON b.id = bc.bom_id
                GROUP BY bc.consumed_product_id
            ) used ON used.product_id = p.id
            WHERE p.type = 'raw-material'
            ORDER BY p.sku
            """
        )
    return [
        RawMaterial(
            id=r["id"],
            sku=r["sku"],
            suppliers_count=r["suppliers_count"],
            used_products_count=r["used_products_count"],
        )
        for r in rows
    ]


async def get_raw_material(rm_id: int) -> Optional[RawMaterial]:
    async with db.get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT id, sku FROM products WHERE id = $1 AND type = 'raw-material'", rm_id
        )
    return RawMaterial(id=row["id"], sku=row["sku"]) if row else None


async def get_raw_material_by_name(name: str) -> Optional[RawMaterial]:
    """Look up a raw-material product by partial SKU/name match."""
    async with db.get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT id, sku FROM products WHERE type = 'raw-material' AND sku ILIKE $1 ORDER BY id LIMIT 1",
            f"%{name}%",
        )
    return RawMaterial(id=row["id"], sku=row["sku"]) if row else None


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


async def cosine_similarity_for_pairs(
    original_name: str,
    candidate_names: list[str],
) -> dict[str, float]:
    """Return cosine similarity between original and each candidate name.

    Uses substitution_groups embeddings. Returns {candidate_name: similarity}.
    Missing candidates get similarity 0.0.
    """
    if not candidate_names:
        return {}
    try:
        async with db.get_conn() as conn:
            rows = await conn.fetch(
                """
                WITH src AS (
                    SELECT embedding FROM substitution_groups WHERE raw_material_name = $1 LIMIT 1
                )
                SELECT sg.raw_material_name,
                       1 - (sg.embedding <=> (SELECT embedding FROM src)) AS similarity
                FROM substitution_groups sg
                WHERE sg.raw_material_name = ANY($2)
                  AND sg.embedding IS NOT NULL
                  AND (SELECT embedding FROM src) IS NOT NULL
                """,
                original_name,
                candidate_names,
            )
    except Exception:
        return {n: 0.0 for n in candidate_names}

    result = {n: 0.0 for n in candidate_names}
    for row in rows:
        result[row["raw_material_name"]] = float(row["similarity"])
    return result


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------

async def list_suppliers() -> list[Supplier]:
    async with db.get_conn() as conn:
        rows = await conn.fetch("SELECT id, name FROM suppliers ORDER BY name")
    return [Supplier(id=r["id"], name=r["name"]) for r in rows]


async def get_supplier(supplier_id: int) -> Optional[Supplier]:
    async with db.get_conn() as conn:
        row = await conn.fetchrow("SELECT id, name FROM suppliers WHERE id = $1", supplier_id)
    return Supplier(id=row["id"], name=row["name"]) if row else None


# ---------------------------------------------------------------------------
# RAG context — used by tools to enrich results with company/supplier data
# ---------------------------------------------------------------------------

async def get_material_specs(names: list[str]) -> dict[str, dict]:
    """Return the enriched spec JSON for each raw material name, keyed by name.

    Specs live in substitution_groups.spec (populated by rag.store_embedding).
    Missing names return no entry; callers should treat absence as unknown.
    """
    if not names:
        return {}
    async with db.get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT raw_material_name, spec
            FROM substitution_groups
            WHERE raw_material_name = ANY($1) AND spec IS NOT NULL
            """,
            names,
        )
    import json as _json
    result: dict[str, dict] = {}
    for r in rows:
        spec = r["spec"]
        if isinstance(spec, str):
            try:
                spec = _json.loads(spec)
            except _json.JSONDecodeError:
                continue
        result[r["raw_material_name"]] = spec or {}
    return result


async def get_product_dietary_profile(product_sku: str) -> dict:
    """Aggregate the dietary/allergen/certification profile of a finished product
    by examining every raw material in its BOM.

    Aggregation rules:
      - dietary_flags: AND across ingredients (product is vegan only if
        EVERY ingredient's dietary_flags.value.vegan is true).
      - allergens.contains: UNION (product contains X if ANY ingredient does).
      - allergens.free_from: INTERSECTION (product is free from X only if
        EVERY ingredient is free from X).
      - certifications: INTERSECTION (product carries cert X only if every
        ingredient is certified).
      - also extracts dietary hints from the product SKU itself (e.g.
        "FG-VEGAN-PROTEIN" → dietary_requirements.vegan = True).

    Returns a dict:
      {
        "product_sku": str,
        "dietary_requirements": {"vegan": bool, ...},
        "allergen_constraints": {"must_contain": [...], "must_be_free_of": [...]},
        "required_certifications": [...],
        "current_ingredients": [{"name": str, "spec": dict}, ...],
      }
    """
    profile = {
        "product_sku": product_sku,
        "dietary_requirements": {},
        "allergen_constraints": {"must_contain": [], "must_be_free_of": []},
        "required_certifications": [],
        "current_ingredients": [],
    }

    async with db.get_conn() as conn:
        ingredient_rows = await conn.fetch(
            """
            SELECT DISTINCT p_rm.sku AS raw_material_sku,
                   regexp_replace(
                       regexp_replace(p_rm.sku, '^RM-C[0-9]+-', ''),
                       '-[a-f0-9]{8}$', ''
                   ) AS raw_material_name
            FROM   products        p_fg
            JOIN   boms            b    ON b.produced_product_id  = p_fg.id
            JOIN   bom_components  bc   ON bc.bom_id              = b.id
            JOIN   products        p_rm ON p_rm.id                = bc.consumed_product_id
            WHERE  p_fg.sku ILIKE $1
              AND  p_fg.type = 'finished-good'
              AND  p_rm.type = 'raw-material'
            """,
            f"%{product_sku}%",
        )

    ingredient_names = [r["raw_material_name"] for r in ingredient_rows]
    specs = await get_material_specs(ingredient_names)

    for name in ingredient_names:
        profile["current_ingredients"].append({"name": name, "spec": specs.get(name, {})})

    # --- dietary flags: AND across ingredients (only keep if ALL true) ---
    dietary_votes: dict[str, list[bool]] = {}
    for spec in specs.values():
        flags = (spec.get("dietary_flags") or {}).get("value") or {}
        for key, val in flags.items():
            if val is True:
                dietary_votes.setdefault(key, []).append(True)
            elif val is False:
                dietary_votes.setdefault(key, []).append(False)
    n_ingredients = len(specs)
    if n_ingredients > 0:
        for key, votes in dietary_votes.items():
            if len(votes) == n_ingredients and all(votes):
                profile["dietary_requirements"][key] = True

    # --- allergens: union of contains, intersection of free_from ---
    contains_union: set[str] = set()
    free_from_sets: list[set[str]] = []
    for spec in specs.values():
        allergens = (spec.get("allergens") or {}).get("value") or {}
        contains_union.update(allergens.get("contains") or [])
        free_from_sets.append(set(allergens.get("free_from") or []))
    if free_from_sets:
        free_from_intersection = set.intersection(*free_from_sets)
    else:
        free_from_intersection = set()
    profile["allergen_constraints"] = {
        "must_contain": sorted(contains_union),
        "must_be_free_of": sorted(free_from_intersection),
    }

    # --- certifications: intersection ---
    cert_sets: list[set[str]] = []
    for spec in specs.values():
        certs = (spec.get("certifications") or {}).get("value") or []
        cert_sets.append(set(certs))
    if cert_sets:
        profile["required_certifications"] = sorted(set.intersection(*cert_sets))

    # --- SKU keyword hints (e.g. "FG-VEGAN-..." forces vegan=true) ---
    sku_upper = product_sku.upper()
    sku_hints = {
        "VEGAN": "vegan",
        "VEGETARIAN": "vegetarian",
        "HALAL": "halal",
        "KOSHER": "kosher",
        "GLUTEN-FREE": "gluten_free",
        "GLUTENFREE": "gluten_free",
        "ORGANIC": "organic",
    }
    for keyword, flag in sku_hints.items():
        if keyword in sku_upper:
            profile["dietary_requirements"][flag] = True

    return profile


async def get_material_context(names: list[str]) -> list[dict]:
    """Fetch company + supplier context for a list of raw material names.

    Queries raw_material_map for each name and returns a flat list of dicts:
    {raw_material_name, company_name, supplier_name, finished_product_sku}
    """
    if not names:
        return []
    async with db.get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT raw_material_name, company_name, supplier_name, finished_product_sku
            FROM raw_material_map
            WHERE raw_material_name = ANY($1)
            ORDER BY raw_material_name, company_name
            """,
            names,
        )
    return [dict(r) for r in rows]
