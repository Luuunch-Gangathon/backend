"""SearchEngine

Enriches raw materials and finished products with specs, then upgrades their embeddings.

Entry points:
  run_all()              — scheduled: enrich all materials that still have no spec
  run_one(rm_name)       — on-demand: enrich a single material
  run_all_products()     — scheduled: enrich all finished products without spec
  run_one_product(sku)   — on-demand: enrich a single product

Flow per entity:
  Name → searchEngine waterfall (web sources → LLM knowledge fallback)
  → rag.store_embedding()  (upserts spec + rich vector)

Raw materials use config.py (8 properties, 12 sources).
Products use product_config.py (5 properties: dietary_flags, allergens,
certifications, regulatory_status, form_grade).

Writes to:
  - substitution_groups (spec + embedding columns via rag.store_embedding)
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from functools import partial

from app.agents.searchEngine.engine import (
    run_material_enrichment,
    run_material_enrichment_shortened,
    run_product_enrichment,
    run_product_enrichment_shortened,
)
from app.agents.searchEngine.models import EnrichmentResult
from app.data import rag

logger = logging.getLogger(__name__)


# ─── Raw material enrichment ─────────────────────────────────────────────────


async def run_all() -> None:
    """Enrich all raw materials that have a name-only embedding but no spec yet."""
    names = await rag.get_unenriched_names()
    logger.info("SearchEngine: enriching %d materials", len(names))
    if not names:
        return

    total = len(names)
    ok, fail = 0, 0
    for i, name in enumerate(names, 1):
        try:
            await _enrich_and_embed(name)
            ok += 1
        except Exception:
            fail += 1
            logger.exception("SearchEngine: failed for %r — skipping", name)
        logger.info("SearchEngine: progress %d/%d (ok=%d, fail=%d)", i, total, ok, fail)

    logger.info("SearchEngine: done — %d ok, %d failed", ok, fail)


async def run_one(raw_material_name: str) -> None:
    """Enrich and embed a single raw material."""
    logger.info("SearchEngine: on-demand enrich for %r", raw_material_name)
    await _enrich_and_embed(raw_material_name)
    logger.info("SearchEngine: done for %r", raw_material_name)


async def _enrich_and_embed(name: str) -> None:
    """Run the material enrichment waterfall, then store a rich embedding."""
    from app.data import db

    t0 = time.monotonic()
    context = {
        "material_id": name,
        "raw_sku": name,
        "company_id": "unknown",
        "supplier_ids": [],
    }

    async with db.get_conn() as conn:
        row = await conn.fetchrow(
            """
            SELECT raw_material_id, raw_material_sku, company_id
            FROM raw_material_map
            WHERE raw_material_name = $1
            LIMIT 1
            """,
            name,
        )
        if row:
            context["material_id"] = f"ing_db_{row['raw_material_id']}"
            context["raw_sku"] = row["raw_material_sku"]
            context["company_id"] = f"co_db_{row['company_id']}"

        supplier_rows = await conn.fetch(
            """
            SELECT DISTINCT s.name
            FROM raw_material_map rm
            JOIN suppliers s ON s.id = rm.supplier_id
            WHERE rm.raw_material_name = $1 AND rm.supplier_id IS NOT NULL
            """,
            name,
        )
        if supplier_rows:
            context["supplier_names"] = [r["name"] for r in supplier_rows]

    loop = asyncio.get_event_loop()
    result: EnrichmentResult = await loop.run_in_executor(
        None, partial(run_material_enrichment, name, context) # todo testing OFF
    )
    elapsed = time.monotonic() - t0

    enriched_result = _to_store_format(result, elapsed)
    logger.info(
        "DB payload for %r:\n%s",
        name, json.dumps(enriched_result, indent=2, default=str),
    )
    await rag.store_embedding(enriched_result)
    logger.info(
        "Stored embedding for %r (completeness %d/%d, %.1fs)",
        name, result.completeness, result.total_properties, elapsed,
    )


# ─── Product enrichment ──────────────────────────────────────────────────────


async def run_all_products() -> None:
    """Enrich all finished products that don't have a spec yet.

    Queries the products table for finished goods, extracts a human-readable
    name from the SKU, and runs the product enrichment waterfall.
    """
    from app.data import db

    async with db.get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT p.id, p.sku, c.name AS company_name
            FROM products p
            JOIN companies c ON p.company_id = c.id
            WHERE p.type = 'finished-good'
              AND p.spec IS NULL
            """,
        )

    logger.info("SearchEngine: enriching %d products", len(rows))
    if not rows:
        return

    ok, fail = 0, 0
    for row in rows:
        try:
            await _enrich_product_and_store(
                product_sku=row["sku"],
                brand=row["company_name"],
                company_id=str(row["id"]),
            )
            ok += 1
        except Exception:
            fail += 1
            logger.exception(
                "SearchEngine: product enrichment failed for %r — skipping",
                row["sku"],
            )

    logger.info("SearchEngine: products done — %d ok, %d failed", ok, fail)


