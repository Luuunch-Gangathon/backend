from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.data import repo
from app.schemas import Company, Product

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[Company])
async def list_companies() -> list[Company]:
    return await repo.list_companies()


@router.get("/{company_id}", response_model=Company)
async def get_company(company_id: int) -> Company:
    result = await repo.get_company(company_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return result
