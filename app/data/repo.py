"""Repository layer: all DB reads go through here.

DB ID scheme on the wire:
  Company      → co_db_{Company.Id}
  FinishedGood → fg_db_{Product.Id}
  RawMaterial  → ing_db_{Product.Id}
  Supplier     → sup_db_{Supplier.Id}
"""

from __future__ import annotations

import sqlite3
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
    """Extract canonical ingredient name from SKU.

    RM-C38-whey-protein-isolate-f910e5ae  →  whey-protein-isolate
    """
    parts = sku.split("-")
    return "-".join(parts[2:-1])


def _human_name(sku: str) -> str:
    """Turn canonical name into a human-readable label."""
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

def list_companies() -> list[Company]:
    if not db.is_available():
        return []
    try:
        with db.get_conn() as conn:
            rows = conn.execute(
                "SELECT Id, Name FROM Company ORDER BY Name"
            ).fetchall()
    except sqlite3.Error:
        return []
    return [Company(id=f"co_db_{r['Id']}", name=r["Name"]) for r in rows]


def list_products_by_company(company_id: str) -> list[FinishedGood]:
    db_id = _parse_int(company_id, "co_db_")
    if db_id is None or not db.is_available():
        return []
    try:
        with db.get_conn() as conn:
            rows = conn.execute(
                "SELECT Id, SKU, CompanyId FROM Product WHERE CompanyId = ? AND Type = 'finished-good' ORDER BY SKU",
                (db_id,),
            ).fetchall()
    except sqlite3.Error:
        return []
    return [
        FinishedGood(id=f"fg_db_{r['Id']}", sku=r["SKU"], company_id=f"co_db_{r['CompanyId']}")
        for r in rows
    ]


def get_company(company_id: str) -> Optional[CompanyDetail]:
    db_id = _parse_int(company_id, "co_db_")
    if db_id is None or not db.is_available():
        return None
    try:
        with db.get_conn() as conn:
            row = conn.execute(
                "SELECT Id, Name FROM Company WHERE Id = ?", (db_id,)
            ).fetchone()
            if row is None:
                return None
            products = conn.execute(
                "SELECT Id FROM Product WHERE CompanyId = ? AND Type = 'finished-good'",
                (db_id,),
            ).fetchall()
    except sqlite3.Error:
        return None
    return CompanyDetail(
        id=f"co_db_{row['Id']}",
        name=row["Name"],
        product_ids=[f"fg_db_{p['Id']}" for p in products],
    )


# ---------------------------------------------------------------------------
# Products (finished goods)
# ---------------------------------------------------------------------------

def get_product(product_id: str) -> Optional[FinishedGoodDetail]:
    db_id = _parse_int(product_id, "fg_db_")
    if db_id is None or not db.is_available():
        return None
    try:
        with db.get_conn() as conn:
            row = conn.execute(
                "SELECT Id, SKU, CompanyId FROM Product WHERE Id = ? AND Type = 'finished-good'",
                (db_id,),
            ).fetchone()
            if row is None:
                return None
            bom_rows = conn.execute(
                """
                SELECT p.Id
                FROM BOM b
                JOIN BOM_Component bc ON bc.BOMId = b.Id
                JOIN Product p ON p.Id = bc.ConsumedProductId
                WHERE b.ProducedProductId = ?
                """,
                (db_id,),
            ).fetchall()
    except sqlite3.Error:
        return None
    return FinishedGoodDetail(
        id=f"fg_db_{row['Id']}",
        sku=row["SKU"],
        company_id=f"co_db_{row['CompanyId']}",
        bom=[f"ing_db_{r['Id']}" for r in bom_rows],
    )


# ---------------------------------------------------------------------------
# Raw materials
# ---------------------------------------------------------------------------

def list_raw_materials(
    name: Optional[str] = None,
    company_id: Optional[str] = None,
) -> list[RawMaterial]:
    """Return all raw materials with their supplier IDs.

    Filters are applied in Python (on canonical name) because the canonical
    name is derived from SKU structure, not a DB column.
    """
    if not db.is_available():
        return []
    try:
        with db.get_conn() as conn:
            # Single JOIN to fetch products + all their supplier IDs at once
            rows = conn.execute(
                """
                SELECT p.Id, p.SKU, p.CompanyId,
                       GROUP_CONCAT(sp.SupplierId) AS supplier_ids
                FROM Product p
                LEFT JOIN Supplier_Product sp ON sp.ProductId = p.Id
                WHERE p.Type = 'raw-material'
                GROUP BY p.Id
                ORDER BY p.SKU
                """
            ).fetchall()
    except sqlite3.Error:
        return []

    results = []
    for row in rows:
        canonical = _canonical(row["SKU"])
        if name and name.lower() not in canonical.lower():
            continue
        cid = f"co_db_{row['CompanyId']}"
        if company_id and company_id != cid:
            continue
        sup_ids = (
            [f"sup_db_{s}" for s in row["supplier_ids"].split(",")]
            if row["supplier_ids"]
            else []
        )
        results.append(
            RawMaterial(
                id=f"ing_db_{row['Id']}",
                sku=row["SKU"],
                name=_human_name(row["SKU"]),
                canonical_name=canonical,
                company_id=cid,
                supplier_ids=sup_ids,
            )
        )
    return results


