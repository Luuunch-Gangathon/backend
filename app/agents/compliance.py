"""ComplianceAgent — quantifiable substitute scoring with evidence trails.

Given a product id and raw material id:
  1. Resolves candidate substitutes (pgvector similarity search, or caller-supplied IDs).
  2. Loads enriched specs for original + candidates from substitution_groups.
  3. Calls GPT-4o structured output with a 5-dimension scoring rubric.
  4. Returns SubstituteProposal[] with score_breakdown + reasoning.

Scoring rubric (0–20 each, total 0–100):
  functional_equivalence — same functional role in the formulation
  spec_compatibility     — physical/chemical spec overlap (form, grade, origin)
  regulatory_fit         — GRAS, recalls, regulatory pathway alignment
  dietary_compliance     — preserves dietary claims (vegan, halal, allergens)
  certification_match    — retains required certifications (organic, non-GMO)

The LLM is instructed to cite each dimension score and evidence in its reasoning,
making every score auditable and defensible.

Hallucination guard: IDs not present in the candidate list are dropped.
Temperature = 0 for deterministic output.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

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

async def check_compliance(
    product_id: int,
    raw_material_id: int,
    top_x: int = 5,
    candidate_ids: Optional[list[int]] = None,
) -> list[SubstituteProposal]:
    """LLM-rank substitute candidates for a raw material in a product.

    Candidate selection:
      - `candidate_ids=None` (default): pgvector similarity search finds candidates.
      - `candidate_ids=[...]`: caller supplies the exact candidates to score;
        the similarity search is skipped.

    Returns up to top_x SubstituteProposal items sorted by score descending.
    Returns [] if product/material are missing, or no candidates could be resolved.
    """
    product, raw_material = await _fetch_inputs(product_id, raw_material_id)
    if product is None or raw_material is None:
        logger.warning(
            "compliance.check_compliance: product_id=%d or raw_material_id=%d not found",
            product_id, raw_material_id,
        )
        return []

    substitutes = await _resolve_candidates(raw_material_id, candidate_ids)
    if not substitutes:
        return []

    all_ids = [raw_material.id] + [s.id for s in substitutes]
    specs = await repo.get_specs_for_raw_materials(all_ids)

    global _client
    if _client is None:
        from openai import AsyncOpenAI
        _client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    system_prompt = render("system/compliance")
    sub_payload = [{"id": s.id, "sku": s.sku, "spec": specs.get(s.id, {})} for s in substitutes]
    user_prompt = render(
        "user/compliance_rank",
        original={"id": raw_material.id, "sku": raw_material.sku, "spec": specs.get(raw_material.id, {})},
        product={"id": product.id, "sku": product.sku},
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
        logger.warning("compliance.check_compliance: model returned no parsed output")
        return []

    candidate_by_id = {s.id: s for s in substitutes}
    validated = []
    for p in sorted(parsed.substitutes, key=lambda s: s.score, reverse=True):
        candidate = candidate_by_id.get(p.id)
        if candidate is None:
            logger.warning("compliance: LLM returned unknown id=%d — dropping hallucinated proposal", p.id)
            continue
        validated.append(SubstituteProposal(id=p.id, sku=candidate.sku, score=p.score, reasoning=p.reasoning))
        if len(validated) == top_x:
            break

    logger.info(
        "compliance.check_compliance: product_id=%d rm_id=%d candidates=%d → %d proposals (%d hallucinated)",
        product_id, raw_material_id, len(substitutes), len(validated), len(parsed.substitutes) - len(validated),
    )
    return validated


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

async def _fetch_inputs(product_id: int, raw_material_id: int):
    product = await repo.get_product(product_id)
    raw_material = await repo.get_raw_material(raw_material_id)
    return product, raw_material


async def _resolve_candidates(raw_material_id: int, candidate_ids: Optional[list[int]]):
    """Return the list of RawMaterial candidates to be scored.

    If `candidate_ids` is provided, resolve each one directly (skip pgvector).
    Otherwise, run the similarity search for the original and resolve its neighbors.
    """
    if candidate_ids is not None:
        resolved = []
        for cid in candidate_ids:
            rm = await repo.get_raw_material(cid)
            if rm is not None:
                resolved.append(rm)
        return resolved

    similar = await repo.find_similar_raw_materials(f"rm_db_{raw_material_id}")
    if not similar:
        logger.info("compliance: no similar materials found for rm_id=%d", raw_material_id)
        return []

    resolved = []
    for item in similar:
        m = _DB_ID_RE.match(item.raw_material_id)
        if not m:
            continue
        rm = await repo.get_raw_material(int(m.group(1)))
        if rm is not None:
            resolved.append(rm)
    return resolved
