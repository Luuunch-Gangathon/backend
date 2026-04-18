from __future__ import annotations
from fastapi import APIRouter
from app.agents.agnes import ask
from app.schemas import AgnesAskRequest, AgnesAskResponse

router = APIRouter(prefix="/agnes", tags=["agnes"])


@router.post("/ask", response_model=AgnesAskResponse)
async def ask_agnes(req: AgnesAskRequest) -> AgnesAskResponse:
    return await ask(req.message, req.session_id)
