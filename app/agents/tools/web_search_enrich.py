"""web_search_enrich tool — discovers ingredient alternatives via web and persists embeddings."""
from __future__ import annotations

import logging

from app.services import web_search
from app.data import rag, repo

logger = logging.getLogger(__name__)


async def web_search_enrich(
    query: str,
    limit: int = 5,
    product_sku: str | None = None,
) -> list[str]:
    """Web-search the internet for candidate substitutes for `query`,
    persist each to substitution_groups with an embedding, return names added.

    If `product_sku` is provided, the product's aggregated dietary/allergen/
    certification profile is loaded and passed to the web search so the LLM
    filters alternatives that match the product's constraints (e.g. finding
    only vegan replacements for a vegan product).
    """
    product_profile: dict | None = None
    if product_sku:
        try:
            product_profile = await repo.get_product_dietary_profile(product_sku)
        except Exception:
            logger.exception(
                "web_search_enrich: failed to load product profile for %r", product_sku
            )

    candidates = await web_search.discover_alternatives(
        query, limit=limit, product_profile=product_profile
    )

    added: list[str] = []
    for candidate in candidates:
        name = candidate.get("normalized_name", "").strip()
        if not name:
            continue
        try:
            await rag.store_embedding(candidate)
            added.append(name)
        except Exception as exc:
            logger.warning("web_search_enrich: failed to store %r: %s", name, exc)

    logger.info("web_search_enrich: added %d new embeddings for query %r", len(added), query)
    return added
