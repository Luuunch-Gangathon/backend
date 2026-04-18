from __future__ import annotations
from pydantic import BaseModel


class Product(BaseModel):
    id: int
    sku: str
    company_id: int


class BOM(BaseModel):
    id: int
    produced_product_id: int
    consumed_raw_material_ids: list[int]
