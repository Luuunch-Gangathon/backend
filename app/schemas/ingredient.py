"""Ingredient schema.

ID scheme (used across all schemas):
- Ingredient IDs:          ``ing_<n>``   (e.g. ``ing_1``)
- Supplier IDs:            ``sup_<n>``   (e.g. ``sup_1``)
- Company IDs:             ``co_<n>``    (e.g. ``co_1``)
- ConsolidationGroup IDs:  ``cg_<n>``    (e.g. ``cg_1``)

Rows sourced from ``data/db.sqlite`` are namespaced with a ``_db`` infix
(``ing_db_<Product.Id>``, ``sup_db_<Supplier.Id>``, ``co_db_<Company.Id>``) so
they never collide with the hand-authored fixture IDs that the frontend mocks
already reference.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class Ingredient(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    canonical_name: Optional[str] = None
    company_id: str
    sku: Optional[str] = None
