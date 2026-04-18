from __future__ import annotations
from pydantic import BaseModel


class RawMaterial(BaseModel):
    id: int
    sku: str
    suppliers_count: int = 0
    used_products_count: int = 0
