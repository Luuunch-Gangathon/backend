"""AgnesAgent — chat with LLM tool calling.

Tools (matching frontend/knowledge/api-contract.md):
  search(query)                              → SearchHit[]
  similarity_compliance_check(original_name) → ComplianceMatch[]
  web_search_enrich(query)                   → string[]

Each tool invocation is captured in AgnesAskResponse.tool_calls so the
frontend can render rich entity surfaces (search lists, proposal cards,
discovered-name tags).

Session-based history: server stores conversation per session_id.
Frontend sends session_id each request — no full history transmission.
"""

from __future__ import annotations
import json
import logging
import re
import uuid
from contextvars import ContextVar

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.tools import tool

from app.data import db, rag, repo
from app.agents import search_engine, compliance as compliance_agent
from app.prompts.loader import render
from app.schemas import (
    AgnesMessage,
    AgnesAskResponse,
    ToolCall,
    SearchHit,
    ComplianceMatch,
)

logger = logging.getLogger(__name__)

_sessions: dict[str, InMemoryChatMessageHistory] = {}
_session_product: dict[str, int] = {}  # session_id → product_id
_llm: ChatOpenAI | None = None

# Context var so @tool callbacks can resolve the active session without exposing it to the LLM
_session_ctx: ContextVar[str | None] = ContextVar("_agnes_session", default=None)

_DB_ID_RE = re.compile(r"^rm_db_(\d+)$")


def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    return _llm


# ---------------------------------------------------------------------------
# Tool helpers — DB lookups for aggregations / id resolution
# ---------------------------------------------------------------------------

async def _aggregate_by_name(names: list[str]) -> dict[str, dict]:
    """For each raw_material_name, return distinct companies + suppliers + a
    representative raw_material_id from raw_material_map."""
    if not names:
        return {}
    async with db.get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT raw_material_name, raw_material_id, company_name, supplier_name
            FROM raw_material_map
            WHERE raw_material_name = ANY($1)
            """,
            names,
        )
    out: dict[str, dict] = {
        n: {"companies": set(), "suppliers": set(), "raw_material_id": None} for n in names
    }
    for r in rows:
        bucket = out[r["raw_material_name"]]
        if r["company_name"]:
            bucket["companies"].add(r["company_name"])
        if r["supplier_name"]:
            bucket["suppliers"].add(r["supplier_name"])
        if bucket["raw_material_id"] is None and r["raw_material_id"] is not None:
            bucket["raw_material_id"] = r["raw_material_id"]
    result = {
        n: {
            "companies": sorted(b["companies"]),
            "suppliers": sorted(b["suppliers"]),
            "raw_material_id": b["raw_material_id"],
        }
        for n, b in out.items()
    }
    for name, agg in result.items():
        logger.info(
            "[agnes] aggregate  %-45s  rm_id=%-6s  companies=%d  suppliers=%d",
            name, agg["raw_material_id"], len(agg["companies"]), len(agg["suppliers"]),
        )
    return result


async def _resolve_rm_id(name: str) -> int | None:
    """Resolve a canonical raw_material_name → raw_material_id (first match)."""
    async with db.get_conn() as conn:
        row = await conn.fetchrow(
            """
            SELECT raw_material_id
            FROM raw_material_map
            WHERE raw_material_name = $1 AND raw_material_id IS NOT NULL
            LIMIT 1
            """,
            name,
        )
    rm_id = row["raw_material_id"] if row else None
    if rm_id is not None:
        logger.info("[agnes] resolve_rm_id  %r  →  rm_id=%d", name, rm_id)
    else:
        logger.warning("[agnes] resolve_rm_id  %r  →  NOT FOUND in raw_material_map", name)
    return rm_id


async def _names_by_id(ids: list[int]) -> dict[int, str]:
    if not ids:
        return {}
    async with db.get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT raw_material_id, raw_material_name
            FROM raw_material_map
            WHERE raw_material_id = ANY($1)
            """,
            ids,
        )
    return {r["raw_material_id"]: r["raw_material_name"] for r in rows}


# ---------------------------------------------------------------------------
# Tools — names match frontend api-contract.md
# ---------------------------------------------------------------------------

