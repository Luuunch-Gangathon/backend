"""AgnesAgent — domain-scoped chat via LangChain + OpenAI.

Session-based history: server stores conversation per session_id.
Frontend sends session_id each request — no full history transmission.
Sessions live in memory. Process restart clears all sessions.

Phase 1: simple chat, domain-scoped to supply chain.
Phase 2: add tools (query DB, run agents).
Phase 3: full agent orchestration.
"""

from __future__ import annotations
import logging
import uuid

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.chat_history import InMemoryChatMessageHistory

from app.schemas import AgnesMessage, AgnesAskResponse

logger = logging.getLogger(__name__)

# In-memory session store: session_id → ChatMessageHistory
_sessions: dict[str, InMemoryChatMessageHistory] = {}
_llm: ChatOpenAI | None = None


def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    return _llm

_SYSTEM_PROMPT = """
You are Agnes, an AI Supply Chain Manager at Spherecast.

You help procurement teams make smarter sourcing decisions across a portfolio of 61 CPG companies.
Your domain covers: raw material consolidation, supplier fragmentation, ingredient substitution,
compliance requirements (allergen, organic, halal, kosher, REACH, RoHS), and cost optimization.

When answering:
- Be concise and specific
- Flag uncertainty clearly
- Cite your reasoning
- Focus on actionable insights for procurement professionals
"""


async def ask(
    proposal_id: int,
    message: str,
    session_id: str | None,
) -> AgnesAskResponse:
    # Create or load session
    if session_id is None or session_id not in _sessions:
        session_id = str(uuid.uuid4())
        _sessions[session_id] = InMemoryChatMessageHistory()
        logger.info("AgnesAgent: new session %s", session_id)
    else:
        logger.info("AgnesAgent: resume session %s", session_id)

    history = _sessions[session_id]

    # Build message list: system + history + new message
    messages = [SystemMessage(content=_SYSTEM_PROMPT)]
    messages.extend(history.messages)
    messages.append(HumanMessage(content=message))

    # Call LLM
    response = await _get_llm().ainvoke(messages)

    # Persist to session history
    history.add_user_message(message)
    history.add_ai_message(response.content)

    logger.info("AgnesAgent: session %s — %d messages total", session_id, len(history.messages))

    return AgnesAskResponse(
        reply=AgnesMessage(role="assistant", content=response.content),
        session_id=session_id,
    )
