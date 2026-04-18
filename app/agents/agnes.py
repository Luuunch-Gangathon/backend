"""AgnesAgent — tool-calling chat agent for ingredient substitution queries.

Session-based history: server stores conversation per session_id.
Frontend sends session_id each request.

Avoids langchain.agents / langchain.chains entirely (Python 3.14 incompatible).
Uses a manual tool-calling loop on top of langchain_core + langchain_openai.
"""

from __future__ import annotations
import json
import logging
import uuid
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
    BaseMessage,
)
from langchain_core.tools import tool
from langchain_core.chat_history import InMemoryChatMessageHistory

from app.agents.tools.search import search as _search
from app.agents.tools.compliance_check import similarity_compliance_check as _compliance_check
from app.agents.tools.web_search_enrich import web_search_enrich as _web_search_enrich
from app.prompts.loader import render
from app.schemas import AgnesMessage, AgnesAskResponse, ToolCall, SearchHit, ComplianceMatch

logger = logging.getLogger(__name__)

_sessions: dict[str, InMemoryChatMessageHistory] = {}
_llm: ChatOpenAI | None = None

_MAX_ITERATIONS = 6


# ---------------------------------------------------------------------------
# LangChain tool wrappers
# ---------------------------------------------------------------------------

@tool
async def search(query: str, top_k: int = 8) -> str:
    """Search for ingredients similar to a given query using semantic vector search.
    Returns a list of matching ingredients with similarity scores, spec details,
    and which companies/suppliers currently use them. Use this to find alternatives
    to an ingredient or to understand portfolio coverage.

    Args:
        query: Ingredient name or description to search for (e.g. "whey protein isolate")
        top_k: Maximum number of results to return (default 8)
    """
    hits = await _search(query, top_k=top_k)
    return json.dumps([h.model_dump() for h in hits])


@tool
async def similarity_compliance_check(
    original_name: str,
    candidate_names: list[str],
    product_sku: str | None = None,
    top_x: int = 5,
) -> str:
    """Score candidate ingredients as substitutes for an original ingredient.
    Returns compliance/functional fit scores (0-100) with reasoning for each candidate.
    Use this after search() to rank which alternatives are most suitable.
    Chain: search → take result names → call this tool.

    Args:
        original_name: The ingredient being replaced (e.g. "whey-protein-isolate")
        candidate_names: List of candidate substitute names to score
        product_sku: Optional finished-good SKU for product-specific compliance context
        top_x: Maximum number of scored results (default 5)
    """
    matches = await _compliance_check(original_name, candidate_names, product_sku, top_x)
    return json.dumps([m.model_dump() for m in matches])


@tool
async def web_search_enrich(
    query: str,
    limit: int = 5,
    product_sku: str | None = None,
) -> str:
    """Search the internet for candidate ingredient substitutes for `query`,
    persist each discovered material into the substitution_groups vector store
    with a full embedding (CAS numbers, source URLs, regulatory status, dietary
    flags, allergens, certifications), and return the list of newly added names.

    Use this tool when:
    - search() returns fewer than 3 results, OR
    - all similarity scores from search() are below 0.75, OR
    - the ingredient is rare, novel, or unlikely to be in the portfolio DB.

    Workflow: call web_search_enrich(original_name, product_sku=...) BEFORE
    search() to populate the index, then call search() again to get ranked
    results including the new embeddings, then feed them into
    similarity_compliance_check() with the same product_sku.

    When `product_sku` is provided, the finished product's aggregated dietary /
    allergen / certification profile is loaded and used to filter candidates —
    e.g. for a vegan product, only vegan alternatives are returned.

    WARNING: This tool writes to the database and calls external APIs. Do NOT
    call it for follow-up analytical questions about already-surfaced materials,
    and do NOT call it repeatedly for the same query in one session.

    Args:
        query: The ingredient name to find alternatives for.
        limit: Maximum number of alternatives to discover and store (default 5).
        product_sku: Optional finished-good SKU to constrain candidates to the
            product's dietary/allergen/certification requirements.
    """
    names = await _web_search_enrich(query, limit=limit, product_sku=product_sku)
    return json.dumps(names)


