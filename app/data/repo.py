"""Repository layer — async PostgreSQL reads via asyncpg.

DB ID scheme on the wire:
  Company      → co_db_{companies.id}
  FinishedGood → fg_db_{products.id}
  RawMaterial  → ing_db_{products.id}
  Supplier     → sup_db_{suppliers.id}

Table names match the Postgres schema (lowercase, plural).
raw_material_map is a pre-computed derived table — use it for
canonical-name lookups instead of joining multiple tables.
"""

from __future__ import annotations

from typing import Optional

from app.schemas import (
    Company,
    CompanyDetail,
    FinishedGood,
    FinishedGoodDetail,
    RawMaterial,
    RawMaterialDetail,
    Supplier,
    SupplierDetail,
)

from . import db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _canonical(sku: str) -> str:
    """RM-C38-whey-protein-isolate-f910e5ae  →  whey-protein-isolate"""
    parts = sku.split("-")
    return "-".join(parts[2:-1])


def _human_name(sku: str) -> str:
    return " ".join(p.capitalize() for p in _canonical(sku).split("-"))


def _parse_int(prefixed: str, prefix: str) -> Optional[int]:
    """'ing_db_42' + 'ing_db_' → 42"""
    if prefixed.startswith(prefix):
        try:
            return int(prefixed[len(prefix):])
        except ValueError:
            pass
    return None


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------

async def list_companies() -> list[Company]:
    async with db.get_conn() as conn:
        rows = await conn.fetch("SELECT id, name FROM companies ORDER BY name")
    return [Company(id=f"co_db_{r['id']}", name=r["name"]) for r in rows]


async def list_products_by_company(company_id: str) -> list[FinishedGood]:
    db_id = _parse_int(company_id, "co_db_")
    if db_id is None:
        return []
    async with db.get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT id, sku, company_id FROM products
            WHERE company_id = $1 AND type = 'finished-good'
            ORDER BY sku
            """,
            db_id,
        )
    return [
        FinishedGood(id=f"fg_db_{r['id']}", sku=r["sku"], company_id=f"co_db_{r['company_id']}")
        for r in rows
    ]


async def get_company(company_id: str) -> Optional[CompanyDetail]:
    db_id = _parse_int(company_id, "co_db_")
    if db_id is None:
        return None
    async with db.get_conn() as conn:
        row = await conn.fetchrow("SELECT id, name FROM companies WHERE id = $1", db_id)
        if row is None:
            return None
        products = await conn.fetch(
            "SELECT id FROM products WHERE company_id = $1 AND type = 'finished-good'",
            db_id,
        )
    return CompanyDetail(
        id=f"co_db_{row['id']}",
        name=row["name"],
        product_ids=[f"fg_db_{p['id']}" for p in products],
    )


# ---------------------------------------------------------------------------
# Products (finished goods)
# ---------------------------------------------------------------------------

async def get_product(product_id: str) -> Optional[FinishedGoodDetail]:
    db_id = _parse_int(product_id, "fg_db_")
    if db_id is None:
        return None
    async with db.get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT id, sku, company_id FROM products WHERE id = $1 AND type = 'finished-good'",
            db_id,
        )
        if row is None:
            return None
        bom_rows = await conn.fetch(
            """
            SELECT p.id
            FROM boms b
            JOIN bom_components bc ON bc.bom_id = b.id
            JOIN products p ON p.id = bc.consumed_product_id
            WHERE b.produced_product_id = $1
            """,
            db_id,
        )
    return FinishedGoodDetail(
        id=f"fg_db_{row['id']}",
        sku=row["sku"],
        company_id=f"co_db_{row['company_id']}",
        bom=[f"ing_db_{r['id']}" for r in bom_rows],
    )


# ---------------------------------------------------------------------------
# Raw materials
# ---------------------------------------------------------------------------

async def list_raw_materials(
    name: Optional[str] = None,
    company_id: Optional[str] = None,
) -> list[RawMaterial]:
    async with db.get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT p.id, p.sku, p.company_id,
                   STRING_AGG(sp.supplier_id::text, ',') AS supplier_ids
            FROM products p
            LEFT JOIN supplier_products sp ON sp.product_id = p.id
            WHERE p.type = 'raw-material'
            GROUP BY p.id
            ORDER BY p.sku
            """
        )

    results = []
    for row in rows:
        canonical = _canonical(row["sku"])
        if name and name.lower() not in canonical.lower():
            continue
        cid = f"co_db_{row['company_id']}"
        if company_id and company_id != cid:
            continue
        sup_ids = (
            [f"sup_db_{s}" for s in row["supplier_ids"].split(",")]
            if row["supplier_ids"]
            else []
        )
        results.append(
            RawMaterial(
                id=f"ing_db_{row['id']}",
                sku=row["sku"],
                name=_human_name(row["sku"]),
                canonical_name=canonical,
                company_id=cid,
                supplier_ids=sup_ids,
            )
        )
    return results


