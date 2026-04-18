# TBD — schema draft, subject to change as AgnesAgent is implemented.
# POST /agnes/ask currently returns a stub response.
# Likely additions: streaming support, tool_calls, evidence items in response.

from __future__ import annotations
from typing import Literal
from pydantic import BaseModel


class AgnesSuggestedQuestion(BaseModel):
    id: int
    question: str


class AgnesMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str


class AgnesAskRequest(BaseModel):
    proposal_id: int
    message: str
    history: list[AgnesMessage] = []


class AgnesAskResponse(BaseModel):
    reply: AgnesMessage
