from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class Supplier(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    certifications: list[str]
    lead_time_days: Optional[int] = None
    moq: Optional[int] = None
    country: Optional[str] = None