_TOOLS = [search, similarity_compliance_check, web_search_enrich]
_TOOLS_BY_NAME = {t.name: t for t in _TOOLS}


# ---------------------------------------------------------------------------
# LLM setup
# ---------------------------------------------------------------------------

def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    return _llm


# ---------------------------------------------------------------------------
# Manual tool-calling loop
# ---------------------------------------------------------------------------

async def _run_agent(messages: list[BaseMessage]) -> tuple[str, list[tuple[Any, str]]]:
    """Run tool-calling loop. Returns (final_text, [(action, tool_output), ...])."""
    llm_with_tools = _get_llm().bind_tools(_TOOLS)
    intermediate: list[tuple[Any, str]] = []
    loop_messages = list(messages)

    for _ in range(_MAX_ITERATIONS):
        response: AIMessage = await llm_with_tools.ainvoke(loop_messages)
        loop_messages.append(response)

        if not response.tool_calls:
            return response.content or "", intermediate

        # Execute each tool call
        for tc in response.tool_calls:
            tool_fn = _TOOLS_BY_NAME.get(tc["name"])
            args = tc.get("args", {})
            if tool_fn is None:
                result_str = json.dumps({"error": f"unknown tool {tc['name']}"})
            else:
                try:
                    result_str = await tool_fn.ainvoke(args)
                    if not isinstance(result_str, str):
                        result_str = json.dumps(result_str)
                except Exception as exc:
                    logger.exception("Tool %s failed", tc["name"])
                    result_str = json.dumps({"error": str(exc)})

            loop_messages.append(ToolMessage(content=result_str, tool_call_id=tc["id"]))
            intermediate.append((tc, result_str))

    # Max iterations reached — ask for final answer without tools
    final_llm = _get_llm()
    final_response: AIMessage = await final_llm.ainvoke(loop_messages)
    return final_response.content or "", intermediate


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def ask(
    message: str,
    session_id: str | None,
) -> AgnesAskResponse:
    if session_id is None or session_id not in _sessions:
        session_id = str(uuid.uuid4())
        _sessions[session_id] = InMemoryChatMessageHistory()
        logger.info("AgnesAgent: new session %s", session_id)
    else:
        logger.info("AgnesAgent: resume session %s", session_id)

    history = _sessions[session_id]

    system_content = render("system/agnes")
    messages: list[BaseMessage] = [SystemMessage(content=system_content)]
    messages.extend(history.messages)
    messages.append(HumanMessage(content=message))

    output, intermediate_steps = await _run_agent(messages)

    # Persist to session history
    history.add_user_message(message)
    history.add_ai_message(output)

    logger.info(
        "AgnesAgent: session %s — %d tool calls, %d history messages",
        session_id, len(intermediate_steps), len(history.messages),
    )

    # Serialise tool calls for the response
    tool_calls: list[ToolCall] = []
    for action, tool_output_str in intermediate_steps:
        tool_name = action["name"]
        args = action.get("args", {})

        try:
            raw_result = json.loads(tool_output_str) if isinstance(tool_output_str, str) else tool_output_str
        except (json.JSONDecodeError, TypeError):
            raw_result = []

        if not isinstance(raw_result, list):
            continue

        if tool_name == "search":
            typed_result = [SearchHit(**item) for item in raw_result if isinstance(item, dict)]
        elif tool_name == "similarity_compliance_check":
            typed_result = [ComplianceMatch(**item) for item in raw_result if isinstance(item, dict)]
        elif tool_name == "web_search_enrich":
            typed_result = [item for item in raw_result if isinstance(item, str)]
        else:
            continue

        tool_calls.append(ToolCall(name=tool_name, arguments=args, result=typed_result))

    return AgnesAskResponse(
        reply=AgnesMessage(role="assistant", content=output),
        session_id=session_id,
        tool_calls=tool_calls,
    )
