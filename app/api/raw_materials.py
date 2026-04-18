from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from app.data import repo
from app.schemas import RawMaterial

router = APIRouter(tags=["raw_materials"])


@router.get("/raw-materials", response_model=list[RawMaterial])
async def list_raw_materials(
    name: Optional[str] = None,
    company_id: Optional[str] = None,
) -> list[RawMaterial]:
    return await repo.list_raw_materials(name=name, company_id=company_id)
