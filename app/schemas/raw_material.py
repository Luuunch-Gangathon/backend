from __future__ import annotations
from pydantic import BaseModel


class RawMaterial(BaseModel):
    id: int
    sku: str
