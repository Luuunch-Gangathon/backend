from __future__ import annotations
from pydantic import BaseModel


class RawMaterial(BaseModel):
    id: int
    sku: str
    suppliers_count: int = 0
    used_products_count: int = 0


class SubstituteCandidate(BaseModel):
    """Vector-similarity candidate for a raw material. No LLM scoring applied."""
    id: int
    sku: str
    similarity_score: float
