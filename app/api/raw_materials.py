from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.data import repo
from app.schemas import RawMaterial

router = APIRouter(prefix="/raw-materials", tags=["raw-materials"])


@router.get("", response_model=list[RawMaterial])
async def list_raw_materials() -> list[RawMaterial]:
    return await repo.list_raw_materials()


@router.get("/{rm_id}", response_model=RawMaterial)
async def get_raw_material(rm_id: int) -> RawMaterial:
    result = await repo.get_raw_material(rm_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Raw material not found")
    return result
