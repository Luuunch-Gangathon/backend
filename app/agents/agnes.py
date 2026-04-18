"""AgnesAgent — chat with keyword-triggered commands.

Phase 1 (current): commands triggered by explicit keywords in message.
Phase 2 (next): LLM decides which tools to call autonomously.
  → swap _try_command() for bind_tools() + agent loop.
  → same functions, just re-add @tool decorators and bind to LLM.
  → see git history for the agent loop implementation (was here before).

Session-based history: server stores conversation per session_id.
Frontend sends session_id each request — no full history transmission.

Commands (user must explicitly write these in chat):
  "search <material>"         → enrich single material via SearchEngine
  "search all"                → enrich all unenriched materials
  "compliance"                → score substitutes for all RMs in product (product_id from session)
  "bom <product_id>"          → show ingredients for a product
  "company <company_id>"      → show company info + products

Anything else → normal chat with RAG context.
"""

from __future__ import annotations
import logging
import re
import uuid

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.chat_history import InMemoryChatMessageHistory

from app.data import rag, repo
from app.agents import search_engine, compliance as compliance_agent
from app.prompts.loader import render
from app.schemas import AgnesMessage, AgnesAskResponse

logger = logging.getLogger(__name__)

_sessions: dict[str, InMemoryChatMessageHistory] = {}
_session_product: dict[str, int] = {}  # session_id → product_id
_llm: ChatOpenAI | None = None


def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    return _llm


# ---------------------------------------------------------------------------
# Commands — keyword-triggered, no LLM reasoning
# ---------------------------------------------------------------------------

async def _cmd_search_all() -> str:
    await search_engine.run_all()
    return "SearchEngine completed for all unenriched materials."


async def _cmd_search(name: str) -> str:
    await search_engine.run_one(name)
    return f"Enriched and embedded '{name}'. Data now available for queries."


async def _cmd_compliance(session_id: str) -> str:
    product_id = _session_product.get(session_id)
    if product_id is None:
        return "No product context for this session. Please provide a product_id when starting the chat."
    bom = await repo.get_bom(product_id)
    if not bom or not bom.consumed_raw_material_ids:
        return f"No raw materials found in BOM for product {product_id}."
    lines = []
    for rm_id in bom.consumed_raw_material_ids:
        proposals = await compliance_agent.check_compliance(product_id, rm_id)
        if proposals:
            lines.append(f"RM {rm_id}:")
            for p in proposals:
                lines.append(f"  - id: {p.id}, score: {p.score}/100 — {p.reasoning}")
    if not lines:
        return f"No substitute proposals found for any raw material in product {product_id}."
    return f"Compliance results for product {product_id}:\n" + "\n".join(lines)


async def _cmd_bom(product_id: int) -> str:
    bom = await repo.get_bom(product_id)
    if not bom:
        return f"No BOM found for product {product_id}."
    rm_lines = []
    for rm_id in bom.consumed_raw_material_ids:
        rm = await repo.get_raw_material(rm_id)
        if rm:
            rm_lines.append(f"- {rm.sku} (id: {rm.id})")
    return f"BOM for product {product_id} ({len(rm_lines)} ingredients):\n" + "\n".join(rm_lines)


async def _cmd_company(company_id: int) -> str:
    company = await repo.get_company(company_id)
    if not company:
        return f"Company {company_id} not found."
    products = await repo.list_products(company_id=company_id)
    lines = [f"Company: {company.name} (id: {company.id})", f"Products ({len(products)}):"]
    for p in products[:10]:
        lines.append(f"- {p.sku} (id: {p.id})")
    if len(products) > 10:
        lines.append(f"  (+{len(products) - 10} more)")
    return "\n".join(lines)


