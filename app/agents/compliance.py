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
    *,
    original_spec: dict | None = None,
    candidate_specs: dict[str, dict] | None = None,
    candidate_names: list[str] | None = None,
    product_profile: dict | None = None,
) -> list[SubstituteScore]:
    """Return the top-X substitutes scored 0–100 with reasoning.

    Args:
        raw_material: The original material being replaced.
        substitutes: Candidate replacements paired with their pgvector cosine similarity score.
        product: The finished good the material is used in.
        top_x: Maximum number of results to return, sorted by score desc.
        original_spec: Full enriched spec of the original material (dietary_flags,
            allergens, certifications, etc.) for detailed comparison.
        candidate_specs: Map of candidate name → spec dict for each substitute.
        candidate_names: List of names parallel to `substitutes`, used to look up
            each candidate's spec in `candidate_specs`. Required for spec injection.
        product_profile: Aggregated dietary/allergen/certification profile of the
            finished product — if provided, candidates must satisfy these constraints
            to receive a high score.
    """
    if not substitutes:
        return []

    global _client
    if _client is None:
        from openai import AsyncOpenAI
        _client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    system_prompt = render("system/compliance")

    names = candidate_names or [None] * len(substitutes)
    specs_by_name = candidate_specs or {}
    sub_payload = [
        {
            **s.model_dump(),
            "vector_similarity": round(score, 4),
            "spec": specs_by_name.get(name, {}) if name else {},
        }
        for (s, score), name in zip(substitutes, names)
    ]

    user_prompt = render(
        "user/compliance_rank",
        original={**raw_material.model_dump(), "spec": original_spec or {}},
        product=product.model_dump(),
        product_profile=product_profile or {},
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


