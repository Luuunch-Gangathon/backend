from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.data import repo
from app.schemas import Proposal

router = APIRouter(prefix="/proposals", tags=["proposals"])


@router.get("", response_model=list[Proposal])
async def list_proposals() -> list[Proposal]:
    return []


@router.get("/{proposal_id}", response_model=Proposal)
async def get_proposal(proposal_id: int) -> Proposal:
    raise HTTPException(status_code=404, detail="Proposal not found")
