from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.agents.controller import controller
from app.schemas import Company, CompanyDetail, FinishedGood

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[Company])
def list_companies() -> list[Company]:
    return controller.list_companies()


@router.get("/{company_id}", response_model=CompanyDetail)
def get_company(company_id: str) -> CompanyDetail:
    result = controller.get_company(company_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return result


@router.get("/{company_id}/products", response_model=list[FinishedGood])
def list_company_products(company_id: str) -> list[FinishedGood]:
    return controller.list_products_by_company(company_id)
