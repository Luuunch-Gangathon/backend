from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.data import repo
from app.schemas import FinishedGoodDetail

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/{product_id}", response_model=FinishedGoodDetail)
async def get_product(product_id: str) -> FinishedGoodDetail:
    result = await repo.get_product(product_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return result
