from __future__ import annotations

from urllib.parse import unquote

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.data import fixtures, repo
from app.schemas import (
    ComplianceInput,
    ComplianceResult,
    EvidenceBundle,
    Supplier,
)

router = APIRouter(tags=["enrichment"])


@router.get("/enrich/{ingredient}", response_model=EvidenceBundle)
def enrich(ingredient: str) -> EvidenceBundle:
    # ``ingredient`` is the canonical name, URL-encoded; decode for future use.
    _canonical = unquote(ingredient)
    return fixtures.EVIDENCE_BUNDLE


@router.post("/compliance-check")
def compliance_check(payload: ComplianceInput) -> JSONResponse:
    result = ComplianceResult(
        passed=True,
        requirements=payload.requirements,
        evidence=fixtures.EVIDENCE_BUNDLE,
    )
    # Serialise with by_alias so the JSON key is the contract-mandated ``pass``.
    return JSONResponse(content=result.model_dump(by_alias=True))


@router.get("/suppliers/rank", response_model=list[Supplier])
def rank_suppliers(ingredient_id: str) -> list[Supplier]:
    return repo.rank_suppliers(ingredient_id)
