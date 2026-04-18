from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FinishedGood(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str          # fg_db_{Product.Id}
    sku: str
    company_id: str


class FinishedGoodDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    sku: str
    company_id: str
    bom: list[str]   # raw-material IDs (ing_db_{Id})
