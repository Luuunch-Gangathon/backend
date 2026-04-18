"""ComplianceAgent

Given a product id and raw material id:
  1. Runs pgvector similarity search to find candidate substitutes.
  2. Ranks them via GPT-4o structured output.
  3. Returns a scored list of proposals.
"""

from __future__ import annotations

import logging
import os
import re

from pydantic import BaseModel

from app.prompts.loader import render
from app.data import repo
from app.schemas import SubstituteProposal

logger = logging.getLogger(__name__)

_client = None  # lazily initialized; replaced by tests via patch.object(compliance, "_client", mock)

_DB_ID_RE = re.compile(r"^rm_db_(\d+)$")


class _RankingResponse(BaseModel):
    substitutes: list[SubstituteProposal]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def check_compliance(product_id: int, raw_material_id: int, top_x: int = 5) -> list[SubstituteProposal]:
    """Similarity-search then LLM-rank substitutes for a raw material in a product.

    Returns up to top_x SubstituteProposal items sorted by score descending.
    Returns [] if the product/material is not found or no similar materials exist.
    """
    product, raw_material = await _fetch_inputs(product_id, raw_material_id)
    if product is None or raw_material is None:
        logger.warning(
            "[compliance] product_id=%d or raw_material_id=%d not found in DB",
            product_id, raw_material_id,
        )
        return []

    logger.info(
        "[compliance] ── START check_compliance ──────────────────────────────"
    )
    logger.info(
        "[compliance] input   product=%s (id=%d)  raw_material=%s (id=%d)",
        product.sku, product_id, raw_material.sku, raw_material_id,
    )

    similar = await repo.find_similar_raw_materials(f"rm_db_{raw_material_id}")
    if not similar:
        logger.info("[compliance] pgvector search returned 0 candidates — returning []")
        return []

    logger.info("[compliance] pgvector returned %d candidate(s):", len(similar))
    substitutes: list[tuple] = []
    for item in similar:
        m = _DB_ID_RE.match(item.raw_material_id)
        if not m:
            logger.debug("[compliance]   skip non-DB id %s", item.raw_material_id)
            continue
        rm = await repo.get_raw_material(int(m.group(1)))
        if rm is not None:
            logger.info(
                "[compliance]   candidate  id=%-5d  sku=%-40s  vector_similarity=%.4f",
                rm.id, rm.sku, item.similarity_score,
            )
            substitutes.append((rm, item.similarity_score))
        else:
            logger.debug("[compliance]   skip rm_id=%s — not found in products", item.raw_material_id)

    if not substitutes:
        logger.info("[compliance] no DB-backed candidates after filter — returning []")
        return []

    global _client
    if _client is None:
        from openai import AsyncOpenAI
        _client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    system_prompt = render("system/compliance")
    sub_payload = [
        {**s.model_dump(), "vector_similarity": round(score, 4)}
        for s, score in substitutes
    ]
    user_prompt = render(
        "user/compliance_rank",
        original=raw_material.model_dump(),
        product=product.model_dump(),
        substitutes=sub_payload,
        top_x=top_x,
    )

    logger.info(
        "[compliance] sending %d candidates to gpt-4o for compliance scoring (top_x=%d)",
        len(sub_payload), top_x,
    )
    for sp in sub_payload:
        logger.info(
            "[compliance]   → sku=%-40s  vector_similarity=%.4f",
            sp.get("sku", sp.get("id")), sp["vector_similarity"],
        )

    response = await _client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=_RankingResponse,
        temperature=0,
    )

    parsed = response.choices[0].message.parsed
    if parsed is None:
        logger.warning("[compliance] gpt-4o returned no parsed output")
        return []

    logger.info("[compliance] gpt-4o raw scores (before sort/trim):")
    for s in parsed.substitutes:
        logger.info(
            "[compliance]   id=%-5d  score=%3d/100  reasoning=%s",
            s.id, s.score, s.reasoning[:120],
        )

    results = sorted(parsed.substitutes, key=lambda s: s.score, reverse=True)[:top_x]
    logger.info("[compliance] final ranking (top %d, score DESC):", len(results))
    for rank, s in enumerate(results, 1):
        logger.info(
            "[compliance]   #%d  id=%-5d  score=%3d/100  reasoning=%s",
            rank, s.id, s.score, s.reasoning[:120],
        )
    logger.info("[compliance] ── END check_compliance ────────────────────────────────")
    return results


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

async def _fetch_inputs(product_id: int, raw_material_id: int):
    product = await repo.get_product(product_id)
    raw_material = await repo.get_raw_material(raw_material_id)
    return product, raw_material
