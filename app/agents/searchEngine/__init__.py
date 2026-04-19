"""Enrichment search engine — config-driven material & product property enrichment.

Usage (sync — enrichment only):
    from app.agents.searchEngine import enrich, enrich_product
    result = enrich(raw_fields)
    result = enrich_product(product_name, brand="Centrum")

Usage (async — enrichment + DB persistence):
    from app.agents.searchEngine import enrich_and_store, enrich_product_and_store
    result = await enrich_and_store(raw_fields, raw_material_name="magnesium-oxide")
    result = await enrich_product_and_store(product_sku, product_name, brand="Centrum")
"""

from __future__ import annotations

import asyncio
import json
import logging
from functools import partial
from pathlib import Path

from app.agents.searchEngine.engine import (
    run_enrichment,
    run_material_enrichment,
    run_material_enrichment_shortened,
    run_product_enrichment,
    run_product_enrichment_shortened,
)
from app.agents.searchEngine.models import EnrichmentResult
from app.agents.searchEngine.normalizer import normalize
from app.data import db, rag
from app.data.rag import store_embedding

logger = logging.getLogger(__name__)

_RESULTS_PATH = Path(__file__).resolve().parents[3] / "enrichment_results.json"


# ─── Raw material enrichment ─────────────────────────────────────────────────


def enrich(raw_fields: dict) -> EnrichmentResult:
    """Enrich a raw material from DB fields (no DB persistence).

    Args:
        raw_fields: Dict with keys Id, SKU, CompanyId, and optionally SupplierIds.

    Returns:
        EnrichmentResult with all properties filled or marked unknown.
    """
    context = normalize(raw_fields)
    return run_material_enrichment_shortened(context["normalized_name"], context)


async def enrich_and_store(
    raw_fields: dict,
    raw_material_name: str,
) -> EnrichmentResult:
    """Enrich a raw material and persist the result to the DB.

    Args:
        raw_fields: Dict with keys Id, SKU, CompanyId, and optionally SupplierIds.
        raw_material_name: Canonical name from raw_material_map (hyphenated).
                           Used as the key in substitution_groups.

    Returns:
        EnrichmentResult with all properties filled or marked unknown.
    """
    # Resolve supplier names at async level so sync handlers don't need DB access
    context = normalize(raw_fields)
    supplier_ids = context.get("supplier_ids", [])
    if supplier_ids:
        raw_ids = [int(sid.replace("sup_db_", "")) for sid in supplier_ids]
        async with db.get_conn() as conn:
            rows = await conn.fetch(
                "SELECT name FROM suppliers WHERE id = ANY($1::int[])",
                raw_ids,
            )
        context["supplier_names"] = [r["name"] for r in rows]

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None, partial(run_material_enrichment_shortened, context["normalized_name"], context)
    )

    await store_embedding({
        "material": {
            "normalized_name": raw_material_name,
            "properties": result.model_dump()["properties"],
        },
    })

    return result


# ─── Product enrichment ──────────────────────────────────────────────────────


def enrich_product(
    product_name: str,
    *,
    brand: str = "unknown",
    product_sku: str = "",
    company_id: str = "unknown",
) -> EnrichmentResult:
    """Enrich a finished product (no DB persistence).

    Args:
        product_name: Human-readable product name (e.g. "Centrum Silver Women 50+").
        brand: Brand/company name for more precise search.
        product_sku: Original SKU (e.g. "FG-walmart-10324636").
        company_id: Company ID string.

    Returns:
        EnrichmentResult with product properties filled or marked unknown.
    """
    context = {
        "material_id": product_sku or product_name,
        "raw_sku": product_sku,
        "company_id": company_id,
        "supplier_ids": [],
        "brand": brand,
    }

    return run_product_enrichment_shortened(product_name, context)


async def enrich_product_and_store(
    product_sku: str,
    product_name: str,
    *,
    brand: str = "unknown",
    company_id: str = "unknown",
) -> EnrichmentResult:
    """Enrich a finished product and persist the result to the DB.

    Args:
        product_sku: Original SKU (e.g. "FG-walmart-10324636").
        product_name: Human-readable product name.
        brand: Brand/company name.
        company_id: Company ID string.

    Returns:
        EnrichmentResult with product properties filled or marked unknown.
    """
    context = {
        "material_id": product_sku,
        "raw_sku": product_sku,
        "company_id": company_id,
        "supplier_ids": [],
        "brand": brand,
    }

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None, partial(run_product_enrichment_shortened, product_name, context),
    )

    # Store product spec on the products table
    spec_json = json.dumps(result.model_dump()["properties"])
    async with db.get_conn() as conn:
        await conn.execute(
            "UPDATE products SET spec = $1 WHERE sku = $2",
            spec_json, product_sku,
        )

    return result


# ─── Utilities ────────────────────────────────────────────────────────────────


def save_results_json(results: list[dict]) -> Path:
    """Write enrichment results to JSON for manual review."""
    _RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info("Saved %d enrichment results to %s", len(results), _RESULTS_PATH)
    return _RESULTS_PATH