async def run_one_product(product_sku: str) -> None:
    """Enrich and embed a single finished product by SKU."""
    from app.data import db

    async with db.get_conn() as conn:
        row = await conn.fetchrow(
            """
            SELECT p.id, p.sku, c.name AS company_name
            FROM products p
            JOIN companies c ON p.company_id = c.id
            WHERE p.sku = $1 AND p.type = 'finished-good'
            """,
            product_sku,
        )

    if not row:
        logger.warning("SearchEngine: product %r not found", product_sku)
        return

    logger.info("SearchEngine: on-demand product enrich for %r", product_sku)
    await _enrich_product_and_store(
        product_sku=row["sku"],
        brand=row["company_name"],
        company_id=str(row["id"]),
    )
    logger.info("SearchEngine: done for product %r", product_sku)


async def _enrich_product_and_store(
    product_sku: str,
    brand: str,
    company_id: str,
) -> None:
    """Run the product enrichment waterfall, then store spec on the products table."""
    from app.data import db

    t0 = time.monotonic()

    product_name = _product_name_from_sku(product_sku, brand)

    context = {
        "material_id": product_sku,
        "raw_sku": product_sku,
        "company_id": company_id,
        "supplier_ids": [],
        "brand": brand,
    }

    loop = asyncio.get_event_loop()
    result: EnrichmentResult = await loop.run_in_executor(
        None, partial(run_product_enrichment_shortened, product_name, context),
    )
    elapsed = time.monotonic() - t0

    enriched_result = _to_store_format(result, elapsed)
    spec_json = json.dumps(enriched_result["material"]["properties"])
    logger.info(
        "DB payload for product %r:\n%s",
        product_sku, json.dumps(enriched_result, indent=2, default=str),
    )

    async with db.get_conn() as conn:
        await conn.execute(
            "UPDATE products SET spec = $1 WHERE sku = $2",
            spec_json, product_sku,
        )

    logger.info(
        "Stored product spec for %r (completeness %d/%d, %.1fs)",
        product_sku, result.completeness, result.total_properties, elapsed,
    )


def _product_name_from_sku(sku: str, brand: str) -> str:
    """Extract a human-readable product name from a finished-good SKU.

    FG-walmart-10324636                → "Equate" (just brand)
    FG-thrive-market-orgain-grass-fed-whey-protein-powder-vanilla-bean
        → "orgain grass fed whey protein powder vanilla bean"
    FG-the-vitamin-shoppe-vs-2453      → "The Vitamin Shoppe" (just brand)
    FG-vitacost-cure-hydration-...     → "cure hydration ..."
    """
    # Known retailer prefixes (multi-word joined by hyphen)
    _RETAILER_PREFIXES = [
        "the-vitamin-shoppe",
        "thrive-market",
        "sams-club",
        "walmart",
        "amazon",
        "target-a",
        "target",
        "cvs",
        "walgreens",
        "costco",
        "iherb",
        "gnc",
        "vitacost",
    ]

    remainder = sku
    if remainder.startswith("FG-"):
        remainder = remainder[3:]

    # Strip retailer prefix
    for prefix in _RETAILER_PREFIXES:
        if remainder.startswith(prefix + "-"):
            remainder = remainder[len(prefix) + 1:]
            break
        elif remainder == prefix:
            remainder = ""
            break

    # Replace hyphens with spaces
    name_candidate = remainder.replace("-", " ").strip()

    # If what remains is just a numeric/hex ID or empty, use brand only
    if not name_candidate or (len(name_candidate.split()) <= 1 and name_candidate.replace(" ", "").isalnum()):
        return brand

    # Don't prepend brand if the name already starts with it
    if name_candidate.lower().startswith(brand.lower()):
        return name_candidate

    return f"{brand} {name_candidate}"


# ─── Shared utilities ────────────────────────────────────────────────────────


def _to_store_format(result: EnrichmentResult, elapsed: float) -> dict:
    """Convert EnrichmentResult to the shape rag.store_embedding() expects."""
    return {
        "material": {
            "normalized_name": result.normalized_name,
            "properties": {
                prop: {
                    "value": pr.value,
                    "confidence": pr.confidence,
                    "source_name": pr.source_name,
                    "source_url_or_reasoning": pr.source_url_or_reasoning
                }
                for prop, pr in result.properties.items()
            },
        },
        "elapsed_seconds": elapsed,
    }
