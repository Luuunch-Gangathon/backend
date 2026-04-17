"""Repository layer: DB-first with fixture fallback.

The SQLite schema in ``data/db.sqlite`` is narrower than the API contract —
it has no certifications, lead times, MOQ or country on suppliers, and no
``canonical_name`` on products. DB-derived rows are returned with best-effort
fields and empty supplier metadata; hand-authored fixtures cover the mock
IDs the frontend already expects.
"""

from __future__ import annotations

import sqlite3
from typing import Optional

from app.schemas import ConsolidationGroup, Ingredient, Supplier

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


def _db_suppliers_for(ingredient_id: str) -> list[Supplier]:
    if not ingredient_id.startswith("ing_db_") or not db.is_available():
        return []
    try:
        product_id = int(ingredient_id.removeprefix("ing_db_"))
    except ValueError:
        return []
    try:
        with db.get_conn() as conn:
            rows = conn.execute(
                """
                SELECT s.Id, s.Name
                FROM Supplier s
                JOIN Supplier_Product sp ON sp.SupplierId = s.Id
                WHERE sp.ProductId = ?
                """,
                (product_id,),
            ).fetchall()
    except sqlite3.Error:
        return []
    return [
        Supplier(
            id=f"sup_db_{row['Id']}",
            name=row["Name"],
            certifications=[],
            lead_time_days=None,
            moq=None,
            country=None,
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


def get_ingredient(ingredient_id: str) -> Optional[Ingredient]:
    for ingredient in list_ingredients():
        if ingredient.id == ingredient_id:
            return ingredient
    return None


def suppliers_for(ingredient_id: str) -> list[Supplier]:
    if ingredient_id in fixtures.SUPPLIERS_BY_INGREDIENT:
        return list(fixtures.SUPPLIERS_BY_INGREDIENT[ingredient_id])
    return _db_suppliers_for(ingredient_id)


def list_consolidation_groups() -> list[ConsolidationGroup]:
    return list(fixtures.CONSOLIDATION_GROUPS)


def get_consolidation_group(group_id: str) -> Optional[ConsolidationGroup]:
    for group in fixtures.CONSOLIDATION_GROUPS:
        if group.id == group_id:
            return group
    return None


def rank_suppliers(ingredient_id: str) -> list[Supplier]:
    suppliers = suppliers_for(ingredient_id)
    # best-first: more certifications, shorter lead time, lower MOQ.
    return sorted(
        suppliers,
        key=lambda s: (
            -len(s.certifications),
            s.lead_time_days if s.lead_time_days is not None else 10**9,
            s.moq if s.moq is not None else 10**9,
        ),
    )