async def _try_command(message: str, session_id: str) -> str | None:
    msg = message.strip()
    msg_lower = msg.lower()

    if msg_lower == "search all":
        return await _cmd_search_all()

    m = re.match(r"^search\s+(.+)$", msg_lower)
    if m:
        return await _cmd_search(msg[len("search "):].strip())

    if msg_lower == "compliance":
        return await _cmd_compliance(session_id)

    m = re.match(r"^bom\s+(\d+)$", msg_lower)
    if m:
        return await _cmd_bom(int(m.group(1)))

    m = re.match(r"^company\s+(\d+)$", msg_lower)
    if m:
        return await _cmd_company(int(m.group(1)))

    return None


# ---------------------------------------------------------------------------
# RAG context retrieval
# ---------------------------------------------------------------------------

async def _retrieve_context(query: str, top_k: int = 5) -> str:
    """Build RAG context block injected into Agnes system prompt.

    1. rag.search()              — embed query, pgvector search → top-k materials
    2. repo.get_material_context() — fetch companies + suppliers from raw_material_map
    3. Format into readable text block (companies/suppliers capped at 5 each)

    Returns empty string if no embeddings exist yet (graceful fallback).
    """
    try:
        results = await rag.search(query, top_k=top_k)
    except Exception:
        logger.warning("AgnesAgent: RAG search failed — proceeding without context", exc_info=True)
        return ""

    if not results:
        return ""

    names = [r["raw_material_name"] for r in results]
    db_rows = await repo.get_material_context(names)

    by_name: dict[str, list[dict]] = {}
    for row in db_rows:
        by_name.setdefault(row["raw_material_name"], []).append(row)

    lines: list[str] = []
    _MAX = 5
    for result in results:
        name = result["raw_material_name"]
        similarity = result.get("similarity") or 0
        lines.append(f"## {name} (relevance: {similarity:.2f})")

        rows = by_name.get(name, [])
        companies = sorted({r["company_name"] for r in rows if r["company_name"]})
        suppliers = sorted({r["supplier_name"] for r in rows if r["supplier_name"]})
        if companies:
            shown = companies[:_MAX]
            suffix = f" (+{len(companies) - _MAX} more)" if len(companies) > _MAX else ""
            lines.append(f"  Companies: {', '.join(shown)}{suffix}")
        if suppliers:
            shown = suppliers[:_MAX]
            suffix = f" (+{len(suppliers) - _MAX} more)" if len(suppliers) > _MAX else ""
            lines.append(f"  Suppliers: {', '.join(shown)}{suffix}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def ask(
    message: str,
    session_id: str | None,
    product_id: int | None = None,
) -> AgnesAskResponse:
    # Create or load session
    if session_id is None or session_id not in _sessions:
        session_id = str(uuid.uuid4())
        _sessions[session_id] = InMemoryChatMessageHistory()
        logger.info("AgnesAgent: new session %s", session_id)
    else:
        logger.info("AgnesAgent: resume session %s", session_id)

    if product_id is not None:
        _session_product[session_id] = product_id

    history = _sessions[session_id]

    # Step 1: check if message is an explicit command
    command_result = await _try_command(message, session_id)
    if command_result is not None:
        logger.info("AgnesAgent: command executed")
        history.add_user_message(message)
        history.add_ai_message(command_result)
        return AgnesAskResponse(
            reply=AgnesMessage(role="assistant", content=command_result),
            session_id=session_id,
        )

    # Step 2: normal chat — RAG context + LLM
    # TODO Phase 2: replace steps 1+2 with bind_tools() agent loop.
    # LLM autonomously decides which tools to call. Same functions, no keyword matching.
    context_block = await _retrieve_context(message)

    system_content = render("system/agnes")
    if context_block:
        system_content += f"\n\n---\nRetrieved supply chain context:\n{context_block}"

    messages = [SystemMessage(content=system_content)]
    messages.extend(history.messages)
    messages.append(HumanMessage(content=message))

    response = await _get_llm().ainvoke(messages)
    reply_text = response.content

    history.add_user_message(message)
    history.add_ai_message(reply_text)

    logger.info("AgnesAgent: session %s — %d messages total", session_id, len(history.messages))

    return AgnesAskResponse(
        reply=AgnesMessage(role="assistant", content=reply_text),
        session_id=session_id,
    )
