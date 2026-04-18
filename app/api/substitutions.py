from __future__ import annotations
from fastapi import APIRouter
from app.data import repo
from app.schemas import Substitution

router = APIRouter(prefix="/substitutions", tags=["substitutions"])


@router.get("", response_model=list[Substitution])
async def list_substitutions() -> list[Substitution]:
    return []
