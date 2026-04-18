from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Company(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str   # co_db_{Company.Id}
    name: str


class CompanyDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    product_ids: list[str]  # finished-good IDs belonging to this company
