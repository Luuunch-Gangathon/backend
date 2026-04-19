"""AgnesAgent — autonomous chat with LLM tool calling.

Architecture:
  LLM decides which tools to call autonomously via LangChain bind_tools().
  No hardcoded routing — tool selection is 100% LLM-driven.
  Agent loop: invoke → check tool_calls → execute → feed result back → repeat.

Session management:
  Server stores conversation history per session_id (in-memory).
  Frontend sends session_id each request — no full history transmission.
  Product context (product_id) is session-scoped, injected into system prompt.

Tools available to the LLM:
  search_all_materials     → enrich all unenriched materials via SearchEngine
  search_material(name)    → enrich single material via SearchEngine
  check_product_compliance → score substitutes for RMs in session product (uses compliance agent)
  show_bom(product_id)     → show ingredients for a product
  show_company(company_id) → show company info + products

Reasoning visibility:
  Each tool call is logged as a reasoning_step in the response,
  so frontend can render the agent's thought process (which tools called, results).

RAG context:
  Every request runs rag.search() on the user message and injects matching
  materials (with company/supplier rollups) into the system prompt.
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
    async def check_product_compliance(rm_id: int | None = None) -> str:
        """Find ranked substitute candidates for raw materials in the current product.

        If rm_id is provided, check only that specific raw material.
        If rm_id is None, check all raw materials in the product's BOM.
        Use the BOM listed in the system prompt to match user's natural language
        (e.g. "citric acid") to the correct rm_id.
        """
        product_id = _session_product.get(session_id)
        if product_id is None:
            return "No product context for this session. Please provide a product_id when starting the chat."
        bom = await repo.get_bom(product_id)
        if not bom or not bom.consumed_raw_material_ids:
            return f"No raw materials found in BOM for product {product_id}."

        if rm_id is not None:
            if rm_id not in bom.consumed_raw_material_ids:
                return f"Raw material id {rm_id} is not in BOM for product {product_id}."
            target_ids = [rm_id]
        else:
            target_ids = bom.consumed_raw_material_ids

        product = await repo.get_product(product_id)
        product_label = product.sku if product else f"product {product_id}"
        lines = []
        for target_id in target_ids:
            original_rm = await repo.get_raw_material(target_id)
            original_label = original_rm.sku if original_rm else f"id: {target_id}"
            proposals = await compliance_agent.check_compliance(product_id, target_id)
            if not proposals:
                continue
            lines.append(f"Original RM {original_label}:")
            for p in proposals:
                lines.append(f"  - {p.sku} (id: {p.id}) — {p.reasoning}")
        if not lines:
            return f"No substitute proposals found for {product_label}."
        return f"Compliance results for {product_label}:\n" + "\n".join(lines)

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
        current_product = await repo.get_product(current_product_id)
        product_label = current_product.sku if current_product else f"product_id={current_product_id}"
        system_content += f"\n\nCurrent product in context: {product_label} (id={current_product_id})."
        bom = await repo.get_bom(current_product_id)
        if bom and bom.consumed_raw_material_ids:
            bom_lines = []
            for rm_id in bom.consumed_raw_material_ids:
                rm = await repo.get_raw_material(rm_id)
                if rm:
                    bom_lines.append(f"  - id {rm.id}: {rm.sku}")
            if bom_lines:
                system_content += (
                    "\nRaw materials in this product's BOM (use these ids when calling compliance tools):\n"
                    + "\n".join(bom_lines)
                )
    if context_block:
        system_content += f"\n\n---\nRetrieved supply chain context:\n{context_block}"

    tools = [search_all_materials, search_material, show_bom, show_company, _make_compliance_tool(session_id)]
    tool_map = {t.name: t for t in tools}
    llm_with_tools = _get_llm().bind_tools(tools)

    messages = [SystemMessage(content=system_content)]
    messages.extend(history.messages)
    messages.append(HumanMessage(content=message))

    # Agent loop: invoke → execute tool calls → invoke again until plain text reply.
    # Collect reasoning_steps so frontend can render the tool-call trace.
    reasoning_steps: list[str] = []

    while True:
        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        for tc in response.tool_calls:
            logger.info("AgnesAgent: calling tool %s args=%s", tc["name"], tc["args"])
            result = await tool_map[tc["name"]].ainvoke(tc["args"])
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

            args_str = ", ".join(f"{k}={v}" for k, v in tc["args"].items())
            result_summary = str(result)[:300]
            reasoning_steps.append(f"Called {tc['name']}({args_str}) → {result_summary}")

    reply_text = response.content
    history.add_user_message(message)
    history.add_ai_message(reply_text)

    logger.info("AgnesAgent: session %s — %d messages, %d tool calls", session_id, len(history.messages), len(reasoning_steps))

    return AgnesAskResponse(
        reply=AgnesMessage(
            role="assistant",
            content=reply_text,
            reasoning_steps=reasoning_steps if reasoning_steps else None,
        ),
        session_id=session_id,
    )
