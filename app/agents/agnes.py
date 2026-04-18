"""AgnesAgent — domain-scoped chat with RAG-backed reasoning.

Session-based history: server stores conversation per session_id.
Frontend sends session_id each request — no full history transmission.
Sessions live in memory. Process restart clears all sessions.

Phase 1: simple chat, domain-scoped to supply chain.
Phase 2 (current): RAG retrieval — embed query, fetch relevant materials
                   + DB context, inject into LLM prompt.
Phase 3: full agent orchestration with tool use.
"""

from __future__ import annotations
import json
import logging
import uuid

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.chat_history import InMemoryChatMessageHistory

from app.data import rag, repo
from app.prompts.loader import render
from app.schemas import AgnesMessage, AgnesAskResponse

logger = logging.getLogger(__name__)

_sessions: dict[str, InMemoryChatMessageHistory] = {}
_llm: ChatOpenAI | None = None


def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    return _llm


async def ask(
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

    # RAG: retrieve relevant materials + DB context
    context_block = await _retrieve_context(message)

    # Build messages: system (+ RAG context) + history + user message
    system_content = render("system/agnes")
    if context_block:
        system_content += f"\n\n---\nRetrieved supply chain context:\n{context_block}"

    messages = [SystemMessage(content=system_content)]
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


async def _retrieve_context(query: str, top_k: int = 5) -> str:
    """Build RAG context block injected into Agnes system prompt.

    Steps:
    1. rag.search()              — embed query, pgvector search → top-k materials
    2. repo.get_material_context() — fetch companies + suppliers from raw_material_map
    3. Format into readable text block (companies/suppliers capped at 5 each)

    Returned string is injected into system prompt before LLM call.
    User never sees it — LLM uses it to ground answers in real DB data.
    Returns empty string if no embeddings exist yet (graceful fallback).
    """
    try:
        results = await rag.search(query, top_k=top_k)
    except Exception:
        logger.warning("AgnesAgent: RAG search failed — proceeding without context", exc_info=True)
        return ""

    if not results:
        logger.info("AgnesAgent: no embeddings found — proceeding without RAG context")
        return ""

    names = [r["raw_material_name"] for r in results]
    db_rows = await repo.get_material_context(names)

    # Group DB rows by material name
    by_name: dict[str, list[dict]] = {}
    for row in db_rows:
        by_name.setdefault(row["raw_material_name"], []).append(row)

    lines: list[str] = []
    for result in results:
        name = result["raw_material_name"]
        similarity = result.get("similarity") or 0
        spec = result.get("spec") or {}

        lines.append(f"## {name} (relevance: {similarity:.2f})")

        # Spec summary
        if spec:
            if isinstance(spec, str):
                try:
                    spec = json.loads(spec)
                except (json.JSONDecodeError, TypeError):
                    logger.warning("AgnesAgent: invalid spec JSON for %s — skipping spec", name)
                    spec = {}
            if not isinstance(spec, dict):
                spec = {}
            func_roles = spec.get("functional_role", {}).get("value") or []
            if func_roles:
                lines.append(f"  Function: {', '.join(func_roles)}")
            certs = spec.get("certifications", {}).get("value") or []
            if certs:
                lines.append(f"  Certifications: {', '.join(certs)}")
            allergens = spec.get("allergens", {}).get("value") or {}
            if allergens.get("contains"):
                lines.append(f"  Allergens: {', '.join(allergens['contains'])}")

        # Companies + suppliers from raw_material_map (capped to avoid token bloat)
        rows = by_name.get(name, [])
        companies = sorted({r["company_name"] for r in rows if r["company_name"]})
        suppliers = sorted({r["supplier_name"] for r in rows if r["supplier_name"]})
        _MAX = 5
        if companies:
            overflow = len(companies) - _MAX
            shown = companies[:_MAX]
            suffix = f" (+{overflow} more)" if overflow > 0 else ""
            lines.append(f"  Companies buying: {', '.join(shown)}{suffix}")
        if suppliers:
            overflow = len(suppliers) - _MAX
            shown = suppliers[:_MAX]
            suffix = f" (+{overflow} more)" if overflow > 0 else ""
            lines.append(f"  Suppliers: {', '.join(shown)}{suffix}")

        lines.append("")

    return "\n".join(lines)
