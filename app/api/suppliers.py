from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.data import repo
from app.schemas import Supplier

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=list[Supplier])
async def list_suppliers() -> list[Supplier]:
    return await repo.list_suppliers()


@router.get("/{supplier_id}", response_model=Supplier)
async def get_supplier(supplier_id: int) -> Supplier:
    result = await repo.get_supplier(supplier_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return result
