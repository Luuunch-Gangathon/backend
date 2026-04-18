from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException

from app.data import repo
from app.agents.substitution.substitution_agent import SubstitutionAgent
from app.schemas import RawMaterial, RawMaterialDetail

router = APIRouter(prefix="/raw-materials", tags=["raw-materials"])

_substitution = SubstitutionAgent()


@router.get("", response_model=list[RawMaterial])
async def list_raw_materials(
    name: Optional[str] = None,
    company_id: Optional[str] = None,
) -> list[RawMaterial]:
    return await repo.list_raw_materials(name=name, company_id=company_id)


@router.get("/{rm_id}", response_model=RawMaterialDetail)
async def get_raw_material(rm_id: str) -> RawMaterialDetail:
    detail = await repo.get_raw_material(rm_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Raw material not found")
    detail.substitute_ids = await _substitution.get_substitutes(
        rm_id=rm_id,
        canonical_name=detail.canonical_name,
    )
    return detail