def get_raw_material(rm_id: str) -> Optional[RawMaterialDetail]:
    db_id = _parse_int(rm_id, "ing_db_")
    if db_id is None or not db.is_available():
        return None
    try:
        with db.get_conn() as conn:
            row = conn.execute(
                "SELECT Id, SKU, CompanyId FROM Product WHERE Id = ? AND Type = 'raw-material'",
                (db_id,),
            ).fetchone()
            if row is None:
                return None

            sup_rows = conn.execute(
                "SELECT SupplierId FROM Supplier_Product WHERE ProductId = ?",
                (db_id,),
            ).fetchall()

            product_rows = conn.execute(
                """
                SELECT DISTINCT b.ProducedProductId
                FROM BOM_Component bc
                JOIN BOM b ON b.Id = bc.BOMId
                WHERE bc.ConsumedProductId = ?
                """,
                (db_id,),
            ).fetchall()
    except sqlite3.Error:
        return None

    canonical = _canonical(row["SKU"])

    return RawMaterialDetail(
        id=f"ing_db_{row['Id']}",
        sku=row["SKU"],
        name=_human_name(row["SKU"]),
        canonical_name=canonical,
        company_id=f"co_db_{row['CompanyId']}",
        supplier_ids=[f"sup_db_{s['SupplierId']}" for s in sup_rows],
        used_in_product_ids=[f"fg_db_{p['ProducedProductId']}" for p in product_rows],
        substitute_ids=[],   # filled in by SubstitutionAgent via controller
        enriched=None,       # filled in by SearchEngine
    )


# ---------------------------------------------------------------------------
# Substitution helper: raw materials with same canonical name (different company)
# ---------------------------------------------------------------------------

def get_same_canonical(canonical_name: str, exclude_id: str) -> list[str]:
    """Return IDs of raw materials sharing the same canonical ingredient name.

    Used by SubstitutionAgent to find substitution candidates.
    Filters by SKU pattern in SQL — canonical name occupies the middle
    segment: RM-C{n}-{canonical_name}-{hash}.
    """
    if not db.is_available():
        return []
    exclude_db_id = _parse_int(exclude_id, "ing_db_")
    pattern = f"%-{canonical_name}-%"
    try:
        with db.get_conn() as conn:
            rows = conn.execute(
                """
                SELECT Id FROM Product
                WHERE Type = 'raw-material'
                  AND SKU LIKE ?
                  AND Id != ?
                """,
                (pattern, exclude_db_id),
            ).fetchall()
    except sqlite3.Error:
        return []
    return [f"ing_db_{r['Id']}" for r in rows]


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------

def list_suppliers() -> list[Supplier]:
    if not db.is_available():
        return []
    try:
        with db.get_conn() as conn:
            rows = conn.execute("SELECT Id, Name FROM Supplier ORDER BY Name").fetchall()
    except sqlite3.Error:
        return []
    return [Supplier(id=f"sup_db_{r['Id']}", name=r["Name"]) for r in rows]


def get_supplier(supplier_id: str) -> Optional[SupplierDetail]:
    db_id = _parse_int(supplier_id, "sup_db_")
    if db_id is None or not db.is_available():
        return None
    try:
        with db.get_conn() as conn:
            row = conn.execute(
                "SELECT Id, Name FROM Supplier WHERE Id = ?", (db_id,)
            ).fetchone()
            if row is None:
                return None
            rm_rows = conn.execute(
                "SELECT ProductId FROM Supplier_Product WHERE SupplierId = ?",
                (db_id,),
            ).fetchall()
    except sqlite3.Error:
        return None
    return SupplierDetail(
        id=f"sup_db_{row['Id']}",
        name=row["Name"],
        raw_material_ids=[f"ing_db_{r['ProductId']}" for r in rm_rows],
    )
