"""AgnesAgent — chat with LLM tool calling.

LLM decides which tools to call autonomously based on user intent.
Session-based history: server stores conversation per session_id.
Frontend sends session_id each request — no full history transmission.

Tools available to the LLM:
  search_all_materials     → enrich all unenriched materials via SearchEngine
  search_material(name)    → enrich single material via SearchEngine
  check_product_compliance → score substitutes for all RMs in session product
  show_bom(product_id)     → show ingredients for a product
  show_company(company_id) → show company info + products

Anything without tool calls → normal chat with RAG context.
"""

from __future__ import annotations
import logging
import uuid

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.tools import tool

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
# Tools — called by the LLM autonomously
# ---------------------------------------------------------------------------

@tool
async def search_all_materials() -> str:
    """Enrich all unenriched raw materials with web search data."""
    await search_engine.run_all()
    return "SearchEngine completed for all unenriched materials."


@tool
async def search_material(name: str) -> str:
    """Enrich a single raw material by name with web search data."""
    await search_engine.run_one(name)
    return f"Enriched and embedded '{name}'. Data now available for queries."


@tool
async def show_bom(product_id: int) -> str:
    """Show bill of materials (ingredients) for a product."""
    bom = await repo.get_bom(product_id)
    if not bom:
        return f"No BOM found for product {product_id}."
    rm_lines = []
    for rm_id in bom.consumed_raw_material_ids:
        rm = await repo.get_raw_material(rm_id)
        if rm:
            rm_lines.append(f"- {rm.sku} (id: {rm.id})")
    return f"BOM for product {product_id} ({len(rm_lines)} ingredients):\n" + "\n".join(rm_lines)


@tool
async def show_company(company_id: int) -> str:
    """Show company info and its products."""
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


def _make_compliance_tool(session_id: str):
    """Build compliance tool as closure so session_id is not exposed to the LLM."""
    @tool
    async def check_product_compliance() -> str:
        """Check compliance and find ranked substitute candidates for all raw materials in the current product."""
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

    return check_product_compliance


# ---------------------------------------------------------------------------
# RAG context retrieval
# ---------------------------------------------------------------------------

async def _retrieve_context(query: str, top_k: int = 5) -> str:
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
    if session_id is None or session_id not in _sessions:
        session_id = str(uuid.uuid4())
        _sessions[session_id] = InMemoryChatMessageHistory()
        logger.info("AgnesAgent: new session %s", session_id)
    else:
        logger.info("AgnesAgent: resume session %s", session_id)

    if product_id is not None:
        _session_product[session_id] = product_id

    history = _sessions[session_id]

    context_block = await _retrieve_context(message)
    system_content = render("system/agnes")
    current_product_id = _session_product.get(session_id)
    if current_product_id is not None:
        system_content += f"\n\nCurrent product in context: product_id={current_product_id}. Use this for any product-related tool calls."
    if context_block:
        system_content += f"\n\n---\nRetrieved supply chain context:\n{context_block}"

    tools = [search_all_materials, search_material, show_bom, show_company, _make_compliance_tool(session_id)]
    tool_map = {t.name: t for t in tools}
    llm_with_tools = _get_llm().bind_tools(tools)

    messages = [SystemMessage(content=system_content)]
    messages.extend(history.messages)
    messages.append(HumanMessage(content=message))

    # Agent loop: invoke → execute tool calls → invoke again until plain text reply
    while True:
        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        for tc in response.tool_calls:
            logger.info("AgnesAgent: calling tool %s args=%s", tc["name"], tc["args"])
            result = await tool_map[tc["name"]].ainvoke(tc["args"])
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    reply_text = response.content
    history.add_user_message(message)
    history.add_ai_message(reply_text)

    logger.info("AgnesAgent: session %s — %d messages total", session_id, len(history.messages))

    return AgnesAskResponse(
        reply=AgnesMessage(role="assistant", content=reply_text),
        session_id=session_id,
    )
