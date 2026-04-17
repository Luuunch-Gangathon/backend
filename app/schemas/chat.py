from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from .evidence import EvidenceItem

MessageRole = Literal["user", "assistant", "system", "tool"]


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: MessageRole
    content: str
    tool_call_id: Optional[str] = None


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[Message]
    session_id: str


class TextEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["text"] = "text"
    content: str


class ToolCallEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["tool_call"] = "tool_call"
    name: str
    args: Any


class ToolResultEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["tool_result"] = "tool_result"
    name: str
    result: Any


class EvidenceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["evidence"] = "evidence"
    items: list[EvidenceItem]


class TraceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["trace"] = "trace"
    agent: Optional[str] = None
    step: str


class DoneEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["done"] = "done"


ChatEvent = Annotated[
    Union[
        TextEvent,
        ToolCallEvent,
        ToolResultEvent,
        EvidenceEvent,
        TraceEvent,
        DoneEvent,
    ],
    Field(discriminator="type"),
]
