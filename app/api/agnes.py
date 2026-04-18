from __future__ import annotations

import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.data import repo
from app.agents.agnes import ask, ask_stream
from app.schemas import AgnesSuggestedQuestion, AgnesAskRequest, AgnesAskResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agnes", tags=["agnes"])


@router.get("/suggestions", response_model=list[AgnesSuggestedQuestion])
async def get_suggestions(proposal_id: int) -> list[AgnesSuggestedQuestion]:
    return await repo.list_agnes_suggestions(proposal_id)


@router.post("/ask", response_model=AgnesAskResponse)
async def ask_agnes(req: AgnesAskRequest) -> AgnesAskResponse:
    return await ask(req.message, req.session_id, req.product_id)


@router.post("/ask/stream")
async def ask_agnes_stream(req: AgnesAskRequest) -> StreamingResponse:
    """NDJSON stream of events — see agnes.ask_stream for event shapes."""

    async def body():
        try:
            async for event in ask_stream(req.message, req.session_id, req.product_id):
                yield json.dumps(event) + "\n"
        except Exception as exc:
            logger.exception("AgnesAgent: stream failed")
            yield json.dumps({"type": "error", "message": str(exc)}) + "\n"

    return StreamingResponse(body(), media_type="application/x-ndjson")
