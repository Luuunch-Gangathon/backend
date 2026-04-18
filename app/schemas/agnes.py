# Agnes chat schemas.
# Session-based: server stores history, frontend sends session_id each request.

from __future__ import annotations
from typing import Literal
from pydantic import BaseModel

from .tool_call import ToolCall


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
    product_id: int | None = None   # set on first request; stored in session


class AgnesAskResponse(BaseModel):
    reply: AgnesMessage
    session_id: str                  # frontend stores and sends back each request
    tool_calls: list[ToolCall] = []
