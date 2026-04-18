from __future__ import annotations
from pydantic import BaseModel


class RawMaterial(BaseModel):
    name: str
    supplier_count: int
    product_count: int
