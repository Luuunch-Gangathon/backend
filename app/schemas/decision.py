from __future__ import annotations
from typing import Literal
from pydantic import BaseModel


class DecisionCreate(BaseModel):
    session_id: str
    status: Literal["accepted", "declined"]
    original_raw_material_name: str
    substitute_raw_material_name: str
    product_sku: str | None = None
    score: int
    reasoning: str


class Decision(BaseModel):
    id: int
    session_id: str
    status: str
    original_raw_material_name: str
    substitute_raw_material_name: str
    product_sku: str | None = None
    score: int
    reasoning: str
