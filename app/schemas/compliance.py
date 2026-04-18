from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class SubstituteProposal(BaseModel):
    id: int
    score: int      # 0–100
    reasoning: str


class ComplianceResult(BaseModel):
    raw_material_id: int
    proposal: Optional[SubstituteProposal] = None


class SubstituteScoreRequest(BaseModel):
    candidate_ids: list[int]
