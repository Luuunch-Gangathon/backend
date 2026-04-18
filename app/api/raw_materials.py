from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException

from app.agents.controller import controller
from app.schemas import RawMaterial, RawMaterialDetail

router = APIRouter(prefix="/raw-materials", tags=["raw-materials"])


@router.get("", response_model=list[RawMaterial])
async def list_raw_materials(
    name: Optional[str] = None,
    company_id: Optional[str] = None,
) -> list[RawMaterial]:
    return await controller.list_raw_materials(name=name, company_id=company_id)


@router.get("/{rm_id}", response_model=RawMaterialDetail)
async def get_raw_material(rm_id: str) -> RawMaterialDetail:
    result = await controller.get_raw_material(rm_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Raw material not found")
    return result
