from __future__ import annotations

from urllib.parse import unquote

from fastapi import APIRouter

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


@router.post(
    "/compliance-check",
    response_model=ComplianceResult,
    response_model_by_alias=True,
)
def compliance_check(payload: ComplianceInput) -> ComplianceResult:
    return ComplianceResult(
        passed=True,
        requirements=payload.requirements,
        evidence=fixtures.EVIDENCE_BUNDLE,
    )


@router.get("/suppliers/rank", response_model=list[Supplier])
def rank_suppliers(ingredient_id: str) -> list[Supplier]:
    return repo.rank_suppliers(ingredient_id)
