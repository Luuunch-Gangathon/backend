# Agnes chat schemas.
# Session-based: server stores history, frontend sends session_id each request.
# TBD: may add streaming, tool_calls, evidence items in future phases.

from __future__ import annotations
from typing import Literal
from pydantic import BaseModel


class AgnesSuggestedQuestion(BaseModel):
    id: int
    question: str


class AgnesMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str
    reasoning_steps: list[str] | None = None
    cited_evidence_indices: list[int] | None = None


class AgnesAskRequest(BaseModel):
    message: str
    session_id: str | None = None   # None = start new session


class AgnesAskResponse(BaseModel):
    reply: AgnesMessage
    session_id: str                  # frontend stores and sends back each request
