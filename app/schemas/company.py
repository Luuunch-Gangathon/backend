from __future__ import annotations
from pydantic import BaseModel


class Company(BaseModel):
    id: int
    name: str