async def get_raw_material(rm_id: str) -> Optional[RawMaterialDetail]:
    db_id = _parse_int(rm_id, "ing_db_")
    if db_id is None:
        return None
    async with db.get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT id, sku, company_id FROM products WHERE id = $1 AND type = 'raw-material'",
            db_id,
        )
        if row is None:
            return None
        sup_rows = await conn.fetch(
            "SELECT supplier_id FROM supplier_products WHERE product_id = $1",
            db_id,
        )
        product_rows = await conn.fetch(
            """
            SELECT DISTINCT b.produced_product_id
            FROM bom_components bc
            JOIN boms b ON b.id = bc.bom_id
            WHERE bc.consumed_product_id = $1
            """,
            db_id,
        )
    canonical = _canonical(row["sku"])
    return RawMaterialDetail(
        id=f"ing_db_{row['id']}",
        sku=row["sku"],
        name=_human_name(row["sku"]),
        canonical_name=canonical,
        company_id=f"co_db_{row['company_id']}",
        supplier_ids=[f"sup_db_{r['supplier_id']}" for r in sup_rows],
        used_in_product_ids=[f"fg_db_{r['produced_product_id']}" for r in product_rows],
        substitute_ids=[],   # filled by SubstitutionAgent via controller
        enriched=None,       # filled by SearchEngine
    )


# ---------------------------------------------------------------------------
# Substitution helper — uses raw_material_map derived table
# ---------------------------------------------------------------------------

async def get_same_canonical(canonical_name: str, exclude_id: str) -> list[str]:
    """Return IDs of raw materials sharing the same canonical ingredient name.

    Queries raw_material_map (pre-computed) for efficiency.
    Used by SubstitutionAgent to find substitution candidates.
    """
    exclude_db_id = _parse_int(exclude_id, "ing_db_")
    async with db.get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT raw_material_id
            FROM raw_material_map
            WHERE raw_material_name = $1
              AND raw_material_id != $2
            """,
            canonical_name,
            exclude_db_id,
        )
    return [f"ing_db_{r['raw_material_id']}" for r in rows]


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------

async def list_suppliers() -> list[Supplier]:
    async with db.get_conn() as conn:
        rows = await conn.fetch("SELECT id, name FROM suppliers ORDER BY name")
    return [Supplier(id=f"sup_db_{r['id']}", name=r["name"]) for r in rows]


async def get_supplier(supplier_id: str) -> Optional[SupplierDetail]:
    db_id = _parse_int(supplier_id, "sup_db_")
    if db_id is None:
        return None
    async with db.get_conn() as conn:
        row = await conn.fetchrow("SELECT id, name FROM suppliers WHERE id = $1", db_id)
        if row is None:
            return None
        rm_rows = await conn.fetch(
            "SELECT product_id FROM supplier_products WHERE supplier_id = $1",
            db_id,
        )
    return SupplierDetail(
        id=f"sup_db_{row['id']}",
        name=row["name"],
        raw_material_ids=[f"ing_db_{r['product_id']}" for r in rm_rows],
    )
