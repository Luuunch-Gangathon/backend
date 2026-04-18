from __future__ import annotations
from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel


class CreateDecisionRequest(BaseModel):
    status: Literal["accepted", "rejected"]
    reason: Optional[str] = None


class Decision(BaseModel):
    id: int
    proposal_id: int
    status: Literal["accepted", "rejected"]
    reason: Optional[str] = None
    created_at: datetime