@tool
async def search(query: str) -> dict:
    """Semantic search over the raw-material catalog.

    Use when the user asks about which materials match a description, or to
    find ingredients similar to a query. Returns up to 5 catalog hits with
    similarity score, the companies that currently use each material, and
    the suppliers that ship it.
    """
    logger.info("[tool:search] ── query=%r", query)
    hits = await rag.search(query, top_k=5)
    if not hits:
        logger.info("[tool:search] 0 hits — returning empty results")
        return {"results": []}

    names = [h["raw_material_name"] for h in hits]
    aggs = await _aggregate_by_name(names)

    results: list[SearchHit] = []
    for h in hits:
        name = h["raw_material_name"]
        agg = aggs.get(name) or {"companies": [], "suppliers": [], "raw_material_id": None}
        hit = SearchHit(
            raw_material_name=name,
            raw_material_id=agg["raw_material_id"],
            similarity=float(h.get("similarity") or 0.0),
            spec=h.get("spec"),
            companies=agg["companies"],
            suppliers=agg["suppliers"],
        )
        logger.info(
            "[tool:search]   → %-45s  sim=%.4f  companies=%s  suppliers=%s",
            name, hit.similarity,
            hit.companies[:3], hit.suppliers[:3],
        )
        results.append(hit)
    logger.info("[tool:search] returning %d SearchHit(s)", len(results))
    return {"results": [r.model_dump() for r in results]}


@tool
async def similarity_compliance_check(original_name: str) -> dict:
    """Score substitution candidates for a raw material against compliance and sourcing constraints.

    Use when the user asks what could replace a material, or whether a
    specific substitute is viable. Returns ranked candidates with a
    compliance score (0..100), short rationale, vector similarity, the
    companies whose BOMs would change, and the suppliers that ship the
    candidate today.
    """
    logger.info("[tool:compliance] ── original_name=%r", original_name)

    session_id = _session_ctx.get()
    product_id = _session_product.get(session_id) if session_id else None
    if product_id is None:
        logger.warning("[tool:compliance] no product_id in session — cannot run compliance check")
        return {"matches": [], "error": "No product context for this session."}
    logger.info("[tool:compliance] session product_id=%d", product_id)

    rm_id = await _resolve_rm_id(original_name)
    if rm_id is None:
        return {"matches": [], "error": f"Raw material '{original_name}' not found in catalog."}

    proposals = await compliance_agent.check_compliance(product_id, rm_id, top_x=5)
    if not proposals:
        logger.info("[tool:compliance] check_compliance returned 0 proposals — returning []")
        return {"matches": []}

    similar = await repo.find_similar_raw_materials(f"rm_db_{rm_id}")
    sim_by_id: dict[int, float] = {}
    for s in similar:
        m = _DB_ID_RE.match(s.raw_material_id)
        if m:
            sim_by_id[int(m.group(1))] = float(s.similarity_score)

    sub_ids = [p.id for p in proposals]
    name_by_id = await _names_by_id(sub_ids)

    orig_agg = (await _aggregate_by_name([original_name])).get(original_name) or {"companies": []}
    companies_affected = orig_agg["companies"]
    logger.info(
        "[tool:compliance] companies affected by replacing %r: %s",
        original_name, companies_affected,
    )

    sub_names = [name_by_id[i] for i in sub_ids if i in name_by_id]
    sub_aggs = await _aggregate_by_name(sub_names)

    matches: list[ComplianceMatch] = []
    logger.info("[tool:compliance] building %d ComplianceMatch(es):", len(proposals))
    for p in proposals:
        sub_name = name_by_id.get(p.id)
        if sub_name is None:
            rm = await repo.get_raw_material(p.id)
            sub_name = rm.sku if rm else f"rm_db_{p.id}"
        sub_agg = sub_aggs.get(sub_name) or {"suppliers": []}
        match = ComplianceMatch(
            raw_material_id=p.id,
            raw_material_name=sub_name,
            score=p.score,
            reasoning=p.reasoning,
            similarity=sim_by_id.get(p.id, 0.0),
            companies_affected=companies_affected,
            suppliers=sub_agg["suppliers"],
        )
        logger.info(
            "[tool:compliance]   %-45s  score=%3d/100  sim=%.4f  suppliers=%s",
            sub_name, match.score, match.similarity, match.suppliers[:3],
        )
        logger.info(
            "[tool:compliance]   reasoning: %s",
            match.reasoning[:160],
        )
        matches.append(match)
    logger.info("[tool:compliance] returning %d ComplianceMatch(es)", len(matches))
    return {"matches": [m.model_dump() for m in matches]}


