from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.data import repo
from app.schemas import ConsolidationGroup

router = APIRouter(tags=["consolidation"])


@router.get("/consolidation-groups", response_model=list[ConsolidationGroup])
def list_groups() -> list[ConsolidationGroup]:
    return repo.list_consolidation_groups()


@router.get("/consolidation-groups/{group_id}", response_model=ConsolidationGroup)
def get_group(group_id: str) -> ConsolidationGroup:
    group = repo.get_consolidation_group(group_id)
    if group is None:
        raise HTTPException(status_code=404, detail=f"Consolidation group {group_id} not found")
    return group
