"""Template endpoint — `GET /ingredients`.

Use this as the reference pattern for every new endpoint:

  1. Declare a Pydantic response model in `app/schemas/` (see `ingredient.py`).
  2. Register the router here (or a new module under `app/api/`).
  3. Pull data through `app/data/repo.py`, not from files directly.
  4. Wire the router into `app/main.py`.
  5. The frontend picks the new endpoint up automatically via
     `npm run gen:types` against `/openapi.json`.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from app.data import repo
from app.schemas import Ingredient

router = APIRouter(tags=["ingredients"])


@router.get("/ingredients", response_model=list[Ingredient])
def list_ingredients(
    name: Optional[str] = None,
    company_id: Optional[str] = None,
) -> list[Ingredient]:
    return repo.list_ingredients(name=name, company_id=company_id)
