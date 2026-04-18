"""Repository layer — all DB reads. No business logic. No agent calls.

All IDs are plain integers matching Postgres PRIMARY KEY.
"""

from __future__ import annotations

import json
import re
from typing import Optional

from app.schemas import (
    Company,
    Product,
    BOM,
    RawMaterial,
    SimilarRawMaterial,
    Supplier,
    Proposal,
    EvidenceItem,
    ComplianceRequirement,
    Tradeoffs,
    RolloutPlan,
    Substitution,
    AgnesSuggestedQuestion,
    Decision,
)

from . import db

SIMILARITY_THRESHOLD: float = 0.75  # cosine similarity cutoff (-1..1)


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------

async def list_companies() -> list[Company]:
    async with db.get_conn() as conn:
        rows = await conn.fetch("SELECT id, name FROM companies ORDER BY name")
    return [Company(id=r["id"], name=r["name"]) for r in rows]


async def get_company(company_id: int) -> Optional[Company]:
    async with db.get_conn() as conn:
        row = await conn.fetchrow("SELECT id, name FROM companies WHERE id = $1", company_id)
    return Company(id=row["id"], name=row["name"]) if row else None


# ---------------------------------------------------------------------------
# Products (finished goods)
# ---------------------------------------------------------------------------

async def list_products(company_id: Optional[int] = None) -> list[Product]:
    async with db.get_conn() as conn:
        if company_id is not None:
            rows = await conn.fetch(
                "SELECT id, sku, company_id FROM products WHERE type = 'finished-good' AND company_id = $1 ORDER BY sku",
                company_id,
            )
        else:
            rows = await conn.fetch(
                "SELECT id, sku, company_id FROM products WHERE type = 'finished-good' ORDER BY sku"
            )
    return [Product(id=r["id"], sku=r["sku"], company_id=r["company_id"]) for r in rows]


async def get_product(product_id: int) -> Optional[Product]:
    async with db.get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT id, sku, company_id FROM products WHERE id = $1 AND type = 'finished-good'",
            product_id,
        )
    return Product(id=row["id"], sku=row["sku"], company_id=row["company_id"]) if row else None


async def get_bom(product_id: int) -> Optional[BOM]:
    async with db.get_conn() as conn:
        bom_row = await conn.fetchrow(
            "SELECT id FROM boms WHERE produced_product_id = $1", product_id
        )
        if bom_row is None:
            return None
        rm_rows = await conn.fetch(
            """
            SELECT p.id
            FROM bom_components bc
            JOIN products p ON p.id = bc.consumed_product_id
            WHERE bc.bom_id = $1
            """,
            bom_row["id"],
        )
    return BOM(
        id=bom_row["id"],
        produced_product_id=product_id,
        consumed_raw_material_ids=[r["id"] for r in rm_rows],
    )


# ---------------------------------------------------------------------------
# Raw materials
# ---------------------------------------------------------------------------

async def list_raw_materials() -> list[RawMaterial]:
    async with db.get_conn() as conn:
        rows = await conn.fetch(
            "SELECT id, sku FROM products WHERE type = 'raw-material' ORDER BY sku"
        )
    return [RawMaterial(id=r["id"], sku=r["sku"]) for r in rows]


async def get_raw_material(rm_id: int) -> Optional[RawMaterial]:
    async with db.get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT id, sku FROM products WHERE id = $1 AND type = 'raw-material'", rm_id
        )
    return RawMaterial(id=row["id"], sku=row["sku"]) if row else None


_DB_ID_RE = re.compile(r"^rm_db_(\d+)$")


