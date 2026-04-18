from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.data import repo
from app.schemas import Company, CompanyDetail, FinishedGood

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[Company])
async def list_companies() -> list[Company]:
    return await repo.list_companies()


@router.get("/{company_id}", response_model=CompanyDetail)
async def get_company(company_id: str) -> CompanyDetail:
    result = await repo.get_company(company_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return result


@router.get("/{company_id}/products", response_model=list[FinishedGood])
async def list_company_products(company_id: str) -> list[FinishedGood]:
    return await repo.list_products_by_company(company_id)
