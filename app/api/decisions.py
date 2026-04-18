from __future__ import annotations
from fastapi import APIRouter, Query
from app.data import db
from app.schemas import Decision, DecisionCreate

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.post("", response_model=Decision)
async def create_decision(req: DecisionCreate) -> Decision:
    async with db.get_conn() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO decisions
              (session_id, status, original_raw_material_name, substitute_raw_material_name,
               product_sku, score, reasoning)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, session_id, status, original_raw_material_name,
                      substitute_raw_material_name, product_sku, score, reasoning
            """,
            req.session_id,
            req.status,
            req.original_raw_material_name,
            req.substitute_raw_material_name,
            req.product_sku,
            req.score,
            req.reasoning,
        )
    return Decision(**dict(row))


@router.get("", response_model=list[Decision])
async def list_decisions(session_id: str = Query(...)) -> list[Decision]:
    async with db.get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT id, session_id, status, original_raw_material_name,
                   substitute_raw_material_name, product_sku, score, reasoning
            FROM decisions
            WHERE session_id = $1
            ORDER BY id
            """,
            session_id,
        )
    return [Decision(**dict(r)) for r in rows]
