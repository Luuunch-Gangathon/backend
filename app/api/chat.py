from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.data import fixtures, repo
from app.schemas import (
    ChatRequest,
    DoneEvent,
    EvidenceEvent,
    TextEvent,
    ToolCallEvent,
    ToolResultEvent,
)

router = APIRouter(tags=["chat"])


def _frame(event: BaseModel) -> str:
    return f"data: {event.model_dump_json()}\n\n"


async def _event_stream(_: ChatRequest) -> AsyncIterator[str]:
    groups = repo.list_consolidation_groups()
    lecithin = next((g for g in groups if g.canonical_name == "lecithin"), None)
    evidence_items = fixtures.EVIDENCE_BUNDLE.items

    yield _frame(TextEvent(content="Looking into lecithin consolidation across the portfolio…"))
    await asyncio.sleep(0.15)

    yield _frame(
        ToolCallEvent(name="get_consolidation", args={"canonical_name": "lecithin"})
    )
    await asyncio.sleep(0.15)

    yield _frame(
        ToolResultEvent(
            name="get_consolidation",
            result=lecithin.model_dump() if lecithin else None,
        )
    )
    await asyncio.sleep(0.15)

    yield _frame(
        TextEvent(content="\nThree companies source soy lecithin; one sources sunflower.")
    )
    await asyncio.sleep(0.15)

    yield _frame(EvidenceEvent(items=list(evidence_items)))
    await asyncio.sleep(0.15)

    yield _frame(DoneEvent())


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        _event_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
