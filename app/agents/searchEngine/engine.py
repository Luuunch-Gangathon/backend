"""Enrichment engine — domain-agnostic waterfall loop.

For each unfilled property, finds sources that declare they provide it,
tries them in trust-tier order, and takes the first value found.

The engine is config-driven: callers pass properties, sources, handlers,
and a normalize_value function. This allows the same engine to enrich
both raw materials and finished products with different schemas.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable

from app.agents.searchEngine.models import EnrichmentResult, PropertyResult

logger = logging.getLogger(__name__)

TRUST_TIERS: list[str] = ["verified", "probable", "inferred", "speculative"]


def _sources_for_property(
    prop: str, tier: str, sources: list[dict],
) -> list[dict]:
    """Return sources that provide `prop` and belong to `tier`."""
    return [
        s
        for s in sources
        if s["trust_tier"] == tier
        and (prop in s["provides"] or "*" in s["provides"])
    ]


def run_enrichment(
    name: str,
    context: dict,
    *,
    properties: list[str] | None = None,
    sources: list[dict] | None = None,
    handlers: dict[str, Callable] | None = None,
    normalizer: Callable[[str, Any], Any] | None = None,
) -> EnrichmentResult:
    """Run the waterfall enrichment loop for a single entity.

    Each source handler is called at most once — its results are cached and
    reused across all properties it provides.

    Args:
        name: Normalized entity name (e.g. "magnesium stearate" or "Centrum Silver").
        context: Dict with material_id, raw_sku, company_id, supplier_ids.
        properties: Property keys to enrich. Defaults to material config.
        sources: Source definitions. Defaults to material config.
        handlers: Source name → handler function mapping. Defaults to material config.
        normalizer: Value normalizer function(prop, raw) -> normalized.
                    Defaults to material property_schema.normalize_value.

    Returns:
        EnrichmentResult with all properties filled or marked unknown.
    """
    # Lazy imports for backwards compatibility — material config is the default
    if properties is None:
        from app.agents.searchEngine.config import PROPERTIES
        properties = PROPERTIES
    if sources is None:
        from app.agents.searchEngine.config import SOURCES
        sources = SOURCES
    if handlers is None:
        from app.agents.searchEngine.handlers import SOURCE_HANDLERS
        handlers = SOURCE_HANDLERS
    if normalizer is None:
        from app.agents.searchEngine.property_schema import normalize_value
        normalizer = normalize_value

    raw_sku = context.get("raw_sku", "")
    supplier_names = context.get("supplier_names", [])
    logger.info("Enriching: %r (SKU: %s, suppliers: %s) — %d properties, %d sources",
                name, raw_sku or "n/a",
                ", ".join(supplier_names) if supplier_names else "none",
                len(properties), len(sources))

    filled: dict[str, PropertyResult] = {}

    # Cache: source_name -> list[dict] (handler results, called at most once)
    _handler_cache: dict[str, list[dict]] = {}

    for i, prop in enumerate(properties, 1):
        logger.info("  [%d/%d] Property: %s", i, len(properties), prop)
        found = False
        for tier in TRUST_TIERS:
            if found:
                break
            for source in _sources_for_property(prop, tier, sources):
                handler = handlers.get(source["name"])
                if handler is None:
                    continue

                # Call each handler at most once, reuse cached results
                if source["name"] not in _handler_cache:
                    logger.info("    Trying: %s (%s)", source["name"], tier)
                    # Inject which properties are still unfilled so handlers
                    # like llm_general_fallback can target only what's missing.
                    call_context = {
                        **context,
                        "missing_properties": [
                            p for p in properties if p not in filled
                        ],
                    }
                    _handler_cache[source["name"]] = handler(name, call_context)
                else:
                    logger.debug("    Reusing cached results from %s", source["name"])

                results = _handler_cache[source["name"]]
                for item in results:
                    if item["property"] == prop:
                        # Handler can override confidence (e.g. LLM self-assessed)
                        confidence = item.get("confidence", source["trust_tier"])
                        filled[prop] = PropertyResult(
                            value=normalizer(prop, item["value"]),
                            confidence=confidence,
                            source_name=source["name"],
                            source_url_or_reasoning=item.get("source_url") or item.get("reasoning"),
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
                source_url_or_reasoning=None,
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
        total_properties=len(properties),
        properties=filled,
    )


# ─── Pre-configured entry points ─────────────────────────────────────────────


def run_material_enrichment(name: str, context: dict) -> EnrichmentResult:
    """Enrich a raw material with the material config."""
    from app.agents.searchEngine.config import PROPERTIES, SOURCES
    from app.agents.searchEngine.handlers import SOURCE_HANDLERS
    from app.agents.searchEngine.property_schema import normalize_value

    return run_enrichment(
        name,
        context,
        properties=PROPERTIES,
        sources=SOURCES,
        handlers=SOURCE_HANDLERS,
        normalizer=normalize_value,
    )


def run_product_enrichment(name: str, context: dict) -> EnrichmentResult:
    """Enrich a finished product with the product config."""
    from app.agents.searchEngine.product_config import (
        PRODUCT_PROPERTIES,
        PRODUCT_SOURCES,
    )
    from app.agents.searchEngine.product_handlers import PRODUCT_SOURCE_HANDLERS
    from app.agents.searchEngine.product_property_schema import normalize_product_value

    return run_enrichment(
        name,
        context,
        properties=PRODUCT_PROPERTIES,
        sources=PRODUCT_SOURCES,
        handlers=PRODUCT_SOURCE_HANDLERS,
        normalizer=normalize_product_value,
    )


# ─── Shortened (demo) entry points ───────────────────────────────────────────


def run_material_enrichment_shortened(name: str, context: dict) -> EnrichmentResult:
    """Enrich a raw material with shortened sources (demo mode).

    supplier_website → llm_knowledge → llm_general_fallback only.
    """
    from app.agents.searchEngine.shortened_config import (
        SHORTENED_MATERIAL_PROPERTIES,
        SHORTENED_MATERIAL_SOURCES,
    )
    from app.agents.searchEngine.handlers import SOURCE_HANDLERS
    from app.agents.searchEngine.property_schema import normalize_value

    return run_enrichment(
        name,
        context,
        properties=SHORTENED_MATERIAL_PROPERTIES,
        sources=SHORTENED_MATERIAL_SOURCES,
        handlers=SOURCE_HANDLERS,
        normalizer=normalize_value,
    )


def run_product_enrichment_shortened(name: str, context: dict) -> EnrichmentResult:
    """Enrich a finished product with shortened sources (demo mode).

    open_food_facts_product → llm_knowledge_product → llm_general_fallback_product only.
    """
    from app.agents.searchEngine.shortened_config import (
        SHORTENED_PRODUCT_PROPERTIES,
        SHORTENED_PRODUCT_SOURCES,
    )
    from app.agents.searchEngine.product_handlers import PRODUCT_SOURCE_HANDLERS
    from app.agents.searchEngine.product_property_schema import normalize_product_value

    return run_enrichment(
        name,
        context,
        properties=SHORTENED_PRODUCT_PROPERTIES,
        sources=SHORTENED_PRODUCT_SOURCES,
        handlers=PRODUCT_SOURCE_HANDLERS,
        normalizer=normalize_product_value,
    )
