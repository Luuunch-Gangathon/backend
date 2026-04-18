from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.agents.controller import controller
from app.schemas import Supplier, SupplierDetail

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=list[Supplier])
async def list_suppliers() -> list[Supplier]:
    return await controller.list_suppliers()


@router.get("/{supplier_id}", response_model=SupplierDetail)
async def get_supplier(supplier_id: str) -> SupplierDetail:
    result = await controller.get_supplier(supplier_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return result
