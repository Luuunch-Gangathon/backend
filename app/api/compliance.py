from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException

from app.data import repo
from app.agents import compliance as compliance_agent
from app.schemas import ComplianceResult, SubstituteProposal, SubstituteScoreRequest

router = APIRouter(prefix="/compliance", tags=["compliance"])
logger = logging.getLogger(__name__)


@router.post(
    "/{product_id}/{original_rm_id}/candidates",
    response_model=list[SubstituteProposal],
)
async def score_substitute_candidates(
    product_id: int,
    original_rm_id: int,
    body: SubstituteScoreRequest,
) -> list[SubstituteProposal]:
    """Compliance-score a batch of candidate substitutes in a single LLM call.

    Scoring all candidates together lets the model rank them relative to each
    other, which yields more-differentiated scores than scoring each alone.
    """
    if await repo.get_product(product_id) is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if await repo.get_raw_material(original_rm_id) is None:
        raise HTTPException(status_code=404, detail="Original raw material not found")
    if not body.candidate_ids:
        return []

    return await compliance_agent.check_compliance(
        product_id,
        original_rm_id,
        top_x=len(body.candidate_ids),
        candidate_ids=body.candidate_ids,
    )


@router.get(
    "/{product_id}/{original_rm_id}/candidates/{candidate_rm_id}",
    response_model=SubstituteProposal,
)
async def score_substitute_candidate(
    product_id: int, original_rm_id: int, candidate_rm_id: int
) -> SubstituteProposal:
    """Compliance-score a single candidate substitute against the original raw material."""
    product = await repo.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if await repo.get_raw_material(original_rm_id) is None:
        raise HTTPException(status_code=404, detail="Original raw material not found")
    if await repo.get_raw_material(candidate_rm_id) is None:
        raise HTTPException(status_code=404, detail="Candidate raw material not found")

    proposals = await compliance_agent.check_compliance(
        product_id, original_rm_id, top_x=1, candidate_ids=[candidate_rm_id]
    )
    if not proposals:
        raise HTTPException(status_code=502, detail="Compliance scoring failed")
    # Prefer the proposal matching the candidate id; otherwise use the top-ranked.
    for p in proposals:
        if p.id == candidate_rm_id:
            return p
    return proposals[0]


@router.get("/{product_id}/{raw_material_id}", response_model=ComplianceResult)
async def get_compliance_for_material(product_id: int, raw_material_id: int) -> ComplianceResult:
    product = await repo.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    raw_material = await repo.get_raw_material(raw_material_id)
    if raw_material is None:
        raise HTTPException(status_code=404, detail="Raw material not found")

    proposals = await compliance_agent.check_compliance(product_id, raw_material_id)
    return ComplianceResult(
        raw_material_id=raw_material_id,
        proposal=proposals[0] if proposals else None,
    )


@router.get("/{product_id}", response_model=list[ComplianceResult])
async def get_compliance(product_id: int) -> list[ComplianceResult]:
    product = await repo.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    bom = await repo.get_bom(product_id)
    if bom is None or not bom.consumed_raw_material_ids:
        return []

    async def _check(rm_id: int) -> ComplianceResult:
        proposals = await compliance_agent.check_compliance(product_id, rm_id)
        return ComplianceResult(
            raw_material_id=rm_id,
            proposal=proposals[0] if proposals else None,
        )

    results = await asyncio.gather(*[_check(rm_id) for rm_id in bom.consumed_raw_material_ids])
    return [r for r in results if r.proposal is not None]
