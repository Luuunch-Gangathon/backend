from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class RawMaterial(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str           # rm_<n> (fixture) or rm_db_<n> (from DB)
    name: str
    canonical_name: Optional[str] = None
    company_id: str   # co_<n> (fixture) or co_db_<n> (from DB)
    sku: Optional[str] = None
