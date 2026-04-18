"""similarity_compliance_check tool — score candidate substitutes for compliance fit."""

from __future__ import annotations
import logging

from app.data import repo
from app.agents import compliance
from app.schemas import RawMaterial, Product, ComplianceMatch

logger = logging.getLogger(__name__)


async def similarity_compliance_check(
    original_name: str,
    candidate_names: list[str],
    product_sku: str | None = None,
    top_x: int = 5,
) -> list[ComplianceMatch]:
    """Score each candidate as a substitute for original_name (0–100).

    Does NOT persist to DB — ephemeral. Persistence happens on user Accept.
    """
    # Resolve original
    original_rm = await repo.get_raw_material_by_name(original_name)
    if original_rm is None:
        # Synthesize minimal RawMaterial so compliance can still run
        original_rm = RawMaterial(id=0, sku=original_name)

    # Resolve candidates
    candidate_rms: list[RawMaterial] = []
    for name in candidate_names:
        rm = await repo.get_raw_material_by_name(name)
        if rm is None:
            rm = RawMaterial(id=0, sku=name)
        candidate_rms.append(rm)

    if not candidate_rms:
        return []

    # Get cosine similarities from embeddings
    similarity_map = await repo.cosine_similarity_for_pairs(original_name, candidate_names)

    sub_pairs = []
    for rm, name in zip(candidate_rms, candidate_names):
        sim = similarity_map.get(name, 0.5)
        sub_pairs.append((rm, sim))

    # Resolve product context
    product: Product
    product_profile: dict | None = None
    if product_sku:
        resolved = await repo.get_product_by_sku(product_sku)
        product = resolved if resolved else Product(id=0, sku=product_sku, company_id=0)
        try:
            product_profile = await repo.get_product_dietary_profile(product_sku)
        except Exception:
            logger.exception("compliance_check: failed to load product profile for %r", product_sku)
            product_profile = None
    else:
        product = Product(id=0, sku="N/A", company_id=0)

    # Fetch enriched specs for the original + all candidates (dietary flags,
    # allergens, certifications) so the compliance LLM can make detailed
    # satisfies/violates decisions against product_profile.
    all_names = [original_name, *candidate_names]
    try:
        spec_map = await repo.get_material_specs(all_names)
    except Exception:
        logger.exception("compliance_check: failed to load material specs")
        spec_map = {}
    original_spec = spec_map.get(original_name)
    candidate_specs = {name: spec_map.get(name, {}) for name in candidate_names}

    # Call compliance ranker with full context
    scores = await compliance.rank_substitutes(
        original_rm,
        sub_pairs,
        product,
        top_x,
        original_spec=original_spec,
        candidate_specs=candidate_specs,
        candidate_names=candidate_names,
        product_profile=product_profile,
    )

    if not scores:
        return []

    # Map scores back to candidate names; enrich with companies/suppliers
    id_to_name = {rm.id: name for rm, name in zip(candidate_rms, candidate_names)}
    id_to_rm = {rm.id: rm for rm in candidate_rms}

    results: list[ComplianceMatch] = []
    for score_obj in scores:
        rm = id_to_rm.get(score_obj.id)
        name = id_to_name.get(score_obj.id, f"id:{score_obj.id}")
        sim = similarity_map.get(name, 0.5)

        context = await repo.get_material_context([name])
        companies = sorted({r["company_name"] for r in context if r.get("company_name")})
        suppliers = sorted({r["supplier_name"] for r in context if r.get("supplier_name")})

        results.append(ComplianceMatch(
            raw_material_id=rm.id if rm and rm.id != 0 else None,
            raw_material_name=name,
            score=score_obj.score,
            reasoning=score_obj.reasoning,
            similarity=sim,
            companies_affected=companies,
            suppliers=suppliers,
        ))

    logger.info(
        "compliance_check tool: %r vs %d candidates → %d scored",
        original_name, len(candidate_names), len(results),
    )
    return results
