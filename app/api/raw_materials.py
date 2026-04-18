from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.data import repo
from app.schemas import RawMaterial, Supplier, Product, Company

router = APIRouter(prefix="/raw-materials", tags=["raw-materials"])


@router.get("", response_model=list[RawMaterial])
async def list_raw_materials() -> list[RawMaterial]:
    return await repo.list_raw_materials()


@router.get("/{rm_id}/suppliers", response_model=list[Supplier])
async def list_raw_material_suppliers(rm_id: int) -> list[Supplier]:
    return await repo.list_suppliers_for_raw_material(rm_id)


@router.get("/{rm_id}/finished-goods", response_model=list[Product])
async def list_raw_material_finished_goods(rm_id: int) -> list[Product]:
    return await repo.list_finished_goods_for_raw_material(rm_id)


@router.get("/{rm_id}/companies", response_model=list[Company])
async def list_raw_material_companies(rm_id: int) -> list[Company]:
    return await repo.list_companies_for_raw_material(rm_id)


@router.get("/{rm_id}", response_model=RawMaterial)
async def get_raw_material(rm_id: int) -> RawMaterial:
    result = await repo.get_raw_material(rm_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Raw material not found")
    return result
