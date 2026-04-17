from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ConsolidationGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    canonical_name: str
    ingredient_ids: list[str]
    supplier_count: int
    fragmentation_score: float
    company_ids: list[str]
