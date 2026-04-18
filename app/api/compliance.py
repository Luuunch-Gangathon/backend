from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException

from app.data import repo
from app.agents import compliance as compliance_agent
from app.schemas import ComplianceResult

router = APIRouter(prefix="/compliance", tags=["compliance"])
logger = logging.getLogger(__name__)


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
