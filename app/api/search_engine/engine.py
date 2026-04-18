"""Enrichment engine — domain-agnostic waterfall loop.

For each unfilled property, finds sources that declare they provide it,
tries them in trust-tier order, and takes the first value found.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.api.search_engine.config import PROPERTIES, SOURCES, TRUST_TIERS
from app.api.search_engine.handlers import SOURCE_HANDLERS
from app.api.search_engine.models import EnrichmentResult, PropertyResult

logger = logging.getLogger(__name__)


def _sources_for_property(prop: str, tier: str) -> list[dict]:
    """Return sources that provide `prop` and belong to `tier`."""
    return [
        s
        for s in SOURCES
        if s["trust_tier"] == tier
        and (prop in s["provides"] or "*" in s["provides"])
    ]


def run_enrichment(name: str, context: dict) -> EnrichmentResult:
    """Run the waterfall enrichment loop for a single material.

    Args:
        name: Normalized material name (e.g. "magnesium stearate").
        context: Dict with material_id, raw_sku, company_id, supplier_ids.

    Returns:
        EnrichmentResult with all properties filled or marked unknown.
    """
    filled: dict[str, PropertyResult] = {}

    for i, prop in enumerate(PROPERTIES, 1):
        logger.info("  [%d/%d] Property: %s", i, len(PROPERTIES), prop)
        found = False
        for tier in TRUST_TIERS:
            if found:
                break
            for source in _sources_for_property(prop, tier):
                handler = SOURCE_HANDLERS.get(source["name"])
                if handler is None:
                    continue
                logger.info("    Trying: %s (%s)", source["name"], tier)
                results = handler(name, context)
                for item in results:
                    if item["property"] == prop:
                        filled[prop] = PropertyResult(
                            value=item["value"],
                            confidence=source["trust_tier"],
                            source_name=source["name"],
                            source_url=item.get("source_url"),
                            raw_excerpt=item.get("raw_excerpt"),
                        )
                        found = True
                        logger.info("    ✓ Filled by %s (%s)", source["name"], tier)
                        break
                if found:
                    break

        if prop not in filled:
            filled[prop] = PropertyResult(
                value=None,
                confidence="unknown",
                source_name=None,
                source_url=None,
                raw_excerpt=None,
            )
            logger.info("    ✗ No source found")

    completeness = sum(
        1 for p in filled.values() if p.confidence != "unknown"
    )

    return EnrichmentResult(
        material_id=context["material_id"],
        raw_sku=context["raw_sku"],
        normalized_name=name,
        company_id=context["company_id"],
        supplier_ids=context.get("supplier_ids", []),
        enriched_at=datetime.now(timezone.utc).isoformat(),
        completeness=completeness,
        total_properties=len(PROPERTIES),
        properties=filled,
    )
