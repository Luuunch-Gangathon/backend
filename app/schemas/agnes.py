from __future__ import annotations
from typing import Literal
from pydantic import BaseModel
from .tool_results import ToolCall


class AgnesMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str
    reasoning_steps: list[str] | None = None
    cited_evidence_indices: list[int] | None = None


class AgnesAskRequest(BaseModel):
    message: str
    session_id: str | None = None


class AgnesAskResponse(BaseModel):
    reply: AgnesMessage
    session_id: str
    tool_calls: list[ToolCall] = []
