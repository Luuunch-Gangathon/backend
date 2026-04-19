"""Open Food Facts source handler — allergen, dietary, and certification data.

Queries the Open Food Facts search API and aggregates allergen/label tags
across the top matching products.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_OFF_SEARCH_URL = "https://world.openfoodfacts.net/cgi/search.pl"
_HEADERS = {"User-Agent": "SphereCast/1.0"}

_DIETARY_KEYWORDS = {"vegan", "vegetarian", "halal", "kosher"}
_CERTIFICATION_KEYWORDS = {"organic", "non-gmo", "fair-trade", "rainforest-alliance", "utz"}


def _clean_tag(tag: str) -> str:
    """Convert an OFF tag like `en:gluten-free` to `Gluten Free`.

    Strips the language prefix (anything up to and including the first colon),
    replaces hyphens with spaces, then applies title-case.
    """
    if ":" in tag:
        tag = tag.split(":", 1)[1]
    return tag.replace("-", " ").title()


def _contains_keyword(tag: str, keywords: set[str]) -> bool:
    """Return True if the bare tag (after stripping prefix) matches any keyword."""
    bare = tag.split(":", 1)[-1].lower()
    return bare in keywords


def _aggregate(products: list[dict]) -> dict[str, Any]:
    """Aggregate allergen and label data from a list of OFF product dicts.

    Returns a dict with keys:
        allergens_contains  – set of allergen tag strings found in allergens_tags
        allergens_free_from – set of allergen tag strings where product has
                              no_<allergen> labels  (OFF doesn't expose free-from
                              directly; we approximate via labels_tags)
        dietary_flags       – dict[str, bool] for dietary keywords seen in labels_tags
        certifications      – set of certification tag strings from labels_tags
    """
    allergen_set: set[str] = set()
    dietary: dict[str, bool] = {}
    cert_set: set[str] = set()

    for product in products:
        # --- allergens ---
        for tag in product.get("allergens_tags", []):
            cleaned = _clean_tag(tag)
            if cleaned:
                allergen_set.add(cleaned)

        # --- labels (dietary + certifications) ---
        for tag in product.get("labels_tags", []):
            bare = tag.split(":", 1)[-1].lower()
            if bare in _DIETARY_KEYWORDS:
                dietary[bare] = True
            # check certifications by substring since tags can be like "en:organic"
            # or multi-word like "en:rainforest-alliance-certified"
            for kw in _CERTIFICATION_KEYWORDS:
                if kw in bare:
                    cert_set.add(_clean_tag(tag))
                    break

    return {
        "allergens": sorted(allergen_set),
        "dietary_flags": dietary,
        "certifications": sorted(cert_set),
    }


def open_food_facts_enrich(name: str, context: dict) -> list[dict]:
    """Enrich ingredient with allergen, dietary, and certification data from Open Food Facts.

    Args:
        name: Ingredient / material name to search for.
        context: Unused by this handler (kept for interface consistency).

    Returns:
        List of property dicts (up to 3: allergens, dietary_flags, certifications).
        Returns an empty list when no products are found or on API error.
    """
    params = {
        "search_terms": name,
        "search_simple": "1",
        "json": "1",
        "page_size": "5",
    }

    try:
        response = httpx.get(_OFF_SEARCH_URL, params=params, headers=_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.warning("Open Food Facts API request failed for '%s' — %s", name, e)
        return []

    products: list[dict] = data.get("products", [])
    if not products:
        logger.info("Open Food Facts: no products found for '%s'", name)
        return []

    aggregated = _aggregate(products)

    source_url = (
        f"https://world.openfoodfacts.net/cgi/search.pl"
        f"?search_terms={name}&search_simple=1&json=1&page_size=5"
    )

    results: list[dict] = []

    # allergens
    allergens_list = aggregated["allergens"]
    if allergens_list:
        # OFF tags represent what IS in the product; we expose as "contains"
        results.append(
            {
                "property": "allergens",
                "value": {"contains": allergens_list, "free_from": []},
                "source_url": source_url,
            }
        )

    # dietary_flags
    dietary = aggregated["dietary_flags"]
    if dietary:
        results.append(
            {
                "property": "dietary_flags",
                "value": dietary,
                "source_url": source_url,
            }
        )

    # certifications
    certs = aggregated["certifications"]
    if certs:
        results.append(
            {
                "property": "certifications",
                "value": certs,
                "source_url": source_url,
            }
        )

    return results
