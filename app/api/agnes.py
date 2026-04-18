from __future__ import annotations
from fastapi import APIRouter
from app.data import repo
from app.agents.agnes import ask
from app.schemas import AgnesSuggestedQuestion, AgnesAskRequest, AgnesAskResponse

router = APIRouter(prefix="/agnes", tags=["agnes"])


@router.get("/suggestions", response_model=list[AgnesSuggestedQuestion])
async def get_suggestions(proposal_id: int) -> list[AgnesSuggestedQuestion]:
    return await repo.list_agnes_suggestions(proposal_id)


@router.post("/ask", response_model=AgnesAskResponse)
async def ask_agnes(req: AgnesAskRequest) -> AgnesAskResponse:
    return await ask(req.proposal_id, req.message, req.history)
