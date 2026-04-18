from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.data import repo
from app.schemas import Product, BOM

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[Product])
async def list_products(company_id: Optional[int] = Query(default=None)) -> list[Product]:
    return await repo.list_products(company_id=company_id)


@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: int) -> Product:
    result = await repo.get_product(product_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return result


@router.get("/{product_id}/bom", response_model=BOM)
async def get_bom(product_id: int) -> BOM:
    result = await repo.get_bom(product_id)
    if result is None:
        raise HTTPException(status_code=404, detail="BOM not found")
    return result
