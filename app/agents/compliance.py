"""ComplianceAgent

Verifies compliance requirements for each proposal, and ranks substitute
raw materials by suitability score using GPT-4o structured output.

Writes to:
  - proposals (compliance_requirements column)
"""

from __future__ import annotations

import logging
import os

from pydantic import BaseModel

from app.prompts.loader import render
from app.schemas import RawMaterial, Product
from app.data import repo

logger = logging.getLogger(__name__)

_client = None  # lazily initialized; replaced by tests via patch.object(compliance, "_client", mock)


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

class SubstituteScore(BaseModel):
    id: int
    score: int      # 0–100
    reasoning: str


class _RankingResponse(BaseModel):
    substitutes: list[SubstituteScore]


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

async def rank_substitutes(
    raw_material: RawMaterial,
    substitutes: list[tuple[RawMaterial, float]],
    product: Product,
    top_x: int = 5,
) -> list[SubstituteScore]:
    """Return the top-X substitutes scored 0–100 with reasoning.

    Args:
        raw_material: The original material being replaced.
        substitutes: Candidate replacements paired with their pgvector cosine similarity score.
        product: The finished good the material is used in.
        top_x: Maximum number of results to return, sorted by score desc.
    """
    if not substitutes:
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
        logger.warning("rank_substitutes: model returned no parsed output")
        return []

    results = sorted(parsed.substitutes, key=lambda s: s.score, reverse=True)[:top_x]
    logger.debug("rank_substitutes: returning %d results", len(results))
    return results


async def run(product: Product, raw_material: RawMaterial, substitutes: list[tuple[RawMaterial, float]]) -> None:
    results = await rank_substitutes(raw_material, substitutes, product)
    if not results:
        return
    await repo.save_substitutions(
        raw_material.id,
        [(r.id, r.score, r.reasoning) for r in results],
    )
    for r in results:
        logger.info(
            "ComplianceAgent: product=%s rm_id=%d sub_id=%d score=%d",
            product.sku, raw_material.id, r.id, r.score,
        )
