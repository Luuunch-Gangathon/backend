from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.data import repo
from app.schemas import Proposal, Decision, CreateDecisionRequest

router = APIRouter(prefix="/proposals", tags=["proposals"])


@router.get("", response_model=list[Proposal])
async def list_proposals() -> list[Proposal]:
    return await repo.list_proposals()


@router.get("/{proposal_id}", response_model=Proposal)
async def get_proposal(proposal_id: int) -> Proposal:
    proposal = await repo.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal


@router.post("/{proposal_id}/decision", response_model=Decision)
async def create_decision(proposal_id: int, body: CreateDecisionRequest) -> Decision:
    return await repo.create_decision(proposal_id, body.status, body.reason)


@router.get("/{proposal_id}/decision", response_model=Decision)
async def get_decision(proposal_id: int) -> Decision:
    decision = await repo.get_decision_by_proposal(proposal_id)
    if not decision:
        raise HTTPException(status_code=404, detail="No decision for this proposal")
    return decision
