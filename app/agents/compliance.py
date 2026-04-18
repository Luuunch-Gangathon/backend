"""ComplianceAgent

Verifies compliance requirements for each proposal, and ranks substitute
raw materials by suitability score using GPT-4o structured output.

Writes to:
  - proposals (compliance_requirements column)
"""

from __future__ import annotations

import json
import logging
import os

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.schemas import RawMaterial, Product

logger = logging.getLogger(__name__)

_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


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
    substitutes: list[RawMaterial],
    product: Product,
    top_x: int = 5,
) -> list[SubstituteScore]:
    """Return the top-X substitutes scored 0–100 with reasoning.

    Args:
        raw_material: The original material being replaced.
        substitutes: Candidate replacements to evaluate.
        product: The finished good the material is used in.
        top_x: Maximum number of results to return, sorted by score desc.
    """
    if not substitutes:
        return []

    system_prompt = (
        "You are a supply-chain compliance expert. "
        "Evaluate each substitute raw material against the original and the "
        "finished-good context. Score each candidate 0–100 where 100 means a "
        "perfect drop-in replacement with no compliance risk. Consider: "
        "functional equivalence, regulatory fit (REACH, RoHS, food-grade, etc.), "
        "specification overlap, and supplier reliability. "
        "Return only the candidates provided — do not invent new ones."
    )

    user_prompt = (
        f"Original material: {json.dumps(raw_material.model_dump())}\n\n"
        f"Finished good (product): {json.dumps(product.model_dump())}\n\n"
        f"Substitute candidates:\n"
        f"{json.dumps([s.model_dump() for s in substitutes], indent=2)}\n\n"
        f"Return the top {top_x} substitutes ranked by score."
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


async def run(product: Product, raw_material: RawMaterial, substitutes: list[RawMaterial]) -> None:
    results = await rank_substitutes(raw_material, substitutes, product)
    for r in results:
        logger.info(
            "ComplianceAgent: product=%s rm_id=%d sub_id=%d score=%d — %s",
            product.sku, raw_material.id, r.id, r.score, r.reasoning,
        )
