from __future__ import annotations
import re

from fastapi import APIRouter, HTTPException
from app.data import repo
from app.schemas import RawMaterial, Supplier, Product, Company, SubstituteCandidate

router = APIRouter(prefix="/raw-materials", tags=["raw-materials"])


@router.get("", response_model=list[RawMaterial])
async def list_raw_materials() -> list[RawMaterial]:
    return await repo.list_raw_materials()


@router.get("/{rm_id}/suppliers", response_model=list[Supplier])
async def list_raw_material_suppliers(rm_id: int) -> list[Supplier]:
    return await repo.list_suppliers_for_raw_material(rm_id)


@router.get("/{rm_id}/finished-goods", response_model=list[Product])
async def list_raw_material_finished_goods(rm_id: int) -> list[Product]:
    return await repo.list_finished_goods_for_raw_material(rm_id)


@router.get("/{rm_id}/companies", response_model=list[Company])
async def list_raw_material_companies(rm_id: int) -> list[Company]:
    return await repo.list_companies_for_raw_material(rm_id)


_DB_ID_RE = re.compile(r"^rm_db_(\d+)$")


@router.get("/{rm_id}/substitutes", response_model=list[SubstituteCandidate])
async def list_raw_material_substitutes(rm_id: int, limit: int = 10) -> list[SubstituteCandidate]:
    """Vector-similarity candidates above the repo threshold. No LLM scoring."""
    original = await repo.get_raw_material(rm_id)
    if original is None:
        raise HTTPException(status_code=404, detail="Raw material not found")

    similar = await repo.find_similar_raw_materials(f"rm_db_{rm_id}")
    if not similar:
        return []

    candidates: list[SubstituteCandidate] = []
    seen: set[int] = set()
    for item in similar:
        m = _DB_ID_RE.match(item.raw_material_id)
        if not m:
            continue
        cid = int(m.group(1))
        if cid in seen:
            continue
        rm = await repo.get_raw_material(cid)
        if rm is None:
            continue
        seen.add(cid)
        candidates.append(
            SubstituteCandidate(id=rm.id, sku=rm.sku, similarity_score=item.similarity_score)
        )
        if len(candidates) >= limit:
            break
    return candidates


@router.get("/{rm_id}", response_model=RawMaterial)
async def get_raw_material(rm_id: int) -> RawMaterial:
    result = await repo.get_raw_material(rm_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Raw material not found")
    return result
