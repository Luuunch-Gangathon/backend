from __future__ import annotations
from pydantic import BaseModel


class Supplier(BaseModel):
    id: int
    name: str