async def find_similar_raw_materials(
    raw_material_id: str,
) -> list[SimilarRawMaterial]:
    """Return raw materials whose embedding is above SIMILARITY_THRESHOLD
    cosine-similar to the source id's embedding.

    DB-backed ids only (rm_db_<n>). Fixture ids and malformed ids return [].
    Source id is excluded from results.
    """
    m = _DB_ID_RE.match(raw_material_id)
    if not m:
        return []
    db_id = int(m.group(1))

    try:
        async with db.get_conn() as conn:
            rows = await conn.fetch(
                """
                WITH source AS (
                    SELECT sg.raw_material_name, sg.embedding
                    FROM raw_material_map rmm
                    JOIN substitution_groups sg
                      ON sg.raw_material_name = rmm.raw_material_name
                    WHERE rmm.raw_material_id = $1
                    LIMIT 1
                )
                SELECT rmm.raw_material_id,
                       1 - (sg.embedding <=> (SELECT embedding FROM source)) AS score
                FROM   substitution_groups sg
                JOIN   raw_material_map    rmm ON rmm.raw_material_name = sg.raw_material_name
                WHERE  sg.raw_material_name <> (SELECT raw_material_name FROM source)
                  AND  1 - (sg.embedding <=> (SELECT embedding FROM source)) >= $2
                ORDER  BY score DESC
                """,
                db_id,
                SIMILARITY_THRESHOLD,
            )
    except Exception:
        return []

    return [
        SimilarRawMaterial(
            raw_material_id=f"rm_db_{row['raw_material_id']}",
            similarity_score=float(row["score"]),
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------

async def list_suppliers() -> list[Supplier]:
    async with db.get_conn() as conn:
        rows = await conn.fetch("SELECT id, name FROM suppliers ORDER BY name")
    return [Supplier(id=r["id"], name=r["name"]) for r in rows]


async def get_supplier(supplier_id: int) -> Optional[Supplier]:
    async with db.get_conn() as conn:
        row = await conn.fetchrow("SELECT id, name FROM suppliers WHERE id = $1", supplier_id)
    return Supplier(id=row["id"], name=row["name"]) if row else None


# ---------------------------------------------------------------------------
# Proposals
# ---------------------------------------------------------------------------

def _parse_proposal(row) -> Proposal:
    evidence_raw = row["evidence"] if row["evidence"] else []
    if isinstance(evidence_raw, str):
        evidence_raw = json.loads(evidence_raw)

    compliance_raw = row["compliance_requirements"] if row["compliance_requirements"] else []
    if isinstance(compliance_raw, str):
        compliance_raw = json.loads(compliance_raw)

    return Proposal(
        id=row["id"],
        kind=row["kind"],
        headline=row["headline"],
        summary=row["summary"],
        raw_material_id=row["raw_material_id"],
        proposed_action=row["proposed_action"],
        companies_involved=list(row["companies_involved"] or []),
        current_suppliers=list(row["current_supplier_ids"] or []),
        proposed_supplier_id=row["proposed_supplier_id"],
        proposed_substitute_raw_material_id=row["proposed_substitute_rm_id"],
        fragmentation_score=row["fragmentation_score"],
        tradeoffs=Tradeoffs(
            gained=list(row["tradeoffs_gained"] or []),
            atRisk=list(row["tradeoffs_at_risk"] or []),
        ),
        conservative=RolloutPlan(
            affected_skus=list(row["conservative_skus"] or []),
            timeline=row["conservative_timeline"] or "",
        ),
        aggressive=RolloutPlan(
            affected_skus=list(row["aggressive_skus"] or []),
            timeline=row["aggressive_timeline"] or "",
        ),
        evidence=[EvidenceItem(**e) for e in evidence_raw],
        estimated_impact=row["estimated_impact"] or "",
        compliance_requirements=[ComplianceRequirement(**c) for c in compliance_raw],
    )


_PROPOSALS_SELECT = """
    SELECT DISTINCT ON (p.id)
           p.id, p.kind, p.headline, p.summary,
           p.proposed_action, p.companies_involved, p.current_supplier_ids,
           p.proposed_supplier_id, p.proposed_substitute_rm_name,
           p.fragmentation_score, p.tradeoffs_gained, p.tradeoffs_at_risk,
           p.conservative_skus, p.conservative_timeline,
           p.aggressive_skus, p.aggressive_timeline,
           p.evidence, p.estimated_impact, p.compliance_requirements,
           pr.id  AS raw_material_id,
           pr2.id AS proposed_substitute_rm_id
    FROM proposals p
    JOIN products pr
      ON pr.sku LIKE '%' || p.raw_material_name || '%'
     AND pr.type = 'raw-material'
    LEFT JOIN products pr2
      ON p.proposed_substitute_rm_name IS NOT NULL
     AND pr2.sku LIKE '%' || p.proposed_substitute_rm_name || '%'
     AND pr2.type = 'raw-material'
"""


async def list_proposals() -> list[Proposal]:
    async with db.get_conn() as conn:
        rows = await conn.fetch(_PROPOSALS_SELECT + " ORDER BY p.id")
    result = [_parse_proposal(r) for r in rows]
    result.sort(key=lambda p: p.fragmentation_score, reverse=True)
    return result


async def get_proposal(proposal_id: int) -> Optional[Proposal]:
    async with db.get_conn() as conn:
        row = await conn.fetchrow(
            _PROPOSALS_SELECT + " WHERE p.id = $1 ORDER BY p.id",
            proposal_id,
        )
    return _parse_proposal(row) if row else None


# ---------------------------------------------------------------------------
# Substitutions
# ---------------------------------------------------------------------------

async def list_substitutions() -> list[Substitution]:
    async with db.get_conn() as conn:
        rows = await conn.fetch(
            "SELECT id, from_raw_material_id, to_raw_material_id, reason FROM substitutions ORDER BY id"
        )
    return [
        Substitution(
            id=r["id"],
            from_raw_material_id=r["from_raw_material_id"],
            to_raw_material_id=r["to_raw_material_id"],
            reason=r["reason"],
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------

async def create_decision(
    proposal_id: int, status: str, reason: Optional[str]
) -> Decision:
    async with db.get_conn() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO decisions (proposal_id, status, reason)
            VALUES ($1, $2, $3)
            ON CONFLICT (proposal_id) DO UPDATE
                SET status     = EXCLUDED.status,
                    reason     = EXCLUDED.reason,
                    created_at = NOW()
            RETURNING id, proposal_id, status, reason, created_at
            """,
            proposal_id, status, reason,
        )
    return Decision(
        id=row["id"],
        proposal_id=row["proposal_id"],
        status=row["status"],
        reason=row["reason"],
        created_at=row["created_at"],
    )


async def get_decision_by_proposal(proposal_id: int) -> Optional[Decision]:
    async with db.get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT id, proposal_id, status, reason, created_at FROM decisions WHERE proposal_id = $1",
            proposal_id,
        )
    if not row:
        return None
    return Decision(
        id=row["id"],
        proposal_id=row["proposal_id"],
        status=row["status"],
        reason=row["reason"],
        created_at=row["created_at"],
    )



# ---------------------------------------------------------------------------
# Agnes suggestions
# ---------------------------------------------------------------------------

async def list_agnes_suggestions(proposal_id: int) -> list[AgnesSuggestedQuestion]:
    async with db.get_conn() as conn:
        rows = await conn.fetch(
            "SELECT id, question FROM agnes_suggestions WHERE proposal_id = $1 ORDER BY id",
            proposal_id,
        )
    return [AgnesSuggestedQuestion(id=r["id"], question=r["question"]) for r in rows]