@tool
async def web_search_enrich(query: str) -> dict:
    """Search the web for candidate raw materials matching the query, enrich them, and embed for future searches.

    Use when local catalog search returns nothing or when the user mentions
    a novel ingredient. Returns the candidate raw-material names that are
    now indexed and discoverable.
    """
    logger.info("[tool:web_search_enrich] ── query=%r", query)
    try:
        await search_engine.run_one(query)
        logger.info("[tool:web_search_enrich] enrichment complete for %r", query)
    except Exception:
        logger.exception("[tool:web_search_enrich] enrichment failed for %r", query)

    hits = await rag.search(query, top_k=5)
    names = [h["raw_material_name"] for h in hits]
    logger.info("[tool:web_search_enrich] discovered %d candidate(s): %s", len(names), names)
    return {"names": names}


# ---------------------------------------------------------------------------
# RAG context retrieval — pre-tool grounding (does NOT appear in tool_calls)
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
# Tool result conversion
# ---------------------------------------------------------------------------

def _build_tool_call(name: str, args: dict, raw_result, product_sku: str | None) -> ToolCall:
    """Convert a raw tool dict result into a typed ToolCall for the API response.

    Augments arguments with product_sku for compliance checks so the frontend
    proposal card can record decisions against the correct finished good.
    """
    augmented_args = {**(args or {})}
    if name == "similarity_compliance_check" and product_sku and "product_sku" not in augmented_args:
        augmented_args["product_sku"] = product_sku

    if name == "search":
        items = raw_result.get("results", []) if isinstance(raw_result, dict) else []
        result = [SearchHit(**i) for i in items]
    elif name == "similarity_compliance_check":
        items = raw_result.get("matches", []) if isinstance(raw_result, dict) else []
        result = [ComplianceMatch(**i) for i in items]
    elif name == "web_search_enrich":
        result = list(raw_result.get("names", [])) if isinstance(raw_result, dict) else []
    else:
        result = []

    return ToolCall(name=name, arguments=augmented_args, result=result)


def _result_to_llm_string(raw_result) -> str:
    try:
        return json.dumps(raw_result, default=str)
    except Exception:
        return str(raw_result)


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
    current_product_id = _session_product.get(session_id)

    product_sku: str | None = None
    if current_product_id is not None:
        product = await repo.get_product(current_product_id)
        product_sku = product.sku if product else None

    context_block = await _retrieve_context(message)
    system_content = render("system/agnes")
    if current_product_id is not None:
        system_content += (
            f"\n\nCurrent product in context: product_id={current_product_id}"
            + (f" (sku={product_sku})." if product_sku else ".")
            + " Use this for any product-related tool calls."
        )
    if context_block:
        system_content += f"\n\n---\nRetrieved supply chain context:\n{context_block}"

    tools = [search, similarity_compliance_check, web_search_enrich]
    tool_map = {t.name: t for t in tools}
    llm_with_tools = _get_llm().bind_tools(tools)

    messages = [SystemMessage(content=system_content)]
    messages.extend(history.messages)
    messages.append(HumanMessage(content=message))

    captured_tool_calls: list[ToolCall] = []

    logger.info("[agnes] ══ BEGIN turn  session=%s  product_id=%s ══", session_id, current_product_id)

    token = _session_ctx.set(session_id)
    iteration = 0
    try:
        while True:
            iteration += 1
            response = await llm_with_tools.ainvoke(messages)
            messages.append(response)

            if not response.tool_calls:
                logger.info("[agnes] iteration=%d  LLM produced plain-text reply — exiting loop", iteration)
                break

            logger.info(
                "[agnes] iteration=%d  LLM requested %d tool call(s)",
                iteration, len(response.tool_calls),
            )
            for tc in response.tool_calls:
                logger.info("[agnes] ▶ tool=%-30s  args=%s", tc["name"], tc["args"])
                try:
                    raw_result = await tool_map[tc["name"]].ainvoke(tc["args"])
                except Exception as exc:
                    logger.exception("[agnes] tool %s raised an exception", tc["name"])
                    raw_result = {"error": str(exc)}

                captured_tool_calls.append(
                    _build_tool_call(tc["name"], tc["args"], raw_result, product_sku)
                )
                messages.append(ToolMessage(
                    content=_result_to_llm_string(raw_result),
                    tool_call_id=tc["id"],
                ))
    finally:
        _session_ctx.reset(token)

    reply_text = response.content
    history.add_user_message(message)
    history.add_ai_message(reply_text)

    logger.info(
        "[agnes] ══ END turn  session=%s  iterations=%d  tool_calls=%d  reply_chars=%d ══",
        session_id, iteration, len(captured_tool_calls), len(reply_text),
    )

    return AgnesAskResponse(
        reply=AgnesMessage(role="assistant", content=reply_text),
        session_id=session_id,
        tool_calls=captured_tool_calls,
    )
