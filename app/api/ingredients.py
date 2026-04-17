from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException

from app.data import repo
from app.schemas import Ingredient, Supplier

router = APIRouter(tags=["ingredients"])


@router.get("/ingredients", response_model=list[Ingredient])
def list_ingredients(
    name: Optional[str] = None,
    company_id: Optional[str] = None,
) -> list[Ingredient]:
    return repo.list_ingredients(name=name, company_id=company_id)


@router.get("/ingredients/{ingredient_id}/suppliers", response_model=list[Supplier])
def suppliers_for_ingredient(ingredient_id: str) -> list[Supplier]:
    if repo.get_ingredient(ingredient_id) is None:
        raise HTTPException(status_code=404, detail=f"Ingredient {ingredient_id} not found")
    return repo.suppliers_for(ingredient_id)
