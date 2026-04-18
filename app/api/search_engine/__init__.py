"""Enrichment search engine — config-driven material property enrichment.

Usage:
    from app.api.search_engine import enrich
    from app.api.search_engine.storage import EnrichmentStore

    store = EnrichmentStore()
    result = enrich(raw_fields, store=store)
"""

from __future__ import annotations

from app.api.search_engine.engine import run_enrichment
from app.api.search_engine.models import EnrichmentResult
from app.api.search_engine.normalizer import normalize
from app.api.search_engine.storage import EnrichmentStore


def enrich(
    raw_fields: dict,
    store: EnrichmentStore | None = None,
) -> EnrichmentResult:
    """Enrich a raw material from DB fields.

    Args:
        raw_fields: Dict with keys Id, SKU, CompanyId, and optionally SupplierIds.
        store: Optional storage backend. If provided, result is persisted.

    Returns:
        EnrichmentResult with all properties filled or marked unknown.
    """
    context = normalize(raw_fields)
    result = run_enrichment(context["normalized_name"], context)

    if store is not None:
        store.save(result.model_dump())

    return result
